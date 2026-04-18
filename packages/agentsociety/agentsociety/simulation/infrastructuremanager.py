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
from ..agent.dispatcher_cache_actor import GlobalDispatcherCacheActor
from ..configs import Config
from ..database import ClickHouseConfig
from ..database.database_actor import DatabaseActor
from ..environment import EnvironmentStarter
from ..llm import LLM, QdrantCacheActor, RoutingLLM
from ..llm.cache import EmbedActor
from ..logger import attach_otlp_handler, get_logger, set_exp_id
from ..message import MessageInterceptor, Messager
from ..performance.monitoring import start_monitoring, stop_monitoring
from ..performance.prometheusActor import PrometheusActor
from ..storage import DatabaseWriter
from ..storage.type import StorageExpInfo
from .type import ExperimentStatus

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
        self._dispatcher_cache_actor: Optional[Any] = None
        self._embed_actor: Optional[Any] = None
        self._llm_cache_actor: Optional[Any] = None
        self._metrics_tool: Optional[CustomTool] = None
        self._db_tool: Optional[CustomTool] = None
        self._dispatcher_cache_tool: Optional[CustomTool] = None
        self._llm_cache_tool: Optional[CustomTool] = None
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
    def dispatcher_cache_tool(self) -> Optional[CustomTool]:
        return self._dispatcher_cache_tool

    @property
    def llm_cache_tool(self) -> Optional[CustomTool]:
        return self._llm_cache_tool

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
            exp_config.pop("logging", None)

        env_config = loaded.get("env")
        if isinstance(env_config, dict):
            env_config.pop("exp_id", None)
            env_config.pop("db", None)
            env_config.pop("clickhouse", None)
            env_config.pop("s3", None)
            env_config.pop("logging_level", None)
            env_config.pop("monitoring_enabled", None)
            env_config.pop("data_dir", None)
            env_config.pop("home_dir", None)

        normalized = InfrastructureManager._normalize_config_value(loaded)
        if isinstance(normalized, dict):
            return normalized
        return {}

    @staticmethod
    def _compute_config_diff(a: dict, b: dict, path: str = "") -> list[str]:
        """Recursively compare two dicts and return a list of human-readable diff lines.

        Args:
            a: Source dictionary
            b: Current dictionary
            path: Current path prefix for nested keys (internal use)

        Returns:
            List of diff lines like "env.qdrant_cache.enabled: source=False, current=True"
        """
        diffs = []

        # Get all keys from both dicts
        all_keys = set(a.keys()) | set(b.keys())

        for key in sorted(all_keys):
            current_path = f"{path}.{key}" if path else key

            value_a = a.get(key)
            value_b = b.get(key)

            # Both are dicts, recurse
            if isinstance(value_a, dict) and isinstance(value_b, dict):
                diffs.extend(InfrastructureManager._compute_config_diff(value_a, value_b, current_path))
            # Both are lists, compare as-is
            elif isinstance(value_a, list) and isinstance(value_b, list):
                if value_a != value_b:
                    diffs.append(f"{current_path}: source={value_a}, current={value_b}")
            # Different types or different values
            elif value_a != value_b:
                diffs.append(f"{current_path}: source={value_a}, current={value_b}")

        return diffs

    def _validate_resume_agent_count(
        self, agents: list[tuple[Any, ...]]
    ) -> None:
        """Validate total agent count matches KV snapshot count from resume source.

        Compares the total number of agents configured for this run (citizens +
        institutions) against the number of unique agent IDs found in the KV
        snapshot table.  Old snapshots that contain only citizens will produce
        a warning instead of an error so that backward-compat is preserved.

        Args:
            agents: List of agent initialization tuples produced by
                ``AgentManager.prepare_agents``.

        @usedBy: simulationengine.SimulationEngine.init
        """
        if self._resume_state is None:
            return

        kv_snapshots = self._resume_state.get("kv_snapshots", {})
        expected_total = len(agents)
        available_total = len(kv_snapshots)

        if expected_total == available_total:
            return

        # Count citizens only to distinguish old-snapshot compat from a real mismatch.
        expected_citizens = sum(
            1 for agent_init in agents
            if issubclass(agent_init[1], CitizenAgentBase)
        )
        if available_total == expected_citizens:
            get_logger().warning(
                f"Resume source experiment '{self._resume_exp_id}' snapshot contains "
                f"only citizen agents ({available_total}), but this run has "
                f"{expected_total} total agents (including institutions). "
                "Institution agent memory will be re-initialized from config."
            )
            return

        raise ValueError(
            f"Agent number mismatch for resume source experiment '{self._resume_exp_id}': "
            f"configured total={expected_total} (citizens={expected_citizens}), "
            f"kv snapshot agent count={available_total}"
        )

    async def load_resume_state(self, expected_agent_ids: Optional[set[int]] = None) -> None:
        """Load resume metadata from database backends when resume_exp_id is set.

        Args:
            expected_agent_ids: Set of agent IDs expected in the snapshot.  When
                provided, the completeness check inside
                ``_fetch_checkpoint_snapshots`` is activated and the system will
                roll back to an earlier step if any of these IDs are missing from
                the chosen snapshot.  Pass ``None`` (or omit) to skip the check.

        @usedBy: simulationengine.SimulationEngine.init
        Side effects: sets ``self._resume_state``.
        """
        if not self._resume_exp_id:
            return

        if self._db_actor is None:
            raise RuntimeError("Database actor is required when resume exp_id is set")

        resume_data = await self._db_actor.fetch_resume_data.remote(
            self._resume_exp_id,
            rollback_depth=self._config.env.resume_rollback_depth,
            expected_agent_ids=expected_agent_ids if expected_agent_ids is not None else set(),
        )
        if resume_data is None:
            get_logger().warning(
                f"No resume data found for experiment id '{self._resume_exp_id}'"
            )
            return

        latest_exp_info = resume_data.get("latest_experiment_info", {})
        source_status = latest_exp_info.get("status")
        if source_status == ExperimentStatus.FINISHED.value:
            raise ValueError(
                f"Cannot resume experiment '{self._resume_exp_id}': it has already FINISHED."
            )

        source_config = self._normalize_resume_config(resume_data.get("config", ""))
        current_config = self._normalize_resume_config(self._exp_info.config)

        # Compute config differences
        diff_lines = self._compute_config_diff(source_config, current_config)

        if diff_lines:
            # Format multi-line diff message
            diff_message = (
                "Configuration mismatch with resume experiment. "
                "The following fields differ between source and current config:\n"
                + "\n".join(f"  {line}" for line in diff_lines)
            )

            # Handle based on configured action
            if self._config.env.resume_config_mismatch_action == "error":
                raise ValueError(diff_message)
            elif self._config.env.resume_config_mismatch_action == "warn":
                get_logger().warning(diff_message)

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
        """Initialize the simulation database actor and corresponding toolbox tool."""
        if not self._config.env.database_enabled:
            get_logger().info("Database disabled by config, skipping database actor.")
            return
        try:
            clickhouse_cfg = self._config.env.clickhouse
            self._db_actor = DatabaseActor.remote(
                exp_id=self._exp_id,
                home_dir=self._config.env.data_dir,
                clickhouse_config=ClickHouseConfig(
                    host=clickhouse_cfg.host,
                    port=clickhouse_cfg.port,
                    username=clickhouse_cfg.username,
                    password=clickhouse_cfg.password,
                    database=clickhouse_cfg.database,
                    auto_create_database=clickhouse_cfg.auto_create_database,
                ),
                batch_size=clickhouse_cfg.batch_size,
                batch_timeout=clickhouse_cfg.batch_timeout,
                metrics_actor=self._metrics_actor,
            )
            self._db_tool = CustomTool(
                name="db_actor",
                tool=self._db_actor,
                description="Ray actor for storing simulation data in the simulation database backend",
            )
            get_logger().info("Simulation database actor initialized")
        except Exception as e:
            get_logger().warning(f"Failed to initialize simulation database actor: {e}")

    def _init_dispatcher_cache_actor(self):
        """Initialize a global dispatcher cache actor and corresponding toolbox tool."""
        try:
            self._dispatcher_cache_actor = GlobalDispatcherCacheActor.remote(
                data_dir=self._config.env.data_dir,
                llm_model_name=self._config.llm[0].model if self._config.llm else None,
                metrics_actor=self._metrics_actor,
            )
            self._dispatcher_cache_tool = CustomTool(
                name="dispatcher_cache_actor",
                tool=self._dispatcher_cache_actor,
                description="Ray actor for global block dispatcher cache",
            )
            get_logger().info("Global dispatcher cache actor initialized")
        except Exception as e:
            get_logger().warning(f"Failed to initialize global dispatcher cache actor: {e}")

    def _init_llm_cache_actor(self):
        """Initialize Qdrant-backed LLM semantic cache actor and tool.

        Creates EmbedActor first (owns the fastembed model), then creates
        QdrantCacheActor (owns the Qdrant client) and passes the EmbedActor
        handle to it. Both actors are torn down in close().
        """
        cfg = self._config.env.qdrant_cache
        if not cfg.enabled:
            get_logger().info("Qdrant LLM cache disabled by config, skipping.")
            return

        qdrant_path = cfg.path or os.path.join(self._config.env.data_dir, "qdrant")
        embedding_cache_dir = cfg.embedding_cache_dir or os.path.join(
            self._config.env.home_dir,
            "huggingface_cache",
        )

        os.makedirs(qdrant_path, exist_ok=True)

        try:
            self._embed_actor = EmbedActor.remote(
                embedding_model=cfg.embedding_model,
                embedding_cache_dir=embedding_cache_dir,
                batch_timeout_ms=cfg.embed_batch_timeout_ms,
                max_batch_size=cfg.embed_max_batch_size,
                metrics_actor=self._metrics_actor,
            )
            self._llm_cache_actor = QdrantCacheActor.remote(
                qdrant_path=qdrant_path,
                embed_actor=self._embed_actor,
                probability_threshold=cfg.probability_threshold,
                batch_size=cfg.batch_size,
                n_neighbors=cfg.n_neighbors,
                distance_quantile=cfg.distance_quantile,
                llm_model_name=self._config.llm[0].model,
                exp_id=self._exp_id,
                metrics_actor=self._metrics_actor,
                min_rebuild_threshold=cfg.min_rebuild_threshold,
                tournament_sample_size=cfg.tournament_sample_size,
            )
            self._llm_cache_tool = CustomTool(
                name="llm_cache_actor",
                tool=self._llm_cache_actor,
                description="Ray actor for Qdrant-backed LLM semantic cache",
            )
            get_logger().info(f"Qdrant LLM cache actor initialized at {qdrant_path}")
        except Exception as e:
            get_logger().warning(f"Failed to initialize LLM cache actor: {e}")

    async def _init_core_components(self):
        """Initialize LLM, environment, messager, and embedding components."""
        get_logger().info("Initializing LLM...")
        self._llm = LLM(
            self._config.llm,
            metrics_actor=self._metrics_actor,
            db_actor=self._db_actor,
            cache_actor=self._llm_cache_actor,
            cache_skip_mode=self._config.env.qdrant_cache.skip_mode,
        )
        if self._config.routing:
            n_keys = sum(len(e.prompt_identities) for e in self._config.routing)
            get_logger().info(f"LLM routing enabled for {n_keys} prompt key(s)")
            self._llm = RoutingLLM(
                base_llm=self._llm,
                routing_entries=self._config.routing,
                metrics_actor=self._metrics_actor,
                db_actor=self._db_actor,
                cache_actor=self._llm_cache_actor,
                cache_skip_mode=self._config.env.qdrant_cache.skip_mode,
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
            sim_bin_name=self._config.env.sim_bin_name,
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
        self._init_dispatcher_cache_actor()
        self._init_llm_cache_actor()
        await self._init_core_components()

    async def close(self):
        """Close all infrastructure components initialized by this manager."""
        get_logger().info("Closing ClickHouse tool...")
        if self._dispatcher_cache_actor is not None:
            try:
                await self._dispatcher_cache_actor.close.remote()
            except Exception as e:
                get_logger().warning(f"Error closing dispatcher cache actor: {e}")

        if self._llm_cache_actor is not None:
            try:
                await self._llm_cache_actor.close.remote()
            except Exception as e:
                get_logger().warning(f"Error closing LLM cache actor: {e}")

        if self._embed_actor is not None:
            try:
                await self._embed_actor.close.remote()
            except Exception as e:
                get_logger().warning(f"Error closing embed actor: {e}")

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
