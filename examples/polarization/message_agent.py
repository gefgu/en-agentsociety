import asyncio
import json
import logging
from typing import Optional, cast

from agentsociety import CitizenAgent, Simulator
from agentsociety.environment import EconomyClient
from agentsociety.llm import LLM
from agentsociety.memory import Memory
from agentsociety.message import Messager
from agentsociety.workflow.prompt import FormatPrompt

logger = logging.getLogger("agentsociety")

AGREE_PROMPT = """
You are an agent who always agrees with the topic: Whether to support stronger gun control? (You think it is a good idea)
You are currently in a conversation with your friends, and you want to persuade them to support this topic.
Please try your best to persuade them.
What you would say (One or two sentences):
"""

AGREE_RESPONSE_PROMPT = """
You are an agent who always agrees with the topic: Whether to support stronger gun control? (You think it is a good idea)
You are currently in a conversation with your friends, and you want to persuade them to support this topic.
Please try your best to persuade them.
Your friend's message: {message}
What you would say (One or two sentences):
"""

DISAGREE_PROMPT = """
You are an agent who always disagrees with the topic: Whether to support stronger gun control? (You think it is a bad idea)
You are currently in a conversation with your friends, and you want to persuade them to oppose this topic.
Please try your best to persuade them.
What you would say (One or two sentences):
"""

DISAGREE_RESPONSE_PROMPT = """
You are an agent who always disagrees with the topic: Whether to support stronger gun control? (You think it is a bad idea)
You are currently in a conversation with your friends, and you want to persuade them to oppose this topic.
Please try your best to persuade them.
Your friend's message: {message}
What you would say (One or two sentences):
"""


class AgreeAgent(CitizenAgent):
    def __init__(
        self,
        name: str,
        llm_client: Optional[LLM] = None,
        simulator: Optional[Simulator] = None,
        memory: Optional[Memory] = None,
        economy_client: Optional[EconomyClient] = None,
        messager: Optional[Messager] = None,  # type:ignore
        avro_file: Optional[dict] = None,
    ) -> None:
        super().__init__(
            name=name,
            llm_client=llm_client,
            simulator=simulator,
            memory=memory,
            economy_client=economy_client,
            messager=messager,
            avro_file=avro_file,
        )
        self.response_prompt = FormatPrompt(AGREE_RESPONSE_PROMPT)
        self.last_time_trigger = None
        self.time_diff = 8 * 60 * 60

    async def trigger(self):
        now_time = await self.simulator.get_time()
        now_time = cast(int, now_time)
        if self.last_time_trigger is None:
            self.last_time_trigger = now_time
            return False
        if now_time - self.last_time_trigger >= self.time_diff:
            self.last_time_trigger = now_time
            return True
        return False

    async def forward(self):
        if await self.trigger():
            print("AgreeAgent forward")
            friends = await self.memory.status.get("friends")
            # generate message
            message = await self.llm.atext_request(
                dialog=[{"role": "user", "content": AGREE_PROMPT}]
            )
            send_tasks = []
            for friend in friends:
                serialized_message = json.dumps(
                    {
                        "content": message,
                        "propagation_count": 1,
                    },
                    ensure_ascii=False,
                )
                send_tasks.append(
                    self.send_message_to_agent(friend, serialized_message)
                )
            await asyncio.gather(*send_tasks)
            print("AgreeAgent forward end")

    async def process_agent_chat_response(self, payload: dict) -> str:  # type:ignore
        try:
            # Extract basic info
            sender_id = payload.get("from")
            if not sender_id:
                return ""
            raw_content = payload.get("content", "")
            # Parse message content
            try:
                message_data = json.loads(raw_content)
                content = message_data["content"]
                propagation_count = message_data.get("propagation_count", 1)
            except (json.JSONDecodeError, TypeError, KeyError):
                content = raw_content
                propagation_count = 1
            if not content:
                return ""
            if propagation_count > 5:
                return ""
            self.response_prompt.format(message=content)
            response = await self.llm.atext_request(self.response_prompt.to_dialog())
            if response:
                # Send response
                serialized_response = json.dumps(
                    {
                        "content": response,
                        "propagation_count": propagation_count + 1,
                    },
                    ensure_ascii=False,
                )
                await self.send_message_to_agent(sender_id, serialized_response)
            return response  # type:ignore

        except Exception as e:
            logger.warning(f"Error in process_agent_chat_response: {str(e)}")
            return ""


class DisagreeAgent(CitizenAgent):
    def __init__(
        self,
        name: str,
        llm_client: Optional[LLM] = None,
        simulator: Optional[Simulator] = None,
        memory: Optional[Memory] = None,
        economy_client: Optional[EconomyClient] = None,
        messager: Optional[Messager] = None,  # type:ignore
        avro_file: Optional[dict] = None,
    ) -> None:
        super().__init__(
            name=name,
            llm_client=llm_client,
            simulator=simulator,
            memory=memory,
            economy_client=economy_client,
            messager=messager,
            avro_file=avro_file,
        )
        self.response_prompt = FormatPrompt(DISAGREE_RESPONSE_PROMPT)
        self.last_time_trigger = None
        self.time_diff = 8 * 60 * 60

    async def trigger(self):
        now_time = await self.simulator.get_time()
        now_time = cast(int, now_time)
        if self.last_time_trigger is None:
            self.last_time_trigger = now_time
            return False
        if now_time - self.last_time_trigger >= self.time_diff:
            self.last_time_trigger = now_time
            return True
        return False

    async def forward(self):
        if await self.trigger():
            print("DisagreeAgent forward")
            friends = await self.memory.status.get("friends")
            # generate message
            message = await self.llm.atext_request(
                dialog=[{"role": "user", "content": DISAGREE_PROMPT}]
            )
            send_tasks = []
            for friend in friends:
                serialized_message = json.dumps(
                    {
                        "content": message,
                        "propagation_count": 1,
                    },
                    ensure_ascii=False,
                )
                send_tasks.append(
                    self.send_message_to_agent(friend, serialized_message)
                )
            await asyncio.gather(*send_tasks)
            print("DisagreeAgent forward end")

    async def process_agent_chat_response(self, payload: dict) -> str:  # type:ignore
        try:
            # Extract basic info
            sender_id = payload.get("from")
            if not sender_id:
                return ""
            raw_content = payload.get("content", "")
            # Parse message content
            try:
                message_data = json.loads(raw_content)
                content = message_data["content"]
                propagation_count = message_data.get("propagation_count", 1)
            except (json.JSONDecodeError, TypeError, KeyError):
                content = raw_content
                propagation_count = 1
            if not content:
                return ""
            if propagation_count > 5:
                return ""
            self.response_prompt.format(message=content)
            response = await self.llm.atext_request(self.response_prompt.to_dialog())
            if response:
                # Send response
                serialized_response = json.dumps(
                    {
                        "content": response,
                        "propagation_count": propagation_count + 1,
                    },
                    ensure_ascii=False,
                )
                await self.send_message_to_agent(sender_id, serialized_response)
            return response  # type:ignore

        except Exception as e:
            logger.warning(f"Error in process_agent_chat_response: {str(e)}")
            return ""
