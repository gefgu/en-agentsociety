"""
A clear version of the simulation.
"""

import asyncio
import inspect
import json
import os
import traceback
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from multiprocessing import cpu_count
from typing import Any, Callable, Literal, Optional, Union, cast
import time
import yaml
from ..database.database_actor import DatabaseActor
from ..database.schema import StaticAgentAttributesRecord
from ..performance.prometheusActor import PrometheusActor
from ..performance.monitoring import start_monitoring, stop_monitoring
from ..agent import CustomTool
from fastembed import SparseTextEmbedding

# from ..modernbert.modernbert_regression_actor import ModernBERTRegressionActor
import ray

from ..agent import (
    Agent,
    AgentToolbox,
    BankAgentBase,
    CitizenAgentBase,
    FirmAgentBase,
    GovernmentAgentBase,
    MemoryAttribute,
    NBSAgentBase,
    SupervisorBase,
)
from ..agent.distribution import Distribution, DistributionConfig, DistributionType
from ..agent.memory_config_generator import (
    MemoryConfig,
    MemoryConfigGenerator,
    default_memory_config_citizen,
    default_memory_config_supervisor,
)
from ..configs import (
    AgentConfig,
    AgentFilterConfig,
    Config,
    WorkflowType,
)
from ..environment import EnvironmentStarter
from ..llm import LLM
from ..logger import attach_otlp_handler, get_logger, set_exp_id, set_logger_level
from ..memory import Memory
from ..message import Message, MessageInterceptor, MessageKind, Messager
from ..s3 import S3Config
from ..storage import DatabaseWriter
from ..storage.type import (
    StorageExpInfo,
    StorageGlobalPrompt,
    StoragePendingSurvey,
    StorageProfile,
    StorageStatus,
)
from ..survey.models import Survey
from .type import ExperimentStatus, Logs
import ray
from enum import Enum

__all__ = ["SimulationEngine"]

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
    agent_class: type[Agent] = agent_config.agent_class
    n: int = agent_config.number
    # memory config function
    memory_config_func = cast(
        Callable[
            [dict[str, Distribution], Optional[list[MemoryAttribute]]],
            MemoryConfig,
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

    pattern = r"\${profile\.([^}]+)}"
    required_keys = set(re.findall(pattern, filter_str))

    # if any required key is not in profile, return False
    for key in required_keys:
        # Handle nested keys
        current = profile
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]

    # replace all ${profile.xxx} with actual values
    for key in required_keys:
        # Get the value by traversing the nested dictionary
        current = profile
        for part in key.split("."):
            current = current[part]
        filter_str = filter_str.replace(f"${{profile.{key}}}", repr(current))

    # use eval to execute the expression
    try:
        return eval(filter_str)
    except Exception:
        return False


class SimulationEngine:
    def __init__(
        self,
        config: Config,
        tenant_id: str = "",
    ) -> None:
        self._config = _set_default_agent_config(config)
        self.tenant_id = tenant_id

        # ====================
        # Initialize the logger
        # ====================
        set_logger_level(self._config.logging_level.upper())

        # In resume mode, keep using the provided experiment id instead of creating a new one.
        configured_resume_exp_id = self._config.env.exp_id
        self.exp_id = str(configured_resume_exp_id or config.exp.id)
        get_logger().debug(
            f"Creating SimulationEngine with config: {self._config.model_dump()} as exp_id={self.exp_id}"
        )

        # typing definition
        self._llm: Optional[LLM] = None
        self._environment: Optional[EnvironmentStarter] = None
        self._message_interceptor: Optional[MessageInterceptor] = None
        self._database_writer: Optional[DatabaseWriter] = None
        self._embedding: Optional[SparseTextEmbedding] = None
        self._metrics_actor: Optional[PrometheusActor] = None
        self._db_actor: Optional[DatabaseActor] = None
        self._db_tool: Optional[CustomTool] = None
        self._id2agent: dict[int, Agent] = {}
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
        self._messager: Optional[Messager] = None

        # simulation context - for information dump
        self.context = {}

        # filter base
        self._filter_base = {}

        self._step_times: list[float] = []
        self._step_start_time: Optional[float] = None
        self._resume_exp_id: Optional[str] = configured_resume_exp_id
        self._resume_state: Optional[dict[str, Any]] = None

    async def _init_embedding(self):
        """Initialize embedding model with timeout."""
        try:
            # Create a task for embedding initialization
            init_task = asyncio.create_task(self._init_embedding_task())

            # Wait for the task with timeout
            try:
                await asyncio.wait_for(init_task, timeout=120)  # 2 minutes timeout
            except asyncio.TimeoutError:
                get_logger().error(
                    "Embedding model initialization timed out after 2 minutes. "
                    "Please check your HuggingFace connection and try again."
                )
                raise

        except Exception as e:
            get_logger().error(f"Failed to initialize embedding model: {str(e)}")
            raise

    async def _init_embedding_task(self):
        """Actual embedding initialization task."""
        self._embedding = SparseTextEmbedding(
            "Qdrant/bm25",
            cache_dir=os.path.join(self._config.env.home_dir, "huggingface_cache"),
            threads=cpu_count(),
        )
        get_logger().info("Embedding models initialized successfully")

    async def _init_database_writer_if_enabled(self):
        """Initialize the pgsql writer when database is enabled."""
        if self._config.env.db.enabled:
            get_logger().info("Initializing database writer...")
            self._database_writer = DatabaseWriter(
                self.tenant_id,
                self.exp_id,
                self._config.env.db,
                self._config.env.home_dir,
            )
            await self._database_writer.init()  # type: ignore
            get_logger().info("Database writer initialized")
            await self._database_writer.update_exp_info(self._exp_info)

    def _start_monitoring_services(self):
        """Initialize Prometheus and Grafana monitoring services."""
        try:
            start_monitoring(self._config.env.data_dir)
            set_exp_id(self.exp_id)
            attach_otlp_handler()
        except Exception as e:
            get_logger().warning(f"Failed to start monitoring services: {e}")

    def _init_metrics_actor(self) -> Optional[CustomTool]:
        """Initialize the Prometheus actor and return it as a toolbox tool."""
        try:
            get_logger().info(
                f"Initializing Prometheus actor with exp_id={self.exp_id}...",
            )
            metrics_actor = PrometheusActor.remote(self.exp_id)
            self._metrics_actor = metrics_actor
            get_logger().info("Performance actor initialized")
            return CustomTool(
                name="metrics_actor",
                tool=metrics_actor,
                description="Ray actor for tracking block performance metrics",
            )
        except Exception as e:
            get_logger().warning(f"Failed to initialize performance actor: {e}")
            return None

    def _init_clickhouse_actor(self):
        """Initialize the ClickHouse actor and corresponding toolbox tool."""
        try:
            self._db_actor = DatabaseActor.remote(
                exp_id=self.exp_id,
                home_dir=self._config.env.data_dir,
                metrics_actor=self._metrics_actor,
            )
            self._db_tool = CustomTool(
                name="db_actor",
                tool=self._db_actor,
                description="Ray actor for storing simulation data in ClickHouse database",
            )
            get_logger().info("ClickHouse actor initialized")
        except Exception as e:
            get_logger().warning(f"Failed to initialize ClickHouse actor: {e}")

    @staticmethod
    def _normalize_config_value(value: Any) -> Any:
        """Convert Python objects from YAML into deterministic, comparable values."""
        if isinstance(value, dict):
            normalized_items = []
            for k, v in value.items():
                normalized_key = SimulationEngine._normalize_config_value(k)
                normalized_value = SimulationEngine._normalize_config_value(v)
                normalized_items.append((normalized_key, normalized_value))
            normalized_items.sort(key=lambda item: str(item[0]))
            return {k: v for k, v in normalized_items}

        if isinstance(value, (list, tuple, set)):
            normalized_list = [SimulationEngine._normalize_config_value(v) for v in value]
            if isinstance(value, set):
                normalized_list.sort(key=str)
            return normalized_list

        if inspect.isclass(value):
            return f"{value.__module__}.{value.__name__}"

        if callable(value) and hasattr(value, "__module__") and hasattr(value, "__qualname__"):
            return f"{value.__module__}.{value.__qualname__}"

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, (str, int, float, bool)) or value is None:
            return value

        return str(value)

    @staticmethod
    def _normalize_resume_config(raw_config: Union[str, dict[str, Any]]) -> dict[str, Any]:
        if isinstance(raw_config, str):
            try:
                loaded = yaml.safe_load(raw_config) or {}
            except yaml.YAMLError:
                # Stored config can include python tags (e.g. !!python/name:...),
                # so fall back to unsafe loader and normalize objects to strings.
                loaded = yaml.load(raw_config, Loader=yaml.UnsafeLoader) or {}
        elif isinstance(raw_config, dict):
            loaded = deepcopy(raw_config)
        else:
            loaded = {}

        if not isinstance(loaded, dict):
            loaded = {}

        exp_config = loaded.get("exp")
        if isinstance(exp_config, dict):
            exp_config.pop("id", None)

        env_config = loaded.get("env")
        if isinstance(env_config, dict):
            env_config.pop("exp_id", None)

        normalized = SimulationEngine._normalize_config_value(loaded)
        if isinstance(normalized, dict):
            return normalized
        return {}

    async def _load_resume_state(self):
        """Load resume metadata from ClickHouse when env.exp_id is provided."""
        if not self._resume_exp_id:
            return

        if self._db_actor is None:
            raise RuntimeError("ClickHouse actor is required when env.exp_id is set")

        resume_data = await self._db_actor.fetch_resume_data.remote(self._resume_exp_id)
        if resume_data is None:
            raise ValueError(
                f"No ClickHouse resume data found for experiment id '{self._resume_exp_id}'"
            )

        source_config = self._normalize_resume_config(resume_data.get("config", ""))
        current_config = self._normalize_resume_config(self._exp_info.config)
        if source_config != current_config:
            raise ValueError(
                "Configuration mismatch with resume experiment. "
                "Current configuration fields must match the source experiment config."
            )

        self._resume_state = resume_data
        self._total_steps = int(resume_data.get("latest_step", 0))
        get_logger().info(
            f"Loaded resume state from exp_id={self._resume_exp_id} at step={self._total_steps}"
        )

    @staticmethod
    def _static_record_to_memory_updates(static_record: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": static_record.get("type"),
            "home": {"aoi_position": {"aoi_id": int(static_record.get("home_aoi_id", 0))}},
            "work": {"aoi_position": {"aoi_id": int(static_record.get("work_aoi_id", 0))}},
            "name": static_record.get("name"),
            "gender": static_record.get("gender"),
            "age": int(static_record.get("age", 0)),
            "education": static_record.get("education"),
            "household": static_record.get("household"),
            "life_stage": static_record.get("life_stage"),
            "skill": static_record.get("skill"),
            "occupation": static_record.get("occupation"),
            "work_skill": float(static_record.get("work_skill", 0.0)),
            "firm_id": int(static_record.get("firm_id", 0)),
            "government_id": int(static_record.get("government_id", 0)),
            "bank_id": int(static_record.get("bank_id", 0)),
            "nbs_id": int(static_record.get("nbs_id", 0)),
            "preferences": {
                "chronotype": static_record.get("preferences_chronotype"),
                "risk_tolerance": float(
                    static_record.get("preferences_risk_tolerance", 0.5)
                ),
                "spending_tendency": float(
                    static_record.get("preferences_spending_tendency", 0.5)
                ),
                "social_frequency": float(
                    static_record.get("preferences_social_frequency", 0.5)
                ),
                "work_ethic": float(static_record.get("preferences_work_ethic", 0.5)),
                "leisure_preference": static_record.get("preferences_leisure_preference"),
            },
            "hobbies": static_record.get("hobbies", []),
            "personality": static_record.get("personality"),
            "big5": {
                "openness": int(static_record.get("big5_openness", 2)),
                "conscientiousness": int(
                    static_record.get("big5_conscientiousness", 2)
                ),
                "extraversion": int(static_record.get("big5_extraversion", 2)),
                "agreeableness": int(static_record.get("big5_agreeableness", 2)),
                "neuroticism": int(static_record.get("big5_neuroticism", 2)),
            },
            "income": float(static_record.get("income", 0.0)),
            "currency": float(static_record.get("currency", 0.0)),
            "residence": static_record.get("residence"),
            "city": static_record.get("city"),
            "race": static_record.get("race"),
            "religion": static_record.get("religion"),
            "marriage_status": static_record.get("marriage_status"),
            "background_story": static_record.get("background_story"),
        }

    @staticmethod
    def _count_citizen_agents(agents: list[tuple[Any, ...]]) -> int:
        count = 0
        for agent_init in agents:
            _, agent_class, *_ = agent_init
            if issubclass(agent_class, CitizenAgentBase):
                count += 1
        return count

    def _validate_resume_agent_count(self, agents: list[tuple[Any, ...]]):
        """Ensure citizen count matches static rows from resume source."""
        if self._resume_state is None:
            return

        static_records = self._resume_state.get("static_records", [])
        expected_citizens = self._count_citizen_agents(agents)
        available_citizens = len(static_records)
        if expected_citizens != available_citizens:
            raise ValueError(
                "Agent number mismatch for resume source experiment "
                f"'{self._resume_exp_id}': configured citizens={expected_citizens}, "
                f"static citizen records={available_citizens}"
            )

    async def _init_core_components(self):
        """Initialize LLM, environment, messager, and embedding components."""
        get_logger().info("Initializing LLM...")
        self._llm = LLM(
            self._config.llm,
            metrics_actor=self._metrics_actor,
            db_actor=self._db_actor,
        )
        get_logger().info("LLM initialized")

        get_logger().info("Initializing environment...")
        self._environment = EnvironmentStarter(
            self._config.map,
            self._config.exp.environment,
            self._config.env.s3,
            os.path.join(
                self._config.env.home_dir,
                "exps",
                self.tenant_id,
                self.exp_id,
                "simulator_log",
            ),
            self._config.env.home_dir,
        )
        await self._environment.init()
        get_logger().info("Environment initialized")

        get_logger().info("Initializing messager...")
        if self._config.agents.supervisor is not None:
            self._message_interceptor = MessageInterceptor(
                self._config.llm,
            )
        self._messager = Messager(exp_id=self.exp_id)
        get_logger().info("Messager initialized")

        get_logger().info("Initializing embedding...")
        await self._init_embedding()
        assert self._embedding is not None, "Embedding is not initialized"
        get_logger().info("Embedding initialized")

    def _split_agent_configs_by_memory_source(self):
        """Split agent configs into normal and memory_from_file buckets."""
        agent_configs_normal: dict[str, list[AgentConfig]] = {
            "firms": [],
            "banks": [],
            "nbs": [],
            "governments": [],
            "citizens": [],
            "supervisor": [],
        }
        agent_configs_from_file: dict[str, list[AgentConfig]] = {
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

        return agent_configs_normal, agent_configs_from_file

    def _append_agents_from_memory_files(
        self,
        label: str,
        configs: list[AgentConfig],
        defined_ids: set[int],
        role_ids: set[int],
        agents: list[tuple[Any, ...]],
        citizen_generators: list[MemoryConfigGenerator],
    ):
        """Build agent init tuples from memory_from_file configs for one role."""
        for agent_config in configs:
            agent_config = cast(AgentConfig, agent_config)
            agent_class = agent_config.agent_class
            agent_params = agent_config.agent_params
            if agent_params is None:
                agent_params = agent_class.ParamsType()
            else:
                agent_params = agent_class.ParamsType.model_validate(agent_params)
            blocks = agent_config.blocks

            generator = MemoryConfigGenerator(
                agent_config.memory_config_func,
                agent_config.agent_class.StatusAttributes,
                agent_config.number,
                agent_config.memory_from_file,
                (
                    agent_config.memory_distributions
                    if agent_config.memory_distributions is not None
                    else {}
                ),
                self._config.env.s3,
            )
            if label.lower() == "citizens":
                citizen_generators.append(generator)

            agent_data = generator.get_agent_data_from_file()
            for index, agent_datum in enumerate(agent_data):
                agent_id = agent_datum.get("id")
                assert agent_id is not None, f"id is required in memory_from_file[{label}]"
                assert agent_id >= MIN_ID, f"id {agent_id} is less than MIN_ID {MIN_ID}"
                assert agent_id <= MAX_ID, f"id {agent_id} is greater than MAX_ID {MAX_ID}"
                assert agent_id not in defined_ids, f"id {agent_id} is already defined"

                defined_ids.add(agent_id)
                role_ids.add(agent_id)
                agents.append(
                    (
                        agent_id,
                        agent_class,
                        generator,
                        index,
                        agent_params,
                        blocks,
                    )
                )

    async def _init_supervisor_from_memory_file(
        self,
        configs: list[AgentConfig],
        defined_ids: set[int],
        supervisor_ids: set[int],
    ):
        """Initialize supervisor directly when configured with memory_from_file."""
        assert len(configs) <= 1, "only one or zero supervisor is allowed"

        for agent_config in configs:
            agent_config = cast(AgentConfig, agent_config)
            generator = MemoryConfigGenerator(
                agent_config.memory_config_func,
                agent_config.agent_class.StatusAttributes,
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
                assert agent_id is not None, "id is required in memory_from_file[Supervisor]"
                assert agent_id >= MIN_ID, f"id {agent_id} is less than MIN_ID {MIN_ID}"
                assert agent_id <= MAX_ID, f"id {agent_id} is greater than MAX_ID {MAX_ID}"
                assert agent_id not in defined_ids, f"id {agent_id} is already defined"

                defined_ids.add(agent_id)
                supervisor_ids.add(agent_id)

                memory_config = generator.generate(i=0)
                memory_init = Memory(
                    environment=self.environment,
                    embedding=self._embedding,
                    memory_config=memory_config,
                )
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

                if agent_config.agent_params is None:
                    agent_params = agent_config.agent_class.ParamsType()
                else:
                    agent_params = agent_config.agent_class.ParamsType.model_validate(
                        agent_config.agent_params
                    )

                supervisor = agent_config.agent_class(
                    id=agent_id,
                    name=f"{agent_config.agent_class.__name__}_{agent_id}",
                    toolbox=AgentToolbox(
                        llm=self._llm,
                        environment=self.environment,
                        messager=self.messager,
                        embedding=self._embedding,
                        database_writer=self._database_writer,
                    ),
                    memory=memory_init,
                    agent_params=agent_params,
                    blocks=blocks,
                )
                assert (
                    self._message_interceptor is not None
                ), "message interceptor is not set"
                await self._message_interceptor.set_supervisor(supervisor)
                break

    async def _prepare_agents(self):
        """Prepare agent init tuples and id groups from all config sources."""
        agents: list[tuple[Any, ...]] = []
        next_id = 1
        defined_ids: set[int] = set()

        def _find_next_id():
            nonlocal next_id
            while next_id in defined_ids:
                next_id += 1
            if next_id > MAX_ID:
                raise ValueError(f"Agent ID {next_id} is greater than MAX_ID {MAX_ID}")
            defined_ids.add(next_id)
            return next_id

        citizen_ids: set[int] = set()
        bank_ids: set[int] = set()
        nbs_ids: set[int] = set()
        government_ids: set[int] = set()
        firm_ids: set[int] = set()
        supervisor_ids: set[int] = set()
        aoi_ids = self._environment.get_aoi_ids()

        agent_configs_normal, agent_configs_from_file = (
            self._split_agent_configs_by_memory_source()
        )
        citizen_generators: list[MemoryConfigGenerator] = []

        self._append_agents_from_memory_files(
            "Firms",
            agent_configs_from_file["firms"],
            defined_ids,
            firm_ids,
            agents,
            citizen_generators,
        )
        self._append_agents_from_memory_files(
            "Banks",
            agent_configs_from_file["banks"],
            defined_ids,
            bank_ids,
            agents,
            citizen_generators,
        )
        self._append_agents_from_memory_files(
            "NBS",
            agent_configs_from_file["nbs"],
            defined_ids,
            nbs_ids,
            agents,
            citizen_generators,
        )
        self._append_agents_from_memory_files(
            "Governments",
            agent_configs_from_file["governments"],
            defined_ids,
            government_ids,
            agents,
            citizen_generators,
        )
        self._append_agents_from_memory_files(
            "Citizens",
            agent_configs_from_file["citizens"],
            defined_ids,
            citizen_ids,
            agents,
            citizen_generators,
        )

        await self._init_supervisor_from_memory_file(
            agent_configs_from_file["supervisor"],
            defined_ids,
            supervisor_ids,
        )

        get_logger().info(
            f"{len(defined_ids)} defined ids found in memory_config_files"
        )

        for agent_config in agent_configs_normal["firms"]:
            agent_config = cast(AgentConfig, agent_config)
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
            firms = [(_find_next_id(), *firm_class) for firm_class in firm_classes]
            firm_ids.update([firm[0] for firm in firms])
            agents += firms

        for agent_config in agent_configs_normal["banks"]:
            bank_classes, _ = _init_agent_class(agent_config, self._config.env.s3)
            banks = [(_find_next_id(), *bank_class) for bank_class in bank_classes]
            bank_ids.update([bank[0] for bank in banks])
            agents += banks

        for agent_config in agent_configs_normal["nbs"]:
            nbs_classes, _ = _init_agent_class(agent_config, self._config.env.s3)
            nbs = [(_find_next_id(), *nbs_class) for nbs_class in nbs_classes]
            nbs_ids.update([nbs_agent[0] for nbs_agent in nbs])
            agents += nbs

        for agent_config in agent_configs_normal["governments"]:
            government_classes, _ = _init_agent_class(agent_config, self._config.env.s3)
            governments = [
                (_find_next_id(), *government_class)
                for government_class in government_classes
            ]
            government_ids.update([government[0] for government in governments])
            agents += governments

        for agent_config in agent_configs_normal["citizens"]:
            citizen_classes, generator = _init_agent_class(agent_config, self._config.env.s3)
            citizen_generators.append(generator)
            citizens = [(_find_next_id(), *citizen_class) for citizen_class in citizen_classes]
            citizen_ids.update([citizen[0] for citizen in citizens])
            agents += citizens

        for agent_config in agent_configs_normal["supervisor"]:
            supervisor_classes, _ = _init_agent_class(agent_config, self._config.env.s3)
            supervisors = [
                (_find_next_id(), *supervisor_class)
                for supervisor_class in supervisor_classes
            ]
            supervisor_ids.update([supervisor[0] for supervisor in supervisors])

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
        self._environment.economy_client.set_ids(
            citizen_ids=citizen_ids,
            firm_ids=firm_ids,
            bank_ids=bank_ids,
            nbs_ids=nbs_ids,
            government_ids=government_ids,
        )

        return agents

    async def _initialize_agents(self, agents: list[tuple[Any, ...]]):
        """Instantiate agents, run init hooks, and build profile/embedding data."""
        agent_toolbox = AgentToolbox(
            llm=self.llm,
            environment=self.environment,
            messager=self.messager,
            embedding=self._embedding,
            database_writer=self._database_writer,
        )
        get_logger().info("Initializing the agents...")
        to_return: dict[int, tuple[type[Agent], dict[str, Any]]] = {}
        resume_static_by_agent_id: dict[int, dict[str, Any]] = {}
        if self._resume_state is not None:
            for record in self._resume_state.get("static_records", []):
                agent_id = int(record.get("agent_id", -1))
                if agent_id >= 0:
                    resume_static_by_agent_id[agent_id] = record

        for agent_init in agents:
            (
                agent_id,
                agent_class,
                memory_config_generator,
                index_for_generator,
                agent_params,
                blocks,
            ) = agent_init
            memory_config = memory_config_generator.generate(index_for_generator)
            to_return[agent_id] = (agent_class, deepcopy(memory_config))

            memory_init = Memory(
                environment=self.environment,
                embedding=self._embedding,
                memory_config=memory_config,
            )

            if self._resume_state is not None and issubclass(agent_class, CitizenAgentBase):
                static_record = resume_static_by_agent_id.get(agent_id)
                if static_record is None:
                    raise ValueError(
                        f"Missing static resume data for citizen agent id {agent_id}"
                    )
                static_updates = self._static_record_to_memory_updates(static_record)
                for key, value in static_updates.items():
                    if value is not None:
                        await memory_init.status.update(key, value, mode="replace")

            if blocks is not None:
                blocks = [
                    block_type(
                        toolbox=agent_toolbox,
                        agent_memory=memory_init,
                        block_params=block_type.ParamsType.model_validate(block_params),
                    )
                    for block_type, block_params in blocks.items()
                ]
            else:
                blocks = None

            agent = agent_class(
                id=agent_id,
                name=f"{agent_class.__name__}_{agent_id}",
                toolbox=agent_toolbox,
                memory=memory_init,
                agent_params=agent_params,
                blocks=blocks,
            )
            self._id2agent[agent_id] = agent

        get_logger().info("-----Initializing by running agent.init() ...")
        tasks = []
        channels = []
        for agent in self._id2agent.values():
            tasks.append(agent.init())
            channels.append(f"exps:{self.exp_id}:agents:{agent.id}:*")
        await asyncio.gather(*tasks)

        get_logger().info("-----Initializing by exporting profiles ...")
        profiles = []
        for agent in self._id2agent.values():
            profile = await agent.status.export(
                [
                    "name",
                    "gender",
                    "age",
                    "education",
                    "occupation",
                    "marriage_status",
                    "persona",
                    "openness",
                    "conscientiousness",
                    "extraversion",
                    "agreeableness",
                    "neuroticism",
                    "background_story",
                ]
            )
            profile["id"] = agent.id
            profiles.append(
                StorageProfile(
                    id=agent.id,
                    name=profile.get("name", ""),
                    profile=json.dumps(
                        {
                            k: v
                            for k, v in profile.items()
                            if k not in {"id", "name", "social_network"}
                        },
                        ensure_ascii=False,
                    ),
                )
            )
        if self._database_writer is not None:
            await self._database_writer.write_profiles(profiles)  # type:ignore

        get_logger().info("-----Initializing embeddings ...")
        embedding_tasks = []
        for agent in self._id2agent.values():
            embedding_tasks.append(agent.memory.initialize_embeddings())
        await asyncio.gather(*embedding_tasks)
        get_logger().info("Agents initialized")

        for agent_id, (agent_class, memory_config) in to_return.items():
            self._filter_base[agent_id] = (agent_class, memory_config)

        return agent_toolbox

    async def _save_agent_static_info(self):
        if self._db_actor is None:
            get_logger().info("ClickHouse actor is not initialized; skip static info save")
            return

        if not self._id2agent:
            get_logger().info("No agents found; skip static info save")
            return

        try:
            await self._db_actor.set_simulation_step.remote(step=self._total_steps)
        except Exception as e:
            get_logger().warning(
                f"Failed to set ClickHouse simulation step for static info save: {e}"
            )

        def _as_int(value: Any, default: int = 0) -> int:
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        def _as_float(value: Any, default: float = 0.0) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        def _as_str(value: Any, default: str = "unknown") -> str:
            if value is None:
                return default
            return str(value)

        def _extract_aoi_id(value: Any) -> int:
            if isinstance(value, dict):
                aoi_position = value.get("aoi_position")
                if isinstance(aoi_position, dict):
                    return _as_int(aoi_position.get("aoi_id"), 0)
                return _as_int(value.get("aoi_id"), 0)
            return _as_int(value, 0)

        saved_count = 0
        for agent in self._id2agent.values():
            if not isinstance(agent, CitizenAgentBase):
                continue

            filter_base_entry = self._filter_base.get(agent.id)
            if filter_base_entry is None:
                get_logger().warning(
                    f"Missing filter base for agent {agent.id}; skip static info save"
                )
                continue

            _, memory_config = filter_base_entry
            static_keys = [
                key
                for key, attr in memory_config.attributes.items()
                if attr.storage_class == "static"
            ]

            try:
                values = await agent.status.export(static_keys)

                preferences = values.get("preferences", {})
                if not isinstance(preferences, dict):
                    preferences = {}

                big5 = values.get("big5", {})
                if not isinstance(big5, dict):
                    big5 = {}

                hobbies = values.get("hobbies", [])
                if not isinstance(hobbies, list):
                    hobbies = [hobbies] if hobbies is not None else []

                record: StaticAgentAttributesRecord = {
                    "exp_id": self.exp_id,
                    "simulation_step": self._total_steps,
                    "timestamp": datetime.now(),
                    "agent_id": agent.id,
                    "type": _as_str(values.get("type"), "citizen"),
                    "home_aoi_id": _extract_aoi_id(values.get("home", {})),
                    "work_aoi_id": _extract_aoi_id(values.get("work", {})),
                    "name": _as_str(values.get("name"), "unknown"),
                    "gender": _as_str(values.get("gender"), "unknown"),
                    "age": _as_int(values.get("age"), 0),
                    "education": _as_str(values.get("education"), "unknown"),
                    "household": _as_str(values.get("household"), "unknown"),
                    "life_stage": _as_str(values.get("life_stage"), "unknown"),
                    "skill": _as_str(values.get("skill"), "unknown"),
                    "occupation": _as_str(values.get("occupation"), "unknown"),
                    "work_skill": _as_float(values.get("work_skill"), 0.0),
                    "firm_id": _as_int(values.get("firm_id"), 0),
                    "government_id": _as_int(values.get("government_id"), 0),
                    "bank_id": _as_int(values.get("bank_id"), 0),
                    "nbs_id": _as_int(values.get("nbs_id"), 0),
                    "preferences_chronotype": _as_str(
                        preferences.get("chronotype"), "standard"
                    ),
                    "preferences_risk_tolerance": _as_float(
                        preferences.get("risk_tolerance"), 0.5
                    ),
                    "preferences_spending_tendency": _as_float(
                        preferences.get("spending_tendency"), 0.5
                    ),
                    "preferences_social_frequency": _as_float(
                        preferences.get("social_frequency"), 0.5
                    ),
                    "preferences_work_ethic": _as_float(
                        preferences.get("work_ethic"), 0.5
                    ),
                    "preferences_leisure_preference": _as_str(
                        preferences.get("leisure_preference"), "indoor"
                    ),
                    "hobbies": [str(item) for item in hobbies],
                    "personality": _as_str(values.get("personality"), "unknown"),
                    "big5_openness": _as_int(big5.get("openness"), 2),
                    "big5_conscientiousness": _as_int(
                        big5.get("conscientiousness"), 2
                    ),
                    "big5_extraversion": _as_int(big5.get("extraversion"), 2),
                    "big5_agreeableness": _as_int(big5.get("agreeableness"), 2),
                    "big5_neuroticism": _as_int(big5.get("neuroticism"), 2),
                    "income": _as_float(values.get("income"), 0.0),
                    "currency": _as_float(values.get("currency"), 0.0),
                    "residence": _as_str(values.get("residence"), "unknown"),
                    "city": _as_str(values.get("city"), "unknown"),
                    "race": _as_str(values.get("race"), "unknown"),
                    "religion": _as_str(values.get("religion"), "unknown"),
                    "marriage_status": _as_str(
                        values.get("marriage_status"), "unknown"
                    ),
                    "background_story": _as_str(
                        values.get("background_story"), "No background story"
                    ),
                }

                self._db_actor.insert_static_agent_attributes_record.remote(
                    record=record
                )
                saved_count += 1
            except Exception as e:
                get_logger().warning(
                    f"Failed to save static info for agent {agent.id}: {e}"
                )

        get_logger().info(
            f"Saved static info to ClickHouse for {saved_count} citizen agents"
        )

    async def _finalize_initialization(
        self,
        agent_toolbox: AgentToolbox,
        metrics_tool: Optional[CustomTool],
    ):
        """Finalize initialization by stepping env, attaching tools, and running hooks."""
        get_logger().info("Agents initialized")
        await self.environment.step(1)
        get_logger().info("run 1 tick to make the initialization complete")

        get_logger().info("Adding Prometheus tool to Agents...")
        if metrics_tool is not None:
            agent_toolbox.add_tool(metrics_tool)

        get_logger().info("Adding clickhouse tool to Agents...")
        if self._db_tool is not None:
            agent_toolbox.add_tool(self._db_tool)

        get_logger().info("Initializing the agents...")

        await self._save_exp_info()
        self._save_context()
        get_logger().info("Experiment info saved")


        if self._resume_exp_id is None:
            await self._save_agent_static_info()
            get_logger().info("Agent static info saved")
        else:
            get_logger().info("Resume source experiment detected; skip saving static agent info to avoid duplication")

        init_funcs = self._config.agents.init_funcs
        for init_func in init_funcs:
            if inspect.iscoroutinefunction(init_func):
                await init_func(self)
            else:
                init_func(self)

    async def init(self):
        """Initialize all the components"""
        try:
            await self._init_database_writer_if_enabled()
            self._start_monitoring_services()
            metrics_tool = self._init_metrics_actor()
            self._init_clickhouse_actor()
            await self._init_core_components()
            await self._load_resume_state()

            agents = await self._prepare_agents()
            self._validate_resume_agent_count(agents)
            agent_toolbox = await self._initialize_agents(agents)
            await self._finalize_initialization(agent_toolbox, metrics_tool)

        except Exception as e:
            get_logger().error(f"Init error: {str(e)}\n{traceback.format_exc()}")
            self._exp_info.status = ExperimentStatus.ERROR.value
            self._exp_info.error = str(e)
            await self._save_exp_info()

            raise e
        get_logger().info("Init functions run")
        get_logger().info("Simulation initialized")

    async def close(self):
        """Close all the components"""

        # ==============================
        # close clickhouse
        # ===============================
        get_logger().info("Closing ClickHouse tool...")
        if self._db_actor is not None:
            try:
                await self._db_actor.close.remote()
            except Exception as e:
                get_logger().warning(f"Error closing ClickHouse actor: {e}")

        # ================================
        # stop monitoring
        # ================================
        get_logger().info("Stopping monitoring services...")
        stop_monitoring()

        # ===================================
        # close groups
        # ===================================

        get_logger().info("Closing agent groups...")
        close_tasks = []
        for agent in self._id2agent.values():
            close_tasks.append(agent.close())  # type:ignore
        await asyncio.gather(*close_tasks)
        get_logger().info("Agents closed")

        if self._environment is not None:
            get_logger().info("Closing environment...")
            await self._environment.close()
            self._environment = None
            get_logger().info("Environment closed")

    @property
    def name(self):
        return self._config.exp.name

    @property
    def config(self):
        return self._config

    @property
    def llm(self):
        assert self._llm is not None, "llm is not initialized"
        return self._llm

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
            return await self.filter(
                types=target_agent.agent_class, filter_str=target_agent.filter_str  # type: ignore
            )
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
        results = {}
        if target_agent_ids is None:
            target_agent_ids = list(self._id2agent.keys())
        if content == "stream_memory":
            for agent in self._id2agent.values():
                if agent.id in target_agent_ids:
                    results[agent.id] = await agent.stream.get_all()
        else:
            for agent in self._id2agent.values():
                if agent.id in target_agent_ids:
                    results[agent.id] = await agent.status.get(content)
        if flatten:
            if not keep_id:
                data_flatten = []
                for _, data in results.items():
                    data_flatten.append(data)
                return data_flatten
            else:
                data_flatten = {}
                for id, data in results.items():
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
            return list(self._id2agent.keys())
        # filter by types first
        if types:
            filtered_ids = [
                agent_id
                for agent_id, (agent_class, _) in self._filter_base.items()
                if any(issubclass(agent_class, t) for t in types)
            ]
        else:
            filtered_ids = list(self._id2agent.keys())

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

    async def update(
        self,
        target_agent_ids: list[int],
        target_key: str,
        content: Any,
        query: bool = False,
    ):
        """
        Update the memory of specified agents.

        - **Args**:
            - `target_agent_id` (list[int]): The IDs of the target agents to update.
            - `target_key` (str): The key in the agent's memory to update.
            - `content` (Any): The new content to set for the target key.
        """
        get_logger().debug(f"-----Updating {target_key} for agent {target_agent_ids}")
        tasks = []
        for agent_id in target_agent_ids:
            agent = self._id2agent[agent_id]
            if query:
                agent.gather_results[target_key] = content
            tasks.append(agent.status.update(target_key, content))
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
        survey_tasks = []
        for agent_id in agent_ids:
            agent = self._id2agent[agent_id]
            if isinstance(agent, CitizenAgentBase):
                survey_tasks.append(
                    agent._handle_survey_with_storage(
                        survey,
                        survey_day,
                        survey_t,
                        is_pending_survey,
                        pending_survey_id,
                    )
                )
            else:
                get_logger().error(
                    f"Agent {agent_id} is not a citizen agent, so skip the survey"
                )
        survey_responses = await asyncio.gather(*survey_tasks)
        return {
            agent_id: response
            for agent_id, response in zip(agent_ids, survey_responses)
        }

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
        day, t = self.environment.get_datetime()
        interview_tasks = []
        for agent_id in agent_ids:
            agent = self._id2agent[agent_id]
            if isinstance(agent, CitizenAgentBase):
                interview_tasks.append(
                    agent._handle_interview_with_storage(
                        Message(
                            from_id=None,
                            to_id=agent_id,
                            payload={"content": question},
                            kind=MessageKind.USER_CHAT,
                            day=day,
                            t=t,
                        )
                    )
                )
            else:
                get_logger().error(
                    f"Agent {agent_id} is not a citizen agent, so skip the interview"
                )
        interview_responses = await asyncio.gather(*interview_tasks)
        return {
            agent_id: response
            for agent_id, response in zip(agent_ids, interview_responses)
        }

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
        react_tasks = []
        for agent_id in agent_ids:
            agent = self._id2agent[agent_id]
            if isinstance(agent, CitizenAgentBase):
                react_tasks.append(agent.react_to_intervention(intervention_message))
            else:
                get_logger().error(
                    f"Agent {agent_id} is not in the group, so skip the intervention"
                )
        await asyncio.gather(*react_tasks)

    async def _save_exp_info(self) -> None:
        """Async save experiment info to YAML file and pgsql"""
        self._exp_info.updated_at = datetime.now(timezone.utc)
        if self.enable_database:
            assert self._database_writer is not None
            await self._database_writer.update_exp_info(self._exp_info)  # type: ignore
        if self._db_actor is not None:
            self._db_actor.insert_experiment_info_record.remote(
                {
                    "tenant_id": self._exp_info.tenant_id,
                    "id": self._exp_info.id,
                    "name": self._exp_info.name,
                    "num_day": self._exp_info.num_day,
                    "status": self._exp_info.status,
                    "cur_day": self._exp_info.cur_day,
                    "cur_t": self._exp_info.cur_t,
                    "config": self._exp_info.config,
                    "error": self._exp_info.error,
                    "input_tokens": self._exp_info.input_tokens,
                    "output_tokens": self._exp_info.output_tokens,
                    "created_at": self._exp_info.created_at,
                    "updated_at": self._exp_info.updated_at,
                }
            )

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
            await self._database_writer.write_global_prompt(prompt_info)  # type:ignore

    async def _gather_and_update_context(
        self, target_agent_ids: list[int], key: str, save_as: str
    ):
        """Gather and update the context"""
        try:
            values = await self.gather(
                key, target_agent_ids, flatten=True, keep_id=True
            )
            self.context[save_as] = values
        except Exception as e:
            get_logger().error(
                f"Error saving context: {str(e)}\n{traceback.format_exc()}"
            )
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

    # ====================
    # Message Handling Methods
    # ====================
    async def _message_dispatch(self):
        """
        Dispatches messages received via Message to the appropriate agents.
        """
        # Step 1: Fetch messages
        messages = await self.messager.fetch_received_messages()
        get_logger().info(f"Received {len(messages)} messages")

        try:
            # Step 2: Distribute messages to corresponding Agents
            # Separate messages into agent messages and aoi messages
            agent_messages = defaultdict(list)  # Dict[agent_id, list[Message]]
            aoi_messages = []  # List[Message]

            for message in messages:
                if message.kind in [MessageKind.AGENT_CHAT, MessageKind.USER_CHAT]:
                    agent_id = message.to_id
                    if agent_id in self._id2agent:
                        agent_messages[agent_id].append(message)
                elif message.kind in [
                    MessageKind.AOI_MESSAGE_REGISTER,
                    MessageKind.AOI_MESSAGE_CANCEL,
                ]:
                    aoi_messages.append(message)

            # Process agent messages in parallel for different agents
            async def process_agent_messages(agent_id: int, messages: list[Message]):
                agent = self._id2agent[agent_id]
                if isinstance(agent, CitizenAgentBase):
                    for message in messages:
                        if message.kind == MessageKind.AGENT_CHAT:
                            await agent._handle_agent_chat_with_storage(message)
                        elif message.kind == MessageKind.USER_CHAT:
                            await agent._handle_interview_with_storage(message)
                else:
                    get_logger().error(
                        f"Agent {agent_id} is not a citizen agent, so skip the message dispatch"
                    )

            # Process agent messages in parallel
            agent_tasks = [
                process_agent_messages(agent_id, msgs)
                for agent_id, msgs in agent_messages.items()
            ]
            await asyncio.gather(*agent_tasks)

            # Process aoi messages
            for message in aoi_messages:
                agent_id = message.from_id
                if message.kind == MessageKind.AOI_MESSAGE_REGISTER:
                    self.environment.register_aoi_message(
                        agent_id, message.to_id, message.payload["content"]
                    )
                elif message.kind == MessageKind.AOI_MESSAGE_CANCEL:
                    self.environment.cancel_aoi_message(agent_id, message.to_id)
        except Exception as e:
            get_logger().error(f"Error dispatching message: {e}")
            import traceback

            get_logger().error(f"Error dispatching message: {traceback.format_exc()}")

    async def _save(self, day: int, t: int):
        """
        Saves the current status of the agents at a given point in the simulation.

        - **Args**:
            - `day` (int): The day number in the simulation time.
            - `t` (int): The tick or time unit in the simulation day.
        """
        if self._database_writer is None:
            return
        created_at = datetime.now(timezone.utc)
        # =========================
        # build statuses data
        # =========================
        statuses = []
        for agent in self._id2agent.values():
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
                current_plan = await agent.status.get("current_plan", {})
                if current_plan is not None and current_plan:
                    step_index = current_plan.get("index", 0)
                    action = current_plan.get("steps", [])[step_index].get(
                        "intention", "Planning"
                    )
                else:
                    action = "Planning"
                status_summary = await agent.status.get("status_summary", "Nothing")
                status = StorageStatus(
                    id=agent.id,
                    day=day,
                    t=t,
                    lng=lng,
                    lat=lat,
                    parent_id=parent_id,
                    action=action,
                    status=status_summary,
                    created_at=created_at,
                )
                statuses.append(status)

                if self._db_actor:
                    self._db_actor.insert_step_agent_status_record.remote(
                        agent_id=agent.id,
                        lng=lng,
                        lat=lat,
                        parent_id=parent_id,
                        action=action,
                        status=status_summary,
                        timestamp=time.time(),
                    )

            elif isinstance(
                agent, (FirmAgentBase, BankAgentBase, NBSAgentBase, GovernmentAgentBase)
            ):
                status_summary = await agent.status.get("status_summary", "Nothing")
                status = StorageStatus(
                    id=agent.id,
                    day=day,
                    t=t,
                    lng=None,
                    lat=None,
                    parent_id=None,
                    action="",
                    status=status_summary,
                    created_at=created_at,
                )
                statuses.append(status)
            else:
                raise ValueError(f"Unknown agent type: {type(agent)}")
        if self._database_writer is not None:
            await self._database_writer.write_statuses(  # type:ignore
                statuses
            )

    async def delete_agents(self, target_agent_ids: list[int]):
        """
        Delete the specified agents.

        - **Args**:
            - `target_agent_ids` (list[int]): The IDs of the agents to delete.
        """
        tasks = []
        for agent_id in target_agent_ids:
            agent = self._id2agent[agent_id]
            tasks.append(agent.close())
        await asyncio.gather(*tasks)
        for agent_id in target_agent_ids:
            del self._id2agent[agent_id]

    async def next_round(self):
        """
        Proceed to the next round of the simulation.
        """
        get_logger().info("Start entering the next round of the simulation")
        tasks = []
        for agent in self._id2agent.values():
            tasks.append(agent.reset())  # type:ignore
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
            step_start = time.perf_counter()
            # ======================
            # run a step
            # ======================
            day, t = self.environment.get_datetime()
            get_logger().info(
                f"Start simulation day {day} at {t}, step {self._total_steps}"
            )
            # Add simulation step to ClickHouse
            if self._db_actor is not None:
                try:
                    await self._db_actor.set_simulation_step.remote(
                        step=self._total_steps,
                    )
                except Exception as e:
                    get_logger().warning(
                        f"Error adding simulation step to ClickHouse: {e}"
                    )

            await self._message_dispatch()
            # main agent workflow
            tasks = [agent.run() for agent in self._id2agent.values()]
            agent_time_log = await asyncio.gather(*tasks)
            simulator_log = (
                self.environment.get_log_list()
                + self.environment.economy_client.get_log_list()
            )
            log = Logs(
                llm_log=self.llm.get_log_list(),
                simulator_log=simulator_log,
                agent_time_log=agent_time_log,
            )
            self.llm.clear_log_list()
            self.environment.clear_log_list()
            self.environment.economy_client.clear_log_list()

            # gather query
            gather_queries = {}
            for agent in self._id2agent.values():
                if agent.gather_query:
                    gather_queries[agent.id] = agent.gather_query

            get_logger().debug(f"({day}-{t}) Finished agent forward steps")
            # ======================
            # log the simulation results
            # ======================
            all_logs = Logs(
                llm_log=[],
                simulator_log=[],
                agent_time_log=[],
            )
            all_logs.append(log)

            # ======================
            # Log metrics from BlockPerformance
            # ======================
            if self._metrics_actor is not None:
                try:
                    perf_stats = ray.get(
                        self._metrics_actor.get_block_performance_stats.remote()
                    )
                    if perf_stats:
                        #     for block_func, metrics in perf_stats.items():
                        #         get_logger().info(
                        #             f"  {block_func}: "
                        #             f"calls={metrics['calls']}, "
                        #             f"avg_duration={metrics['average_duration']:.3f}s, "
                        #             f"total_tokens_in={metrics['total_token_input']}, "
                        #             f"total_tokens_out={metrics['total_token_output']}"
                        #         )

                        # Convert nested stats to flat format for database
                        if self._database_writer is not None:
                            # Create list of metric tuples (key, value, step)
                            metric_tuples = []
                            for block_func, metrics in perf_stats.items():
                                metric_tuples.extend(
                                    [
                                        (
                                            f"bp.{block_func}.calls",
                                            metrics["calls"],
                                            self._total_steps,
                                        ),
                                        (
                                            f"bp.{block_func}.avg_duration",
                                            metrics["average_duration"],
                                            self._total_steps,
                                        ),
                                        (
                                            f"bp.{block_func}.total_token_input",
                                            metrics["total_token_input"],
                                            self._total_steps,
                                        ),
                                        (
                                            f"bp.{block_func}.total_token_output",
                                            metrics["total_token_output"],
                                            self._total_steps,
                                        ),
                                    ]
                                )

                            await self._database_writer.log_metric(metric_tuples)
                except Exception as e:
                    get_logger().warning(
                        f"Error retrieving performance stats: {str(e)}"
                    )
            else:
                get_logger().warning(
                    "No performance actor available to retrieve stats."
                )

            # ======================
            # Log metrics from RoutingTracker
            # ======================

            if self._metrics_actor is not None:
                try:
                    perf_stats = ray.get(self._metrics_actor.get_routing_stats.remote())
                    if perf_stats:
                        # for block_func, metrics in perf_stats.items():
                        #     get_logger().info(
                        #         f"  {block_func}: "
                        #         f"calls={metrics['calls']}, "
                        #         f"routing_ratio={metrics['routing_ratio']:.3f}, "

                        #     )

                        # Convert nested stats to flat format for database
                        if self._database_writer is not None:
                            # Create list of metric tuples (key, value, step)
                            metric_tuples = []
                            for block_func, metrics in perf_stats.items():
                                metric_tuples.extend(
                                    [
                                        (
                                            f"bp.{block_func}.calls",
                                            metrics["calls"],
                                            self._total_steps,
                                        ),
                                        (
                                            f"bp.{block_func}.routing_ratio",
                                            metrics["routing_ratio"],
                                            self._total_steps,
                                        ),
                                    ]
                                )

                            await self._database_writer.log_metric(metric_tuples)
                except Exception as e:
                    get_logger().warning(
                        f"Error retrieving performance stats: {str(e)}"
                    )
            else:
                get_logger().warning(
                    "No performance actor available to retrieve stats."
                )

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
            for agent_id, group_queries in gather_queries.items():
                for query_key, query in group_queries.items():
                    result = await self.gather(query.key, query.target_agent_ids, flatten=query.flatten, keep_id=query.keep_id)  # type: ignore
                    await self.update([agent_id], query.key, result, query=True)  # type: ignore

            # ======================
            # save the simulation results
            # ======================
            await self._save(day, t)
            # save global prompt
            await self._save_global_prompt(
                prompt=self.environment.get_environment(),
                day=day,
                t=t,
            )
            get_logger().debug(f"({day}-{t}) Finished saving simulation results")
            # ======================
            # forward message
            # ======================
            all_messages = await self.messager.fetch_pending_messages()
            get_logger().info(
                f"({day}-{t}) Finished fetching pending messages. {len(all_messages)} messages fetched."
            )

            if self._message_interceptor is not None:
                all_messages = await self._message_interceptor.forward(all_messages)
            # ======================
            # fetch pending dialogs from USER
            # ======================
            if self.enable_database:
                pending_dialogs = await self._database_writer.fetch_pending_dialogs()  # type: ignore
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
            await self.messager.set_received_messages(all_messages)
            get_logger().info(f"({day}-{t}) Finished setting received messages")
            # ======================
            # handle pending surveys
            # ======================
            if self.enable_database:
                pending_surveys = await self._database_writer.fetch_pending_surveys()  # type: ignore
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

            # ========================
            # Log step duration
            # ========================
            step_end = time.perf_counter()
            step_duration = step_end - step_start
            get_logger().info(
                f"Finished simulation day {day} at {t}, step {self._total_steps} in {step_duration:.3f} seconds"
            )
            if self.enable_database:
                await self._database_writer.log_metric(
                    [
                        (
                            "simulation.step_duration_seconds",
                            step_duration,
                            self._total_steps,
                        )
                    ]
                )

                self._metrics_actor.record_simulation_step_duration.remote(
                    step_duration
                )

            # ======================
            # Log metrics from environment
            # ======================
            metrics = await self.environment.get_metrics()
            if self.enable_database:
                await self._database_writer.log_metric(metrics)
            get_logger().debug(f"({day}-{t}) Finished simulator sync")
            # ======================
            # go to next step
            # ======================
            self._total_steps += 1
            await self.environment.step(num_environment_ticks)
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
                    await self._gather_and_update_context(
                        target_agent_ids, step.key, step.save_as
                    )
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
