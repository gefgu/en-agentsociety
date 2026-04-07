"""
A clear version of the simulation.
"""

import asyncio
import inspect
import json
import traceback
import time
import yaml
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Literal, Optional, Union, cast
from ..database.database_actor import DatabaseActor
from ..performance.prometheusActor import PrometheusActor
from ..agent import CustomTool
from fastembed import SparseTextEmbedding

from ..agent import (
    Agent,
    AgentToolbox,
    CitizenAgentBase,
)
from ..configs import (
    AgentFilterConfig,
    Config,
    WorkflowType,
)
from .agentmanager import AgentManager
from .checkpointmanager import CheckpointManager
from .datarecorder import DataRecorder
from .infrastructuremanager import InfrastructureManager
from ..environment import EnvironmentStarter
from ..llm import LLM
from ..logger import get_logger, set_logger_level
from ..memory import Memory
from ..message import Message, MessageInterceptor, MessageKind, Messager
from ..storage import DatabaseWriter
from ..storage.type import (
    StorageExpInfo,
    StorageGlobalPrompt,
    StoragePendingSurvey,
)
from ..survey.models import Survey
from .type import ExperimentStatus, Logs
from .utils import set_default_agent_config

__all__ = ["SimulationEngine"]

MIN_ID = 1
MAX_ID = 100000000


class SimulationEngine:
    def __init__(
        self,
        config: Config,
        tenant_id: str = "",
    ) -> None:
        self._config = set_default_agent_config(config)
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
        self._dispatcher_cache_tool: Optional[CustomTool] = None
        self._agent_manager: Optional[AgentManager] = None
        self._data_recorder: Optional[DataRecorder] = None
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

        self._step_times: list[float] = []
        self._step_start_time: Optional[float] = None
        self._resume_exp_id: Optional[str] = configured_resume_exp_id
        self._resume_state: Optional[dict[str, Any]] = None
        self._infrastructure_manager = InfrastructureManager(
            config=self._config,
            tenant_id=self.tenant_id,
            exp_id=self.exp_id,
            exp_info=self._exp_info,
        )
        self._checkpoint_manager = CheckpointManager(
            exp_id=self.exp_id,
            home_dir=self._config.env.home_dir,
            start_tick=self._config.exp.environment.start_tick,
        )
        # Pass resume exp_id to infrastructure manager so it can load resume state
        if configured_resume_exp_id:
            self._infrastructure_manager.set_resume_exp_id(configured_resume_exp_id)

    def _sync_infrastructure_state(self):
        """Sync engine fields from the infrastructure manager outputs."""
        self._llm = self._infrastructure_manager.llm
        self._environment = self._infrastructure_manager.environment
        self._message_interceptor = self._infrastructure_manager.message_interceptor
        self._database_writer = self._infrastructure_manager.database_writer
        self._embedding = self._infrastructure_manager.embedding
        self._metrics_actor = self._infrastructure_manager.metrics_actor
        self._db_actor = self._infrastructure_manager.db_actor
        self._messager = self._infrastructure_manager.messager
        self._db_tool = self._infrastructure_manager.db_tool
        self._dispatcher_cache_tool = self._infrastructure_manager.dispatcher_cache_tool
        self._resume_state = self._infrastructure_manager.resume_state

    def _start_data_recorder(self) -> None:
        """Start async recorder after infrastructure dependencies are ready."""
        self._data_recorder = DataRecorder(
            database_writer=self._database_writer,
            db_actor=self._db_actor,
            metrics_actor=self._metrics_actor,
        )
        self._data_recorder.start_background_worker()

    async def _flush_data_recorder(self, step: Optional[int] = None) -> None:
        if self._data_recorder is None:
            return
        await self._data_recorder.flush(step=step)

    async def _stop_data_recorder(self) -> None:
        if self._data_recorder is None:
            return
        await self._data_recorder.stop_background_worker()
        self._data_recorder = None

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

        get_logger().info("Adding dispatcher cache tool to Agents...")
        if self._dispatcher_cache_tool is not None:
            agent_toolbox.add_tool(self._dispatcher_cache_tool)

        get_logger().info("Initializing the agents...")

        await self._save_exp_info()
        await self._flush_data_recorder(step=self._total_steps)
        self._save_context()
        get_logger().info("Experiment info saved")

        init_funcs = self._config.agents.init_funcs
        for init_func in init_funcs:
            if inspect.iscoroutinefunction(init_func):
                await init_func(self)
            else:
                init_func(self)

    async def init(self):
        """Initialize all the components"""
        try:
            await self._infrastructure_manager.initialize_all()
            self._sync_infrastructure_state()
            metrics_tool = self._infrastructure_manager.metrics_tool

            assert self._llm is not None, "LLM is not initialized"
            assert self._environment is not None, "Environment is not initialized"
            assert self._messager is not None, "Messager is not initialized"
            assert self._embedding is not None, "Embedding is not initialized"

            # Initialize agent manager and prepare agent list before loading resume state
            # so we can pass expected_agent_ids to the snapshot completeness check.
            self._agent_manager = AgentManager(
                config=self._config,
                llm=self._llm,
                environment=self._environment,
                messager=self._messager,
                message_interceptor=self._message_interceptor,
                embedding=self._embedding,
                database_writer=self._database_writer,
                db_actor=self._db_actor,
                exp_id=self.exp_id,
            )
            await self._agent_manager.create_toolbox()
            agents = await self._agent_manager.prepare_agents()
            expected_agent_ids = {agent_init[0] for agent_init in agents}

            await self._infrastructure_manager.load_resume_state(expected_agent_ids=expected_agent_ids)
            self._sync_infrastructure_state()
            self._total_steps = self._checkpoint_manager.restore_runtime_state(
                resume_state=self._resume_state,
                exp_info=self._exp_info,
                llm=self._llm,
                environment=self._environment,
            )
            self._start_data_recorder()

            self._infrastructure_manager._validate_resume_agent_count(agents)
            await self._agent_manager.initialize_agents(agents, self._resume_state)

            # Restore external simulators and Messager state on resume
            await self._finalize_initialization(self._agent_manager._agent_toolbox, metrics_tool)
            await self._checkpoint_manager.restore_external_simulator_state(
                resume_state=self._resume_state,
                environment=self._environment,
                agent_manager=self._agent_manager,
            )
            await self._checkpoint_manager.restore_messager_state(
                resume_state=self._resume_state,
                messager=self._messager,
            )

        except Exception as e:
            get_logger().error(f"Init error: {str(e)}\n{traceback.format_exc()}")
            self._exp_info.status = ExperimentStatus.ERROR.value
            self._exp_info.error = str(e)
            await self._save_exp_info()
            await self._flush_data_recorder(step=self._total_steps)

            raise e
        get_logger().info("Init functions run")
        get_logger().info("Simulation initialized")

    async def close(self):
        """Close all the components"""
        get_logger().info("Closing agent groups...")
        if self._agent_manager is not None:
            await self._agent_manager.close_all_agents()

        await self._stop_data_recorder()

        await self._infrastructure_manager.close()
        self._sync_infrastructure_state()

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
        assert self._agent_manager is not None, "Agent manager not initialized"
        return await self._agent_manager.gather_from_agents(
            content, target_agent_ids, flatten, keep_id
        )

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
        assert self._agent_manager is not None, "Agent manager not initialized"
        return await self._agent_manager.filter_agents(types, filter_str)

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
        assert self._agent_manager is not None, "Agent manager not initialized"
        
        # Handle special query case
        if query:
            for agent_id in target_agent_ids:
                agent = self._agent_manager.get_agent(agent_id)
                if agent is not None:
                    agent.gather_results[target_key] = content
        
        # Update memory
        await self._agent_manager.update_agent_memory(target_agent_ids, target_key, content)

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
        assert self._agent_manager is not None, "Agent manager not initialized"
        survey_tasks = []
        for agent_id in agent_ids:
            agent = self._agent_manager.get_agent(agent_id)
            if agent and isinstance(agent, CitizenAgentBase):
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
        assert self._agent_manager is not None, "Agent manager not initialized"
        for agent_id in agent_ids:
            agent = self._agent_manager.get_agent(agent_id)
            if agent and isinstance(agent, CitizenAgentBase):
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
        assert self._agent_manager is not None, "Agent manager not initialized"
        react_tasks = []
        for agent_id in agent_ids:
            agent = self._agent_manager.get_agent(agent_id)
            if agent and isinstance(agent, CitizenAgentBase):
                react_tasks.append(agent.react_to_intervention(intervention_message))
            else:
                get_logger().error(
                    f"Agent {agent_id} is not in the group, so skip the intervention"
                )
        await asyncio.gather(*react_tasks)

    async def _save_exp_info(self) -> None:
        """Async save experiment info to YAML file and pgsql"""
        if self._data_recorder is None:
            self._data_recorder = DataRecorder(
                database_writer=self._database_writer,
                db_actor=self._db_actor,
                metrics_actor=self._metrics_actor,
            )

        await self._data_recorder.save_exp_info(self._exp_info)

    async def _save_global_prompt(self, prompt: str, day: int, t: float):
        """Save global prompt"""
        if self._data_recorder is not None:
            await self._data_recorder.save_global_prompt(prompt, day, t)
            return

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
        assert self._agent_manager is not None, "Agent manager not initialized"
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
                    if agent_id in self._agent_manager.agents:
                        agent_messages[agent_id].append(message)
                elif message.kind in [
                    MessageKind.AOI_MESSAGE_REGISTER,
                    MessageKind.AOI_MESSAGE_CANCEL,
                ]:
                    aoi_messages.append(message)

            # Process agent messages in parallel for different agents
            async def process_agent_messages(agent_id: int, messages: list[Message]):
                agent = self._agent_manager.get_agent(agent_id)
                if agent and isinstance(agent, CitizenAgentBase):
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
        if self._database_writer is None and self._db_actor is None:
            return

        assert self._agent_manager is not None, "Agent manager not initialized"
        if self._data_recorder is not None:
            await self._data_recorder.save_statuses(
                day=day,
                t=t,
                agents=self._agent_manager.agents,
                environment=self.environment,
            )
            return

        # Fallback path when DataRecorder is not available.
        get_logger().warning("DataRecorder unavailable; status saving skipped")

    async def delete_agents(self, target_agent_ids: list[int]):
        """
        Delete the specified agents.

        - **Args**:
            - `target_agent_ids` (list[int]): The IDs of the agents to delete.
        """
        assert self._agent_manager is not None, "Agent manager not initialized"
        await self._agent_manager.delete_agents(target_agent_ids)

    async def next_round(self):
        """
        Proceed to the next round of the simulation.
        """
        get_logger().info("Start entering the next round of the simulation")
        assert self._agent_manager is not None, "Agent manager not initialized"
        await self._agent_manager.reset_all_agents()
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
            assert self._agent_manager is not None, "Agent manager not initialized"
            agent_time_log = await self._agent_manager.run_all_agents()
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
            for agent in self._agent_manager.agents.values():
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

            if self._data_recorder is not None:
                await self._data_recorder.record_block_performance_metrics(
                    self._total_steps
                )
                await self._data_recorder.record_routing_metrics(self._total_steps)

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
            # checkpoint agent memory + pending messages (before drain)
            # ======================
            await self._checkpoint_manager.save_checkpoint(
                day=day,
                t=t,
                total_steps=self._total_steps,
                agent_manager=self._agent_manager,
                messager=self._messager,
                data_recorder=self._data_recorder,
                db_actor=self._db_actor,
                environment=self._environment,
            )
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
            if self._data_recorder is not None:
                await self._data_recorder.record_simulation_step_duration(
                    step_duration,
                    self._total_steps,
                )

            # ======================
            # Log metrics from environment
            # ======================
            metrics = await self.environment.get_metrics()
            if self._data_recorder is not None:
                await self._data_recorder.record_environment_metrics(metrics)

            await self._flush_data_recorder(step=self._total_steps)
            get_logger().debug(f"({day}-{t}) Finished simulator sync")
            # ======================
            # go to next step
            # ======================
            self._total_steps += 1
            await self.environment.step(num_environment_ticks)
            return all_logs
        except Exception as e:
            get_logger().error(f"Simulation error: {str(e)}\n{traceback.format_exc()}")
            await self._flush_data_recorder(step=self._total_steps)
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
            await self._flush_data_recorder(step=self._total_steps)

            raise RuntimeError(str(e)) from e
        self._exp_info.status = ExperimentStatus.FINISHED.value
        self._save_context()
        await self._save_exp_info()
        await self._flush_data_recorder(step=self._total_steps)
        return logs
