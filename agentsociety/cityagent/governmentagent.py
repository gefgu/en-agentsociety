import asyncio
import logging
from typing import Any

import numpy as np

from ..agent import AgentToolbox, GovernmentAgentBase
from ..environment import EconomyClient, Environment
from ..llm import LLM
from ..logger import get_logger
from ..memory import Memory
from ..message import Messager

__all__ = ["GovernmentAgent"]


class GovernmentAgent(GovernmentAgentBase):
    """A government institution agent that handles periodic economic operations such as tax collection."""

    configurable_fields = ["time_diff"]
    default_values = {
        "time_diff": 30 * 24 * 60 * 60,
    }
    fields_description = {
        "time_diff": "Time difference between each forward, day * hour * minute * second",
    }

    def __init__(
        self,
        id: int,
        name: str,
        toolbox: AgentToolbox,
        memory: Memory,
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
        )
        self.initailzed = False
        self.last_time_trigger = None
        self.time_diff = 30 * 24 * 60 * 60
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
        if now_tick - self.last_time_trigger >= self.time_diff:
            self.last_time_trigger = now_tick
            return True
        return False

    async def gather_messages(self, agent_ids: list[int], target: str) -> list[Any]:
        """
        Collect messages from specified agents filtered by content type.

        Args:
            agent_ids: List of agent IDs to gather messages from.
            target: Message content type to filter (e.g., "forward", "income_currency").

        Returns:
            List of message contents from the specified agents.
        """
        infos = await super().gather_messages(agent_ids, target)
        return [info["content"] for info in infos]

    async def forward(self):
        """Execute the government's periodic tax collection and notification cycle."""
        if await self.month_trigger():
            get_logger().debug(
                f"Agent {self.id}: Start main workflow - government forward"
            )
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
