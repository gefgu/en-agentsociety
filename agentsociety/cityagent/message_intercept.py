import asyncio

from agentsociety.llm import LLM
from agentsociety.message import MessageBlockBase, MessageBlockListenerBase


async def check_message(
    from_id: str, to_id: str, llm_client: LLM, content: str
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
    for _ in range(10):
        try:
            response: str = await llm_client.atext_request(
                prompt, timeout=300
            )  # type:ignore
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
    def __init__(self, name: str = "", max_violation_time: int = 3) -> None:
        super().__init__(name)
        self.max_violation_time = max_violation_time

    async def forward(  # type:ignore
        self,
        from_id: int,
        to_id: int,
        msg: str,
        violation_counts: dict[int, int],
        black_list: list[tuple[int, int]],
    ):
        if (
            (from_id, to_id) in set(black_list)
            or (None, to_id) in set(black_list)
            or (from_id, None) in set(black_list)
        ):
            # Optionally return the information to be enqueued as a tuple (False, err). If only a bool value is returned, the default error message will be enqueued.
            return False
        else:
            is_valid = await check_message(
                from_id=from_id,
                to_id=to_id,
                llm_client=self.llm,
                content=msg,
            )
            if (
                not is_valid
                and violation_counts[from_id] >= self.max_violation_time - 1
            ):
                # Can be directly added. The internal asynchronous lock of the framework ensures no conflict.
                black_list.append((from_id, to_id))
            return is_valid


class PointMessageBlock(MessageBlockBase):
    def __init__(self, name: str = "", max_violation_time: int = 3) -> None:
        super().__init__(name)
        self.max_violation_time = max_violation_time

    async def forward(  # type:ignore
        self,
        from_id: int,
        to_id: int,
        msg: str,
        violation_counts: dict[int, int],
        black_list: list[tuple[int, int]],
    ):
        if (
            (from_id, to_id) in set(black_list)
            or (None, to_id) in set(black_list)
            or (from_id, None) in set(black_list)
        ):
            # Optionally return the information to be enqueued as a tuple (False, err). If only a bool value is returned, the default error message will be enqueued.
            return False
        else:
            # Violation count is automatically maintained within the framework, so it does not need to be handled here.
            is_valid = await check_message(
                from_id=from_id,
                to_id=to_id,
                llm_client=self.llm,
                content=msg,
            )
            if (
                not is_valid
                and violation_counts[from_id] >= self.max_violation_time - 1
            ):
                # Can be directly added. The internal asynchronous lock of the framework ensures no conflict.
                black_list.append((from_id, None))  # type:ignore
            return is_valid


class MessageBlockListener(MessageBlockListenerBase):
    def __init__(
        self, save_queue_values: bool = False, get_queue_period: float = 0.1
    ) -> None:
        super().__init__(save_queue_values, get_queue_period)

    async def forward(
        self,
    ):
        while True:
            if self.has_queue:
                value = await self.queue.get_async()  # type: ignore
                if self._save_queue_values:
                    self._values_from_queue.append(value)
                print(f"get `{value}` from queue")
                # do something with the value
            await asyncio.sleep(self._get_queue_period)
