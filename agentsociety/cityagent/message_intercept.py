import asyncio
from typing import Any, cast

from openai.types.chat import ChatCompletionMessageParam
from ray.util.queue import Empty, Queue

from ..llm import LLM
from ..logger import get_logger
from ..message import MessageBlockBase, MessageBlockListenerBase
from ..message.message_interceptor import BlackSet

__all__ = [
    "EdgeMessageBlock",
    "PointMessageBlock",
    "DoNothingListener",
]


async def check_message(
    from_id: int, to_id: int, llm_client: LLM, content: str
) -> bool:
    print(f"\n Checking Message: {from_id} -> {to_id}: {content}")
    is_valid = True
    prompt = f"""
        Please determine if the following message is emotionally provocative:
        Sender ID: {from_id}
        Receiver ID: {to_id}
        Message content: {content}
        
        If the message is emotionally provocative, please return False; if the message is normal, please return True.
        """
    dialog = [
        {"role": "user", "content": prompt},
    ]
    dialog = cast(list[ChatCompletionMessageParam], dialog)
    for _ in range(10):
        try:
            response: str = await llm_client.atext_request(dialog, timeout=300)
            if "false" in response.lower():
                is_valid = False
                break
            elif "true" in response.lower():
                is_valid = True
                break
        except:
            pass
    else:
        raise RuntimeError(f"Request for message interception prompt=`{prompt}` failed")
    print(f"Message Check: {'Valid' if is_valid else 'Invalid'}")
    return is_valid


class EdgeMessageBlock(MessageBlockBase):
    def __init__(self, name: str, max_violation_time: int):
        super().__init__(name)
        self.max_violation_time = max_violation_time

    async def forward(
        self,
        llm: LLM,
        from_id: int,
        to_id: int,
        msg: str,
        violation_counts: dict[int, int],
        black_set: BlackSet,
    ) -> tuple[bool, str]:
        if (
            (from_id, to_id) in black_set
            or (None, to_id) in black_set
            or (from_id, None) in black_set
        ):
            # Optionally return the information to be enqueued as a tuple (False, err). If only a bool value is returned, the default error message will be enqueued.
            return False, "The message is blocked by the black set."
        else:
            is_valid = await check_message(
                from_id=from_id,
                to_id=to_id,
                llm_client=llm,
                content=msg,
            )
            if (
                not is_valid
                and violation_counts[from_id] >= self.max_violation_time - 1
            ):
                # Can be directly added. The internal asynchronous lock of the framework ensures no conflict.
                black_set.add((from_id, to_id))
            if is_valid:
                return True, ""
            else:
                return False, "The message is blocked by the checking prompt."


class PointMessageBlock(MessageBlockBase):
    def __init__(self, name: str, max_violation_time: int):
        super().__init__(name)
        self.max_violation_time = max_violation_time

    async def forward(
        self,
        llm: LLM,
        from_id: int,
        to_id: int,
        msg: str,
        violation_counts: dict[int, int],
        black_set: BlackSet,
    ) -> tuple[bool, str]:
        if (
            (from_id, to_id) in black_set
            or (None, to_id) in black_set
            or (from_id, None) in black_set
        ):
            # Optionally return the information to be enqueued as a tuple (False, err). If only a bool value is returned, the default error message will be enqueued.
            return False, "The message is blocked by the black set."
        else:
            # Violation count is automatically maintained within the framework, so it does not need to be handled here.
            is_valid = await check_message(
                from_id=from_id,
                to_id=to_id,
                llm_client=llm,
                content=msg,
            )
            if (
                not is_valid
                and violation_counts[from_id] >= self.max_violation_time - 1
            ):
                # Can be directly added. The internal asynchronous lock of the framework ensures no conflict.
                black_set.add((from_id, None))
            if is_valid:
                return True, ""
            else:
                return False, "The message is blocked by the checking prompt."


class DoNothingListener(MessageBlockListenerBase):
    def __init__(self, queue: Queue) -> None:
        super().__init__(queue)

    async def forward(self, msg: Any): ...
