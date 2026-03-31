"""Infrastructure lifecycle management for SimulationEngine."""

import asyncio
import os
import yaml
import inspect
from copy import deepcopy
from enum import Enum
from multiprocessing import cpu_count
from typing import Any, Optional, Union

from fastembed import SparseTextEmbedding

from ..agent import Agent, CustomTool, CitizenAgentBase
from ..configs import Config
from ..database.database_actor import DatabaseActor
from ..environment import EnvironmentStarter
from ..llm import LLM
from ..logger import attach_otlp_handler, get_logger, set_exp_id
from ..message import MessageInterceptor, Messager
from ..performance.monitoring import start_monitoring, stop_monitoring
from ..performance.prometheusActor import PrometheusActor
from ..storage import DatabaseWriter
from ..storage.type import StorageExpInfo

__all__ = ["InfrastructureManager"]


class InfrastructureManager:
    """Initialize and tear down external services used by the simulation."""

    def __init__(
        self,
        config: Config,
        tenant_id: str,
        exp_id: str,
        exp_info: StorageExpInfo,
    ) -> None:
        self._config = config
        self._tenant_id = tenant_id
        self._exp_id = exp_id
        self._exp_info = exp_info

        self._llm: Optional[LLM] = None
        self._environment: Optional[EnvironmentStarter] = None
        self._message_interceptor: Optional[MessageInterceptor] = None
        self._database_writer: Optional[DatabaseWriter] = None
        self._embedding: Optional[SparseTextEmbedding] = None
        self._metrics_actor: Optional[PrometheusActor] = None
        self._db_actor: Optional[DatabaseActor] = None
        self._messager: Optional[Messager] = None
        self._metrics_tool: Optional[CustomTool] = None
        self._db_tool: Optional[CustomTool] = None
        self._resume_exp_id: Optional[str] = None
        self._resume_state: Optional[dict[str, Any]] = None

    @property
    def llm(self) -> Optional[LLM]:
        return self._llm

    @property
    def environment(self) -> Optional[EnvironmentStarter]:
        return self._environment

    @property
    def message_interceptor(self) -> Optional[MessageInterceptor]:
        return self._message_interceptor

    @property
    def database_writer(self) -> Optional[DatabaseWriter]:
        return self._database_writer

    @property
    def embedding(self) -> Optional[SparseTextEmbedding]:
        return self._embedding

    @property
    def metrics_actor(self) -> Optional[PrometheusActor]:
        return self._metrics_actor

    @property
    def db_actor(self) -> Optional[DatabaseActor]:
        return self._db_actor

    @property
    def messager(self) -> Optional[Messager]:
        return self._messager

    @property
    def metrics_tool(self) -> Optional[CustomTool]:
        return self._metrics_tool

    @property
    def db_tool(self) -> Optional[CustomTool]:
        return self._db_tool

    @property
    def resume_state(self) -> Optional[dict[str, Any]]:
        return self._resume_state

    def set_resume_exp_id(self, resume_exp_id: Optional[str]) -> None:
        """Set the resume experiment ID."""
        self._resume_exp_id = resume_exp_id

    @staticmethod
    def _normalize_config_value(value: Any) -> Any:
        """Convert Python objects from YAML into deterministic, comparable values."""
        if isinstance(value, dict):
            normalized_items = []
            for k, v in value.items():
                normalized_key = InfrastructureManager._normalize_config_value(k)
                normalized_value = InfrastructureManager._normalize_config_value(v)
                normalized_items.append((normalized_key, normalized_value))
            normalized_items.sort(key=lambda item: str(item[0]))
            return {k: v for k, v in normalized_items}

        if isinstance(value, (list, tuple, set)):
            normalized_list = [InfrastructureManager._normalize_config_value(v) for v in value]
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
        """Normalize resume configuration for comparison."""
        if isinstance(raw_config, str):
            try:
                loaded = yaml.safe_load(raw_config) or {}
            except yaml.YAMLError:
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

        normalized = InfrastructureManager._normalize_config_value(loaded)
        if isinstance(normalized, dict):
            return normalized
        return {}

    @staticmethod
    def _count_citizen_agents(agents: list[tuple[Any, ...]]) -> int:
        """Count citizen agents in agent initialization list."""
        count = 0
        for agent_init in agents:
            _, agent_class, *_ = agent_init
            if issubclass(agent_class, CitizenAgentBase):
                count += 1
        return count

    def _validate_resume_agent_count(
        self, agents: list[tuple[Any, ...]]
    ) -> None:
        """Validate citizen agent count matches resume source."""
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

    async def load_resume_state(self) -> None:
        """Load resume metadata from ClickHouse when resume_exp_id is set."""
        if not self._resume_exp_id:
            return

        if self._db_actor is None:
            raise RuntimeError("ClickHouse actor is required when resume exp_id is set")

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
        get_logger().info(
            f"Loaded resume state from exp_id={self._resume_exp_id} at step={resume_data.get('latest_step', 0)}"
        )

    async def _init_embedding(self):
        """Initialize embedding model with timeout."""
        try:
            init_task = asyncio.create_task(self._init_embedding_task())
            try:
                await asyncio.wait_for(init_task, timeout=120)
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
        """Initialize the database writer when database is enabled."""
        if self._config.env.db.enabled:
            get_logger().info("Initializing database writer...")
            self._database_writer = DatabaseWriter(
                self._tenant_id,
                self._exp_id,
                self._config.env.db,
                self._config.env.home_dir,
            )
            await self._database_writer.init()  # type: ignore
            get_logger().info("Database writer initialized")
            await self._database_writer.update_exp_info(self._exp_info)

    def _start_monitoring_services(self):
        """Initialize Prometheus and Grafana monitoring services."""
        if not self._config.env.monitoring_enabled:
            get_logger().info("Monitoring disabled by config, skipping.")
            return
        try:
            start_monitoring(self._config.env.data_dir)
            set_exp_id(self._exp_id)
            attach_otlp_handler()
            return self._init_metrics_actor()
        except Exception as e:
            get_logger().warning(f"Failed to start monitoring services: {e}")

    def _init_metrics_actor(self) -> Optional[CustomTool]:
        """Initialize the Prometheus actor and return it as a toolbox tool."""
        try:
            get_logger().info(
                f"Initializing Prometheus actor with exp_id={self._exp_id}...",
            )
            metrics_actor = PrometheusActor.remote(self._exp_id)
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
        if not self._config.env.database_enabled:
            get_logger().info("Database disabled by config, skipping ClickHouse actor.")
            return
        try:
            clickhouse_cfg = self._config.env.clickhouse
            self._db_actor = DatabaseActor.remote(
                exp_id=self._exp_id,
                home_dir=self._config.env.data_dir,
                host=clickhouse_cfg.host,
                port=clickhouse_cfg.port,
                username=clickhouse_cfg.username,
                password=clickhouse_cfg.password,
                database=clickhouse_cfg.database,
                batch_size=clickhouse_cfg.batch_size,
                batch_timeout=clickhouse_cfg.batch_timeout,
                auto_create_database=clickhouse_cfg.auto_create_database,
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
                self._tenant_id,
                self._exp_id,
                "simulator_log",
            ),
            self._config.env.home_dir,
        )
        await self._environment.init()
        get_logger().info("Environment initialized")

        get_logger().info("Initializing messager...")
        if self._config.agents.supervisor is not None:
            self._message_interceptor = MessageInterceptor(self._config.llm)
        self._messager = Messager(exp_id=self._exp_id)
        get_logger().info("Messager initialized")

        get_logger().info("Initializing embedding...")
        await self._init_embedding()
        assert self._embedding is not None, "Embedding is not initialized"
        get_logger().info("Embedding initialized")

    async def initialize_all(self):
        """Initialize all infrastructure components used by the simulation engine."""
        await self._init_database_writer_if_enabled()
        self._metrics_tool = self._start_monitoring_services()
        self._init_clickhouse_actor()
        await self._init_core_components()

    async def close(self):
        """Close all infrastructure components initialized by this manager."""
        get_logger().info("Closing ClickHouse tool...")
        if self._db_actor is not None:
            try:
                await self._db_actor.close.remote()
            except Exception as e:
                get_logger().warning(f"Error closing ClickHouse actor: {e}")

        if self._database_writer is not None:
            try:
                await self._database_writer.close()
            except Exception as e:
                get_logger().warning(f"Error closing database writer: {e}")

        if self._config.env.monitoring_enabled:
            get_logger().info("Stopping monitoring services...")
            stop_monitoring()

        if self._environment is not None:
            get_logger().info("Closing environment...")
            await self._environment.close()
            self._environment = None
            get_logger().info("Environment closed")
