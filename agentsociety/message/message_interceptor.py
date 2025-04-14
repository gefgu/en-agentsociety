import asyncio
import inspect
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from typing import Any, Optional, Union, TypeVar, Set

import ray
from ray.util.queue import Queue, Empty

from ..llm import LLM, LLMConfig, monitor_requests
from ..utils.decorators import lock_decorator
from ..logger import get_logger

DEFAULT_ERROR_STRING = """
From `{from_id}` To `{to_id}` abort due to block `{block_name}`
"""

logger = logging.getLogger("message_interceptor")

__all__ = [
    "MessageBlockBase",
    "MessageInterceptor",
    "MessageBlockListenerBase",
]

BlackSetEntry = TypeVar(
    "BlackSetEntry", bound=tuple[Union[int, None], Union[int, None]]
)
BlackSet = Set[BlackSetEntry]


class MessageBlockBase(ABC):
    """
    block for message interception
    """

    def __init__(self, name: str = ""):
        self._name = name
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    @lock_decorator
    async def forward(
        self,
        llm: LLM,
        from_id: int,
        to_id: int,
        msg: str,
        violation_counts: dict[int, int],
        black_set: BlackSet,
    ) -> tuple[bool, str]:
        """
        Forward a message through the block.

        - **Args**:
            - `llm` (LLM): The LLM instance.
            - `from_id` (int): The ID of the sender.
            - `to_id` (int): The ID of the recipient.
            - `msg` (str): The message content to forward.
            - `violation_counts` (dict[int, int]): The violation counts.
            - `black_set` (BlackSet): The blacklist.

        - **Returns**:
            - `tuple[bool, str]`: A tuple containing a boolean indicating whether the message was processed successfully and a string containing the error message if the message was not processed successfully.
        """
        raise NotImplementedError()


@ray.remote
class MessageInterceptor:
    """
    A class to intercept and process messages based on configured rules.
    """

    def __init__(
        self,
        blocks: list[MessageBlockBase],
        llm_config: list[LLMConfig],
        queue: Queue,
        black_set: BlackSet = set(),
    ) -> None:
        """
        Initialize the MessageInterceptor with optional configuration.

        - **Args**:
            - `blocks` (list[MessageBlockBase], optional): Initial list of message interception rules. Defaults to an empty list.
            - `llm_config` (LLMConfig): Configuration dictionary for initializing the LLM instance. Defaults to None.
            - `queue` (Queue): Queue for message processing. Defaults to None.
            - `black_set` (BlackSet, optional): Initial blacklist of communication pairs. Defaults to an empty set.
        """
        self._blocks = blocks
        self._violation_counts: dict[int, int] = defaultdict(int)
        self._black_set = black_set
        self._llm = LLM(llm_config)
        self._queue = queue
        self._lock = asyncio.Lock()

    async def init(self):
        asyncio.create_task(monitor_requests(self._llm))

    async def close(self):
        pass

    # Property accessors
    @property
    def llm(self) -> LLM:
        """
        Access the Large Language Model instance.

        - **Description**:
            - Provides access to the internal LLM instance. Raises an error if accessed before assignment.

        - **Raises**:
            - `RuntimeError`: If accessed before setting the LLM.

        - **Returns**:
            - `LLM`: The Large Language Model instance.
        """
        if self._llm is None:
            raise RuntimeError(f"LLM access before assignment, please `set_llm` first!")
        return self._llm

    # Black set related methods
    @lock_decorator
    async def black_set(self) -> BlackSet:
        """
        Retrieve the blacklist.

        - **Description**:
            - Returns a deep copy of the current blacklist to protect the original data from external modifications.

        - **Returns**:
            - `BlackSet`: The blacklist.
        """
        return deepcopy(self._black_set)

    @lock_decorator
    async def add_to_black_set(self, black_set: Union[BlackSet, BlackSetEntry]):
        """
        Add entries to the blacklist.

        - **Description**:
            - Adds one or more entries to the blacklist, ensuring each entry's uniqueness.

        - **Args**:
            - `black_set` (Union[BlackSet, BlackSetEntry]):
                Can be a single tuple or a set of tuples indicating the entries to add to the blacklist.

        - **Returns**:
            - `None`
        """
        if isinstance(black_set, tuple):
            # Single tuple case
            self._black_set.add(black_set)
        else:
            # Set of tuples case
            self._black_set.update(black_set)

    @lock_decorator
    async def remove_from_black_set(
        self, to_remove_black_set: Union[BlackSet, BlackSetEntry]
    ):
        """
        Remove entries from the blacklist.

        - **Description**:
            - Removes one or more entries from the blacklist, ensuring each entry's removal.

        - **Args**:
            - `to_remove_black_set` (Union[BlackSet, BlackSetEntry]):
                Can be a single tuple or a set of tuples indicating the entries to remove from the blacklist.

        - **Returns**:
            - `None`
        """
        if isinstance(to_remove_black_set, tuple):
            # Single tuple case
            self._black_set.discard(to_remove_black_set)
        else:
            # Set of tuples case
            self._black_set.difference_update(to_remove_black_set)

    @lock_decorator
    async def set_black_set(self, black_set: Union[BlackSet, BlackSetEntry]):
        """
        Set the blacklist with new entries.

        - **Description**:
            - Updates the blacklist with new entries, ensuring each entry's uniqueness.

        - **Args**:
            - `black_set` (Union[BlackSet, BlackSetEntry]):
                Can be a single tuple or a set of tuples indicating the new blacklist entries.

        - **Returns**:
            - `None`
        """
        if isinstance(black_set, tuple):
            # Single tuple case
            self._black_set = {black_set}
        else:
            # Set of tuples case
            self._black_set = black_set.copy()

    # Blocks related methods
    @lock_decorator
    async def blocks(self) -> list[MessageBlockBase]:
        """
        Retrieve the message interception rules.

        - **Description**:
            - Returns a copy of the current list of message interception rules.

        - **Returns**:
            - `list[MessageBlockBase]`: The list of message interception rules.
        """
        return self._blocks

    @lock_decorator
    async def insert_block(self, block: MessageBlockBase, index: Optional[int] = None):
        """
        Insert a message block into the blocks list at a specified position.

        - **Description**:
            - Inserts a new message interception rule into the list at the specified index or appends it if no index is provided.

        - **Args**:
            - `block` (MessageBlockBase): The message block to insert.
            - `index` (Optional[int], optional): The position at which to insert the block. Defaults to appending at the end.

        - **Returns**:
            - `None`
        """
        if index is None:
            index = len(self._blocks)
        self._blocks.insert(index, block)

    @lock_decorator
    async def pop_block(self, index: Optional[int] = None) -> MessageBlockBase:
        """
        Remove and return a message block from the blocks list.

        - **Description**:
            - Removes and returns the message block at the specified index or the last one if no index is provided.

        - **Args**:
            - `index` (Optional[int], optional): The position of the block to remove. Defaults to removing the last element.

        - **Returns**:
            - `MessageBlockBase`: The removed message block.
        """
        if index is None:
            index = -1
        return self._blocks.pop(index)

    @lock_decorator
    async def set_blocks(self, blocks: list[MessageBlockBase]):
        """
        Replace the current blocks list with a new list of message blocks.

        - **Description**:
            - Sets a new list of message interception rules, replacing the existing list.

        - **Args**:
            - `blocks` (list[MessageBlockBase]): The new list of message blocks to set.

        - **Returns**:
            - `None`
        """
        self._blocks = blocks

    # Message forwarding related methods
    @lock_decorator
    async def violation_counts(self) -> dict[int, int]:
        """
        Retrieve the violation counts.

        - **Description**:
            - Returns a deep copy of the violation counts to prevent external modification of the original data.

        - **Returns**:
            - `dict[str, int]`: The dictionary of violation counts.
        """
        return deepcopy(self._violation_counts)

    @lock_decorator
    async def forward(
        self,
        from_id: int,
        to_id: int,
        msg: str,
    ):
        """
        Forward a message through all message blocks.

        - **Description**:
            - Processes a message by passing it through all configured message blocks. Each block can modify the message or prevent its forwarding based on implemented logic.

        - **Args**:
            - `from_id` (int): The ID of the sender.
            - `to_id` (int): The ID of the recipient.
            - `msg` (str): The message content to forward.

        - **Returns**:
            - `bool`: True if the message was successfully processed by all blocks, otherwise False.
        """
        for _block in self._blocks:
            is_valid, err = await _block.forward(
                llm=self.llm,
                from_id=from_id,
                to_id=to_id,
                msg=msg,
                violation_counts=self._violation_counts,
                black_set=self._black_set,
            )
            if not is_valid:
                get_logger().debug(f"put `{err}` into queue")
                await self._queue.put_async(err)
                self._violation_counts[from_id] += 1
                # print(self._black_set)
                return False
        # print(self._black_set)
        return True


class MessageBlockListenerBase(ABC):
    """
    Base class for message block listeners that can listen to a queue and process items.

    - **Attributes**:
        - `_queue` (Optional[Queue]): Queue from which the listener retrieves items.
        - `_lock` (asyncio.Lock): Lock for thread-safe access in asynchronous environments.
        - `_values_from_queue` (list[Any]): List of values retrieved from the queue if saving is enabled.
        - `_save_queue_values` (bool): Flag indicating whether to save values from the queue.
        - `_get_queue_period` (float): Period in seconds between queue retrieval attempts.
    """

    def __init__(self, queue: Queue):
        """
        Initialize the MessageBlockListenerBase with optional configuration.

        - **Args**:
            - `queue` (Queue): The queue instance to be set.
        """
        self._queue = queue
        self._listen_task: Optional[asyncio.Task] = None

    @property
    def queue(self) -> Queue:
        """
        Access the queue used by the listener.

        - **Description**:
            - Provides access to the internal queue. Raises an error if accessed before assignment.

        - **Raises**:
            - `RuntimeError`: If accessed before setting the queue.

        - **Returns**:
            - `Queue`: The queue instance.
        """
        if self._queue is None:
            raise RuntimeError(
                f"Queue access before assignment, please `set_queue` first!"
            )
        return self._queue

    @abstractmethod
    async def forward(self, msg: Any):
        """
        Continuously retrieve items from the queue and process them.

        - **Description**:
            - Listens to the queue, retrieves items at intervals defined by `_get_queue_period`,
              and processes each item. If `_save_queue_values` is True, it saves the items in `_values_from_queue`.

        - **Returns**:
            - `None`
        """
        raise NotImplementedError()

    async def _listen(self):
        while True:
            try:
                value = await self.queue.get_async(timeout=1)
            except Empty:
                continue
            get_logger().debug(f"get `{value}` from queue")
            await self.forward(value)

    def init(self):
        self._listen_task = asyncio.create_task(self._listen())

    async def close(self):
        if self._listen_task is not None:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                get_logger().error(f"Error closing listener task: {e}")
            self._listen_task = None
