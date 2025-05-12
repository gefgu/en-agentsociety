import asyncio
from datetime import datetime, timezone
from typing import Any, Optional, Union, cast

import jsonc
import ray

from ..agent import (Agent, AgentToolbox, BankAgentBase, CitizenAgentBase,
                     FirmAgentBase, GovernmentAgentBase, NBSAgentBase)
from ..agent.memory_config_generator import MemoryConfigGenerator
from ..configs import Config
from ..environment import Environment
from ..llm import LLM, init_embedding, monitor_requests
from ..logger import get_logger, set_logger_level
from ..memory import FaissQuery, Memory
from ..message import Messager, MessageIdentifier
from ..metrics import MlflowClient
from ..storage import AvroSaver
from ..storage.type import StorageProfile, StorageStatus
from .type import Logs

__all__ = ["AgentGroup"]


@ray.remote
class AgentGroup:
    def __init__(
        self,
        tenant_id: str,
        exp_name: str,
        exp_id: str,
        group_id: str,
        config: Config,
        agent_inits: list[
            tuple[
                int,
                type[
                    Union[
                        CitizenAgentBase,
                        FirmAgentBase,
                        BankAgentBase,
                        NBSAgentBase,
                        GovernmentAgentBase,
                    ]
                ],
                MemoryConfigGenerator,
                int,
                dict[str, Any],
            ]
        ],
        environment_init: dict,
        # PostgreSQL
        pgsql_writer: Optional[ray.ObjectRef],
        # Message Interceptor
        message_interceptor: ray.ObjectRef,
        # MLflow
        mlflow_run_id: Optional[str],
        # Others
        agent_config_file: Optional[dict[type[Agent], Any]] = None,
    ):
        """
        Initialize the AgentGroupV2.

        """
        set_logger_level(config.advanced.logging_level.upper())

        self._tenant_id = tenant_id
        self._exp_name = exp_name
        self._exp_id = exp_id
        self._group_id = group_id
        self._config = config
        self._agent_inits = agent_inits
        self._environment_init = environment_init
        self._pgsql_writer = pgsql_writer
        self._message_interceptor = message_interceptor
        self._mlflow_run_id = mlflow_run_id
        self._agent_config_file = agent_config_file
        self._embedding_model = init_embedding(config.advanced.embedding_model)
        self._faiss_query = FaissQuery(self._embedding_model)

        # typing definition
        self._llm: Optional[LLM] = None
        self._environment: Optional[Environment] = None
        self._messager: Optional[Messager] = None
        self._avro_saver: Optional[AvroSaver] = None
        self._mlflow_client: Optional[MlflowClient] = None

        self._agents: list[Agent] = []
        self._id2agent: dict[int, Agent] = {}
        self._message_dispatch_task: Optional[asyncio.Task] = None
        self._last_asyncio_pg_task: Optional[asyncio.Task] = None

    # ====================
    # Property Accessors
    # ====================
    @property
    def config(self):
        return self._config

    @property
    def embedding_model(self):
        return self._embedding_model

    @property
    def faiss_query(self):
        return self._faiss_query

    @property
    def llm(self):
        assert self._llm is not None, "llm is not initialized"
        return self._llm

    @property
    def environment(self):
        assert self._environment is not None, "environment is not initialized"
        return self._environment

    @property
    def messager(self):
        assert self._messager is not None, "messager is not initialized"
        return self._messager

    @property
    def agent_count(self):
        return len(self._agents)

    @property
    def agent_ids(self):
        return list(self._id2agent.keys())

    # ====================
    # Initialization Methods
    # ====================
    async def init(self):
        """Initialize the AgentGroupV2."""

        # ====================
        # Initialize LLM client
        # ====================
        get_logger().info(f"Initializing LLM client...")
        self._llm = LLM(self._config.llm)
        asyncio.create_task(monitor_requests(self._llm))
        get_logger().info(f"LLM client initialized")

        # ====================
        # Initialize environment
        # ====================
        get_logger().info(f"Initializing environment...")
        self._environment = Environment(**self._environment_init)
        self._environment.init()
        get_logger().info(f"Environment initialized")

        # ====================
        # Initialize messager
        # ====================
        get_logger().info(f"Initializing messager...")
        self._messager = Messager(
            self._config.env.redis, self._exp_id, self._message_interceptor
        )
        await self._messager.init()
        get_logger().info(f"Messager initialized")

        # ====================
        # Initialize the avro saver
        # ====================
        if self._config.env.avro.enabled:
            get_logger().info(f"Initializing the avro saver...")
            self._avro_saver = AvroSaver(
                self._config.env.avro, self._exp_id, self._group_id
            )
            get_logger().info(f"Avro saver initialized")

        # ====================
        # Initialize the mlflow
        # ====================
        if self._config.env.mlflow.enabled:
            get_logger().info(f"Initializing the mlflow...")
            self._mlflow_client = MlflowClient(
                config=self._config.env.mlflow,
                exp_name=self._exp_name,
                exp_id=self._exp_id,
                current_run_id=self._mlflow_run_id,
            )
            get_logger().info(f"Mlflow initialized")

        # ====================================
        # Initialize the agents
        # ====================================
        get_logger().info(f"Initializing the agents...")
        agent_toolbox = AgentToolbox(
            self.llm,
            self.environment,
            self.messager,
            self._avro_saver,
            self._pgsql_writer,
            self._mlflow_client,
        )
        for agent_init in self._agent_inits:
            (
                id,
                agent_class,
                memory_config_generator,
                index_for_generator,
                param_config,
            ) = agent_init
            memory_dict = memory_config_generator.generate(index_for_generator)
            extra_attributes = memory_dict.get("extra_attributes", {})
            profile = memory_dict.get("profile", {})
            base = memory_dict.get("base", {})
            memory_init = Memory(
                agent_id=id,
                environment=self.environment,
                faiss_query=self.faiss_query,
                embedding_model=self.embedding_model,
                config=extra_attributes,
                profile=profile,
                base=base,
            )
            agent = agent_class(
                id=id,
                name=f"{agent_class.__name__}_{id}",
                toolbox=agent_toolbox,
                memory=memory_init,
            )
            # load_from_config
            if param_config is not None:
                agent.load_from_config(param_config)
            self._agents.append(agent)
            self._id2agent[id] = agent
        get_logger().info(
            f"-----Initializing by running agent.init() in AgentGroup {self._group_id} ..."
        )
        tasks = []
        channels = []
        for agent in self._agents:
            tasks.append(agent.init())
            channels.append(f"exps:{self._exp_id}:agents:{agent.id}:*")
        await asyncio.gather(*tasks)
        await self.messager.subscribe_and_start_listening(channels)
        self._message_dispatch_task = asyncio.create_task(self._message_dispatch())
        get_logger().info(
            f"-----Initializing by exporting profiles in AgentGroup {self._group_id} ..."
        )
        profiles = []
        for agent in self._agents:
            profile = await agent.status.profile.export()
            profile = profile[0]
            profile["id"] = agent.id
            profiles.append(
                StorageProfile(
                    id=agent.id,
                    name=profile.get("name", ""),
                    profile=jsonc.dumps(
                        {k: v for k, v in profile.items() if k not in {"id", "name"}},
                        ensure_ascii=False,
                    ),
                )
            )
        if self._avro_saver is not None:
            self._avro_saver.append_profiles(profiles)
        if self._pgsql_writer is not None:
            await self._pgsql_writer.write_profiles.remote(profiles)  # type:ignore
        get_logger().info(
            f"-----Initializing embeddings in AgentGroup {self._group_id} ..."
        )
        embedding_tasks = []
        for agent in self._agents:
            embedding_tasks.append(agent.memory.initialize_embeddings())
        await asyncio.gather(*embedding_tasks)

        get_logger().info(f"Agents initialized")

    async def close(self):
        """Close the AgentGroupV2."""

        if self._message_dispatch_task is not None:
            self._message_dispatch_task.cancel()
            try:
                await self._message_dispatch_task
            except asyncio.CancelledError:
                pass
            self._message_dispatch_task = None

        if self._mlflow_client is not None:
            self._mlflow_client.close()
            self._mlflow_client = None

        if self._avro_saver is not None:
            self._avro_saver.close()
            self._avro_saver = None

        if self._messager is not None:
            await self._messager.close()
            self._messager = None

        if self._environment is not None:
            self._environment.close()
            self._environment = None

        if self._llm is not None:
            await self._llm.close()
            self._llm = None

    # ====================
    # Reset Methods
    # ====================
    async def reset(self):
        """Reset all agents in the group."""
        reset_tasks = []
        for agent in self._agents:
            reset_tasks.append(agent.reset())
        await asyncio.gather(*reset_tasks)

    # ====================
    # Core Functionality Methods
    # ====================
    async def step(self, tick: int):
        """
        Executes a single simulation step by running all agents concurrently.

        - **Description**:
            - This method initiates the `run` coroutine for each agent in parallel using asyncio.gather.
            - Any exceptions raised during the execution are caught, logged, and re-raised as a RuntimeError.

        - **Raises**:
            - `RuntimeError`: If an exception occurs during the execution of any agent's `run` method.
        """
        self.environment.set_tick(tick)
        try:
            tasks = [agent.run() for agent in self._agents]
            agent_time_log = await asyncio.gather(*tasks)
            simulator_log = (
                self.environment.get_log_list()
                + self.environment.economy_client.get_log_list()
            )
            group_logs = Logs(
                llm_log=self.llm.get_log_list(),
                redis_log=self.messager.get_log_list(),
                simulator_log=simulator_log,
                agent_time_log=agent_time_log,
            )
            self.llm.clear_log_list()
            self.messager.clear_log_list()
            self.environment.clear_log_list()
            self.environment.economy_client.clear_log_list()
            return group_logs
        except Exception as e:
            import traceback

            get_logger().error(f"Simulator Error: {str(e)}\n{traceback.format_exc()}")
            raise RuntimeError(str(e)) from e

    async def react_to_intervention(
        self, intervention_message: str, agent_ids: list[int]
    ):
        """
        React to an intervention.
        """
        react_tasks = []
        for agent in self._agents:
            if agent.id in agent_ids:
                react_tasks.append(agent.react_to_intervention(intervention_message))
        await asyncio.gather(*react_tasks)

    # ====================
    # Message Handling Methods
    # ====================
    async def _message_dispatch(self):
        """
        Dispatches messages received via Redis to the appropriate agents.

        - **Description**:
            - Continuously listens for incoming Redis messages and dispatches them to the relevant agents based on the topic.
            - Messages are expected to have a topic formatted as "exps:{exp_id}:agents:{agent.id}:{topic_type}".
            - The payload is decoded from bytes to string and then parsed as JSON.
            - Depending on the `topic_type`, different handler methods on the agent are called to process the message.
        """
        get_logger().info(f"-----Starting message dispatch for group {self._group_id}")
        while True:
            # Step 1: Fetch messages
            messages = await self.messager.fetch_messages()
            if len(messages) > 0:
                get_logger().info(
                    f"Group {self._group_id} received {len(messages)} messages"
                )
            else:
                get_logger().debug(
                    f"Group {self._group_id} received no messages, waiting..."
                )

            try:
                # Step 2: Distribute messages to corresponding Agents
                for message in messages:
                    channel = cast(bytes, message["channel"]).decode("utf-8")
                    payload = cast(bytes, message["data"])
                    payload = jsonc.loads(payload.decode("utf-8"))

                    # Extract agent_id (channel format is "exps:{exp_id}:agents:{agent_id}:{topic_type}")
                    _, _, _, agent_id, topic_type = channel.strip(":").split(":")
                    agent_id = int(agent_id)
                    if agent_id in self._id2agent:
                        agent = self._id2agent[agent_id]
                        # topic_type: agent-chat, user-chat, user-survey, gather
                        if topic_type == "agent-chat":
                            await agent.handle_agent_chat_message(payload)
                        elif topic_type == "user-chat":
                            await agent.handle_user_chat_message(payload)
                        elif topic_type == "user-survey":
                            await agent.handle_user_survey_message(payload)
                        elif topic_type == "gather":
                            await agent.handle_gather_message(payload)
            except Exception as e:
                get_logger().error(f"Error dispatching message: {e}")
                import traceback

                get_logger().error(
                    f"Error dispatching message: {traceback.format_exc()}"
                )
            await asyncio.sleep(3)

    # ====================
    # Status Management Methods
    # ====================
    async def save(self, day: int, t: int):
        """
        Saves the current status of the agents at a given point in the simulation.

        - **Args**:
            - `day` (int): The day number in the simulation time.
            - `t` (int): The tick or time unit within the simulation day.

        - **Raises**:
            - `RuntimeError`: If an exception occurs while saving the status.
        """
        try:
            await self.save_status(day, t)
        except Exception as e:
            import traceback

            get_logger().error(f"Simulator Error: {str(e)}\n{traceback.format_exc()}")
            raise RuntimeError(
                str(e) + f" input arg day:({day}, {type(day)}), t:({t}, {type(t)})"
            ) from e

    async def save_status(self, day: int, t: int):
        """
        Saves the current status of the agents at a given point in the simulation.

        - **Args**:
            - `day` (int): The day number in the simulation time.
            - `t` (int): The tick or time unit in the simulation day.
        """
        if self._avro_saver is None and self._pgsql_writer is None:
            return
        created_at = datetime.now(timezone.utc)
        # =========================
        # build statuses data
        # =========================
        statuses = []
        for agent in self._agents:
            if isinstance(agent, CitizenAgentBase):
                position = await agent.status.get("position")
                x = position["xy_position"]["x"]
                y = position["xy_position"]["y"]
                lng, lat = self.environment.projector(x, y, inverse=True)
                if "aoi_position" in position:
                    parent_id = position["aoi_position"]["aoi_id"]
                elif "lane_position" in position:
                    parent_id = position["lane_position"]["lane_id"]
                else:
                    parent_id = None
                hunger_satisfaction = await agent.status.get("hunger_satisfaction")
                energy_satisfaction = await agent.status.get("energy_satisfaction")
                safety_satisfaction = await agent.status.get("safety_satisfaction")
                social_satisfaction = await agent.status.get("social_satisfaction")
                current_need = await agent.status.get("current_need", "None")
                current_plan = await agent.status.get("current_plan")
                if current_plan is not None and current_plan:
                    intention = current_plan.get("target", "Other")
                    step_index = current_plan.get("index", 0)
                    action = current_plan.get("steps", [])[step_index].get(
                        "intention", "Planning"
                    )
                else:
                    intention = "Other"
                    action = "Planning"
                emotion = await agent.status.get("emotion", {})
                emotion_types = await agent.status.get("emotion_types", "")
                sadness = emotion.get("sadness", 0)
                joy = emotion.get("joy", 0)
                fear = emotion.get("fear", 0)
                disgust = emotion.get("disgust", 0)
                anger = emotion.get("anger", 0)
                surprise = emotion.get("surprise", 0)
                friend_ids = await agent.status.get("friends", [])
                status = StorageStatus(
                    id=agent.id,
                    day=day,
                    t=t,
                    lng=lng,
                    lat=lat,
                    parent_id=parent_id,
                    friend_ids=friend_ids,
                    action=action,
                    status=jsonc.dumps(
                        {
                            "hungry": hunger_satisfaction,
                            "tired": energy_satisfaction,
                            "safe": safety_satisfaction,
                            "social": social_satisfaction,
                            "sadness": sadness,
                            "joy": joy,
                            "fear": fear,
                            "disgust": disgust,
                            "anger": anger,
                            "surprise": surprise,
                            "emotion_types": emotion_types,
                            "current_need": current_need,
                            "intention": intention,
                        },
                        ensure_ascii=False,
                    ),
                    created_at=created_at,
                )
                statuses.append(status)
            elif isinstance(
                agent, (FirmAgentBase, BankAgentBase, NBSAgentBase, GovernmentAgentBase)
            ):
                nominal_gdp = await agent.status.get("nominal_gdp", [])
                real_gdp = await agent.status.get("real_gdp", [])
                unemployment = await agent.status.get("unemployment", [])
                wages = await agent.status.get("wages", [])
                prices = await agent.status.get("prices", [])
                inventory = await agent.status.get("inventory", 0)
                price = await agent.status.get("price", 0.0)
                interest_rate = await agent.status.get("interest_rate", 0.0)
                bracket_cutoffs = await agent.status.get("bracket_cutoffs", [])
                bracket_rates = await agent.status.get("bracket_rates", [])
                employees = await agent.status.get("employees", [])
                status = StorageStatus(
                    id=agent.id,
                    day=day,
                    t=t,
                    lng=None,
                    lat=None,
                    parent_id=None,
                    friend_ids=[],
                    action="",
                    status=jsonc.dumps(
                        {
                            "nominal_gdp": nominal_gdp,
                            "real_gdp": real_gdp,
                            "unemployment": unemployment,
                            "wages": wages,
                            "prices": prices,
                            "inventory": inventory,
                            "price": price,
                            "interest_rate": interest_rate,
                            "bracket_cutoffs": bracket_cutoffs,
                            "bracket_rates": bracket_rates,
                            "employees": employees,
                        },
                        ensure_ascii=False,
                    ),
                    created_at=created_at,
                )
                statuses.append(status)
            else:
                raise ValueError(f"Unknown agent type: {type(agent)}")
        if self._avro_saver is not None:
            self._avro_saver.append_statuses(statuses)
        if self._pgsql_writer is not None:
            if self._last_asyncio_pg_task is not None:
                await self._last_asyncio_pg_task
            self._last_asyncio_pg_task = (
                self._pgsql_writer.write_statuses.remote(  # type:ignore
                    statuses
                )
            )

    async def update_environment(self, key: str, value: str):
        """
        Update the environment variables for the simulation and all agent groups.

        - **Args**:
            - `key` (str): The environment variable key to update.
            - `value` (str): The new value for the environment variable.
        """
        self.environment.update_environment(key, value)

    async def update(self, target_agent_id: int, target_key: str, content: Any):
        """
        Updates a specific key in the status of a targeted agent.

        - **Args**:
            - `target_agent_id` (int): The ID of the agent to update.
            - `target_key` (str): The key in the agent's status to update.
            - `content` (Any): The new value for the specified key.
        """
        get_logger().debug(
            f"-----Updating {target_key} for agent {target_agent_id} in group {self._group_id}"
        )
        agent = self._id2agent[target_agent_id]
        await agent.status.update(target_key, content)

    # ====================
    # Utility Methods
    # ====================
    def get_llm_consumption(self):
        """
        Retrieves the consumption statistics from the LLM client.

        - **Returns**:
            - The consumption data provided by the LLM client.
        """
        return self.llm.get_consumption()

    async def get_llm_error_statistics(self):
        """
        Retrieves the error statistics from the LLM client.
        """
        return self.llm.get_error_statistics()

    async def filter(
        self,
        types: Optional[tuple[type[Agent]]] = None,
        keys: Optional[list[str]] = None,
        values: Optional[list[Any]] = None,
    ) -> list[int]:
        """
        Filters agents based on type and/or key-value pairs in their status.

        - **Args**:
            - `types` (Optional[List[Type[Agent]]]): A list of agent types to filter by.
            - `keys` (Optional[List[str]]): A list of keys to check in the agent's status.
            - `values` (Optional[List[Any]]): The corresponding values for each key in the `keys` list.

        - **Returns**:
            - `List[int]`: A list of agent IDs for agents that match the filter criteria.
        """
        filtered_ids = []
        for agent in self._agents:
            add = True
            if types:
                if isinstance(agent, types):
                    if keys:
                        for key in keys:
                            assert values is not None
                            if agent.status.get(key) != values[keys.index(key)]:
                                add = False
                                break
                    if add:
                        filtered_ids.append(agent.id)
            elif keys:
                for key in keys:
                    assert values is not None
                    if agent.status.get(key) != values[keys.index(key)]:
                        add = False
                        break
                if add:
                    filtered_ids.append(agent.id)
        return filtered_ids

    async def gather(self, content: str, target_agent_ids: Optional[list[int]] = None):
        """
        Gathers specific content from all or targeted agents within the group.

        - **Args**:
            - `content` (str): The key of the status content to gather from the agents.
            - `target_agent_ids` (Optional[List[int]]): A list of agent IDs to target. If None, targets all agents.

        - **Returns**:
            - `Dict[str, Any]`: A dictionary mapping agent IDs to the gathered content.
        """
        get_logger().debug(
            f"-----Gathering {content} from all agents in group {self._group_id}"
        )
        results = {}
        if target_agent_ids is None:
            target_agent_ids = list(self._id2agent.keys())
        if content == "stream_memory":
            for agent in self._agents:
                if agent.id in target_agent_ids:
                    results[agent.id] = await agent.stream.get_all()
        else:
            for agent in self._agents:
                if agent.id in target_agent_ids:
                    results[agent.id] = await agent.status.get(content)
        return results
    async def forward_message(self, validation_dict: MessageIdentifier):
        """
        Forward the message to the channel if the message is valid.
        """
        await self.messager.forward(validation_dict)
