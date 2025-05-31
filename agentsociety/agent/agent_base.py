from __future__ import annotations

import asyncio
import inspect
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, NamedTuple, Optional, Union

import jsonc
import ray
from pycityproto.city.person.v2 import person_pb2 as person_pb2
from pydantic import BaseModel, Field

from ..environment import Environment
from ..llm import LLM
from ..logger import get_logger
from ..memory import Memory
from ..message import Messager, Message, MessageKind
from ..metrics import MlflowClient
from ..storage import AvroSaver, StorageDialog, StorageDialogType
from .context import AgentContext, context_to_dot_dict
from .block import Block, BlockOutput
from .dispatcher import DISPATCHER_PROMPT, BlockDispatcher
from .memory_config_generator import StatusAttribute

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
    Supervisor = "Supervisor"


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

    ParamsType: type[AgentParams] = AgentParams  # Determine agent parameters
    Context: type[AgentContext] = (
        AgentContext  # Agent Context for information retrieval
    )
    BlockOutputType: type[BlockOutput] = BlockOutput  # Block output
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

        # initialize context
        context = self.default_context()
        self.context = context_to_dot_dict(context)

        # register blocks
        self.dispatcher = BlockDispatcher(
            self.llm, self.memory, self.params.block_dispatch_prompt
        )
        if blocks is not None:
            # Block output type checking
            for block in blocks:
                if block.OutputType != self.BlockOutputType:
                    raise ValueError(
                        f"Block output type mismatch, expected {self.BlockOutputType}, got {block.OutputType}"
                    )
                if block.NeedAgent:
                    block.set_agent(self)
            self.blocks = blocks
            self.dispatcher.register_blocks(self.blocks)
        else:
            self.blocks = []

    @classmethod
    def default_params(cls):
        return cls.ParamsType()

    @classmethod
    def default_context(cls):
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
            "content": content,
            "type": type,
        }
        await self.messager.send_message(
            Message(
                from_id=self.id,
                to_id=to_agent_id,
                kind=MessageKind.AGENT_CHAT,
                payload=payload,
                day=day,
                t=t,
            )
        )
        storage_dialog = StorageDialog(
            id=self.id,
            day=day,
            t=t,
            type=StorageDialogType.Talk,
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
            target_aoi = [target_aoi]
        for aoi in target_aoi:
            payload = {
                "content": content,
            }
            await self.messager.send_message(
                Message(
                    from_id=self.id,
                    to_id=aoi,
                    day=day,
                    t=t,
                    kind=MessageKind.AOI_MESSAGE_REGISTER,
                    payload=payload,
                )
            )

    async def cancel_aoi_message(self, target_aoi: Union[int, list[int]]):
        """
        Cancel a message to target aoi
        """
        day, t = self.environment.get_datetime()
        if isinstance(target_aoi, int):
            target_aoi = [target_aoi]
        for aoi in target_aoi:
            await self.messager.send_message(
                Message(
                    from_id=self.id,
                    to_id=aoi,
                    day=day,
                    t=t,
                    kind=MessageKind.AOI_MESSAGE_CANCEL,
                    payload={},
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

    async def close(self):
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
        # wait for all asyncio tasks to complete
        if self._last_asyncio_pg_task is not None:
            await self._last_asyncio_pg_task
        return end_time - start_time
