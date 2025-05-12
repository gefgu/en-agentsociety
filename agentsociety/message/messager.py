import asyncio
import logging
import time
from typing import List, Optional, Any, Literal

import jsonc
from pydantic import BaseModel, Field
import ray
import redis.asyncio as aioredis
from redis.asyncio.client import PubSub

from ..logger import get_logger
from ..utils.decorators import lock_decorator
from .message_interceptor import MessageIdentifier

__all__ = [
    "Messager",
    "RedisConfig",
]


class RedisConfig(BaseModel):
    """Redis configuration class."""

    server: str = Field(...)
    """Redis server address"""

    port: int = Field(6379, ge=0, le=65535)
    """Port number for Redis connection"""

    password: Optional[str] = Field(None)
    """Password for Redis connection"""

    db: int = Field(0)
    """Database number for Redis connection"""

    timeout: float = Field(60, ge=0)
    """Timeout for Redis connection"""


class Messager:
    """
    A class to manage message sending and receiving using Redis pub/sub.

    - **Attributes**:
        - `client` (aioredis.Redis): An instance of the Redis async client.
        - `connected` (bool): Indicates whether the connection to Redis is established.
        - `message_queue` (asyncio.Queue): Queue for storing received messages.
        - `receive_messages_task` (Optional[Task]): Task for listening to incoming messages.
        - `_message_interceptor` (Optional[ray.ObjectRef]): Reference to a remote message interceptor object.
        - `_log_list` (list): List to store message logs.
        - `_lock` (asyncio.Lock): Lock for thread-safe operations.
        - `_topics` (set[str]): Set of topics the client is subscribed to.
    """

    def __init__(
        self,
        config: RedisConfig,
        exp_id: str,
        message_interceptor: Optional[ray.ObjectRef] = None,
        forward_strategy: Literal["outer_control", "inner_control"] = "inner_control",
    ):
        """
        Initialize the Messager with Redis connection parameters.

        - **Args**:
            - `config` (RedisConfig): Redis configuration.
            - `exp_id` (str): Experiment ID.
            - `message_interceptor` (Optional[ray.ObjectRef], optional): Reference to a message interceptor object.
        """
        get_logger().info(f"Connecting to Redis at {config.server}:{config.port}")
        self.client = aioredis.Redis(
            host=config.server,
            port=config.port,
            db=config.db,
            password=config.password,
            socket_timeout=config.timeout,
            socket_keepalive=True,
            health_check_interval=5,
            single_connection_client=True,
        )
        self.exp_id = exp_id
        self.forward_strategy = forward_strategy
        self.connected = False  # whether is messager connected
        self.message_queue = asyncio.Queue()  # store received messages
        self.receive_messages_task = None
        self._message_interceptor = message_interceptor
        self._log_list = []
        self._wait_for_send_message: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()
        get_logger().info("Messager initialized")

    @property
    def message_interceptor(self) -> Optional[ray.ObjectRef]:
        """
        Access the message interceptor reference.

        - **Returns**:
            - `Optional[ray.ObjectRef]`: The message interceptor reference.
        """
        return self._message_interceptor

    def get_log_list(self):
        """
        Retrieve the list of message logs.

        - **Returns**:
            - `list`: The list of message logs containing message details and metrics.
        """
        return self._log_list

    def clear_log_list(self):
        """
        Clear all message logs.

        - **Description**:
            - Resets the message log list to an empty list.
        """
        self._log_list = []

    def set_message_interceptor(self, message_interceptor: ray.ObjectRef):
        """
        Set the message interceptor reference.

        - **Args**:
            - `message_interceptor` (ray.ObjectRef): The message interceptor reference to be set.
        """
        self._message_interceptor = message_interceptor

    async def init(self):
        """
        Attempt to connect to the Redis server up to three times.

        - **Description**:
            - Tries to establish a connection to Redis. Retries up to three times with delays between attempts.
            - Logs success or failure accordingly.
        """
        await self.client.__aenter__()
        self.connected = True
        get_logger().info("Connected to Redis")

    async def close(self):
        """
        Stop the listener and disconnect from Redis.

        - **Description**:
            - Cancels the receive_messages_task if it exists and ensures the Redis connection is closed.
            - Gracefully handles any exceptions during the task cancellation.
        """
        if self.connected:
            if self.receive_messages_task:
                self.receive_messages_task.cancel()
                await asyncio.gather(self.receive_messages_task, return_exceptions=True)

            await self.client.__aexit__(None, None, None)
            self.connected = False
            get_logger().info("Disconnected from Redis")

    @lock_decorator
    async def subscribe_and_start_listening(self, channels: List[str]):
        """
        Subscribe to one or more Redis channels.

        - **Args**:
            - `channels` (Union[str, list[str]]): Channel or list of channels to subscribe to.

        - **Description**:
            - Creates a new pubsub connection and starts listening for messages on the specified channels.
            - Logs the start of message listening.
        """
        if not self.connected:
            raise Exception(
                "Cannot subscribe to channels because not connected to Redis."
            )
        # Create a new pubsub connection
        pubsub = self.client.pubsub()

        # Create task to monitor messages
        self.receive_messages_task = asyncio.create_task(
            self._listen_for_messages(pubsub, channels)
        )
        get_logger().info("Started message listening")

    @lock_decorator
    async def fetch_messages(self):
        """
        Retrieve all messages currently in the queue.

        - **Returns**:
            - `list[Any]`: List of messages retrieved from the queue.
        """
        messages = []
        while not self.message_queue.empty():
            messages.append(await self.message_queue.get())
        return messages

    async def send_message(
        self,
        channel: str,
        payload: dict,
        from_id: Optional[int] = None,
        to_id: Optional[int] = None,
    ):
        """
        Send a message through Redis pub/sub.

        - **Args**:
            - `channel` (str): Channel to which the message should be published.
            - `payload` (dict): Payload of the message to send.
            - `from_id` (Optional[int], optional): ID of the sender. Required for interception.
            - `to_id` (Optional[int], optional): ID of the recipient. Required for interception.

        - **Description**:
            - Serializes the payload to JSON, checks it against the message interceptor (if any),
              and publishes the message to the specified channel if valid.
            - Records message metadata in the log list.
        """
        start_time = time.time()
        log = {
            "channel": channel,
            "payload": payload,
            "from_id": from_id,
            "to_id": to_id,
            "start_time": start_time,
            "consumption": 0,
            "sent": False,
        }
        message = jsonc.dumps(payload, default=str)
        if self.forward_strategy == "outer_control":
            async with self._lock:
                self._wait_for_send_message.append(
                    {
                        "channel": channel,
                        "from_id": from_id,
                        "to_id": to_id,
                        "message": message,
                    }
                )
            interceptor = self.message_interceptor
            assert interceptor is not None, "Message interceptor must be set when using `outer_control` strategy"
            if (from_id is not None and to_id is not None):
                # if all of from_id and to_id are not None, the message is intercepted by the message interceptor (agent-agent message)
                interceptor.add_message.remote(from_id, to_id, message)  # type: ignore
                # ATTENTION: the message is sent to the interceptor, but the message is not sent to the channel until forward() is called
            else:
                await self.client.publish(channel, message)
                log["sent"] = True
                get_logger().info(f"Message sent to {channel}: {message}")
                log["consumption"] = time.time() - start_time
                async with self._lock:
                    self._log_list.append(log)
        elif self.forward_strategy == "inner_control":
            interceptor = self.message_interceptor
            if (interceptor is not None and from_id is not None and to_id is not None):
                # if all of from_id and to_id are not None, the message is intercepted by the message interceptor (agent-agent message)
                is_valid = await interceptor.check_message.remote(from_id, to_id, message)  # type: ignore
                if is_valid:
                    await self.client.publish(channel, message)
                    log["sent"] = True
                    get_logger().info(f"Message sent to {channel}: {message}")
                    log["consumption"] = time.time() - start_time
                    async with self._lock:
                        self._log_list.append(log)
                else:
                    get_logger().info(f"Message not sent to {channel}: {message} due to interceptor")
            else:
                await self.client.publish(channel, message)
                log["sent"] = True
                get_logger().info(f"Message sent to {channel}: {message}")
        else:
            raise ValueError(f"Invalid forward strategy: {self.forward_strategy}")

    async def _listen_for_messages(self, pubsub: PubSub, channels: List[str]):
        """
        Internal method to continuously listen for messages and handle dynamic subscriptions.

        - **Args**:
            - `pubsub` (aioredis.client.PubSub): The Redis pubsub connection to use for subscribing and receiving messages.

        - **Description**:
            - Continuously checks for new topics to subscribe to.
            - Listens for incoming messages and places them in the message queue.
            - Handles cancellation and errors gracefully.
        """
        try:
            await pubsub.psubscribe(*channels)
            get_logger().info(
                f"Subscribed to new channels: len(channels)={len(channels)}"
            )
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1
                )
                get_logger().debug(f"Received message: {message}")
                if message and message["type"] in ("pmessage",):
                    await self.message_queue.put(message)

        except asyncio.CancelledError:
            await pubsub.punsubscribe()
            await pubsub.aclose()
            get_logger().info("Message listening stopped")
        except Exception as e:
            get_logger().error(f"Error in message listening: {e}")
            await pubsub.unsubscribe()
            await pubsub.aclose()
            raise e

    async def forward(
        self,
        validation_dict: Optional[MessageIdentifier] = None,
    ):
        """
        Forward the message to the channel if the message is valid.
        """
        if self.forward_strategy == "outer_control":
            assert validation_dict is not None, "Validation dict must be set when using `outer_control` strategy"
            for _wait_for_send_message in self._wait_for_send_message:
                is_valid = validation_dict.get((_wait_for_send_message["from_id"], _wait_for_send_message["to_id"], _wait_for_send_message["message"]), True)
                if is_valid:
                    await self.client.publish(
                        _wait_for_send_message["channel"],
                        _wait_for_send_message["message"],
                    )
                else:
                    get_logger().info(
                        f"Message not sent to {_wait_for_send_message['channel']}: {_wait_for_send_message['message']} due to interceptor"
                    )
        elif self.forward_strategy == "inner_control":
            # do nothing
            pass
        else:
            raise ValueError(f"Invalid forward strategy: {self.forward_strategy}")

    # utility

    def get_subtopic_channel(self, agent_id: int, subtopic: str):
        return f"exps:{self.exp_id}:agents:{agent_id}:{subtopic}"

    def get_user_survey_channel(self, agent_id: int):
        return self.get_subtopic_channel(agent_id, "user-survey")

    def get_user_chat_channel(self, agent_id: int):
        return self.get_subtopic_channel(agent_id, "user-chat")

    def get_agent_chat_channel(self, agent_id: int):
        return self.get_subtopic_channel(agent_id, "agent-chat")

    def get_user_payback_channel(self):
        return f"exps:{self.exp_id}:user-payback"
