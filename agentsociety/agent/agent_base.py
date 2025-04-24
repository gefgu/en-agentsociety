from __future__ import annotations

import asyncio
import inspect
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, NamedTuple, Optional, Union, get_type_hints

import jsonc
import ray
from pycityproto.city.person.v2 import person_pb2 as person_pb2

from ..environment import Environment
from ..llm import LLM
from ..logger import get_logger
from ..memory import Memory
from ..message import Messager
from ..metrics import MlflowClient
from ..storage import AvroSaver, StorageDialog, StorageSurvey
from ..utils import process_survey_for_llm
from .block import Block

__all__ = [
    "Agent",
    "AgentType",
]


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

    configurable_fields: list[str] = []
    default_values: dict[str, Any] = {}
    fields_description: dict[str, str] = {}

    def __init__(
        self,
        id: int,
        name: str,
        type: AgentType,
        toolbox: AgentToolbox,
        memory: Memory,
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

    async def init(self):
        await self._memory.status.update(
            "id", self._id, protect_llm_read_only_fields=False
        )

    def __getstate__(self):
        state = self.__dict__.copy()
        # Exclude lock objects
        del state["_toolbox"]
        return state

    @classmethod
    def export_class_config(cls) -> dict[str, dict]:
        """
        Export the class configuration as a dictionary.

        - **Args**:
            - None. This method relies on class attributes and type hints.

        - **Returns**:
            - `dict[str, dict]`: A dictionary containing the class configuration information, including:
                - `agent_name`: The name of the class.
                - `config`: A mapping of configurable fields to their default values.
                - `description`: A mapping of descriptions for each configurable field.
                - `blocks`: A list of dictionaries with configuration information for fields that are of type `Block`, each containing:
                    - `name`: The name of the field.
                    - `config`: Configuration information for the Block.
                    - `description`: Description information for the Block.
                    - `children`: Configuration information for any child Blocks (if applicable).

        - **Description**:
            - This method parses the annotations within the class to identify and process all fields that inherit from the `Block` class.
            - For each `Block`-typed field, it calls the corresponding `export_class_config` method to retrieve its configuration and adds it to the result.
            - If there are child `Block`s, it recursively exports their configurations using the `_export_subblocks` method.
        """
        result = {
            "agent_name": cls.__name__,
            "config": {},
            "description": {},
            "blocks": [],
        }
        config = {
            field: cls.default_values.get(field, "default_value")
            for field in cls.configurable_fields
        }
        result["config"] = config
        result["description"] = {
            field: cls.fields_description.get(field, "")
            for field in cls.configurable_fields
        }
        # Parse class annotations to find fields of type Block
        hints = get_type_hints(cls)
        for attr_name, attr_type in hints.items():
            if inspect.isclass(attr_type) and issubclass(attr_type, Block):
                block_config = attr_type.export_class_config()
                result["blocks"].append(
                    {
                        "name": attr_name,
                        "config": block_config[0],
                        "description": block_config[1],
                        "children": cls._export_subblocks(attr_type),
                    }
                )
        return result

    @classmethod
    def _export_subblocks(cls, block_cls: type[Block]) -> list[dict]:
        children = []
        hints = get_type_hints(block_cls)  # Get class annotations
        for attr_name, attr_type in hints.items():
            if inspect.isclass(attr_type) and issubclass(attr_type, Block):
                block_config = attr_type.export_class_config()
                children.append(
                    {
                        "name": attr_name,
                        "config": block_config[0],
                        "description": block_config[1],
                        "children": cls._export_subblocks(attr_type),
                    }
                )
        return children

    @classmethod
    def export_to_file(cls, filepath: str) -> None:
        """
        Export the class configuration to a JSON file.

        - **Args**:
            - `filepath` (`str`): The path where the JSON file will be saved.

        - **Returns**:
            - `None`

        - **Description**:
            - This method calls `export_class_config` to get the configuration dictionary and writes it to the specified file in JSON format with indentation for readability.
        """
        config = cls.export_class_config()
        with open(filepath, "w") as f:
            jsonc.dump(config, f, indent=4)

    @classmethod
    def import_block_config(cls, config: dict[str, Union[list[dict], str]]) -> "Agent":
        """
        Import an agent's configuration from a dictionary and initialize the Agent instance along with its Blocks.

        - **Args**:
            - `config` (`dict[str, Union[list[dict], str]]`): A dictionary containing the configuration of the agent and its blocks.

        - **Returns**:
            - `Agent`: An initialized Agent instance configured according to the provided configuration.

        - **Description**:
            - Initializes a new agent using the name found in the configuration.
            - Dynamically creates Block instances based on the configuration data and assigns them to the agent.
            - If a block is not found in the global namespace or cannot be created, this method may raise errors.
        """
        raise NotImplementedError("Bad implementation and should be re-implemented!")
        agent = cls(name=config["agent_name"])

        def build_block(block_data: dict[str, Any]) -> Block:
            block_cls = globals()[block_data["name"]]
            block_instance = block_cls.import_config(block_data)
            return block_instance

        # Create top-level Blocks
        for block_data in config["blocks"]:
            assert isinstance(block_data, dict)
            block = build_block(block_data)
            setattr(agent, block.name.lower(), block)
        return agent

    @classmethod
    def import_from_file(cls, filepath: str) -> "Agent":
        """
        Load an agent's configuration from a JSON file and initialize the Agent instance.

        - **Args**:
            - `filepath` (`str`): The path to the JSON file containing the agent's configuration.

        - **Returns**:
            - `Agent`: An initialized Agent instance configured according to the loaded configuration.

        - **Description**:
            - Reads the JSON configuration from the given file path.
            - Delegates the creation of the agent and its blocks to `import_block_config`.
        """
        with open(filepath, "r") as f:
            config = jsonc.load(f)
            return cls.import_block_config(config)

    def load_from_config(self, config: dict[str, Any]) -> None:
        """
        Update the current Agent instance's Block hierarchy using the provided configuration.

        - **Args**:
            - `config` (`dict[str, Any]`): A dictionary containing the configuration for updating the agent and its blocks.

        - **Returns**:
            - `None`

        - **Description**:
            - Updates the base parameters of the current agent instance according to the provided configuration.
            - Recursively updates or creates top-level Blocks as specified in the configuration.
            - Raises a `KeyError` if a required Block is not found in the agent.
        """
        for field in self.configurable_fields:
            if field in config["config"]:
                if config["config"][field] != "default_value":
                    setattr(self, field, config["config"][field])

        for block_data in config.get("blocks", []):
            block_name = block_data["name"]
            existing_block = getattr(self, block_name, None)

            if existing_block:
                existing_block.load_from_config(block_data)
            else:
                raise KeyError(
                    f"Block '{block_name}' not found in agent '{self.__class__.__name__}'"
                )

    def load_from_file(self, filepath: str) -> None:
        """
        Load configuration from a JSON file and update the current Agent instance.

        - **Args**:
            - `filepath` (`str`): The path to the JSON file containing the agent's configuration.

        - **Returns**:
            - `None`

        - **Description**:
            - Reads the configuration from the specified JSON file.
            - Uses the `load_from_config` method to apply the loaded configuration to the current Agent instance.
            - This method is useful for restoring an Agent's state from a saved configuration file.
        """
        with open(filepath, "r") as f:
            config = jsonc.load(f)
            self.load_from_config(config)

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

    async def generate_user_survey_response(self, survey: dict) -> str:
        """
        Generate a response to a user survey based on the agent's memory and current state.

        - **Args**:
            - `survey` (`dict`): The survey that needs to be answered.

        - **Returns**:
            - `str`: The generated response from the agent.

        - **Description**:
            - Prepares a prompt for the Language Model (LLM) based on the provided survey.
            - Constructs a dialog including system prompts, relevant memory context, and the survey question itself.
            - Uses the LLM client to generate a response asynchronously.
            - If the LLM client is not available, it returns a default message indicating unavailability.
            - This method can be overridden by subclasses to customize survey response generation.
        """
        survey_prompt = process_survey_for_llm(survey)
        dialog = []

        # Add system prompt
        system_prompt = "Please answer the survey question in first person. Follow the format requirements strictly and provide clear and specific answers."
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
                _response = await self.llm.atext_request(
                    dialog, response_format={"type": "json_object"}
                )
                json_str = extract_json(_response)
                if json_str:
                    json_dict = jsonc.loads(json_str)
                    json_str = jsonc.dumps(json_dict, ensure_ascii=False)
                    break
            except:
                pass
        else:
            raise Exception("Failed to generate survey response")
        return json_str

    async def _process_survey(self, survey: dict):
        """
        Process a survey by generating a response and recording it in Avro format and PostgreSQL.

        - **Args**:
            - `survey` (`dict`): The survey data that includes an ID and other relevant information.

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
            survey_id=survey["id"],
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
        await self.messager.send_message(
            self.messager.get_user_payback_channel(), {"count": 1}
        )
        get_logger().info(f"Sent payback message for survey {survey['id']}")

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
        await self._process_survey(payload["data"])

    async def handle_gather_message(self, payload: Any):
        """
        Placeholder for handling gather messages.

        - **Args**:
            - `payload` (`Any`): The received message payload.

        - **Raises**:
            - `NotImplementedError`: As this method is not implemented.

        - **Description**:
            - This method is intended to handle specific types of gather messages but has not been implemented yet.
        """

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

    async def run(self) -> Any:
        """
        Unified entry point for executing the agent's logic.

        - **Description**:
            - It calls the `forward` method to execute the agent's behavior logic.
            - Acts as the main control flow for the agent, coordinating when and how the agent performs its actions.
        """
        return await self.forward()
