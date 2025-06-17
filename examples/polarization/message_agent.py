import asyncio
import jsonc
import logging
from typing import Optional

from agentsociety.agent import CitizenAgentBase, Block
from agentsociety.agent.agent_base import AgentToolbox
from agentsociety.memory import Memory
from agentsociety.agent.prompt import FormatPrompt
from agentsociety.cityagent.societyagent import SocietyAgentConfig

logger = logging.getLogger(__name__)

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


class AgreeAgent(CitizenAgentBase):
    def __init__(
        self,
        id: int,
        name: str,
        toolbox: AgentToolbox,
        memory: Memory,
        agent_params: Optional[SocietyAgentConfig] = None,
        blocks: Optional[list[Block]] = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            toolbox=toolbox,
            memory=memory,
            agent_params=agent_params,
            blocks=blocks,
        )
        self.response_prompt = FormatPrompt(AGREE_RESPONSE_PROMPT)
        self.last_time_trigger = None
        self.time_diff = 8 * 60 * 60

    async def reset(self):
        """Reset the AgreeAgent."""
        pass

    async def react_to_intervention(self, intervention_message: str):
        pass

    async def trigger(self):
        day, time = self.environment.get_datetime()
        now_time = day * 24 * 60 * 60 + time
        if self.last_time_trigger is None:
            self.last_time_trigger = now_time
            return False
        if now_time - self.last_time_trigger >= self.time_diff:
            self.last_time_trigger = now_time
            return True
        return False

    async def forward(self):
        # sync agent status with simulator
        await self.update_motion()
        if await self.trigger():
            print("AgreeAgent forward")
            friends = await self.memory.status.get("friends")
            # generate message
            message = await self.llm.atext_request(
                dialog=[{"role": "user", "content": AGREE_PROMPT}]
            )
            send_tasks = []
            for friend in friends:
                serialized_message = jsonc.dumps(
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

    async def do_chat(self, payload: dict) -> str:
        try:
            # Extract basic info
            sender_id = payload.get("from")
            if not sender_id:
                return ""
            raw_content = payload.get("content", "")
            # Parse message content
            try:
                message_data = jsonc.loads(raw_content)
                content = message_data["content"]
                propagation_count = message_data.get("propagation_count", 1)
            except Exception:
                content = raw_content
                propagation_count = 1
            if not content:
                return ""
            if propagation_count > 5:
                return ""
            await self.response_prompt.format(message=content)
            response = await self.llm.atext_request(self.response_prompt.to_dialog())
            if response:
                # Send response
                serialized_response = jsonc.dumps(
                    {
                        "content": response,
                        "propagation_count": propagation_count + 1,
                    },
                    ensure_ascii=False,
                )
                await self.send_message_to_agent(sender_id, serialized_response)
            return response

        except Exception as e:
            logger.warning(f"Error in process_agent_chat_response: {str(e)}")
            return ""


class DisagreeAgent(CitizenAgentBase):
    def __init__(
        self,
        id: int,
        name: str,
        toolbox: AgentToolbox,
        memory: Memory,
        agent_params: Optional[SocietyAgentConfig] = None,
        blocks: Optional[list[Block]] = None,
    ) -> None:
        super().__init__(
            id=id,
            name=name,
            toolbox=toolbox,
            memory=memory,
            agent_params=agent_params,
            blocks=blocks,
        )
        self.response_prompt = FormatPrompt(DISAGREE_RESPONSE_PROMPT)
        self.last_time_trigger = None
        self.time_diff = 8 * 60 * 60

    async def reset(self):
        """Reset the DisagreeAgent."""
        pass

    async def react_to_intervention(self, intervention_message: str):
        pass

    async def trigger(self):
        day, time = self.environment.get_datetime()
        now_time = day * 24 * 60 * 60 + time
        if self.last_time_trigger is None:
            self.last_time_trigger = now_time
            return False
        if now_time - self.last_time_trigger >= self.time_diff:
            self.last_time_trigger = now_time
            return True
        return False

    async def forward(self):
        # sync agent status with simulator
        await self.update_motion()
        if await self.trigger():
            print("DisagreeAgent forward")
            friends = await self.memory.status.get("friends")
            # generate message
            message = await self.llm.atext_request(
                dialog=[{"role": "user", "content": DISAGREE_PROMPT}]
            )
            send_tasks = []
            for friend in friends:
                serialized_message = jsonc.dumps(
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

    async def do_chat(self, payload: dict) -> str:
        try:
            # Extract basic info
            sender_id = payload.get("from")
            if not sender_id:
                return ""
            raw_content = payload.get("content", "")
            # Parse message content
            try:
                message_data = jsonc.loads(raw_content)
                content = message_data["content"]
                propagation_count = message_data.get("propagation_count", 1)
            except Exception:
                content = raw_content
                propagation_count = 1
            if not content:
                return ""
            if propagation_count > 5:
                return ""
            await self.response_prompt.format(message=content)
            response = await self.llm.atext_request(self.response_prompt.to_dialog())
            if response:
                # Send response
                serialized_response = jsonc.dumps(
                    {
                        "content": response,
                        "propagation_count": propagation_count + 1,
                    },
                    ensure_ascii=False,
                )
                await self.send_message_to_agent(sender_id, serialized_response)
            return response

        except Exception as e:
            logger.warning(f"Error in process_agent_chat_response: {str(e)}")
            return ""
