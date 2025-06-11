import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Optional, Union

import jsonc
import ray

from ..agent import (
    Agent,
    AgentParams,
    AgentToolbox,
    BankAgentBase,
    Block,
    BlockParams,
    CitizenAgentBase,
    FirmAgentBase,
    GovernmentAgentBase,
    NBSAgentBase,
)
from ..survey import Survey
from ..agent.memory_config_generator import MemoryConfigGenerator
from ..configs import Config
from ..environment import Environment
from ..llm import LLM, init_embedding, monitor_requests
from ..logger import get_logger, set_logger_level
from ..memory import FaissQuery, Memory
from ..message import Messager, Message, MessageKind
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
                AgentParams,  # agent_params
                dict[type[Block], BlockParams],  # blocks
            ]
        ],
        environment_init: dict,
        database_writer: Optional[ray.ObjectRef],
        agent_config_file: Optional[dict[type[Agent], Any]] = None,
    ):
        """
        Initialize the AgentGroup.

        """
        try:
            get_logger().info("Starting AgentGroup initialization...")
            set_logger_level(config.advanced.logging_level.upper())

            self._tenant_id = tenant_id
            get_logger().debug(f"Set tenant_id: {tenant_id}")
            self._exp_name = exp_name
            get_logger().debug(f"Set exp_name: {exp_name}")
            self._exp_id = exp_id
            get_logger().debug(f"Set exp_id: {exp_id}")
            self._group_id = group_id
            get_logger().debug(f"Set group_id: {group_id}")
            self._config = config
            get_logger().debug(f"Config loaded")
            self._agent_inits = agent_inits
            get_logger().debug(f"Agent inits loaded, count: {len(agent_inits)}")
            self._environment_init = environment_init
            get_logger().debug(f"Environment init loaded")
            self._database_writer = database_writer
            get_logger().debug(f"Database writer reference set")
            self._agent_config_file = agent_config_file
            get_logger().debug(f"Agent config file loaded")

            get_logger().info("Initializing embedding model...")
            self._embedding_model = init_embedding(config.advanced.embedding_model)
            get_logger().debug(f"Embedding model initialized")
            self._faiss_query = FaissQuery(self._embedding_model)
            get_logger().debug(f"FAISS query initialized")

            # typing definition
            self._llm = None
            self._environment = None
            self._messager = None

            self._agents = []
            self._id2agent = {}
            get_logger().info("AgentGroup initialization completed successfully")
        except Exception as e:
            get_logger().error(f"Error in AgentGroup.__init__: {str(e)}")
            import traceback

            get_logger().error(f"Traceback: {traceback.format_exc()}")
            raise

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
        self._messager = Messager(self._exp_id)
        await self._messager.init()
        get_logger().info(f"Messager initialized")

        # ====================================
        # Initialize the agents
        # ====================================
        get_logger().info(f"Initializing the agents...")
        agent_toolbox = AgentToolbox(
            self.llm,
            self.environment,
            self.messager,
            self._database_writer,
        )
        to_return = {}
        for agent_init in self._agent_inits:
            (
                id,
                agent_class,
                memory_config_generator,
                index_for_generator,
                agent_params,
                blocks,
            ) = agent_init
            memory_dict = memory_config_generator.generate(index_for_generator)
            extra_attributes = memory_dict.get("extra_attributes", {})
            profile = memory_dict.get("profile", {})
            base = memory_dict.get("base", {})
            profile_ = {}
            for k, v in profile.items():
                if isinstance(v, tuple):
                    profile_[k] = v[1]
                else:
                    profile_[k] = v
            to_return[id] = (agent_class, profile_)
            memory_init = Memory(
                agent_id=id,
                environment=self.environment,
                faiss_query=self.faiss_query,
                embedding_model=self.embedding_model,
                config=extra_attributes,
                profile=profile,
                base=base,
            )
            # # build blocks
            if blocks is not None:
                blocks = [
                    block_type(
                        llm=self.llm,
                        environment=self.environment,
                        agent_memory=memory_init,
                        block_params=block_type.ParamsType.model_validate(block_params),
                    )
                    for block_type, block_params in blocks.items()
                ]
            else:
                blocks = None
            # build agent
            agent = agent_class(
                id=id,
                name=f"{agent_class.__name__}_{id}",
                toolbox=agent_toolbox,
                memory=memory_init,
                agent_params=agent_params,
                blocks=blocks,
            )
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
            await self._database_writer.write_profiles.remote(profiles)  # type:ignore
        get_logger().info(
            f"-----Initializing embeddings in AgentGroup {self._group_id} ..."
        )
        embedding_tasks = []
        for agent in self._agents:
            embedding_tasks.append(agent.memory.initialize_embeddings())
        await asyncio.gather(*embedding_tasks)

        get_logger().info(f"Agents initialized")
        return to_return

    async def close(self):
        """Close the AgentGroupV2."""
        tasks = []
        for agent in self._agents:
            tasks.append(agent.close())
        await asyncio.gather(*tasks)

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
            await self._message_dispatch()
            # main agent workflow
            tasks = [agent.run() for agent in self._agents]
            agent_time_log = await asyncio.gather(*tasks)
            simulator_log = (
                self.environment.get_log_list()
                + self.environment.economy_client.get_log_list()
            )
            group_logs = Logs(
                llm_log=self.llm.get_log_list(),
                simulator_log=simulator_log,
                agent_time_log=agent_time_log,
            )
            self.llm.clear_log_list()
            self.environment.clear_log_list()
            self.environment.economy_client.clear_log_list()

            # gather query
            gather_queries = {}
            for agent in self._agents:
                if agent.gather_query:
                    gather_queries[agent.id] = agent.gather_query

            return group_logs, gather_queries
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
        for agent_id in agent_ids:
            agent = self._id2agent[agent_id]
            if isinstance(agent, CitizenAgentBase):
                react_tasks.append(agent.react_to_intervention(intervention_message))
            else:
                get_logger().error(
                    f"Agent {agent_id} is not in the group, so skip the intervention"
                )
        await asyncio.gather(*react_tasks)

    # ====================
    # Message Handling Methods
    # ====================
    async def _message_dispatch(self):
        """
        Dispatches messages received via Message to the appropriate agents.
        """
        # Step 1: Fetch messages
        messages = await self.messager.fetch_received_messages()
        if len(messages) > 0:
            get_logger().info(
                f"Group {self._group_id} received {len(messages)} messages"
            )
        else:
            get_logger().debug(
                f"Group {self._group_id} received no messages in this step"
            )

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

    async def handle_survey(
        self,
        survey: Survey,
        agent_ids: list[int],
        survey_day: Optional[int] = None,
        survey_t: Optional[float] = None,
        is_pending_survey: bool = False,
        pending_survey_id: Optional[int] = None,
    ) -> dict[int, str]:
        """
        Handle a user survey.
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

    async def handle_interview(
        self, question: str, agent_ids: list[int]
    ) -> dict[int, str]:
        """
        Handle a user interview.
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
        if self._database_writer is None:
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
                hunger_satisfaction = await agent.status.get("hunger_satisfaction", 0)
                energy_satisfaction = await agent.status.get("energy_satisfaction", 0)
                safety_satisfaction = await agent.status.get("safety_satisfaction", 0)
                social_satisfaction = await agent.status.get("social_satisfaction", 0)
                current_need = await agent.status.get("current_need", "None")
                current_plan = await agent.status.get("current_plan", {})
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
        if self._database_writer is not None:
            await self._database_writer.write_statuses.remote(  # type:ignore
                statuses
            )

    async def update_environment(self, key: str, value: str):
        """
        Update the environment variables for the simulation and all agent groups.

        - **Args**:
            - `key` (str): The environment variable key to update.
            - `value` (str): The new value for the environment variable.
        """
        self.environment.update_environment(key, value)

    async def update(self, target_agent_id: int, target_key: str, content: Any, query: bool = False):
        """
        Updates a specific key in the status of a targeted agent.

        - **Args**:
            - `target_agent_id` (int): The ID of the agent to update.
            - `target_key` (str): The key in the agent's status to update.
            - `content` (Any): The new value for the specified key.
            - `query` (bool): Whether to update the gather results.
        """
        get_logger().debug(
            f"-----Updating {target_key} for agent {target_agent_id} in group {self._group_id}"
        )
        agent = self._id2agent[target_agent_id]
        if query:
            agent.gather_results[target_key] = content
        else:
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

    async def delete_agents(self, target_agent_ids: list[int]):
        """
        Deletes the specified agents from the agent group.

        - **Description**:
            - Removes agents with the specified IDs from both the agents list and the ID-to-agent mapping.
            - Handles cases where specified agent IDs might not exist in the group.

        - **Args**:
            - `target_agent_ids` (list[int]): List of agent IDs to be deleted.

        - **Returns**:
            - None
        """
        # Finalize the agents that are being deleted
        agents_to_delete = [
            agent for agent in self._agents if agent.id in target_agent_ids
        ]
        final_tasks = []
        for agent in agents_to_delete:
            final_tasks.append(agent.close())
        await asyncio.gather(*final_tasks)

        # Create a new list with agents that should be kept
        self._agents = [
            agent for agent in self._agents if agent.id not in target_agent_ids
        ]

        # Remove from the id-to-agent mapping
        for agent_id in target_agent_ids:
            if agent_id in self._id2agent:
                del self._id2agent[agent_id]
            else:
                get_logger().warning(
                    f"Attempted to delete non-existent agent with ID {agent_id}"
                )

    async def fetch_pending_messages(self):
        """
        Fetch the pending messages from the messager.
        """
        return await self.messager.fetch_pending_messages()

    async def set_received_messages(self, messages: list[Message]):
        """
        Set the received messages.
        """
        await self.messager.set_received_messages(messages)
