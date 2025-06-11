from __future__ import annotations

import asyncio
import functools
import inspect
from collections.abc import Callable, Coroutine
from typing import Any, Optional, Union, cast
from pydantic import BaseModel, Field

from ..environment import Environment
from ..llm import LLM
from ..memory import Memory
from ..memory.state import StateMemory
from ..utils.decorators import record_call_aio
from .context import DotDict, BlockContext, context_to_dot_dict, auto_deepcopy_dotdict
from ..logger import get_logger

TRIGGER_INTERVAL = 1

__all__ = [
    "Block",
    "log_and_check",
    "log_and_check_with_memory",
    "trigger_class",
]


class BlockParams(BaseModel):
    block_memory: Optional[dict[str, Any]] = None


class BlockOutput(BaseModel): ...


def log_and_check_with_memory(
    condition: Union[
        Callable[[Memory], Coroutine[Any, Any, bool]],
        Callable[[], Coroutine[Any, Any, bool]],
        Callable[[Memory], bool],
        Callable[[], bool],
    ] = lambda: True,
    trigger_interval: float = TRIGGER_INTERVAL,
    record_function_calling: bool = False,
):
    """
    A decorator that logs function calls and optionally checks a condition before executing the function.

    This decorator is specifically designed to be used with the `block` method. A 'Memory' object is required in method input.

    - **Args**:
        - `condition` (Callable): A condition function that must be satisfied before the decorated function is executed.
                             Can be synchronous or asynchronous.
        - `trigger_interval` (float): The interval (in seconds) to wait between condition checks.
        - `record_function_calling` (bool): Whether to log the function call information.
    """

    def decorator(func):
        @record_call_aio(record_function_calling)
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            memory = None
            for arg in list(args) + list(kwargs.values()):
                if memory is not None:
                    break
                if isinstance(arg, Memory):
                    memory = arg
            assert isinstance(memory, Memory), "Input arguments has no `Memory` object!"
            # Wait until the condition is met
            sig = inspect.signature(condition)
            params = list(sig.parameters.values())
            if len(params) == 1 and params[0].annotation is Memory:
                if inspect.iscoroutinefunction(condition):
                    condition_func = cast(
                        Callable[[Memory], Coroutine[Any, Any, bool]], condition
                    )
                    while not await condition_func(memory):
                        await asyncio.sleep(trigger_interval)
                else:
                    condition_func = cast(Callable[[Memory], bool], condition)
                    while not condition_func(memory):
                        await asyncio.sleep(trigger_interval)
            elif len(params) == 0:
                if inspect.iscoroutinefunction(condition):
                    condition_func = cast(
                        Callable[[], Coroutine[Any, Any, bool]], condition
                    )
                    while not await condition_func():
                        await asyncio.sleep(trigger_interval)
                else:
                    condition_func = cast(Callable[[], bool], condition)
                    while not condition_func():
                        await asyncio.sleep(trigger_interval)
            else:
                raise RuntimeError(
                    f"Invalid parameter format in condition function {condition}"
                )
            result = await func(self, *args, **kwargs)
            return result

        return wrapper

    return decorator


def log_and_check(
    condition: Union[
        Callable[[], Coroutine[Any, Any, bool]],
        Callable[[], bool],
    ] = lambda: True,
    trigger_interval: float = TRIGGER_INTERVAL,
    record_function_calling: bool = False,
):
    """
    A decorator that logs function calls and optionally checks a condition before executing the function.

    This decorator is specifically designed to be used with the `block` method.

    - **Args**:
        - `condition` (Callable): A condition function that must be satisfied before the decorated function is executed.
                             Can be synchronous or asynchronous.
        - `trigger_interval` (float): The interval (in seconds) to wait between condition checks.
        - `record_function_calling` (bool): Whether to log the function call information.
    """

    def decorator(func):
        @record_call_aio(record_function_calling)
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Wait until the condition is met
            sig = inspect.signature(condition)
            params = list(sig.parameters.values())
            if len(params) == 0:
                if inspect.iscoroutinefunction(condition):
                    while not await condition():
                        await asyncio.sleep(trigger_interval)
                else:
                    while not condition():
                        await asyncio.sleep(trigger_interval)
            else:
                raise RuntimeError(
                    f"Invalid parameter format in condition function {condition}"
                )
            result = await func(self, *args, **kwargs)
            return result

        return wrapper

    return decorator


def trigger_class():
    def decorator(cls):
        original_forward = cls.forward

        @functools.wraps(original_forward)
        async def wrapped_forward(self, *args, **kwargs):
            if self.trigger is not None:
                await self.trigger.wait_for_trigger()
            return await original_forward(self, *args, **kwargs)

        cls.forward = wrapped_forward
        return cls

    return decorator


# Behavior Block, used for augmenting agent's behavior capabilities
class Block:
    """
    A foundational component similar to a layer in PyTorch, used for building complex systems.
    """

    ParamsType = BlockParams
    Context = BlockContext
    OutputType = None
    NeedAgent: bool = (
        False  # Whether the block needs an agent, if True, the associated agent will be set automatically
    )
    name: str = ""
    description: str = ""
    actions: dict[str, str] = {}

    def __init__(
        self,
        llm: Optional[LLM] = None,
        environment: Optional[Environment] = None,
        agent_memory: Optional[Memory] = None,
        block_params: Optional[Any] = None,
    ):
        """
        - **Description**:
            - Initializes a new instance of the Block class with optional LLM, Memory, Simulator, and Trigger components.

        - **Args**:
            - `name` (str): The name of the block.
            - `llm` (Optional[LLM], optional): An instance of LLM. Defaults to None.
            - `environment` (Optional[Environment], optional): An instance of Environment. Defaults to None.
            - `memory` (Optional[Memory], optional): An instance of Memory. Defaults to None.
            - `trigger` (Optional[EventTrigger], optional): An event trigger that may be associated with this block. Defaults to None.
        """
        self._llm = llm
        self._agent_memory = agent_memory
        self._environment = environment
        self._agent = None

        # parse block_params
        if block_params is None:
            block_params = self.default_params()
        self.params = block_params
        for key, value in self.params.model_dump().items():
            if key == "block_memory":
                self._block_memory = StateMemory(value)
            else:
                setattr(self, key, value)

        # initialize context
        context = self.default_context()
        self.context = context_to_dot_dict(context)

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
            if hasattr(method, "_register_info"):
                info = method._register_info
                cls.get_functions[info["function_name"]] = info

    def set_agent(self, agent: Any):
        self._agent = agent

    @property
    def agent(self) -> Any:
        if self._agent is None:
            raise RuntimeError(
                f"Agent access before assignment, please `set_agent` first!"
            )
        return self._agent

    @property
    def llm(self) -> LLM:
        if self._llm is None:
            raise RuntimeError(f"LLM access before assignment, please `set_llm` first!")
        return self._llm

    @property
    def memory(self) -> Memory:
        if self._agent_memory is None:
            raise RuntimeError(
                f"Memory access before assignment, please `set_memory` first!"
            )
        return self._agent_memory

    @property
    def agent_memory(self) -> Memory:
        if self._agent_memory is None:
            raise RuntimeError(
                f"Memory access before assignment, please `set_memory` first!"
            )
        return self._agent_memory

    @property
    def block_memory(self) -> StateMemory:
        if self._block_memory is None:
            raise RuntimeError(
                f"Block memory access before assignment, please `set_block_memory` first!"
            )
        return self._block_memory

    @property
    def environment(self) -> Environment:
        if self._environment is None:
            raise RuntimeError(
                f"Environment access before assignment, please `set_environment` first!"
            )
        return self._environment

    async def before_forward(self):
        """
        Before forward - prepare context
        """
        pass

    async def after_forward(self):
        """
        After forward - update/clean context
        """
        pass

    @auto_deepcopy_dotdict
    async def forward(self, agent_context: DotDict):
        """
        - **Description**:
            - Each block performs a specific reasoning task. This method should be overridden by subclasses.
            - Subclasses can define their own parameters as needed.

        - **Args**:
            - `*args`: Variable length argument list.
            - `**kwargs`: Arbitrary keyword arguments.

        - **Raises**:
            - `NotImplementedError`: Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses should implement this method")
