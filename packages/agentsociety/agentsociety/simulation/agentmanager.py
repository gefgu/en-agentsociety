"""
Agent Manager for handling agent creation, initialization, and lifecycle management.

This module provides the AgentManager class, which is responsible for:
1. Creating agents from configurations
2. Initializing agents and their memory
3. Managing agent lifetimes (init, run, close, delete)
4. Storing and retrieving agent memory
5. Filtering and querying agents
"""

import asyncio
import json
from copy import deepcopy
from datetime import datetime
from typing import Any, Optional, Union, cast

from ..agent import (
    Agent,
    AgentToolbox,
    CitizenAgentBase,
)
from ..agent.distribution import DistributionConfig, DistributionType
from ..agent.memory_config_generator import (
    MemoryConfigGenerator,
)
from ..configs import AgentConfig, AgentFilterConfig, Config
from ..database.database_actor import DatabaseActor
from ..database.schema import StaticAgentAttributesRecord
from ..logger import get_logger
from ..llm import LLM
from ..memory import Memory
from ..memory.memory import MemoryNode, SpatialMemoryNode
from ..storage import DatabaseWriter
from ..storage.type import StorageProfile
from .utils import init_agent_class, evaluate_filter

__all__ = ["AgentManager"]

MIN_ID = 1
MAX_ID = 100000000
class AgentManager:
    """
    Manages the lifecycle and execution of all agents in the simulation.

    Responsibilities:
    - Agent creation from configurations
    - Agent initialization including memory setup
    - Agent storage and retrieval
    - Agent memory management (storage and retrieval)
    - Agent execution (running agents in each step)
    - Agent filtering and querying
    - Agent lifecycle events (init, close, delete)
    """

    def __init__(
        self,
        config: Config,
        llm: LLM,
        environment: Any,  # EnvironmentStarter
        messager: Any,  # Messager
        message_interceptor: Optional[Any] = None,  # MessageInterceptor
        embedding: Optional[Any] = None,  # SparseTextEmbedding
        database_writer: Optional[DatabaseWriter] = None,
        db_actor: Optional[DatabaseActor] = None,
        exp_id: str = "",
    ):
        """
        Initialize the AgentManager.

        Args:
            config: The configuration object
            llm: The language model instance
            environment: The environment instance
            messager: The messager instance
            embedding: The embedding model instance (optional)
            database_writer: The database writer instance (optional)
            db_actor: The database actor instance (optional)
            exp_id: The experiment ID
        """
        self._config = config
        self._llm = llm
        self._environment = environment
        self._messager = messager
        self._message_interceptor = message_interceptor
        self._embedding = embedding
        self._database_writer = database_writer
        self._db_actor = db_actor
        self._exp_id = exp_id

        # Agent storage
        self._id2agent: dict[int, Agent] = {}
        self._filter_base: dict[int, tuple[type[Agent], dict[str, Any]]] = {}

        # Agent initialization tracking
        self._agent_toolbox: Optional[AgentToolbox] = None

    @property
    def agents(self) -> dict[int, Agent]:
        """Get all agents by ID."""
        return self._id2agent

    @property
    def agent_ids(self) -> list[int]:
        """Get all agent IDs."""
        return list(self._id2agent.keys())

    def get_agent(self, agent_id: int) -> Optional[Agent]:
        """Get a specific agent by ID."""
        return self._id2agent.get(agent_id)

    async def create_toolbox(self) -> AgentToolbox:
        """
        Create the agent toolbox used by all agents.

        Returns:
            AgentToolbox: The toolbox instance
        """
        from ..message import Messager

        self._agent_toolbox = AgentToolbox(
            llm=self._llm,
            environment=self._environment,
            messager=self._messager,
            embedding=self._embedding,
            database_writer=self._database_writer,
        )
        return self._agent_toolbox

    @staticmethod
    def _count_citizen_agents(agents: list[tuple[Any, ...]]) -> int:
        """Count the number of citizen agents in a list of agent tuples."""
        count = 0
        for agent_init in agents:
            _, agent_class, *_ = agent_init
            if issubclass(agent_class, CitizenAgentBase):
                count += 1
        return count

    @staticmethod
    def _static_record_to_memory_updates(static_record: dict[str, Any]) -> dict[str, Any]:
        """Convert a static database record to memory update format."""
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

    async def prepare_agents(
        self,
        agent_configs: Optional[list[AgentConfig]] = None,
        resume_state: Optional[dict[str, Any]] = None,
    ) -> list[tuple[Any, ...]]:
        """
        Prepare agent initialization tuples from configurations.

        This method processes agent configurations and creates initialization tuples
        that can be used to instantiate agents later.

        Args:
            agent_configs: List of agent configurations
            resume_state: Resume state data if resuming a simulation

        Returns:
            List of agent initialization tuples
        """
        del agent_configs, resume_state

        agents: list[tuple[Any, ...]] = []
        next_id = 1
        defined_ids: set[int] = set()

        def _find_next_id() -> int:
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
            firm_classes, _ = init_agent_class(agent_config, self._config.env.s3)
            firms = [(_find_next_id(), *firm_class) for firm_class in firm_classes]
            firm_ids.update([firm[0] for firm in firms])
            agents += firms

        for agent_config in agent_configs_normal["banks"]:
            bank_classes, _ = init_agent_class(agent_config, self._config.env.s3)
            banks = [(_find_next_id(), *bank_class) for bank_class in bank_classes]
            bank_ids.update([bank[0] for bank in banks])
            agents += banks

        for agent_config in agent_configs_normal["nbs"]:
            nbs_classes, _ = init_agent_class(agent_config, self._config.env.s3)
            nbs = [(_find_next_id(), *nbs_class) for nbs_class in nbs_classes]
            nbs_ids.update([nbs_agent[0] for nbs_agent in nbs])
            agents += nbs

        for agent_config in agent_configs_normal["governments"]:
            government_classes, _ = init_agent_class(agent_config, self._config.env.s3)
            governments = [
                (_find_next_id(), *government_class)
                for government_class in government_classes
            ]
            government_ids.update([government[0] for government in governments])
            agents += governments

        for agent_config in agent_configs_normal["citizens"]:
            citizen_classes, generator = init_agent_class(agent_config, self._config.env.s3)
            citizen_generators.append(generator)
            citizens = [(_find_next_id(), *citizen_class) for citizen_class in citizen_classes]
            citizen_ids.update([citizen[0] for citizen in citizens])
            agents += citizens

        for agent_config in agent_configs_normal["supervisor"]:
            supervisor_classes, _ = init_agent_class(agent_config, self._config.env.s3)
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
                    environment=self._environment,
                    embedding=self._embedding,
                    memory_config=memory_config,
                )
                if agent_config.blocks is not None:
                    assert self._agent_toolbox is not None
                    blocks = [
                        block_type(
                            toolbox=self._agent_toolbox,
                            agent_memory=memory_init,
                            block_params=block_type.ParamsType.model_validate(block_params),
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

                assert self._agent_toolbox is not None
                supervisor = agent_config.agent_class(
                    id=agent_id,
                    name=f"{agent_config.agent_class.__name__}_{agent_id}",
                    toolbox=self._agent_toolbox,
                    memory=memory_init,
                    agent_params=agent_params,
                    blocks=blocks,
                )
                if self._message_interceptor is not None:
                    await self._message_interceptor.set_supervisor(supervisor)
                break

    async def initialize_agents(
        self,
        agents: list[tuple[Any, ...]],
        resume_state: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Instantiate and initialize agents.

        Creates actual agent instances from initialization tuples, runs init hooks,
        and builds profile/embedding data.

        Args:
            agents: List of agent initialization tuples
            resume_state: Resume state data if resuming a simulation

        Raises:
            ValueError: If initialization fails for any agent
        """
        if self._agent_toolbox is None:
            raise RuntimeError("Agent toolbox not created. Call create_toolbox() first.")

        get_logger().info(f"Initializing {len(agents)} agents...")
        resume_static_by_agent_id: dict[int, dict[str, Any]] = {}
        if resume_state is not None:
            for record in resume_state.get("static_records", []):
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
            self._filter_base[agent_id] = (agent_class, deepcopy(memory_config))

            memory_init = Memory(
                environment=self._environment,
                embedding=self._embedding,
                memory_config=memory_config,
            )

            # Apply resume state if available
            if resume_state is not None and issubclass(agent_class, CitizenAgentBase):
                static_record = resume_static_by_agent_id.get(agent_id)
                if static_record is None:
                    raise ValueError(
                        f"Missing static resume data for citizen agent id {agent_id}"
                    )
                static_updates = self._static_record_to_memory_updates(static_record)
                static_keys = set(static_updates.keys())
                for key, value in static_updates.items():
                    if value is not None:
                        await memory_init.status.update(key, value, mode="replace")

                # Restore dynamic KV snapshot (skip static keys already applied)
                kv_snapshots = resume_state.get("kv_snapshots", {})
                kv_entries = kv_snapshots.get(agent_id, [])
                for entry in kv_entries:
                    key = entry.get("key", "")
                    if not key or key in static_keys:
                        continue
                    try:
                        value = json.loads(entry["value_json"])
                    except (json.JSONDecodeError, KeyError):
                        continue
                    await memory_init.status.update(key, value, mode="replace")

                # Restore stream memory
                stream_snapshots = resume_state.get("stream_snapshots", {})
                stream_entries = stream_snapshots.get(agent_id, [])
                if stream_entries:
                    for entry in stream_entries:
                        node = MemoryNode(
                            id=int(entry.get("memory_id") or 0),
                            topic=str(entry.get("topic", "")),
                            location=str(entry.get("location", "")),
                            description=str(entry.get("description", "")),
                            day=int(entry.get("day", 0)),
                            t=int(entry.get("t", 0)),
                            cognition_id=entry.get("cognition_id"),
                        )
                        memory_init.stream._memories.append(node)
                        if memory_init.stream._memory_id_counter <= node.id:
                            memory_init.stream._memory_id_counter = node.id + 1

                # Restore spatial memory
                spatial_snapshots = resume_state.get("spatial_snapshots", {})
                spatial_entries = spatial_snapshots.get(agent_id, [])
                for entry in spatial_entries:
                    loc_id = str(entry.get("location_id", ""))
                    if not loc_id:
                        continue
                    node = SpatialMemoryNode(
                        location_id=loc_id,
                        description=str(entry.get("description", "")),
                        price=float(entry.get("price", 0.5)),
                        atmosphere=float(entry.get("atmosphere", 0.5)),
                        satisfaction=float(entry.get("satisfaction", 0.5)),
                        convenience=float(entry.get("convenience", 0.5)),
                        uncertainty=float(entry.get("uncertainty", 0.25)),
                    )
                    memory_init.spatial._locations[loc_id] = node

            # Create blocks if provided
            if blocks is not None:
                blocks = [
                    block_type(
                        toolbox=self._agent_toolbox,
                        agent_memory=memory_init,
                        block_params=block_type.ParamsType.model_validate(block_params),
                    )
                    for block_type, block_params in blocks.items()
                ]
            else:
                blocks = None

            # Create the agent instance
            agent = agent_class(
                id=agent_id,
                name=f"{agent_class.__name__}_{agent_id}",
                toolbox=self._agent_toolbox,
                memory=memory_init,
                agent_params=agent_params,
                blocks=blocks,
            )
            self._id2agent[agent_id] = agent

        # Run init hooks for all agents
        get_logger().info("Running agent.init() hooks...")
        tasks = [agent.init() for agent in self._id2agent.values()]
        await asyncio.gather(*tasks)

        # Export and save profiles
        get_logger().info("Exporting agent profiles...")
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

        # Initialize embeddings
        get_logger().info("Initializing agent embeddings...")
        embedding_tasks = [agent.memory.initialize_embeddings() for agent in self._id2agent.values()]
        await asyncio.gather(*embedding_tasks)
        get_logger().info("All agents initialized successfully")

    async def run_all_agents(self) -> list[Any]:
        """
        Run all agents for one simulation step.

        Returns:
            List of time logs from agent execution
        """
        tasks = [agent.run() for agent in self._id2agent.values()]
        agent_time_log = await asyncio.gather(*tasks)
        return agent_time_log

    async def close_all_agents(self) -> None:
        """Close all agents and clean up resources."""
        get_logger().info("Closing all agents...")
        close_tasks = [agent.close() for agent in self._id2agent.values()]  # type:ignore
        await asyncio.gather(*close_tasks)
        get_logger().info("All agents closed")

    async def delete_agents(self, agent_ids: list[int]) -> None:
        """
        Delete specified agents.

        Args:
            agent_ids: List of agent IDs to delete
        """
        tasks = []
        for agent_id in agent_ids:
            if agent_id in self._id2agent:
                agent = self._id2agent[agent_id]
                tasks.append(agent.close())
        await asyncio.gather(*tasks)
        for agent_id in agent_ids:
            if agent_id in self._id2agent:
                del self._id2agent[agent_id]
                del self._filter_base[agent_id]

    async def reset_all_agents(self) -> None:
        """Reset all agents for the next round."""
        get_logger().info("Resetting all agents...")
        tasks = [agent.reset() for agent in self._id2agent.values()]  # type:ignore
        await asyncio.gather(*tasks)
        get_logger().info("All agents reset")

    async def update_agent_memory(
        self,
        agent_ids: list[int],
        key: str,
        content: Any,
    ) -> None:
        """
        Update agent memory for specified agents.

        Args:
            agent_ids: List of agent IDs to update
            key: Memory key to update
            content: New content for the memory key
        """
        tasks = []
        for agent_id in agent_ids:
            if agent_id in self._id2agent:
                agent = self._id2agent[agent_id]
                tasks.append(agent.status.update(key, content))
        await asyncio.gather(*tasks)

    async def gather_from_agents(
        self,
        content: str,
        agent_ids: Optional[list[int]] = None,
        flatten: bool = False,
        keep_id: bool = False,
    ) -> Union[dict[int, Any], list[Any]]:
        """
        Gather information from agents.

        Args:
            content: The information key to gather
            agent_ids: Specific agent IDs to gather from (None = all)
            flatten: Whether to flatten the result
            keep_id: Whether to keep agent IDs in flattened results

        Returns:
            Dictionary or list of gathered content
        """
        if agent_ids is None:
            agent_ids = list(self._id2agent.keys())

        results = {}
        if content == "stream_memory":
            for agent in self._id2agent.values():
                if agent.id in agent_ids:
                    results[agent.id] = await agent.stream.get_all()
        else:
            for agent in self._id2agent.values():
                if agent.id in agent_ids:
                    results[agent.id] = await agent.status.get(content)

        if flatten:
            if not keep_id:
                data_flatten = []
                for _, data in results.items():
                    data_flatten.append(data)
                return data_flatten
            else:
                return results
        else:
            return results

    async def filter_agents(
        self,
        types: Optional[tuple[type[Agent], ...]] = None,
        filter_str: Optional[str] = None,
    ) -> list[int]:
        """
        Filter agents by type or custom filter string.

        Args:
            types: Tuple of agent types to filter for
            filter_str: Filter string for custom filtering (e.g., "${profile.age} > 18")

        Returns:
            List of filtered agent IDs
        """
        if not types and not filter_str:
            return list(self._id2agent.keys())

        # Filter by types first
        if types:
            filtered_ids = [
                agent_id
                for agent_id, (agent_class, _) in self._filter_base.items()
                if any(issubclass(agent_class, t) for t in types)
            ]
        else:
            filtered_ids = list(self._id2agent.keys())

        # Filter by filter_str
        if filter_str:
            filtered_ids = [
                agent_id
                for agent_id in filtered_ids
                if evaluate_filter(filter_str, self._filter_base[agent_id][1])
            ]

        return filtered_ids

    async def save_agent_static_info(self, step: int) -> int:
        """
        Save static agent information to the database.

        Args:
            step: Current simulation step

        Returns:
            Number of agents for which info was saved
        """
        if self._db_actor is None:
            get_logger().info("ClickHouse actor is not initialized; skip static info save")
            return 0

        if not self._id2agent:
            get_logger().info("No agents found; skip static info save")
            return 0

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
                    "exp_id": self._exp_id,
                    "simulation_step": step,
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
            f"Saved static info for {saved_count} citizen agents"
        )
        return saved_count
