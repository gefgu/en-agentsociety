from __future__ import annotations

import asyncio
import inspect
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import (Any, NamedTuple, Optional, Union)

import jsonc
import ray
from pycityproto.city.person.v2 import person_pb2 as person_pb2
from pydantic import BaseModel, Field

from ..environment import Environment
from ..llm import LLM
from ..logger import get_logger
from ..memory import Memory
from ..message import Messager
from ..metrics import MlflowClient
from ..storage import AvroSaver, StorageDialog, StorageSurvey
from ..survey.models import Survey
from .context import AgentContext, context_to_dot_dict
from .block import Block
from .decorator import register_get
from .dispatcher import DISPATCHER_PROMPT, BlockDispatcher
from .memory_config_generator import MemoryT, StatusAttribute

__all__ = [
    "Agent",
    "AgentType",
]


class AgentParams(BaseModel):
    block_dispatch_prompt: str = Field(
        default=DISPATCHER_PROMPT,
        description="The prompt used for the block dispatcher, there is a variable 'intention' in the prompt, which is the intention of the task, used to select the most appropriate block",
    )


class AgentToolbox(NamedTuple):
    """
    A named tuple representing the toolbox of an agent.
    """

    llm: LLM
    environment: Environment
    messager: Messager
    avro_saver: Optional[AvroSaver]
    pgsql_writer: Optional[ray.ObjectRef]
    mlflow_client: Optional[MlflowClient]


class AgentType(Enum):
    """
    Agent Type

    - Citizen, Citizen type agent
    - Institution, Organization or institution type agent
    """

    Unspecified = "Unspecified"
    Citizen = "Citizen"
    Institution = "Institution"


def extract_json(output_str):
    """Extract JSON substring from a raw string response.

    Args:
        output_str: Raw string output that may contain JSON data.

    Returns:
        Extracted JSON string if valid, otherwise None.

    Note:
        Searches for the first '{' and last '}' to isolate JSON content.
        Catches JSON decoding errors and logs warnings.
    """
    try:
        # Find the positions of the first '{' and the last '}'
        start = output_str.find("{")
        end = output_str.rfind("}")

        # Extract the substring containing the JSON
        json_str = output_str[start : end + 1]

        # Convert the JSON string to a dictionary
        return json_str
    except (ValueError, jsonc.JSONDecodeError) as e:
        get_logger().warning(f"Failed to extract JSON: {e}")
        return None


class Agent(ABC):
    """
    Agent base class
    """

    ParamsType = AgentParams  # Determine agent parameters
    Context = AgentContext  # Agent Context for information retrieval
    BlockOutputType = None  # Block output
    StatusAttributes: list[StatusAttribute] = []  # Memory configuration
    description: str = ""  # Agent description: How this agent works

    def __init__(
        self,
        id: int,
        name: str,
        type: AgentType,
        toolbox: AgentToolbox,
        memory: Memory,
        agent_params: Optional[Any] = None,
        blocks: Optional[list[Block]] = None,
    ) -> None:
        """
        Initialize the `Agent`.

        - **Args**:
            - `id` (`int`): The ID of the agent.
            - `name` (`str`): The name of the agent.
            - `type` (`AgentType`): The type of the agent. Defaults to `AgentType.Unspecified`.
            - `toolbox` (`AgentToolbox`): The toolbox of the agent.
            - `memory` (`Memory`): The memory of the agent.
        """
        self._id = id
        self._name = name
        self._type = type
        self._toolbox = toolbox
        self._memory = memory

        self._last_asyncio_pg_task = None  # Hide SQL writes behind computational tasks
        self._gather_responses: dict[int, asyncio.Future] = {}

        # parse agent_params
        if agent_params is None:
            agent_params = self.default_params()
        self.params = agent_params
        for key, value in agent_params.model_dump().items():
            setattr(self, key, value)

        # initialize context
        context = self.default_context()
        self.context = context_to_dot_dict(context)

        # register blocks
        self.dispatcher = BlockDispatcher(self.llm, self.memory, self.params.block_dispatch_prompt)
        if blocks is not None:
            # Block output type checking
            for block in blocks:
                if block.OutputType != self.BlockOutputType:
                    raise ValueError(f"Block output type mismatch, expected {self.BlockOutputType}, got {block.OutputType}")
                if block.NeedAgent:
                    block.set_agent(self)
            self.blocks = blocks
            self.dispatcher.register_blocks(self.blocks)
        else:
            self.blocks = []

    @classmethod
    def default_params(cls) -> ParamsType:
        return cls.ParamsType()

    @classmethod
    def default_context(cls) -> Context:
        return cls.Context()

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Create a new dictionary that inherits from parent
        cls.get_functions = dict(cls.__base__.get_functions) if hasattr(cls.__base__, "get_functions") else {}  # type: ignore

        # Register all methods with _register_info
        for name, method in cls.__dict__.items():
            if hasattr(method, "_get_info"):
                info = method._get_info
                cls.get_functions[info["function_name"]] = info

    async def _getx(self, function_name: str, *args, **kwargs):
        """
        Calls a registered function by name.

        - **Description**:
            - Calls a registered function by its function_name.

        - **Args**:
            - `function_name` (str): The name of the function to call.
            - `*args`: Variable length argument list to pass to the function.
            - `**kwargs`: Arbitrary keyword arguments to pass to the function.

        - **Returns**:
            - The result of the called function.

        - **Raises**:
            - `ValueError`: If the function_name is not registered.
        """
        if function_name not in self.__class__.get_functions:
            raise ValueError(f"GET function '{function_name}' is not registered")

        func_info = self.__class__.get_functions[function_name]
        if func_info.get("is_async", False):
            result = await func_info["original_method"](self, *args, **kwargs)
        else:
            result = func_info["original_method"](self, *args, **kwargs)
        return result

    async def init(self):
        await self._memory.status.update(
            "id", self._id, protect_llm_read_only_fields=False
        )

    def __getstate__(self):
        state = self.__dict__.copy()
        # Exclude lock objects
        del state["_toolbox"]
        return state

    @property
    def id(self):
        """The Agent's Simulator ID"""
        return self._id

    @property
    def llm(self):
        """The Agent's LLM"""
        return self._toolbox.llm

    @property
    def environment(self):
        """The Agent's Environment"""
        return self._toolbox.environment

    @property
    def messager(self):
        """The Agent's Messager"""
        return self._toolbox.messager

    @property
    def avro_saver(self):
        """The Agent's Avro Saver"""
        return self._toolbox.avro_saver

    @property
    def pgsql_writer(self):
        """The Agent's PgSQL Writer"""
        return self._toolbox.pgsql_writer

    @property
    def mlflow_client(self):
        """The Agent's MLflow Client"""
        return self._toolbox.mlflow_client

    @property
    def memory(self):
        """The Agent's Memory"""
        if self._memory is None:
            raise RuntimeError(
                f"Memory access before assignment, please `set_memory` first!"
            )
        return self._memory

    @property
    def status(self):
        """The Agent's Status Memory"""
        if self.memory.status is None:
            raise RuntimeError(
                f"Status access before assignment, please `set_memory` first!"
            )
        return self.memory.status

    @property
    def stream(self):
        """The Agent's Stream Memory"""
        if self.memory.stream is None:
            raise RuntimeError(
                f"Stream access before assignment, please `set_memory` first!"
            )
        return self.memory.stream

    @abstractmethod
    async def reset(self):
        """Reset the agent."""
        raise NotImplementedError("This method should be implemented by subclasses")

    @abstractmethod
    async def react_to_intervention(self, intervention_message: str):
        """
        React to an intervention.

        - **Args**:
            - `intervention_message` (`str`): The message of the intervention.

        - **Description**:
            - React to an intervention.
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    async def generate_user_survey_response(self, survey: Survey) -> str:
        """
        Generate a response to a user survey based on the agent's memory and current state.

        - **Args**:
            - `survey` (`Survey`): The survey that needs to be answered.

        - **Returns**:
            - `str`: The generated response from the agent.

        - **Description**:
            - Prepares a prompt for the Language Model (LLM) based on the provided survey.
            - Constructs a dialog including system prompts, relevant memory context, and the survey question itself.
            - Uses the LLM client to generate a response asynchronously.
            - If the LLM client is not available, it returns a default message indicating unavailability.
            - This method can be overridden by subclasses to customize survey response generation.
        """
        survey_prompt = survey.to_prompt()
        dialog = []

        # Add system prompt
        system_prompt = "Please answer the survey question in first person. Follow the format requirements strictly and provide clear and specific answers (In JSON format)."
        dialog.append({"role": "system", "content": system_prompt})

        # Add memory context
        if self.memory:
            profile_and_states = await self.status.search(survey_prompt)
            relevant_activities = await self.stream.search(survey_prompt)

            dialog.append(
                {
                    "role": "system",
                    "content": f"Answer based on following profile and states:\n{profile_and_states}\n Related activities:\n{relevant_activities}",
                }
            )

        # Add survey question
        dialog.append({"role": "user", "content": survey_prompt})

        for retry in range(10):
            try:
                # Use LLM to generate a response
                # print(f"dialog: {dialog}")
                _response = await self.llm.atext_request(
                    dialog, response_format={"type": "json_object"}
                )
                # print(f"response: {_response}")
                json_str = extract_json(_response)
                if json_str:
                    json_dict = jsonc.loads(json_str)
                    json_str = jsonc.dumps(json_dict, ensure_ascii=False)
                    break
            except:
                pass
        else:
            import traceback

            traceback.print_exc()
            get_logger().error("Failed to generate survey response")
            json_str = ""
        return json_str

    async def _process_survey(self, survey: Survey):
        """
        Process a survey by generating a response and recording it in Avro format and PostgreSQL.

        - **Args**:
            - `survey` (`Survey`): The survey data that includes an ID and other relevant information.

        - **Description**:
            - Generates a survey response using `generate_user_survey_response`.
            - Records the response with metadata (such as timestamp, survey ID, etc.) in Avro format and appends it to an Avro file if `_avro_file` is set.
            - Writes the response and metadata into a PostgreSQL database asynchronously through `_pgsql_writer`, ensuring any previous write operation has completed.
            - Sends a message through the Messager indicating user feedback has been processed.
            - Handles asynchronous tasks and ensures thread-safe operations when writing to PostgreSQL.
        """
        survey_response = await self.generate_user_survey_response(survey)
        date_time = datetime.now(timezone.utc)
        # Avro
        day, t = self.environment.get_datetime()
        storage_survey = StorageSurvey(
            id=self.id,
            day=day,
            t=t,
            survey_id=str(survey.id),
            result=survey_response,
            created_at=date_time,
        )
        if self.avro_saver is not None:
            self.avro_saver.append_surveys([storage_survey])
        # Pg
        if self.pgsql_writer is not None:
            if self._last_asyncio_pg_task is not None:
                await self._last_asyncio_pg_task
            self._last_asyncio_pg_task = (
                self.pgsql_writer.write_surveys.remote(  # type:ignore
                    [storage_survey]
                )
            )
        # status memory
        await self.memory.status.update(
            "survey_responses",
            survey_response,
            mode="merge",
            protect_llm_read_only_fields=False,
        )
        await self.messager.send_message(
            self.messager.get_user_payback_channel(), {"count": 1}
        )
        get_logger().info(f"Sent payback message for survey {survey.id}")

    async def generate_user_chat_response(self, question: str) -> str:
        """
        Generate a response to a user's chat question based on the agent's memory and current state.

        - **Args**:
            - `question` (`str`): The question that needs to be answered.

        - **Returns**:
            - `str`: The generated response from the agent.

        - **Description**:
            - Prepares a prompt for the Language Model (LLM) with a system prompt to guide the response style.
            - Constructs a dialog including relevant memory context and the user's question.
            - Uses the LLM client to generate a concise and clear response asynchronously.
            - If the LLM client is not available, it returns a default message indicating unavailability.
            - This method can be overridden by subclasses to customize chat response generation.
        """
        dialog = []

        # Add system prompt
        system_prompt = "Please answer the question in first person and keep the response concise and clear."
        dialog.append({"role": "system", "content": system_prompt})

        # Add memory context
        if self._memory:
            profile_and_states = await self.status.search(question, top_k=10)
            relevant_activities = await self.stream.search(question, top_k=10)

            dialog.append(
                {
                    "role": "system",
                    "content": f"Answer based on following profile and states:\n{profile_and_states}\n Related activities:\n{relevant_activities}",
                }
            )

        # Add user question
        dialog.append({"role": "user", "content": question})

        # Use LLM to generate a response
        response = await self.llm.atext_request(dialog)

        return response

    async def _process_interview(self, payload: dict):
        """
        Process an interview interaction by generating a response and recording it in Avro format and PostgreSQL.

        - **Args**:
            - `payload` (`dict`): The interview data containing the content of the user's message.

        - **Description**:
            - Logs the user's message as part of the interview process.
            - Generates a response to the user's question using `generate_user_chat_response`.
            - Records both the user's message and the generated response with metadata (such as timestamp, speaker, etc.) in Avro format and appends it to an Avro file if `_avro_file` is set.
            - Writes the messages and metadata into a PostgreSQL database asynchronously through `_pgsql_writer`, ensuring any previous write operation has completed.
            - Sends a message through the Messager indicating that user feedback has been processed.
            - Handles asynchronous tasks and ensures thread-safe operations when writing to PostgreSQL.
        """
        date_time = datetime.now(timezone.utc)
        day, t = self.environment.get_datetime()
        storage_dialog = StorageDialog(
            id=self.id,
            day=day,
            t=t,
            type=2,
            speaker="user",
            content=payload["content"],
            created_at=date_time,
        )
        if self.avro_saver is not None:
            self.avro_saver.append_dialogs([storage_dialog])
        if self.pgsql_writer is not None:
            if self._last_asyncio_pg_task is not None:
                await self._last_asyncio_pg_task
            self._last_asyncio_pg_task = (
                self.pgsql_writer.write_dialogs.remote(  # type:ignore
                    [storage_dialog]
                )
            )
        question = payload["content"]
        response = await self.generate_user_chat_response(question)
        date_time = datetime.now(timezone.utc)
        storage_dialog = StorageDialog(
            id=self.id,
            day=day,
            t=t,
            type=2,
            speaker="",
            content=response,
            created_at=date_time,
        )
        # Avro
        if self.avro_saver is not None:
            self.avro_saver.append_dialogs([storage_dialog])
        # Pg
        if self.pgsql_writer is not None:
            if self._last_asyncio_pg_task is not None:
                await self._last_asyncio_pg_task
            self._last_asyncio_pg_task = (
                self.pgsql_writer.write_dialogs.remote(  # type:ignore
                    [storage_dialog]
                )
            )
        await self.messager.send_message(
            self.messager.get_user_payback_channel(), {"count": 1}
        )
        get_logger().info(f"Sent payback message for interview {question}")

    async def save_agent_thought(self, thought: str):
        """
        Save the agent's thought to the memory.

        - **Args**:
            - `thought` (`str`): The thought data to be saved.

        - **Description**:
            - Saves the thought data to the memory.
        """
        day, t = self.environment.get_datetime()
        await self.memory.stream.add_cognition(thought)
        storage_thought = StorageDialog(
            id=self.id,
            day=day,
            t=t,
            type=0,
            speaker="",
            content=thought,
            created_at=datetime.now(timezone.utc),
        )
        # Avro
        if self.avro_saver is not None:
            self.avro_saver.append_dialogs([storage_thought])
        # Pg
        if self.pgsql_writer is not None:
            if self._last_asyncio_pg_task is not None:
                await self._last_asyncio_pg_task
            self._last_asyncio_pg_task = (
                self.pgsql_writer.write_dialogs.remote(  # type:ignore
                    [storage_thought]
                )
            )

    async def process_agent_chat_response(self, payload: dict) -> str:
        """
        Log the reception of an agent chat response.

        - **Args**:
            - `payload` (`dict`): The chat response data received from another agent.

        - **Returns**:
            - `str`: A log message indicating the reception of the chat response.

        - **Description**:
            - Logs the receipt of a chat response from another agent.
            - Returns a formatted string for logging purposes.
        """
        resp = f"Agent {self.id} received agent chat response: {payload}"
        get_logger().info(resp)
        return resp

    async def _process_agent_chat(self, payload: dict):
        """
        Process a chat message received from another agent and record it.

        - **Args**:
            - `payload` (`dict`): The chat message data received from another agent.

        - **Description**:
            - Logs the incoming chat message from another agent.
            - Prepares the chat message for storage in Avro format and PostgreSQL.
            - Writes the chat message and metadata into an Avro file if `_avro_file` is set.
            - Ensures thread-safe operations when writing to PostgreSQL by waiting for any previous write task to complete before starting a new one.
        """
        storage_dialog = StorageDialog(
            id=self.id,
            day=payload["day"],
            t=payload["t"],
            type=1,
            speaker=str(payload["from"]),
            content=payload["content"],
            created_at=datetime.now(timezone.utc),
        )
        await self.process_agent_chat_response(payload)
        # Avro
        if self.avro_saver is not None:
            self.avro_saver.append_dialogs([storage_dialog])
        # Pg
        if self.pgsql_writer is not None:
            if self._last_asyncio_pg_task is not None:
                await self._last_asyncio_pg_task
            self._last_asyncio_pg_task = (
                self.pgsql_writer.write_dialogs.remote(  # type:ignore
                    [storage_dialog]
                )
            )

    # Callback functions for Redis message
    async def handle_agent_chat_message(self, payload: dict):
        """
        Handle an incoming chat message from another agent.

        - **Args**:
            - `payload` (`dict`): The received message payload containing the chat data.

        - **Description**:
            - Logs receipt of a chat message from another agent.
            - Delegates the processing of the chat message to `_process_agent_chat`.
            - This method is typically used as a callback function for Redis messages.
        """
        # Process the received message, identify the sender
        # Parse sender ID and message content from the message
        get_logger().info(f"Agent {self.id} received agent chat message: {payload}")
        await self._process_agent_chat(payload)

    async def handle_user_chat_message(self, payload: dict):
        """
        Handle an incoming chat message from a user.

        - **Args**:
            - `payload` (`dict`): The received message payload containing the chat data.

        - **Description**:
            - Logs receipt of a chat message from a user.
            - Delegates the processing of the interview (which includes generating a response) to `_process_interview`.
            - This method is typically used as a callback function for Redis messages.
        """
        # Process the received message, identify the sender
        # Parse sender ID and message content from the message
        get_logger().info(f"Agent {self.id} received user chat message: {payload}")
        await self._process_interview(payload)

    async def handle_user_survey_message(self, payload: dict):
        """
        Handle an incoming survey message from a user.

        - **Args**:
            - `payload` (`dict`): The received message payload containing the survey data.

        - **Description**:
            - Logs receipt of a survey message from a user.
            - Extracts the survey data from the payload and delegates its processing to `_process_survey`.
            - This method is typically used as a callback function for Redis messages.
        """
        # Process the received message, identify the sender
        # Parse sender ID and message content from the message
        get_logger().info(f"Agent {self.id} received user survey message: {payload}")
        survey = Survey.model_validate(payload["data"])
        await self._process_survey(survey)

    async def handle_gather_message(self, payload: dict):
        """
        Handle a gather message received by the agent.

        - **Args**:
            - `payload` (`dict`): The message payload containing the target attribute and sender ID.

        - **Description**:
            - Extracts the target attribute and sender ID from the payload.
            - Retrieves the content associated with the target attribute from the agent's status.
            - Prepares a response payload with the retrieved content and sends it back to the sender using `_send_message`.
        """
        # Process the received message, identify the sender
        # Parse sender ID and message content from the message
        target = payload["target"]
        sender_id = payload["from"]
        if not isinstance(target, list):
            content = await self.status.get(target)
        else:
            content = {}
            for single in target:
                try:
                    content[single] = await self.status.get(single)
                except Exception as e:
                    get_logger().error(f"Error gathering {single} from status: {e}")
                    content[single] = None
        payload = {
            "from": self.id,
            "content": content,
        }
        await self._send_message(sender_id, payload, "gather_receive")

    async def handle_gather_receive_message(self, payload: Any):
        """
        Handle a gather receive message.
        """
        content = payload["content"]
        sender_id = payload["from"]

        # Store the response into the corresponding Future
        response_key = sender_id
        if response_key in self._gather_responses:
            self._gather_responses[response_key].set_result(
                {
                    "from": sender_id,
                    "content": content,
                }
            )

    async def gather_messages(
        self, agent_ids: list[int], target: Union[str, list[str]]
    ) -> list[Any]:
        """
        Gather messages from multiple agents.

        - **Args**:
            - `agent_ids` (`list[int]`): A list of IDs for the target agents.
            - `target` (`Union[str, list[str]]`): The type of information to collect from each agent.

        - **Returns**:
            - `list[Any]`: A list of collected responses.

        - **Description**:
            - For each agent ID provided, creates a `Future` object to wait for its response.
            - Sends a gather request to each specified agent.
            - Waits for all responses and returns them as a list of dictionaries.
            - Ensures cleanup of Futures after collecting responses.
        """
        # Create a Future for each agent
        futures = {}
        for agent_id in agent_ids:
            futures[agent_id] = asyncio.Future()
            self._gather_responses[agent_id] = futures[agent_id]

        # Send gather requests
        payload = {
            "from": self.id,
            "target": target,
        }
        for agent_id in agent_ids:
            await self._send_message(agent_id, payload, "gather")

        try:
            # Wait for all responses
            responses = await asyncio.gather(*futures.values())
            return responses
        finally:
            # Cleanup Futures
            for key in futures:
                self._gather_responses.pop(key, None)

    # Redis send message
    async def _send_message(self, to_agent_id: int, payload: dict, sub_topic: str):
        """
        Send a message to another agent through the Messager.

        - **Args**:
            - `to_agent_id` (`int`): The ID of the recipient agent.
            - `payload` (`dict`): The content of the message to send.
            - `sub_topic` (`str`): The sub-topic for the Redis topic structure.

        - **Raises**:
            - `RuntimeError`: If the Messager is not set.

        - **Description**:
            - Constructs the full Redis topic based on the experiment ID, recipient ID, and sub-topic.
            - Sends the message asynchronously through the Messager.
            - Used internally by other methods like `send_message_to_agent`.
        """
        # send message with `Messager`
        topic = self.messager.get_subtopic_channel(to_agent_id, sub_topic)
        await self.messager.send_message(
            topic,
            payload,
            self.id,
            to_agent_id,
        )

    async def send_message_to_agent(
        self, to_agent_id: int, content: str, type: str = "social"
    ):
        """
        Send a social or economy message to another agent.

        - **Args**:
            - `to_agent_id` (`int`): The ID of the recipient agent.
            - `content` (`str`): The content of the message to send.
            - `type` (`str`, optional): The type of the message ("social" or "economy"). Defaults to "social".

        - **Raises**:
            - `RuntimeError`: If the Messager is not set.

        - **Description**:
            - Validates the message type and logs a warning if it's invalid.
            - Prepares the message payload with necessary metadata such as sender ID, timestamp, etc.
            - Sends the message asynchronously using `_send_message`.
            - Optionally records the message in Avro format and PostgreSQL if it's a "social" type message.
            - Ensures thread-safe operations when writing to PostgreSQL by waiting for any previous write task to complete before starting a new one.
        """
        day, t = self.environment.get_datetime()
        # send message with `Messager`
        if type not in ["social", "economy"]:
            get_logger().warning(f"Invalid message type: {type}, sent from {self.id}")
        payload = {
            "from": self.id,
            "content": content,
            "type": type,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "day": day,
            "t": t,
        }
        await self._send_message(to_agent_id, payload, "agent-chat")
        storage_dialog = StorageDialog(
            id=self.id,
            day=day,
            t=t,
            type=1,
            speaker=str(self.id),
            content=content,
            created_at=datetime.now(timezone.utc),
        )
        # Avro
        if self.avro_saver is not None and type == "social":
            self.avro_saver.append_dialogs([storage_dialog])
        # Pg
        if self.pgsql_writer is not None and type == "social":
            if self._last_asyncio_pg_task is not None:
                await self._last_asyncio_pg_task
            self._last_asyncio_pg_task = (
                self.pgsql_writer.write_dialogs.remote(  # type:ignore
                    [storage_dialog]
                )
            )

    async def register_aoi_message(
        self, target_aoi: Union[int, list[int]], content: str
    ):
        """
        Register a message to target aoi

        - **Args**:
            - `target_aoi` (`Union[int, list[int]]`): The ID of the target aoi.
            - `content` (`str`): The content of the message to send.

        - **Description**:
            - Register a message to target aoi.
        """
        day, t = self.environment.get_datetime()
        if isinstance(target_aoi, int):
            payload = {
                "from": self.id,
                "content": content,
                "type": "aoi_message_register",
                "timestamp": int(datetime.now().timestamp() * 1000),
                "day": day,
                "t": t,
            }
            await self.messager.send_message(
                self.messager.get_aoi_channel(target_aoi), payload
            )
        else:
            for aoi in target_aoi:
                payload = {
                    "from": self.id,
                    "content": content,
                    "type": "aoi_message_register",
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "day": day,
                    "t": t,
                }
                await self.messager.send_message(
                    self.messager.get_aoi_channel(aoi), payload
                )

    async def cancel_aoi_message(self, target_aoi: Union[int, list[int]]):
        """
        Cancel a message to target aoi
        """
        day, t = self.environment.get_datetime()
        if isinstance(target_aoi, int):
            payload = {
                "from": self.id,
                "type": "aoi_message_cancel",
                "timestamp": int(datetime.now().timestamp() * 1000),
                "day": day,
                "t": t,
            }
            await self.messager.send_message(
                self.messager.get_aoi_channel(target_aoi), payload
            )
        else:
            for aoi in target_aoi:
                payload = {
                    "from": self.id,
                    "type": "aoi_message_cancel",
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "day": day,
                    "t": t,
                }
                await self.messager.send_message(
                    self.messager.get_aoi_channel(aoi), payload
                )

    # Agent logic
    @abstractmethod
    async def forward(self) -> Any:
        """
        Define the behavior logic of the agent.

        - **Raises**:
            - `NotImplementedError`: As this method must be implemented by subclasses.

        - **Description**:
            - This abstract method should contain the core logic for what the agent does at each step of its operation.
            - It is intended to be overridden by subclasses to define specific behaviors.
        """
        raise NotImplementedError

    async def final(self):
        """Execute when the agent is deleted or the simulation is finished."""
        pass

    async def before_forward(self):
        """
        Before forward
        """
        pass

    async def after_forward(self):
        """
        After forward
        """
        pass

    async def before_blocks(self):
        """
        Before blocks
        """
        for block in self.blocks:
            await block.before_forward()

    async def after_blocks(self):
        """
        After blocks
        """
        for block in self.blocks:
            await block.after_forward()

    async def run(self) -> Any:
        """
        Unified entry point for executing the agent's logic.

        - **Description**:
            - It calls the `forward` method to execute the agent's behavior logic.
            - Acts as the main control flow for the agent, coordinating when and how the agent performs its actions.
        """
        start_time = time.time()
        # run required methods before agent forward
        await self.before_forward()
        await self.before_blocks()
        # run agent forward
        await self.forward()
        # run required methods after agent forward
        await self.after_blocks()
        await self.after_forward()
        end_time = time.time()
        return end_time - start_time
