import random
from typing import Any, Optional

from ...agent import (
    AgentToolbox,
    Block,
    BlockParams,
    BlockContext,
    DotDict,
)
from ...logger import get_logger
from ...memory import Memory
from ...agent.dispatcher import BlockDispatcher
from ..sharing_params import SocietyAgentBlockOutput
from .utils import coerce_minutes


class SleepBlock(Block):
    """Block implementation for handling sleep-related actions in an agent's workflow.

    Attributes:
        description (str): Human-readable block purpose.
        prompt_name (str): PromptManager key for time estimation.
    """

    name = "SleepBlock"
    description = "Handles sleep-related actions"
    NeedAgent = True

    def __init__(
        self,
        toolbox: AgentToolbox,
        agent_memory: Optional[Memory] = None,
    ):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )
        self.prompt_name = "other_sleep_time_estimate"

    async def forward(self, context: DotDict):
        """Execute sleep action and estimate time consumption using LLM.

        Args:
            context: Workflow context containing plan and other metadata.

        Returns:
            Dictionary with execution status, evaluation, time consumed, and node ID.
        """
        node_id = await self.memory.stream.add(topic="other", description="I slept")
        result = await self.execute_prompt(
            self.prompt_name, dict(context), func_name="forward",
        )
        if result.success:
            consumed_time = coerce_minutes(
                result.parsed.get("time"),
                lambda: random.randint(1, 8) * 60,
                minimum=1,
            )
        else:
            get_logger().warning(f"SleepBlock LLM failed: {result.error}")
            consumed_time = random.randint(1, 8) * 60
        return {
            "success": True,
            "evaluation": f'Sleep: {context["current_step"]["intention"]}',
            "consumed_time": consumed_time,
            "node_id": node_id,
        }


class OtherNoneBlock(Block):
    """Fallback block for handling undefined/non-specific actions in workflows.

    Attributes:
        description (str): Human-readable block purpose.
        prompt_name (str): PromptManager key for time estimation.
    """

    name = "OtherNoneBlock"
    description = "Handles all kinds of intentions/actions except sleep"
    NeedAgent = True

    def __init__(self, toolbox: AgentToolbox, agent_memory: Optional[Memory] = None):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )
        self.prompt_name = "other_time_estimate"

    async def forward(self, context: DotDict):
        node_id = await self.memory.stream.add(
            topic="other", description=f"I {context['current_step']['intention']}"
        )
        result = await self.execute_prompt(
            self.prompt_name, dict(context), func_name="forward",
        )
        if result.success:
            consumed_time = coerce_minutes(
                result.parsed.get("time"),
                lambda: random.randint(1, 180),
                minimum=1,
            )
        else:
            get_logger().warning(f"OtherNoneBlock LLM failed: {result.error}")
            consumed_time = random.randint(1, 180)
        return {
            "success": True,
            "evaluation": f'Finished executing {context["current_step"]["intention"]}',
            "consumed_time": consumed_time,
            "node_id": node_id,
        }


class OtherBlockParams(BlockParams):
    pass


class OtherBlockContext(BlockContext): ...


class OtherBlock(Block):
    """Orchestration block for managing specialized sub-blocks (SleepBlock/OtherNoneBlock).

    Attributes:
        sleep_block (SleepBlock): Specialized block for sleep actions.
        other_none_block (OtherNoneBlock): Fallback block for generic actions.
        trigger_time (int): Counter for block activation frequency.
        token_consumption (int): Accumulated LLM token usage.
        dispatcher (BlockDispatcher): Router for selecting appropriate sub-blocks.
    """

    ParamsType = OtherBlockParams
    OutputType = SocietyAgentBlockOutput
    ContextType = OtherBlockContext
    name = "OtherBlock"
    description = "Responsible for all kinds of intentions/actions except mobility, economy, and social, for example, sleep, other actions, etc."
    actions = {
        "sleep": "Support the sleep action",
        "other": "Support other actions",
    }
    NeedAgent = True

    def __init__(
        self,
        toolbox: AgentToolbox,
        agent_memory: Memory,
        block_params: Optional[OtherBlockParams] = None,
    ):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
            block_params=block_params,
        )
        # init all blocks
        self.sleep_block = SleepBlock(toolbox, agent_memory)
        self.other_none_block = OtherNoneBlock(toolbox, agent_memory)
        self.trigger_time = 0
        self.token_consumption = 0
        # init dispatcher
        self.dispatcher = BlockDispatcher(toolbox, agent_memory)
        # register all blocks
        self.dispatcher.register_blocks([self.sleep_block, self.other_none_block])

    def set_agent(self, agent: Any) -> None:
        """Associate the block and its sub-blocks with a specific agent.

        Args:
            agent: The agent instance to associate with.
        """
        super().set_agent(agent)

        self.sleep_block.set_agent(agent)
        self.other_none_block.set_agent(agent)

    async def forward(self, agent_context: DotDict) -> SocietyAgentBlockOutput:
        """Route workflow steps to appropriate sub-blocks and track resource usage.

        Args:
            context: Workflow context containing plan and metadata.

        Returns:
            Execution result from the selected sub-block.
        """
        self.trigger_time += 1
        consumption_start = (
            self.llm.prompt_tokens_used + self.llm.completion_tokens_used
        )

        context = agent_context | self.context

        # Select the appropriate sub-block using dispatcher
        selected_block = await self.dispatcher.dispatch(context)

        if selected_block is None:
            node_id = await self.memory.stream.add(
                topic="other", description=f"I {context['current_step']['intention']}"
            )
            return self.OutputType(
                success=True,
                evaluation=f"Successfully {context['current_step']['intention']}",
                consumed_time=random.randint(1, 30),
                node_id=node_id,
            )

        # Execute the selected sub-block and get the result
        result = await selected_block.forward(context)

        consumption_end = self.llm.prompt_tokens_used + self.llm.completion_tokens_used
        self.token_consumption += consumption_end - consumption_start

        return self.OutputType(**result)
