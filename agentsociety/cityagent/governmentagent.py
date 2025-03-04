import asyncio
import logging
from typing import Optional

import numpy as np

from agentsociety import InstitutionAgent, Simulator
from agentsociety.environment import EconomyClient
from agentsociety.llm.llm import LLM
from agentsociety.memory import Memory
from agentsociety.message import Messager

logger = logging.getLogger("agentsociety")


class GovernmentAgent(InstitutionAgent):
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
        name: str,
        llm_client: Optional[LLM] = None,
        simulator: Optional[Simulator] = None,
        memory: Optional[Memory] = None,
        economy_client: Optional[EconomyClient] = None,
        messager: Optional[Messager] = None,  # type:ignore
        avro_file: Optional[dict] = None,
    ) -> None:
        """
        Initialize the GovernmentAgent.

        Args:
            name: Unique identifier for the agent.
            llm_client: Language model client for decision-making (optional).
            simulator: Simulation environment controller (optional).
            memory: Storage for agent state and citizen data (optional).
            economy_client: Client for economic operations like tax calculation (optional).
            messager: Communication handler for inter-agent messages (optional).
            avro_file: Schema definition for data serialization (optional).
        """
        super().__init__(
            name=name,
            llm_client=llm_client,
            simulator=simulator,
            memory=memory,
            economy_client=economy_client,
            messager=messager,
            avro_file=avro_file,
        )
        self.initailzed = False
        self.last_time_trigger = None
        self.time_diff = 30 * 24 * 60 * 60
        self.forward_times = 0

    async def month_trigger(self):
        """
        Check if the monthly tax cycle should be triggered based on elapsed time.

        Returns:
            True if the time difference since last trigger exceeds `time_diff`, False otherwise.
        """
        now_time = await self.simulator.get_time()
        if self.last_time_trigger is None:
            self.last_time_trigger = now_time
            return False
        if now_time - self.last_time_trigger >= self.time_diff:  # type:ignore
            self.last_time_trigger = now_time
            return True
        return False

    async def gather_messages(self, agent_ids, content):  # type:ignore
        """
        Collect messages from specified agents filtered by content type.

        Args:
            agent_ids: List of agent IDs to gather messages from.
            content: Message content type to filter (e.g., "forward", "income_currency").

        Returns:
            List of message contents from the specified agents.
        """
        infos = await super().gather_messages(agent_ids, content)
        return [info["content"] for info in infos]

    async def forward(self):
        """Execute the government's periodic tax collection and notification cycle."""
        if await self.month_trigger():
            citizen_ids = await self.memory.status.get("citizen_ids")
            agents_forward = await self.gather_messages(citizen_ids, "forward")
            if not np.all(np.array(agents_forward) > self.forward_times):
                return
            incomes = await self.gather_messages(citizen_ids, "income_currency")
            _, post_tax_incomes = await self.economy_client.calculate_taxes_due(
                self._agent_id, citizen_ids, incomes, enable_redistribution=False
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
