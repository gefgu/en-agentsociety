"""
A clear version of the simulation.
"""

import asyncio
import inspect
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Literal, Optional, cast

import ray
import ray.util.queue
import yaml

from ..agent import Agent
from ..agent.distribution import (Distribution, DistributionConfig,
                                  DistributionType)
from ..agent.memory_config_generator import MemoryConfigGenerator
from ..configs import (AgentConfig, Config, MetricExtractorConfig, MetricType,
                       WorkflowType)
from ..environment import EnvironmentStarter
from ..logger import get_logger, set_logger_level
from ..message import MessageInterceptor, Messager
from ..message.message_interceptor import MessageBlockListenerBase
from ..metrics import MlflowClient
from ..s3 import S3Config
from ..storage import AvroSaver
from ..storage.pgsql import PgWriter
from ..storage.type import StorageExpInfo, StorageGlobalPrompt
from ..survey.models import Survey
from ..utils import NONE_SENDER_ID
from .agentgroup import AgentGroup
from .type import ExperimentStatus, Logs

__all__ = ["AgentSociety"]


def _init_agent_class(agent_config: AgentConfig, s3config: S3Config):
    """
    Initialize the agent class.

    - **Args**:
        - `agent_config` (AgentConfig): The agent configuration.

    - **Returns**:
        - `agents`: A list of tuples, each containing an agent class, a memory config generator, and an index.
    """
    agent_class = agent_config.agent_class
    n = agent_config.number
    # memory config function
    memory_config_func = cast(
        Callable[
            [dict[str, Distribution]],
            tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
        ],
        agent_config.memory_config_func,
    )
    generator = MemoryConfigGenerator(
        memory_config_func,
        agent_config.memory_from_file,
        (
            agent_config.memory_distributions
            if agent_config.memory_distributions is not None
            else {}
        ),
        s3config,
    )
    # lazy generate memory values
    # param config
    param_config = agent_config.param_config
    agents = [(agent_class, generator, i, param_config) for i in range(n)]
    return agents


class AgentSociety:
    def __init__(
        self,
        config: Config,
        tenant_id: str = "",
    ) -> None:
        config.set_auto_workers()
        self._config = config
        self.tenant_id = tenant_id

        # ====================
        # Initialize the logger
        # ====================
        set_logger_level(self._config.advanced.logging_level.upper())

        self.exp_id = str(config.exp.id)
        get_logger().info(
            f"Creating AgentSociety with config: {self._config.model_dump()} as exp_id={self.exp_id}"
        )

        # typing definition
        self._environment: Optional[EnvironmentStarter] = None
        self._message_interceptor: Optional[ray.ObjectRef] = None
        self._message_interceptor_listener: Optional[MessageBlockListenerBase] = None
        self._messager: Optional[Messager] = None
        self._avro_saver: Optional[AvroSaver] = None
        self._mlflow: Optional[MlflowClient] = None
        self._pgsql_writers: list[ray.ObjectRef] = []
        self._groups: dict[str, ray.ObjectRef] = {}
        self._agent_ids: set[int] = set()
        self._agent_id2group: dict[int, ray.ObjectRef] = {}
        yaml_config = yaml.dump(
            self._config.model_dump(
                exclude_defaults=True,
                exclude_none=True,
                exclude={
                    "llm": {
                        "__all__": {"api_key": True},
                    },
                    "env": {
                        "redis": True,
                        "pgsql": {"dsn": True},
                        "mlflow": {
                            "username": True,
                            "password": True,
                            "mlflow_uri": True,
                        },
                        "s3": True,
                    },
                },
            ),
            allow_unicode=True,
        )
        self._exp_info: StorageExpInfo = StorageExpInfo(
            id=self.exp_id,
            tenant_id=self.tenant_id,
            name=self.name,
            num_day=0,
            status=0,
            cur_day=0,
            cur_t=0.0,
            config=yaml_config,
            error="",
            input_tokens=0,
            output_tokens=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._total_steps: int = 0

    async def init(self):
        """Initialize all the components"""

        # ====================
        # Initialize the environment
        # ====================
        get_logger().info(f"Initializing environment...")
        self._environment = EnvironmentStarter(
            self._config.map,
            self._config.advanced.simulator,
            self._config.exp.environment,
            self._config.env.s3,
        )
        await self._environment.init()
        get_logger().info(f"Environment initialized")

        # ====================
        # Initialize the messager
        # ====================
        get_logger().info(f"Initializing messager...")
        if self._config.exp.message_intercept is not None:
            queue = ray.util.queue.Queue()
            self._message_interceptor = MessageInterceptor.remote(
                blocks=self._config.exp.message_intercept.blocks,  # type: ignore
                llm_config=self._config.llm,
                queue=queue,
                public_network=self._config.exp.message_intercept.public_network,
                private_network=self._config.exp.message_intercept.private_network,
                black_set=set(),
            )
            await self._message_interceptor.init.remote()  # type: ignore
            assert (
                self._config.exp.message_intercept.listener is not None
            ), "listener is not set"
            self._message_interceptor_listener = (
                self._config.exp.message_intercept.listener(
                    queue=queue,
                )
            )
            self._message_interceptor_listener.init()
        self._messager = Messager(
            config=self._config.env.redis,
            exp_id=self.exp_id,
            message_interceptor=self._message_interceptor,
        )
        await self._messager.init()
        await self._messager.subscribe_and_start_listening(
            [self._messager.get_user_payback_channel()]
        )
        get_logger().info(f"Messager initialized")

        # ====================
        # Initialize the avro saver
        # ====================
        if self._config.env.avro.enabled:
            get_logger().info(f"Initializing avro saver...")
            self._avro_saver = AvroSaver(
                config=self._config.env.avro,
                exp_id=self.exp_id,
                group_id=None,
            )
            get_logger().info(f"Avro saver initialized")

        # ====================
        # Initialize the mlflow
        # ====================
        if self._config.env.mlflow.enabled:
            get_logger().info(f"Initializing mlflow...")
            self._mlflow = MlflowClient(
                config=self._config.env.mlflow,
                exp_name=self.name,
                exp_id=self.exp_id,
            )
            get_logger().info(f"Mlflow initialized")

        # ====================
        # Initialize the pgsql writer
        # ====================
        if self._config.env.pgsql.enabled:
            assert self._config.env.pgsql.num_workers != "auto"
            get_logger().info(
                f"Initializing {self._config.env.pgsql.num_workers} pgsql writers..."
            )
            self._pgsql_writers = [
                PgWriter.remote(
                    self.tenant_id, self.exp_id, self._config.env.pgsql.dsn, (i == 0)
                )
                for i in range(self._config.env.pgsql.num_workers)
            ]
            get_logger().info(
                f"{self._config.env.pgsql.num_workers} pgsql writers initialized"
            )
        # ======================================
        # Initialize agent groups
        # ======================================
        agents = []  # (id, agent_class, generator, memory_index)
        next_id = 1
        group_size = self._config.advanced.group_size
        get_logger().info(f"Initializing agent groups (size={group_size})...")
        citizen_ids = set()
        bank_ids = set()
        nbs_ids = set()
        government_ids = set()
        firm_ids = set()
        aoi_ids = self._environment.get_aoi_ids()
        for agent_config in self._config.agents.firms:
            if agent_config.memory_distributions is None:
                agent_config.memory_distributions = {}
            assert (
                "aoi_id" not in agent_config.memory_distributions
            ), "aoi_id is not allowed to be set in memory_distributions because it will be generated in the initialization"
            agent_config.memory_distributions["aoi_id"] = DistributionConfig(
                dist_type=DistributionType.CHOICE,
                choices=list(aoi_ids),
            )
            firm_classes = _init_agent_class(agent_config, self._config.env.s3)
            firms = [
                (next_id + i, *firm_class) for i, firm_class in enumerate(firm_classes)
            ]
            firm_ids.update([firm[0] for firm in firms])
            agents += firms
            next_id += len(firms)
        for agent_config in self._config.agents.banks:
            bank_classes = _init_agent_class(agent_config, self._config.env.s3)
            banks = [
                (next_id + i, *bank_class) for i, bank_class in enumerate(bank_classes)
            ]
            bank_ids.update([bank[0] for bank in banks])
            agents += banks
            next_id += len(banks)
        for agent_config in self._config.agents.nbs:
            nbs_classes = _init_agent_class(agent_config, self._config.env.s3)
            nbs = [(next_id + i, *nbs_class) for i, nbs_class in enumerate(nbs_classes)]
            nbs_ids.update([nbs[0] for nbs in nbs])
            agents += nbs
            next_id += len(nbs)
        for agent_config in self._config.agents.governments:
            government_classes = _init_agent_class(agent_config, self._config.env.s3)
            governments = [
                (next_id + i, *government_class)
                for i, government_class in enumerate(government_classes)
            ]
            government_ids.update([government[0] for government in governments])
            agents += governments
            next_id += len(governments)
        for agent_config in self._config.agents.citizens:
            # append distribution for firm_id, bank_id, nbs_id, government_id, home_aoi_id, work_aoi_id
            if agent_config.memory_distributions is None:
                agent_config.memory_distributions = {}
            assert (
                "firm_id" not in agent_config.memory_distributions
            ), "firm_id is not allowed to be set in memory_distributions because it will be generated in the initialization"
            agent_config.memory_distributions["firm_id"] = DistributionConfig(
                dist_type=DistributionType.CHOICE,
                choices=list(firm_ids),
            )
            assert (
                "bank_id" not in agent_config.memory_distributions
            ), "bank_id is not allowed to be set in memory_distributions because it will be generated in the initialization"
            agent_config.memory_distributions["bank_id"] = DistributionConfig(
                dist_type=DistributionType.CHOICE,
                choices=list(bank_ids),
            )
            assert (
                "nbs_id" not in agent_config.memory_distributions
            ), "nbs_id is not allowed to be set in memory_distributions because it will be generated in the initialization"
            agent_config.memory_distributions["nbs_id"] = DistributionConfig(
                dist_type=DistributionType.CHOICE,
                choices=list(nbs_ids),
            )
            assert (
                "government_id" not in agent_config.memory_distributions
            ), "government_id is not allowed to be set in memory_distributions because it will be generated in the initialization"
            agent_config.memory_distributions["government_id"] = DistributionConfig(
                dist_type=DistributionType.CHOICE,
                choices=list(government_ids),
            )
            assert (
                "home_aoi_id" not in agent_config.memory_distributions
            ), "home_aoi_id is not allowed to be set in memory_distributions because it will be generated in the initialization"
            agent_config.memory_distributions["home_aoi_id"] = DistributionConfig(
                dist_type=DistributionType.CHOICE,
                choices=list(aoi_ids),
            )
            assert (
                "work_aoi_id" not in agent_config.memory_distributions
            ), "work_aoi_id is not allowed to be set in memory_distributions because it will be generated in the initialization"
            agent_config.memory_distributions["work_aoi_id"] = DistributionConfig(
                dist_type=DistributionType.CHOICE,
                choices=list(aoi_ids),
            )
            citizen_classes = _init_agent_class(agent_config, self._config.env.s3)
            citizens = [
                (next_id + i, *citizen_class)
                for i, citizen_class in enumerate(citizen_classes)
            ]
            citizen_ids.update([citizen[0] for citizen in citizens])
            next_id += len(citizens)
            agents += citizens
        get_logger().info(
            f"agents: len(citizens)={len(citizen_ids)}, len(firms)={len(firm_ids)}, len(banks)={len(bank_ids)}, len(nbs)={len(nbs_ids)}, len(governments)={len(government_ids)}"
        )
        self._agent_ids = set([agent[0] for agent in agents])
        self._environment.economy_client.set_ids(
            citizen_ids=citizen_ids,
            firm_ids=firm_ids,
            bank_ids=bank_ids,
            nbs_ids=nbs_ids,
            government_ids=government_ids,
        )
        environment_init = self._environment.to_init_args()
        assert group_size != "auto"
        for i in range(0, len(agents), group_size):
            group_agents = agents[i : i + group_size]
            group_id = str(uuid.uuid4())
            self._groups[group_id] = AgentGroup.remote(
                tenant_id=self.tenant_id,  # type:ignore
                exp_name=self.name,
                exp_id=self.exp_id,
                group_id=group_id,
                config=self._config,
                agent_inits=group_agents,
                environment_init=environment_init,
                message_interceptor=self._messager.message_interceptor,
                pgsql_writer=(
                    self._pgsql_writers[i % len(self._pgsql_writers)]
                    if len(self._pgsql_writers) > 0
                    else None
                ),
                mlflow_run_id=self._mlflow.run_id if self._mlflow is not None else None,
            )
            for agent_id, _, _, _, _ in group_agents:
                self._agent_id2group[agent_id] = self._groups[group_id]
        get_logger().info(
            f"groups: len(self._groups)={len(self._groups)}, waiting for groups to init..."
        )
        await asyncio.gather(
            *[group.init.remote() for group in self._groups.values()]  # type:ignore
        )
        get_logger().info(f"Agent groups initialized")
        # step 1 tick to make the initialization complete
        await self.environment.step(1)
        get_logger().info(f"run 1 tick to make the initialization complete")

        # ===================================
        # save the experiment info
        # ===================================
        await self._save_exp_info()
        get_logger().info(f"Experiment info saved")

        # ===================================
        # run init functions
        # ===================================
        init_funcs = self._config.agents.init_funcs
        for init_func in init_funcs:
            if inspect.iscoroutinefunction(init_func):
                await init_func(self)
            else:
                init_func(self)
        get_logger().info(f"Init functions run")
        get_logger().info(f"Simulation initialized")

    async def close(self):
        """Close all the components"""

        # ===================================
        # close groups
        # ===================================

        get_logger().info(f"Closing agent groups...")
        close_tasks = []
        for group in self._groups.values():
            close_tasks.append(group.close.remote())  # type:ignore
        await asyncio.gather(*close_tasks)
        get_logger().info(f"Agent groups closed")

        if self._mlflow is not None:
            get_logger().info(f"Closing mlflow...")
            self._mlflow.close()
            self._mlflow = None
            get_logger().info(f"Mlflow closed")

        if self._avro_saver is not None:
            get_logger().info(f"Closing avro saver...")
            self._avro_saver.close()
            self._avro_saver = None
            get_logger().info(f"Avro saver closed")

        if self._message_interceptor is not None:
            get_logger().info(f"Closing message interceptor...")
            await self._message_interceptor.close.remote()  # type: ignore
            self._message_interceptor = None
            get_logger().info(f"Message interceptor closed")

        if self._message_interceptor_listener is not None:
            get_logger().info(f"Closing message interceptor listener...")
            await self._message_interceptor_listener.close()
            self._message_interceptor_listener = None
            get_logger().info(f"Message interceptor listener closed")

        if self._messager is not None:
            get_logger().info(f"Closing messager...")
            await self._messager.close()
            self._messager = None
            get_logger().info(f"Messager closed")

        if self._environment is not None:
            get_logger().info(f"Closing environment...")
            await self._environment.close()
            self._environment = None
            get_logger().info(f"Environment closed")

    @property
    def name(self):
        return self._config.exp.name

    @property
    def config(self):
        return self._config

    @property
    def enable_avro(self):
        return self._config.env.avro.enabled

    @property
    def enable_pgsql(self):
        return self._config.env.pgsql.enabled

    @property
    def environment(self):
        assert self._environment is not None, "environment is not initialized"
        return self._environment

    @property
    def messager(self):
        assert self._messager is not None, "messager is not initialized"
        return self._messager

    @property
    def mlflow_client(self):
        assert self._mlflow is not None, "mlflow is not initialized"
        return self._mlflow

    async def gather(
        self,
        content: str,
        target_agent_ids: Optional[list[int]] = None,
        flatten: bool = False,
    ):
        """
        Collect specific information from agents.

        - **Description**:
            - Asynchronously gathers specified content from targeted agents within all groups.

        - **Args**:
            - `content` (str): The information to collect from the agents.
            - `target_agent_ids` (Optional[List[int]], optional): A list of agent IDs to target. Defaults to None, meaning all agents are targeted.
            - `flatten` (bool, optional): Whether to flatten the result. Defaults to False.

        - **Returns**:
            - Result of the gathering process as returned by each group's `gather` method.
        """
        gather_tasks = []
        for group in self._groups.values():
            gather_tasks.append(
                group.gather.remote(content, target_agent_ids)  # type:ignore
            )
        results = await asyncio.gather(*gather_tasks)
        if flatten:
            data_flatten = []
            for group_data in results:
                for _, data in group_data.items():
                    data_flatten.append(data)
            return data_flatten
        else:
            return results

    async def filter(
        self,
        types: Optional[tuple[type[Agent]]] = None,
        keys: Optional[list[str]] = None,
        values: Optional[list[Any]] = None,
    ) -> list[int]:
        """
        Filter out agents of specified types or with matching key-value pairs.

        - **Args**:
            - `types` (Optional[Tuple[Type[Agent]]], optional): Types of agents to filter for. Defaults to None.
            - `keys` (Optional[List[str]], optional): Keys to match in agent attributes. Defaults to None.
            - `values` (Optional[List[Any]], optional): Values corresponding to keys for matching. Defaults to None.

        - **Raises**:
            - `ValueError`: If neither types nor keys and values are provided, or if the lengths of keys and values do not match.

        - **Returns**:
            - `List[int]`: A list of filtered agent UUIDs.
        """
        if not types and not keys and not values:
            return list(self._agent_ids)
        filtered_ids = []
        if keys:
            if values is None or len(keys) != len(values):
                raise ValueError("the length of key and value does not match")
            for group in self._groups.values():
                filtered_ids.extend(
                    await group.filter.remote(types, keys, values)  # type:ignore
                )
            return filtered_ids
        else:
            for group in self._groups.values():
                filtered_ids.extend(await group.filter.remote(types))  # type:ignore
            return filtered_ids

    async def update_environment(self, key: str, value: str):
        """
        Update the environment variables for the simulation and all agent groups.

        - **Args**:
            - `key` (str): The environment variable key to update.
            - `value` (str): The new value for the environment variable.
        """
        self.environment.update_environment(key, value)
        await asyncio.gather(
            *[
                group.update_environment.remote(key, value)  # type:ignore
                for group in self._groups.values()
            ]
        )

    async def update(self, target_agent_ids: list[int], target_key: str, content: Any):
        """
        Update the memory of specified agents.

        - **Args**:
            - `target_agent_id` (list[int]): The IDs of the target agents to update.
            - `target_key` (str): The key in the agent's memory to update.
            - `content` (Any): The new content to set for the target key.
        """
        tasks = []
        for id in target_agent_ids:
            group = self._agent_id2group[id]
            tasks.append(group.update.remote(id, target_key, content))  # type:ignore
        await asyncio.gather(*tasks)

    async def economy_update(
        self,
        target_agent_id: int,
        target_key: str,
        content: Any,
        mode: Literal["replace", "merge"] = "replace",
    ):
        """
        Update economic data for a specified agent.

        - **Args**:
            - `target_agent_id` (int): The ID of the target agent whose economic data to update.
            - `target_key` (str): The key in the agent's economic data to update.
            - `content` (Any): The new content to set for the target key.
            - `mode` (Literal["replace", "merge"], optional): Mode of updating the economic data. Defaults to "replace".
        """
        await self.environment.economy_client.update(
            id=target_agent_id, key=target_key, value=content, mode=mode
        )

    async def send_survey(
        self,
        survey: Survey,
        agent_ids: list[int] = [],
        poll_interval: float = 3,
        timeout: float = -1,
    ):
        """
        Send a survey to specified agents.

        - **Args**:
            - `survey` (Survey): The survey object to send.
            - `agent_ids` (List[int], optional): List of agent IDs to receive the survey. Defaults to an empty list.
            - `poll_interval` (float, optional): The interval to poll for messages. Defaults to 3 seconds.
            - `timeout` (float, optional): The timeout for the survey. Defaults to -1 (no timeout).

        - **Returns**:
            - None
        """
        survey_dict = survey.to_dict()
        _date_time = datetime.now(timezone.utc)
        payload = {
            "from": NONE_SENDER_ID,
            "survey_id": survey_dict["id"],
            "timestamp": int(_date_time.timestamp() * 1000),
            "data": survey_dict,
            "_date_time": _date_time,
        }
        tasks = []
        for id in agent_ids:
            channel = self.messager.get_user_survey_channel(id)
            tasks.append(self.messager.send_message(channel, payload))
        await asyncio.gather(*tasks)
        remain_payback = len(agent_ids)
        start_t = time.time()
        while True:
            messages = await self.messager.fetch_messages()
            get_logger().info(f"Received {len(messages)} payback messages [survey]")
            remain_payback -= len(messages)
            if remain_payback <= 0:
                break
            await asyncio.sleep(poll_interval)
            if timeout > 0:
                if time.time() - start_t > timeout:
                    get_logger().warning(f"Survey timeout after {timeout} seconds")
                    break

    async def send_interview_message(
        self,
        content: str,
        agent_ids: list[int],
        poll_interval: float = 3,
        timeout: float = -1,
    ):
        """
        Send an interview message to specified agents.

        - **Args**:
            - `content` (str): The content of the message to send.
            - `agent_ids` (list[int]): A list of IDs for the agents to receive the message.
            - `poll_interval` (float, optional): The interval to poll for messages. Defaults to 3 seconds.
            - `timeout` (float, optional): The timeout for the survey. Defaults to -1 (no timeout).

        - **Returns**:
            - None
        """
        _date_time = datetime.now(timezone.utc)
        payload = {
            "from": NONE_SENDER_ID,
            "content": content,
            "timestamp": int(_date_time.timestamp() * 1000),
            "_date_time": _date_time,
        }
        tasks = []
        for id in agent_ids:
            channel = self.messager.get_user_chat_channel(id)
            tasks.append(self.messager.send_message(channel, payload))
        await asyncio.gather(*tasks)
        remain_payback = len(agent_ids)
        start_t = time.time()
        while True:
            messages = await self.messager.fetch_messages()
            get_logger().info(f"Received {len(messages)} payback messages [interview]")
            remain_payback -= len(messages)
            if remain_payback <= 0:
                break
            await asyncio.sleep(poll_interval)
            if timeout > 0:
                if time.time() - start_t > timeout:
                    get_logger().warning(f"Interview timeout after {timeout} seconds")
                    break

    async def send_intervention_message(
        self, intervention_message: str, agent_ids: list[int]
    ):
        """
        Send an intervention message to specified agents.

        - **Description**:
            - Send an intervention message to specified agents.

        - **Args**:
            - `intervention_message` (str): The content of the intervention message to send.
            - `agent_ids` (list[int]): A list of agent IDs to receive the intervention message.
        """
        tasks = []
        for group in self._groups.values():
            tasks.append(
                group.react_to_intervention.remote(  # type:ignore
                    intervention_message, agent_ids
                )
            )
        await asyncio.gather(*tasks)

    async def extract_metric(self, metric_extractors: list[MetricExtractorConfig]):
        """
        Extract metrics using provided extractors.

        - **Description**:
            - Asynchronously applies each metric extractor function to the simulation to collect various metrics.

        - **Args**:
            - `metric_extractors` (List[MetricExtractorConfig]): A list of MetricExtractorConfig for extracting metrics from the simulation.

        - **Returns**:
            - None
        """
        for metric_extractor in metric_extractors:
            if metric_extractor.type == MetricType.FUNCTION:
                if metric_extractor.func is not None:
                    await metric_extractor.func(self)
                else:
                    raise ValueError("func is not set for metric extractor")
            elif metric_extractor.type == MetricType.STATE:
                assert metric_extractor.key is not None
                values = await self.gather(
                    metric_extractor.key, metric_extractor.target_agent, flatten=True
                )
                if values is None or len(values) == 0:
                    get_logger().warning(
                        f"No values found for metric extractor {metric_extractor.key} in extraction step {metric_extractor.extract_time}"
                    )
                    return
                if type(values[0]) == float or type(values[0]) == int:
                    if metric_extractor.method == "mean":
                        value = sum(values) / len(values)
                    elif metric_extractor.method == "sum":
                        value = sum(values)
                    elif metric_extractor.method == "max":
                        value = max(values)
                    elif metric_extractor.method == "min":
                        value = min(values)
                    else:
                        raise ValueError(
                            f"method {metric_extractor.method} is not supported"
                        )
                    assert (
                        self.mlflow_client is not None
                        and metric_extractor.key is not None
                    )
                    await self.mlflow_client.log_metric(
                        key=metric_extractor.key,
                        value=value,
                        step=metric_extractor.extract_time,
                    )
                else:
                    raise ValueError(f"values type {type(values[0])} is not supported")
            metric_extractor.extract_time += 1

    async def _save_exp_info(self) -> None:
        """Async save experiment info to YAML file and pgsql"""
        self._exp_info.updated_at = datetime.now(timezone.utc)
        if self.enable_avro:
            assert self._avro_saver is not None
            with open(self._avro_saver.exp_info_file, "w") as f:
                yaml.dump(
                    self._exp_info.model_dump(exclude_defaults=True, exclude_none=True),
                    f,
                    allow_unicode=True,
                )
        if self.enable_pgsql:
            assert self._pgsql_writers is not None
            worker: ray.ObjectRef = self._pgsql_writers[0]
            await worker.update_exp_info.remote(self._exp_info)  # type: ignore

    async def _save_global_prompt(self, prompt: str, day: int, t: float):
        """Save global prompt"""
        prompt_info = StorageGlobalPrompt(
            day=day,
            t=t,
            prompt=prompt,
            created_at=datetime.now(timezone.utc),
        )
        if self.enable_avro:
            assert self._avro_saver is not None
            self._avro_saver.append_global_prompt(prompt_info)
        if self.enable_pgsql:
            worker: ray.ObjectRef = self._pgsql_writers[0]
            await worker.write_global_prompt.remote(prompt_info)  # type:ignore

    async def next_round(self):
        """
        Proceed to the next round of the simulation.
        """
        get_logger().info("Start entering the next round of the simulation")
        tasks = []
        for group in self._groups.values():
            tasks.append(group.reset.remote())  # type:ignore
        await asyncio.gather(*tasks)
        await self.environment.step(1)
        get_logger().info("Finished entering the next round of the simulation")

    async def step(self, num_environment_ticks: int = 1) -> Logs:
        """
        Execute one step of the simulation where each agent performs its forward action.

        - **Description**:
            - Checks if new agents need to be inserted based on the current day of the simulation. If so, it inserts them.
            - Executes the forward method for each agent group to advance the simulation by one step.
            - Saves the state of all agent groups after the step has been completed.
            - Optionally extracts metrics if the current step matches the interval specified for any metric extractors.

        - **Args**:
            - `num_environment_ticks` (int): The number of ticks for the environment to step forward.

        - **Raises**:
            - `RuntimeError`: If there is an error during the execution of the step, it logs the error and rethrows it as a RuntimeError.

        - **Returns**:
            - `Logs`: The logs of the simulation.
        """
        try:
            # ======================
            # run a step
            # ======================
            day, t = self.environment.get_datetime()
            get_logger().info(
                f"Start simulation day {day} at {t}, step {self._total_steps}"
            )
            tick = self.environment.get_tick()
            tasks = []
            for group in self._groups.values():
                tasks.append(group.step.remote(tick))  # type:ignore
            logs: list[Logs] = await asyncio.gather(*tasks)
            get_logger().debug(f"({day}-{t}) Finished agent forward steps")
            # ======================
            # log the simulation results
            # ======================
            all_logs = Logs(
                llm_log=[],
                redis_log=[],
                simulator_log=[],
                agent_time_log=[],
            )
            for log in logs:
                all_logs.append(log)
            # ======================
            # save the experiment info
            # ======================
            self._exp_info.status = ExperimentStatus.RUNNING.value
            self._exp_info.cur_day = day
            self._exp_info.cur_t = t
            for log in all_logs.llm_log:
                self._exp_info.input_tokens += log["input_tokens"]
                self._exp_info.output_tokens += log["output_tokens"]
            await self._save_exp_info()
            # ======================
            # save the simulation results
            # ======================
            save_tasks = []
            for group in self._groups.values():
                save_tasks.append(group.save.remote(day, t))  # type:ignore
            await asyncio.gather(*save_tasks)
            # save global prompt
            await self._save_global_prompt(
                prompt=self.environment.get_environment(),
                day=day,
                t=t,
            )
            get_logger().debug(f"({day}-{t}) Finished saving simulation results")
            # ======================
            # extract metrics
            # ======================
            if self.config.exp.metric_extractors is not None:
                to_execute_metric = []
                for metric_extractor in self.config.exp.metric_extractors:
                    if self._total_steps % metric_extractor.step_interval == 0:
                        if metric_extractor.type == MetricType.FUNCTION:
                            to_execute_metric.append(metric_extractor)
                        elif metric_extractor.type == MetricType.STATE:
                            # For STATE type, we need to gather data from target agents
                            to_execute_metric.append(metric_extractor)

                if to_execute_metric:
                    await self.extract_metric(to_execute_metric)
                get_logger().debug(f"({day}-{t}) Finished extracting metrics")
            # ======================
            # forward message
            # ======================
            message_intercept_config = self.config.exp.message_intercept
            if message_intercept_config is not None:
                if message_intercept_config.forward_strategy == "outer_control":
                    interceptor = self._message_interceptor
                    assert (
                        interceptor is not None
                    ), "Message interceptor must be set when using `outer_control` strategy"
                    validation_dict = await interceptor.get_validation_dict.remote()  # type: ignore
                    # TODO(yanjunbo): implement the logic of outer control
                    validation_dict, blocked_agent_ids, blocked_social_edges = None, None, None  # type: ignore
                    interceptor.update_blocked_agent_ids.remote(blocked_agent_ids)  # type: ignore
                    interceptor.update_blocked_social_edges.remote(blocked_social_edges)  # type: ignore
                    # TODO(yanjunbo): modify validation_dict based on blocked_agent_ids and blocked_social_edges
                    message_tasks = [self.messager.forward(validation_dict)]
                    message_tasks.extend(
                        [
                            group.forward_message.remote(validation_dict)  # type: ignore
                            for group in self._groups.values()
                        ]
                    )
                    await asyncio.gather(*message_tasks)
            else:
                message_tasks = [self.messager.forward()]
                message_tasks.extend(
                    [
                        group.forward_message.remote(None)  # type: ignore
                        for group in self._groups.values()
                    ]
                )
                await asyncio.gather(*message_tasks)
            # ======================
            # go to next step
            # ======================
            self._total_steps += 1
            await self.environment.step(num_environment_ticks)
            get_logger().debug(f"({day}-{t}) Finished simulator sync")
            return all_logs
        except Exception as e:
            get_logger().error(f"Simulation error: {str(e)}\n{traceback.format_exc()}")
            raise RuntimeError(str(e)) from e

    async def run_one_day(
        self,
        ticks_per_step: int,
    ):
        """
        Run the simulation for a day.

        - **Args**:
            - `ticks_per_step` (int): The number of ticks per step.

        - **Description**:
            - Updates the experiment status to running and sets up monitoring for the experiment's status.
            - Runs the simulation loop until the end time, which is calculated based on the current time and the number of days to simulate.
            - After completing the simulation, updates the experiment status to finished, or to failed if an exception occurs.

        - **Raises**:
            - `RuntimeError`: If there is an error during the simulation, it logs the error and updates the experiment status to failed before rethrowing the exception.

        - **Returns**:
            - None
        """
        logs = Logs(
            llm_log=[],
            redis_log=[],
            simulator_log=[],
            agent_time_log=[],
        )
        start_day, _ = self.environment.get_datetime()
        while True:
            this_logs = await self.step(ticks_per_step)
            logs.append(this_logs)
            day, _ = self.environment.get_datetime()
            if day != start_day:
                break
        return logs

    async def run(self):
        """
        Run the simulation following the workflow in the config.
        """
        logs = Logs(
            llm_log=[],
            redis_log=[],
            simulator_log=[],
            agent_time_log=[],
        )
        try:
            for step in self.config.exp.workflow:
                get_logger().info(
                    f"Running workflow: type: {step.type} - description: {step.description}"
                )
                if step.type == WorkflowType.STEP:
                    for _ in range(step.steps):
                        log = await self.step(step.ticks_per_step)
                        logs.append(log)
                elif step.type == WorkflowType.RUN:
                    days = int(step.days)
                    remain = step.days - days
                    for _ in range(days):
                        log = await self.run_one_day(step.ticks_per_step)
                        logs.append(log)
                    if remain > 0.001:
                        ticks_remain = int(remain * 24 * 60 * 60 / step.ticks_per_step)
                        for _ in range(ticks_remain):
                            log = await self.step(step.ticks_per_step)
                            logs.append(log)
                elif step.type == WorkflowType.INTERVIEW:
                    target_agents = step.target_agent
                    interview_message = step.interview_message
                    assert interview_message is not None
                    assert target_agents is not None
                    await self.send_interview_message(interview_message, target_agents)
                elif step.type == WorkflowType.SURVEY:
                    assert step.target_agent is not None
                    assert step.survey is not None
                    await self.send_survey(step.survey, step.target_agent)
                elif step.type == WorkflowType.ENVIRONMENT_INTERVENE:
                    assert step.key is not None
                    assert step.value is not None
                    await self.update_environment(step.key, step.value)
                elif step.type == WorkflowType.UPDATE_STATE_INTERVENE:
                    assert step.key is not None
                    assert step.value is not None
                    assert step.target_agent is not None
                    await self.update(step.target_agent, step.key, step.value)
                elif step.type == WorkflowType.MESSAGE_INTERVENE:
                    assert step.intervene_message is not None
                    assert step.target_agent is not None
                    await self.send_intervention_message(
                        step.intervene_message, step.target_agent
                    )
                elif step.type == WorkflowType.NEXT_ROUND:
                    await self.next_round()
                elif step.type == WorkflowType.INTERVENE:
                    get_logger().warning(
                        "MESSAGE_INTERVENE is not fully implemented yet, it can only influence the congnition of target agents"
                    )
                    assert step.target_agent is not None
                    assert step.intervene_message is not None
                    await self.send_intervention_message(
                        step.intervene_message, step.target_agent
                    )
                elif step.type == WorkflowType.FUNCTION:
                    assert step.func is not None
                    await step.func(self)
                else:
                    raise ValueError(f"Unknown workflow type: {step.type}")
        except Exception as e:
            get_logger().error(f"Simulation error: {str(e)}\n{traceback.format_exc()}")
            self._exp_info.status = ExperimentStatus.ERROR.value
            self._exp_info.error = str(e)
            await self._save_exp_info()

            raise RuntimeError(str(e)) from e
        self._exp_info.status = ExperimentStatus.FINISHED.value
        await self._save_exp_info()
        return logs
