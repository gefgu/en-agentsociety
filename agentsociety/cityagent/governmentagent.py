import asyncio
import logging
from typing import Any, Optional

import numpy as np
from pydantic import Field

from ..agent import AgentParams, AgentToolbox, GovernmentAgentBase, Block
from ..environment import EconomyClient, Environment
from ..llm import LLM
from ..logger import get_logger
from ..memory import Memory
from ..message import Messager

__all__ = ["GovernmentAgent"]


class GovernmentAgentConfig(AgentParams):
    """Configuration for GovernmentAgent."""

    time_diff: int = Field(
        default=30 * 24 * 60 * 60,
        description="Time difference between each forward, day * hour * minute * second",
    )


class GovernmentAgent(GovernmentAgentBase):
    """A government institution agent that handles periodic economic operations such as tax collection."""

    ParamsType = GovernmentAgentConfig
    description: str = """
A government institution agent that handles periodic economic operations such as tax collection.
    """

    def __init__(
        self,
        id: int,
        name: str,
        toolbox: AgentToolbox,
        memory: Memory,
        agent_params: Optional[GovernmentAgentConfig] = None,
        blocks: Optional[list[Block]] = None,
    ) -> None:
        """
        Initialize the GovernmentAgent.

        Args:
            - `name` (`str`): The name or identifier of the agent.
            - `toolbox` (`AgentToolbox`): The toolbox of the agent.
            - `memory` (`Memory`): The memory of the agent.

        - **Description**:
            - Initializes the GovernmentAgent with the provided parameters and sets up necessary internal states.
        """
        super().__init__(
            id=id,
            name=name,
            toolbox=toolbox,
            memory=memory,
            agent_params=agent_params,
            blocks=blocks,
        )
        self.initailzed = False
        self.last_time_trigger = None
        self.forward_times = 0

    async def reset(self):
        """Reset the GovernmentAgent."""
        pass

    async def month_trigger(self):
        """
        Check if the monthly tax cycle should be triggered based on elapsed time.

        Returns:
            True if the time difference since last trigger exceeds `time_diff`, False otherwise.
        """
        now_tick = self.environment.get_tick()
        if self.last_time_trigger is None:
            self.last_time_trigger = now_tick
            return False
        if now_tick - self.last_time_trigger >= self.params.time_diff:
            self.last_time_trigger = now_tick
            return True
        return False

    async def forward(self):
        """Execute the government's periodic tax collection and notification cycle."""
        if await self.month_trigger():
            get_logger().debug(
                f"Agent {self.id}: Start main workflow - government forward"
            )
            # TODO: move gather_messages to simulator
            citizen_ids = await self.memory.status.get("citizen_ids")
            agents_forward = await self.gather_messages(citizen_ids, "forward")
            if not np.all(np.array(agents_forward) > self.forward_times):
                return
            incomes = await self.gather_messages(citizen_ids, "income_currency")
            _, post_tax_incomes = (
                await self.environment.economy_client.calculate_taxes_due(
                    self.id, citizen_ids, incomes, enable_redistribution=False
                )
            )
            for citizen_id, income, post_tax_income in zip(
                citizen_ids, incomes, post_tax_incomes
            ):
                tax_paid = income - post_tax_income
                await self.send_message_to_agent(
                    citizen_id, f"tax_paid@{tax_paid}", "economy"
                )
            self.forward_times += 1
            for citizen_id in citizen_ids:
                await self.send_message_to_agent(
                    citizen_id, f"government_forward@{self.forward_times}", "economy"
                )
            get_logger().debug(
                f"Agent {self.id}: Finished main workflow - government forward"
            )
