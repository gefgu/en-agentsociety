"""
A clear version of the simulation.
"""

import asyncio
import inspect
import itertools
import json
import os
import traceback
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Literal, Optional, Union, cast

import ray
import ray.util.queue
import yaml

from ..agent import Agent, AgentToolbox, StatusAttribute, SupervisorBase
from ..agent.distribution import (Distribution, DistributionConfig,
                                  DistributionType)
from ..agent.memory_config_generator import (MemoryConfigGenerator,
                                             default_memory_config_citizen,
                                             default_memory_config_supervisor)
from ..configs import (AgentConfig, AgentFilterConfig, Config,
                       MetricExtractorConfig, MetricType, WorkflowType)
from ..environment import EnvironmentStarter
from ..llm import LLM, monitor_requests
from ..llm.embeddings import init_embedding
from ..logger import get_logger, set_logger_level
from ..memory import FaissQuery, Memory
from ..message import Message, MessageInterceptor, MessageKind, Messager
from ..s3 import S3Config
from ..storage import DatabaseWriter
from ..storage.type import (StorageExpInfo, StorageGlobalPrompt,
                            StoragePendingSurvey)
from ..survey.models import Survey
from ..utils import NONE_SENDER_ID
from .agentgroup import AgentGroup
from .type import ExperimentStatus, Logs

__all__ = ["AgentSociety"]

MIN_ID = 1
MAX_ID = 100000000


def _set_default_agent_config(self: Config):
    """
    Validates configuration options to ensure the user selects the correct combination.
    - **Description**:
        - If citizens contains at least one CITIZEN type agent, automatically fills
            empty institution agent lists with default configurations.
        - Sets default memory_config_func for citizen agents if not specified.

    - **Returns**:
        - `AgentsConfig`: The validated configuration instance.
    """
    # Set default memory config function for citizens
    for agent_config in self.agents.citizens:
        if agent_config.memory_config_func is None:
            agent_config.memory_config_func = default_memory_config_citizen

    if self.agents.supervisor is not None:
        if self.agents.supervisor.memory_config_func is None:
            self.agents.supervisor.memory_config_func = default_memory_config_supervisor

    return self


def _init_agent_class(agent_config: AgentConfig, s3config: S3Config):
    """
    Initialize the agent class.

    - **Args**:
        - `agent_config` (AgentConfig): The agent configuration.

    - **Returns**:
        - `agents`: A list of tuples, each containing an agent class, a memory config generator, and an index.
    """
    agent_class: type[Agent] = agent_config.agent_class  # type: ignore
    n: int = agent_config.number  # type: ignore
    # memory config function
    memory_config_func = cast(
        Callable[
            [dict[str, Distribution], Optional[list[StatusAttribute]]],
            tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
        ],
        agent_config.memory_config_func,
    )
    generator = MemoryConfigGenerator(
        memory_config_func,
        agent_class.StatusAttributes,
        agent_config.number,
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
    agent_params = agent_config.agent_params
    if agent_params is None:
        agent_params = agent_class.ParamsType()
    else:
        agent_params = agent_class.ParamsType.model_validate(agent_params)
    blocks = agent_config.blocks
    agents = [(agent_class, generator, i, agent_params, blocks) for i in range(n)]
    return agents, generator


def evaluate_filter(filter_str: str, profile: dict) -> bool:
    """
    Evaluate a filter string against a profile dictionary.
    
    - **Args**:
        - `filter_str` (str): The filter string to evaluate, e.g. "${profile.age} > 0"
        - `profile` (dict): The profile dictionary to evaluate against
        
    - **Returns**:
        - `bool`: True if the filter matches, False otherwise
        
    - **Note**:
        - Returns False if profile is empty
        - Returns False if any key in filter_str is not in profile
    """
    # if profile is empty, return False
    if not profile:
        return False
        
    # check if all keys in filter_str are in profile
    import re
    pattern = r'\${profile\.([^}]+)}'
    required_keys = set(re.findall(pattern, filter_str))
    
    # if any required key is not in profile, return False
    for key in required_keys:
        # Handle nested keys
        current = profile
        for part in key.split('.'):
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
    
    # replace all ${profile.xxx} with actual values
    for key in required_keys:
        # Get the value by traversing the nested dictionary
        current = profile
        for part in key.split('.'):
            current = current[part]
        filter_str = filter_str.replace(f"${{profile.{key}}}", repr(current))
    
    # use eval to execute the expression
    try:
        return eval(filter_str)
    except Exception:
        return False


class AgentSociety:
    def __init__(
        self,
        config: Config,
        tenant_id: str = "",
    ) -> None:
        config.set_auto_workers()
        self._config = _set_default_agent_config(config)
        self.tenant_id = tenant_id

        # ====================
        # Initialize the logger
        # ====================
        set_logger_level(self._config.advanced.logging_level.upper())

        self.exp_id = str(config.exp.id)
        get_logger().debug(
            f"Creating AgentSociety with config: {self._config.model_dump()} as exp_id={self.exp_id}"
        )

        # typing definition
        self._environment: Optional[EnvironmentStarter] = None
        self._message_interceptor: Optional[MessageInterceptor] = None
        self._database_writer: Optional[ray.ObjectRef] = None
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
                        "db": {"pg_dsn": True},
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
        self._messager = None

        # simulation context - for information dump
        self.context = {}

        # filter base
        self._filter_base = {}

    async def init(self):
        """Initialize all the components"""
        # ====================
        # Initialize the pgsql writer
        # ====================
        if self._config.env.db.enabled:
            get_logger().info(f"Initializing database writer...")
            self._database_writer = DatabaseWriter.remote(
                self.tenant_id,
                self.exp_id,
                self._config.env.db,
                self._config.env.home_dir,
            )
            await self._database_writer.init.remote() # type: ignore
            get_logger().info(f"Database writer initialized")
            # save to local
            self._database_writer.update_exp_info.remote(self._exp_info) # type: ignore

        try:
            # ====================
            # Initialize the LLM
            # ====================
            get_logger().info(f"Initializing LLM...")
            self._llm = LLM(self._config.llm)
            asyncio.create_task(monitor_requests(self._llm))
            get_logger().info(f"LLM initialized")

            # ====================
            # Initialize the environment
            # ====================
            get_logger().info(f"Initializing environment...")
            self._environment = EnvironmentStarter(
                self._config.map,
                self._config.advanced.simulator,
                self._config.exp.environment,
                self._config.env.s3,
                os.path.join(self._config.env.home_dir, "exps", self.tenant_id, self.exp_id, "simulator_log"),
            )
            await self._environment.init()
            get_logger().info(f"Environment initialized")

            # ====================
            # Initialize the messager
            # ====================
            get_logger().info(f"Initializing messager...")
            if self._config.agents.supervisor is not None:
                self._message_interceptor = MessageInterceptor(
                    self._config.llm,
                )
                await self._message_interceptor.init()
            self._messager = Messager(exp_id=self.exp_id)
            await self._messager.init()
            get_logger().info(f"Messager initialized")

            # ======================================
            # Initialize agent groups
            # ======================================
            agents = []  # (id, agent_class, generator, memory_index)
            next_id = 1
            defined_ids = set()  # used to check if the id is already defined

            def _find_next_id():
                nonlocal next_id  # Declare that we want to modify the outer variable
                while next_id in defined_ids:
                    next_id += 1
                if next_id > MAX_ID:
                    raise ValueError(f"Agent ID {next_id} is greater than MAX_ID {MAX_ID}")
                defined_ids.add(next_id)
                return next_id

            group_size = self._config.advanced.group_size
            get_logger().info(f"Initializing agent groups (size={group_size})...")
            citizen_ids = set()
            bank_ids = set()
            nbs_ids = set()
            government_ids = set()
            firm_ids = set()
            supervisor_ids = set()
            aoi_ids = self._environment.get_aoi_ids()

            self._embedding_model = init_embedding(self._config.advanced.embedding_model)
            get_logger().debug(f"Embedding model initialized")
            self._faiss_query = FaissQuery(self._embedding_model)
            get_logger().debug(f"FAISS query initialized")

            # Check if any agent config uses memory_from_file
            agent_configs_normal = {
                "firms": [],
                "banks": [],
                "nbs": [],
                "governments": [],
                "citizens": [],
                "supervisor": [],
            }
            agent_configs_from_file = {
                "firms": [],
                "banks": [],
                "nbs": [],
                "governments": [],
                "citizens": [],
                "supervisor": [],
            }
            for agent_config in self._config.agents.firms:
                if agent_config.memory_from_file is None:
                    agent_configs_normal["firms"].append(agent_config)
                else:
                    agent_configs_from_file["firms"].append(agent_config)
            for agent_config in self._config.agents.banks:
                if agent_config.memory_from_file is None:
                    agent_configs_normal["banks"].append(agent_config)
                else:
                    agent_configs_from_file["banks"].append(agent_config)
            for agent_config in self._config.agents.nbs:
                if agent_config.memory_from_file is None:
                    agent_configs_normal["nbs"].append(agent_config)
                else:
                    agent_configs_from_file["nbs"].append(agent_config)
            for agent_config in self._config.agents.governments:
                if agent_config.memory_from_file is None:
                    agent_configs_normal["governments"].append(agent_config)
                else:
                    agent_configs_from_file["governments"].append(agent_config)
            for agent_config in self._config.agents.citizens:
                if agent_config.memory_from_file is None:
                    agent_configs_normal["citizens"].append(agent_config)
                else:
                    agent_configs_from_file["citizens"].append(agent_config)
            if self._config.agents.supervisor is not None:
                agent_config = self._config.agents.supervisor
                if agent_config.memory_from_file is None:
                    agent_configs_normal["supervisor"] = [agent_config]
                else:
                    agent_configs_from_file["supervisor"] = [agent_config]

            citizen_generators = []
            # Step 1: Process all agents with memory_from_file
            # Firms
            for agent_config in agent_configs_from_file["firms"]:
                agent_class = agent_config.agent_class
                agent_params = agent_config.agent_params
                if agent_params is None:
                    agent_params = agent_class.ParamsType()
                else:
                    agent_params = agent_class.ParamsType.model_validate(agent_params)
                blocks = agent_config.blocks
                # Create generator
                generator = MemoryConfigGenerator(
                    agent_config.memory_config_func,  # type: ignore
                    agent_config.agent_class.StatusAttributes,  # type: ignore
                    agent_config.number,
                    agent_config.memory_from_file,
                    (
                        agent_config.memory_distributions
                        if agent_config.memory_distributions is not None
                        else {}
                    ),
                    self._config.env.s3,
                )
                # Get agent data from file
                agent_data = generator.get_agent_data_from_file()
                # Extract IDs from agent data
                for agent_datum in agent_data:
                    agent_id = agent_datum.get("id")
                    assert agent_id is not None, "id is required in memory_from_file[Firms]"
                    assert agent_id >= MIN_ID, f"id {agent_id} is less than MIN_ID {MIN_ID}"
                    assert (
                        agent_id <= MAX_ID
                    ), f"id {agent_id} is greater than MAX_ID {MAX_ID}"
                    assert agent_id not in defined_ids, f"id {agent_id} is already defined"
                    defined_ids.add(agent_id)
                    firm_ids.add(agent_id)
                    agents.append(
                        (
                            agent_id,
                            agent_class,
                            generator,
                            agent_data.index(agent_datum),
                            agent_params,
                            blocks,
                        )
                    )

            # Banks
            for agent_config in agent_configs_from_file["banks"]:
                agent_class = agent_config.agent_class
                agent_params = agent_config.agent_params
                if agent_params is None:
                    agent_params = agent_class.ParamsType()
                else:
                    agent_params = agent_class.ParamsType.model_validate(agent_params)
                blocks = agent_config.blocks
                generator = MemoryConfigGenerator(
                    agent_config.memory_config_func,  # type: ignore
                    agent_config.agent_class.StatusAttributes,  # type: ignore
                    agent_config.number,
                    agent_config.memory_from_file,
                    (
                        agent_config.memory_distributions
                        if agent_config.memory_distributions is not None
                        else {}
                    ),
                    self._config.env.s3,
                )
                agent_data = generator.get_agent_data_from_file()
                for agent_datum in agent_data:
                    agent_id = agent_datum.get("id")
                    assert agent_id is not None, "id is required in memory_from_file[Banks]"
                    assert agent_id >= MIN_ID, f"id {agent_id} is less than MIN_ID {MIN_ID}"
                    assert (
                        agent_id <= MAX_ID
                    ), f"id {agent_id} is greater than MAX_ID {MAX_ID}"
                    assert agent_id not in defined_ids, f"id {agent_id} is already defined"
                    defined_ids.add(agent_id)
                    bank_ids.add(agent_id)
                    agents.append(
                        (
                            agent_id,
                            agent_class,
                            generator,
                            agent_data.index(agent_datum),
                            agent_params,
                            blocks,
                        )
                    )

            # NBS
            for agent_config in agent_configs_from_file["nbs"]:
                agent_class = agent_config.agent_class
                agent_params = agent_config.agent_params
                if agent_params is None:
                    agent_params = agent_class.ParamsType()
                else:
                    agent_params = agent_class.ParamsType.model_validate(agent_params)
                blocks = agent_config.blocks
                generator = MemoryConfigGenerator(
                    agent_config.memory_config_func,  # type: ignore
                    agent_config.agent_class.StatusAttributes,  # type: ignore
                    agent_config.number,
                    agent_config.memory_from_file,
                    (
                        agent_config.memory_distributions
                        if agent_config.memory_distributions is not None
                        else {}
                    ),
                    self._config.env.s3,
                )
                agent_data = generator.get_agent_data_from_file()
                for agent_datum in agent_data:
                    agent_id = agent_datum.get("id")
                    assert agent_id is not None, "id is required in memory_from_file[NBS]"
                    assert agent_id >= MIN_ID, f"id {agent_id} is less than MIN_ID {MIN_ID}"
                    assert (
                        agent_id <= MAX_ID
                    ), f"id {agent_id} is greater than MAX_ID {MAX_ID}"
                    assert agent_id not in defined_ids, f"id {agent_id} is already defined"
                    defined_ids.add(agent_id)
                    nbs_ids.add(agent_id)
                    agents.append(
                        (
                            agent_id,
                            agent_class,
                            generator,
                            agent_data.index(agent_datum),
                            agent_params,
                            blocks,
                        )
                    )

            # Governments
            for agent_config in agent_configs_from_file["governments"]:
                agent_class = agent_config.agent_class
                agent_params = agent_config.agent_params
                if agent_params is None:
                    agent_params = agent_class.ParamsType()
                else:
                    agent_params = agent_class.ParamsType.model_validate(agent_params)
                blocks = agent_config.blocks
                generator = MemoryConfigGenerator(
                    agent_config.memory_config_func,  # type: ignore
                    agent_config.agent_class.StatusAttributes,  # type: ignore
                    agent_config.number,
                    agent_config.memory_from_file,
                    (
                        agent_config.memory_distributions
                        if agent_config.memory_distributions is not None
                        else {}
                    ),
                    self._config.env.s3,
                )
                agent_data = generator.get_agent_data_from_file()
                for agent_datum in agent_data:
                    agent_id = agent_datum.get("id")
                    assert (
                        agent_id is not None
                    ), "id is required in memory_from_file[Governments]"
                    assert agent_id >= MIN_ID, f"id {agent_id} is less than MIN_ID {MIN_ID}"
                    assert (
                        agent_id <= MAX_ID
                    ), f"id {agent_id} is greater than MAX_ID {MAX_ID}"
                    assert agent_id not in defined_ids, f"id {agent_id} is already defined"
                    defined_ids.add(agent_id)
                    government_ids.add(agent_id)
                    agents.append(
                        (
                            agent_id,
                            agent_class,
                            generator,
                            agent_data.index(agent_datum),
                            agent_params,
                            blocks,
                        )
                    )

            # Citizens
            for agent_config in agent_configs_from_file["citizens"]:
                agent_class = agent_config.agent_class
                agent_params = agent_config.agent_params
                if agent_params is None:
                    agent_params = agent_class.ParamsType()
                else:
                    agent_params = agent_class.ParamsType.model_validate(agent_params)
                blocks = agent_config.blocks
                generator = MemoryConfigGenerator(
                    agent_config.memory_config_func,  # type: ignore
                    agent_config.agent_class.StatusAttributes,  # type: ignore
                    agent_config.number,
                    agent_config.memory_from_file,
                    (
                        agent_config.memory_distributions
                        if agent_config.memory_distributions is not None
                        else {}
                    ),
                    self._config.env.s3,
                )
                citizen_generators.append(generator)
                agent_data = generator.get_agent_data_from_file()
                for agent_datum in agent_data:
                    agent_id = agent_datum.get("id")
                    assert (
                        agent_id is not None
                    ), "id is required in memory_from_file[Citizens]"
                    assert agent_id >= MIN_ID, f"id {agent_id} is less than MIN_ID {MIN_ID}"
                    assert (
                        agent_id <= MAX_ID
                    ), f"id {agent_id} is greater than MAX_ID {MAX_ID}"
                    assert agent_id not in defined_ids, f"id {agent_id} is already defined"
                    defined_ids.add(agent_id)
                    citizen_ids.add(agent_id)
                    agents.append(
                        (
                            agent_id,
                            agent_class,
                            generator,
                            agent_data.index(agent_datum),
                            agent_params,
                            blocks,
                        )
                    )

            # Supervisor
            # ATTENTION: will not be initialized in AgentGroup
            assert (
                len(agent_configs_from_file["supervisor"]) <= 1
            ), "only one or zero supervisor is allowed"
            supervisor: Optional[SupervisorBase] = None
            for agent_config in agent_configs_from_file["supervisor"]:
                generator = MemoryConfigGenerator(
                    agent_config.memory_config_func,  # type: ignore
                    agent_config.agent_class.StatusAttributes,  # type: ignore
                    agent_config.number,
                    agent_config.memory_from_file,
                    (
                        agent_config.memory_distributions
                        if agent_config.memory_distributions is not None
                        else {}
                    ),
                    self._config.env.s3,
                )
                agent_data = generator.get_agent_data_from_file()
                for agent_datum in agent_data:
                    agent_id = agent_datum.get("id")
                    assert (
                        agent_id is not None
                    ), "id is required in memory_from_file[Supervisor]"
                    assert agent_id >= MIN_ID, f"id {agent_id} is less than MIN_ID {MIN_ID}"
                    assert (
                        agent_id <= MAX_ID
                    ), f"id {agent_id} is greater than MAX_ID {MAX_ID}"
                    assert agent_id not in defined_ids, f"id {agent_id} is already defined"
                    defined_ids.add(agent_id)
                    supervisor_ids.add(agent_id)
                    memory_dict = generator.generate(i=0)
                    extra_attributes = memory_dict.get("extra_attributes", {})
                    profile = memory_dict.get("profile", {})
                    base = memory_dict.get("base", {})
                    memory_init = Memory(
                        agent_id=agent_id,
                        environment=self.environment,
                        faiss_query=self._faiss_query,
                        embedding_model=self._embedding_model,
                        config=extra_attributes,
                        profile=profile,
                        base=base,
                    )
                    # build blocks
                    if agent_config.blocks is not None:
                        blocks = [
                            block_type(
                                llm=self._llm,
                                environment=self.environment,
                                agent_memory=memory_init,
                                block_params=block_params,
                            )
                            for block_type, block_params in agent_config.blocks.items()
                        ]
                    else:
                        blocks = None
                    # build agent
                    agent_params = agent_config.agent_class.ParamsType.model_validate(
                        agent_config.agent_params
                    )
                    supervisor = agent_config.agent_class(
                        id=agent_id,
                        name=f"{agent_config.agent_class.__name__}_{agent_id}",
                        toolbox=AgentToolbox(
                            self._llm,
                            self.environment,
                            self.messager,
                            self._database_writer,
                        ),
                        memory=memory_init,
                        agent_params=agent_params,
                        blocks=blocks,
                    )
                    # set supervisor
                    assert (
                        self._message_interceptor is not None
                    ), "message interceptor is not set"
                    await self._message_interceptor.set_supervisor(supervisor)
                    break

            get_logger().info(
                f"{len(defined_ids)} defined ids found in memory_config_files"
            )

            # Step 2: Process all agents without memory_from_file
            for agent_config in agent_configs_normal["firms"]:
                # Handle distribution-based configuration as before
                if agent_config.memory_distributions is None:
                    agent_config.memory_distributions = {}
                assert (
                    "aoi_id" not in agent_config.memory_distributions
                ), "aoi_id is not allowed to be set in memory_distributions because it will be generated in the initialization"
                agent_config.memory_distributions["aoi_id"] = DistributionConfig(
                    dist_type=DistributionType.CHOICE,
                    choices=list(aoi_ids),
                )
                firm_classes, _ = _init_agent_class(agent_config, self._config.env.s3)
                firms = [
                    (_find_next_id(), *firm_class)
                    for i, firm_class in enumerate(firm_classes)
                ]
                firm_ids.update([firm[0] for firm in firms])
                agents += firms

            for agent_config in agent_configs_normal["banks"]:
                bank_classes, _ = _init_agent_class(agent_config, self._config.env.s3)
                banks = [
                    (_find_next_id(), *bank_class)
                    for i, bank_class in enumerate(bank_classes)
                ]
                bank_ids.update([bank[0] for bank in banks])
                agents += banks

            for agent_config in agent_configs_normal["nbs"]:
                nbs_classes, _ = _init_agent_class(agent_config, self._config.env.s3)
                nbs = [
                    (_find_next_id(), *nbs_class) for i, nbs_class in enumerate(nbs_classes)
                ]
                nbs_ids.update([nbs[0] for nbs in nbs])
                agents += nbs

            for agent_config in agent_configs_normal["governments"]:
                government_classes, _ = _init_agent_class(agent_config, self._config.env.s3)
                governments = [
                    (_find_next_id(), *government_class)
                    for i, government_class in enumerate(government_classes)
                ]
                government_ids.update([government[0] for government in governments])
                agents += governments

            for agent_config in agent_configs_normal["citizens"]:
                citizen_classes, generator = _init_agent_class(
                    agent_config, self._config.env.s3
                )
                citizen_generators.append(generator)
                citizens = [
                    (_find_next_id(), *citizen_class)
                    for i, citizen_class in enumerate(citizen_classes)
                ]
                citizen_ids.update([citizen[0] for citizen in citizens])
                agents += citizens

            for agent_config in agent_configs_normal["supervisor"]:
                supervisor_classes, _ = _init_agent_class(agent_config, self._config.env.s3)
                supervisors = [
                    (_find_next_id(), *supervisor_class)
                    for i, supervisor_class in enumerate(supervisor_classes)
                ]
                supervisor_ids.update([supervisor[0] for supervisor in supervisors])

            # Step 3: Insert essential distributions for citizens
            memory_distributions = {}
            for key, ids in [
                ("home_aoi_id", aoi_ids),
                ("work_aoi_id", aoi_ids),
            ]:
                memory_distributions[key] = DistributionConfig(
                    dist_type=DistributionType.CHOICE,
                    choices=list(ids),
                )
            for generator in citizen_generators:
                generator.merge_distributions(memory_distributions)

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
                    database_writer=self._database_writer,
                )
                for agent_id, _, _, _, _, _ in group_agents:
                    self._agent_id2group[agent_id] = self._groups[group_id]
            get_logger().info(
                f"groups: len(self._groups)={len(self._groups)}, waiting for groups to init..."
            )
            filter_base_tasks = await asyncio.gather(
                *[group.init.remote() for group in self._groups.values()]  # type:ignore
            )
            for group_filter_base in filter_base_tasks:
                for agent_id, (agent_class, profile) in group_filter_base.items():
                    self._filter_base[agent_id] = (agent_class, profile)

            get_logger().info(f"Agent groups initialized")
            # step 1 tick to make the initialization complete
            await self.environment.step(1)
            get_logger().info(f"run 1 tick to make the initialization complete")

            # ===================================
            # save the experiment info
            # ===================================
            await self._save_exp_info()
            self._save_context()
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

        except Exception as e:
            get_logger().error(f"Init error: {str(e)}\n{traceback.format_exc()}")
            self._exp_info.status = ExperimentStatus.ERROR.value
            self._exp_info.error = str(e)
            await self._save_exp_info()

            raise e
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

        if self._message_interceptor is not None:
            get_logger().info(f"Closing message interceptor...")
            await self._message_interceptor.close()
            self._message_interceptor = None
            get_logger().info(f"Message interceptor closed")

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
    def enable_database(self):
        return self._config.env.db.enabled

    @property
    def database_writer(self):
        assert self._database_writer is not None, "database writer is not initialized"
        return self._database_writer

    @property
    def environment(self):
        assert self._environment is not None, "environment is not initialized"
        return self._environment

    @property
    def messager(self):
        assert self._messager is not None, "messager is not initialized"
        return self._messager

    async def _extract_target_agent_ids(
        self, target_agent: Optional[Union[list[int], AgentFilterConfig]] = None
    ) -> list[int]:
        if target_agent is None:
            raise ValueError("target_agent is required")
        elif isinstance(target_agent, list):
            return target_agent
        elif isinstance(target_agent, AgentFilterConfig):
            return await self.filter(target_agent.agent_class, target_agent.filter_str)
        else:
            raise ValueError("target_agent must be a list of int or AgentFilterConfig")

    async def gather(
        self,
        content: str,
        target_agent_ids: Optional[list[int]] = None,
        flatten: bool = False,
        keep_id: bool = False,
    ) -> Union[dict[int, Any], list[Any]]:
        """
        Collect specific information from agents.

        - **Description**:
            - Asynchronously gathers specified content from targeted agents within all groups.

        - **Args**:
            - `content` (str): The information to collect from the agents.
            - `target_agent_ids` (Optional[List[int]], optional): A list of agent IDs to target. Defaults to None, meaning all agents are targeted.
            - `flatten` (bool, optional): Whether to flatten the result. Defaults to False.
            - `keep_id` (bool, optional): Whether to keep the agent IDs in the result. Defaults to False.

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
            if not keep_id:
                data_flatten = []
                for group_data in results:
                    for _, data in group_data.items():
                        data_flatten.append(data)
                return data_flatten
            else:
                data_flatten = {}
                for group_data in results:
                    for id, data in group_data.items():
                        data_flatten[id] = data
                return data_flatten
        else:
            return results

    async def filter(
        self,
        types: Optional[tuple[type[Agent]]] = None,
        filter_str: Optional[str] = None,
    ) -> list[int]:
        """
        Filter out agents of specified types or with matching key-value pairs.

        - **Args**:
            - `types` (Optional[Tuple[Type[Agent]]], optional): Types of agents to filter for. Defaults to None.
            - `filter_str` (Optional[str], optional): Filter string to match in agent attributes. Defaults to None.

        - **Raises**:
            - `ValueError`: If neither types nor filter_str are provided.

        - **Returns**:
            - `List[int]`: A list of filtered agent UUIDs.
        """
        if not types and not filter_str:
            return list(self._agent_ids)

        # filter by types first
        if types:
            filtered_ids = [
                agent_id 
                for agent_id, (agent_class, _) in self._filter_base.items()
                if any(issubclass(agent_class, t) for t in types)
            ]
        else:
            filtered_ids = list(self._agent_ids)

        # filter by filter_str
        if filter_str:
            filtered_ids = [
                agent_id 
                for agent_id in filtered_ids
                if evaluate_filter(filter_str, self._filter_base[agent_id][1])
            ]

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

    async def update(self, target_agent_ids: list[int], target_key: str, content: Any, query: bool = False):
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
            tasks.append(group.update.remote(id, target_key, content, query))  # type:ignore
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
        survey_day: Optional[int] = None,
        survey_t: Optional[float] = None,
        is_pending_survey: bool = False,
        pending_survey_id: Optional[int] = None,
    ) -> dict[int, str]:
        """
        Send a survey to specified agents.

        - **Args**:
            - `survey` (Survey): The survey object to send.
            - `agent_ids` (List[int], optional): List of agent IDs to receive the survey. Defaults to an empty list.
            - `survey_day` (int, optional): The day of the survey. Defaults to None.
            - `survey_t` (float, optional): The time of the survey. Defaults to None.
            - `is_pending_survey` (bool, optional): Whether the survey is a pending survey. Defaults to False.
            - `pending_survey_id` (int, optional): The ID of the pending survey. Defaults to None.

        - **Returns**:
            - `dict[int, str]`: A dictionary mapping agent IDs to their survey responses.
        """
        group_to_agent_ids = defaultdict(list)
        for agent_id in agent_ids:
            if agent_id not in self._agent_id2group:
                continue
            group_to_agent_ids[self._agent_id2group[agent_id]].append(agent_id)
        tasks = []
        for group, agent_ids in group_to_agent_ids.items():
            tasks.append(
                group.handle_survey.remote(
                    survey,
                    agent_ids,
                    survey_day,
                    survey_t,
                    is_pending_survey,
                    pending_survey_id,
                )  # type:ignore
            )
        results = await asyncio.gather(*tasks)
        all_responses = {}
        for result in results:
            all_responses.update(result)
        return all_responses

    async def send_interview_message(
        self,
        question: str,
        agent_ids: list[int],
    ):
        """
        Send an interview message to specified agents.

        - **Args**:
            - `question` (str): The content of the message to send.
            - `agent_ids` (list[int]): A list of IDs for the agents to receive the message.

        - **Returns**:
            - None
        """
        group_to_agent_ids = defaultdict(list)
        for agent_id in agent_ids:
            if agent_id not in self._agent_id2group:
                continue
            group_to_agent_ids[self._agent_id2group[agent_id]].append(agent_id)
        tasks = []
        for group, agent_ids in group_to_agent_ids.items():
            tasks.append(
                group.handle_interview.remote(question, agent_ids)
            )  # type:ignore
        results = await asyncio.gather(*tasks)
        all_responses = {}
        for result in results:
            all_responses.update(result)
        return all_responses

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
        group_to_agent_ids = defaultdict(list)
        for agent_id in agent_ids:
            if agent_id not in self._agent_id2group:
                continue
            group_to_agent_ids[self._agent_id2group[agent_id]].append(agent_id)
        tasks = []
        for group, agent_ids in group_to_agent_ids.items():
            tasks.append(
                group.react_to_intervention.remote(
                    intervention_message, agent_ids
                )  # type:ignore
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
                target_agent_ids = await self._extract_target_agent_ids(metric_extractor.target_agent)
                values = await self.gather(
                    metric_extractor.key, target_agent_ids, flatten=True
                )
                if values is None or len(values) == 0:
                    get_logger().warning(
                        f"No values found for metric extractor {metric_extractor.key} in extraction step {metric_extractor.extract_time}"
                    )
                    return
                if type(values[0]) == float or type(values[0]) == int:
                    value = values[0]
                    if len(values) > 1:
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
                    if self.enable_database:
                        assert self._database_writer is not None
                        await self._database_writer.log_metric.remote( # type: ignore
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
        if self.enable_database:
            assert self._database_writer is not None
            await self._database_writer.update_exp_info.remote(self._exp_info)  # type: ignore

    async def _save_global_prompt(self, prompt: str, day: int, t: float):
        """Save global prompt"""
        prompt_info = StorageGlobalPrompt(
            day=day,
            t=t,
            prompt=prompt,
            created_at=datetime.now(timezone.utc),
        )
        if self.enable_database:
            assert self._database_writer is not None
            await self._database_writer.write_global_prompt.remote(prompt_info)  # type:ignore

    async def _gather_and_update_context(self, target_agent_ids: list[int], key: str, save_as: str):
        """Gather and update the context"""
        try:
            values = await self.gather(key, target_agent_ids, flatten=True, keep_id=True)
            self.context[save_as] = values
        except Exception as e:
            get_logger().error(f"Error saving context: {str(e)}\n{traceback.format_exc()}")
            self.context[save_as] = {}

    def _save_context(self):
        fs_client = self._config.env.fs_client
        json_bytes = json.dumps(self.context, indent=2, ensure_ascii=False).encode(
            "utf-8"
        )
        fs_client.upload(
            data=json_bytes,
            remote_path=f"exps/{self.tenant_id}/{self.exp_id}/artifacts.json",
        )

    async def delete_agents(self, target_agent_ids: list[int]):
        """
        Delete the specified agents.

        - **Args**:
            - `target_agent_ids` (list[int]): The IDs of the agents to delete.
        """
        tasks = []
        groups_to_delete = {}
        for id in target_agent_ids:
            group = self._agent_id2group[id]
            if group not in groups_to_delete:
                groups_to_delete[group] = []
            groups_to_delete[group].append(id)
        for group in groups_to_delete.keys():
            tasks.append(
                group.delete_agents.remote(groups_to_delete[group])
            )  # type:ignore
        await asyncio.gather(*tasks)

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
            all_results = await asyncio.gather(*tasks)
            logs = []
            gather_queries = []
            for result in all_results:
                logs.append(result[0])
                gather_queries.append(result[1])

            get_logger().debug(f"({day}-{t}) Finished agent forward steps")
            # ======================
            # log the simulation results
            # ======================
            all_logs = Logs(
                llm_log=[],
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
                self._exp_info.input_tokens += log.get("input_tokens", 0)
                self._exp_info.output_tokens += log.get("output_tokens", 0)
            await self._save_exp_info()
            self._save_context()
            # ======================
            # process gather queries
            # ======================
            for group_queries in gather_queries:
                for agent_id, queries in group_queries.items():
                    for query in queries:
                        result = await self.gather(query.key, query.target_agent_ids, flatten=query.flatten, keep_id=query.keep_id) # type: ignore
                        await self.update([agent_id], query.key, result, query=True) # type: ignore

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
            tasks = []
            for group in self._groups.values():
                tasks.append(group.fetch_pending_messages.remote())  # type: ignore
            all_messages = list(itertools.chain(*await asyncio.gather(*tasks)))
            get_logger().info(
                f"({day}-{t}) Finished fetching pending messages. {len(all_messages)} messages fetched."
            )

            if self._message_interceptor is not None:
                all_messages = await self._message_interceptor.forward(all_messages)
            # ======================
            # fetch pending dialogs from USER
            # ======================
            if self.enable_database:
                pending_dialogs = await self._database_writer.fetch_pending_dialogs.remote()  # type: ignore
                get_logger().info(
                    f"({day}-{t}) Finished fetching pending dialogs. {len(pending_dialogs)} dialogs fetched."
                )
                user_messages = []
                for pending_dialog in pending_dialogs:
                    user_messages.append(
                        Message(
                            from_id=None,
                            to_id=pending_dialog.agent_id,
                            payload={"content": pending_dialog.content},
                            created_at=pending_dialog.created_at,
                            kind=MessageKind.USER_CHAT,
                            day=pending_dialog.day,
                            t=pending_dialog.t,
                            extra={"pending_dialog_id": pending_dialog.id},
                        )
                    )
                all_messages += user_messages
            # dispatch messages to each agent group based on their to_id
            group_to_messages = defaultdict(list)
            for message in all_messages:
                if message.to_id is not None and message.to_id in self._agent_id2group:
                    group_actor = self._agent_id2group[message.to_id]
                    group_to_messages[group_actor].append(message)
            get_logger().info(f"({day}:{t}) Finished grouping messages.")
            tasks = []
            for group_actor, messages in group_to_messages.items():
                tasks.append(group_actor.set_received_messages.remote(messages))  # type: ignore
            await asyncio.gather(*tasks)
            get_logger().info(f"({day}-{t}) Finished setting received messages")
            # ======================
            # handle pending surveys
            # ======================
            if self.enable_database:
                pending_surveys = await self._database_writer.fetch_pending_surveys.remote()  # type: ignore
                get_logger().info(
                    f"({day}-{t}) Finished fetching pending surveys. {len(pending_surveys)} surveys fetched."
                )
                pending_surveys = cast(list[StoragePendingSurvey], pending_surveys)
                for pending_survey in pending_surveys:
                    try:
                        pending_survey.data["id"] = pending_survey.survey_id
                        survey = Survey.model_validate(pending_survey.data)
                    except Exception as e:
                        get_logger().error(
                            f"Error validating survey data: {str(e)}\n{traceback.format_exc()}"
                        )
                        continue
                    await self.send_survey(
                        survey,
                        [pending_survey.agent_id],
                        pending_survey.day,
                        pending_survey.t,
                        is_pending_survey=True,
                        pending_survey_id=pending_survey.id,
                    )
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
                    target_agent_ids = await self._extract_target_agent_ids(
                        target_agents
                    )
                    await self.send_interview_message(
                        interview_message, target_agent_ids
                    )
                elif step.type == WorkflowType.SURVEY:
                    assert step.target_agent is not None
                    assert step.survey is not None
                    target_agent_ids = await self._extract_target_agent_ids(
                        step.target_agent
                    )
                    await self.send_survey(step.survey, target_agent_ids)
                elif step.type == WorkflowType.ENVIRONMENT_INTERVENE:
                    assert step.key is not None
                    assert step.value is not None
                    await self.update_environment(step.key, step.value)
                elif step.type == WorkflowType.UPDATE_STATE_INTERVENE:
                    assert step.key is not None
                    assert step.value is not None
                    assert step.target_agent is not None
                    target_agent_ids = await self._extract_target_agent_ids(
                        step.target_agent
                    )
                    await self.update(target_agent_ids, step.key, step.value)
                elif step.type == WorkflowType.MESSAGE_INTERVENE:
                    assert step.intervene_message is not None
                    assert step.target_agent is not None
                    target_agent_ids = await self._extract_target_agent_ids(
                        step.target_agent
                    )
                    await self.send_intervention_message(
                        step.intervene_message, target_agent_ids
                    )
                elif step.type == WorkflowType.NEXT_ROUND:
                    await self.next_round()
                elif step.type == WorkflowType.DELETE_AGENT:
                    assert step.target_agent is not None
                    target_agent_ids = await self._extract_target_agent_ids(
                        step.target_agent
                    )
                    await self.delete_agents(target_agent_ids)
                elif step.type == WorkflowType.SAVE_CONTEXT:
                    assert step.target_agent is not None
                    assert step.key is not None
                    assert step.save_as is not None
                    target_agent_ids = await self._extract_target_agent_ids(
                        step.target_agent
                    )
                    await self._gather_and_update_context(target_agent_ids, step.key, step.save_as)
                elif step.type == WorkflowType.INTERVENE:
                    get_logger().warning(
                        "MESSAGE_INTERVENE is not fully implemented yet, it can only influence the congnition of target agents"
                    )
                    assert step.target_agent is not None
                    assert step.intervene_message is not None
                    target_agent_ids = await self._extract_target_agent_ids(
                        step.target_agent
                    )
                    await self.send_intervention_message(
                        step.intervene_message, target_agent_ids
                    )
                elif step.type == WorkflowType.FUNCTION:
                    assert step.func is not None
                    assert not isinstance(step.func, str)
                    await step.func(self)
                else:
                    raise ValueError(f"Unknown workflow type: {step.type}")
                self._save_context()
            # Finalize the agents
            tasks = []
            for group in self._groups.values():
                tasks.append(group.close.remote())  # type:ignore
            await asyncio.gather(*tasks)

        except Exception as e:
            get_logger().error(f"Simulation error: {str(e)}\n{traceback.format_exc()}")
            self._exp_info.status = ExperimentStatus.ERROR.value
            self._exp_info.error = str(e)
            self._save_context()
            await self._save_exp_info()

            raise RuntimeError(str(e)) from e
        self._exp_info.status = ExperimentStatus.FINISHED.value
        self._save_context()
        await self._save_exp_info()
        return logs
