from typing import Any

import numpy as np

from ..agent import AgentToolbox, NBSAgentBase
from ..logger import get_logger
from ..memory import Memory

__all__ = ["NBSAgent"]


class NBSAgent(NBSAgentBase):
    """National Bureau of Statistics Agent simulating economic data collection and analysis.

    Inherits from InstitutionAgent to manage economic indicators and interactions with other
    agents in a simulated environment. Handles monthly economic metrics calculations including
    GDP, labor statistics, prices, and citizen welfare indicators.
    """

    configurable_fields = ["time_diff", "num_labor_hours", "productivity_per_labor"]
    default_values = {
        "time_diff": 30 * 24 * 60 * 60,
        "num_labor_hours": 168,
        "productivity_per_labor": 1,
    }
    fields_description = {
        "time_diff": "Time difference between each forward, day * hour * minute * second",
        "num_labor_hours": "Number of labor hours per week",
        "productivity_per_labor": "Productivity per labor hour",
    }

    def __init__(
        self,
        id: int,
        name: str,
        toolbox: AgentToolbox,
        memory: Memory,
    ) -> None:
        """Initialize NBSAgent with dependencies and configuration.

        - **Args**:
            - `name` (`str`): The name or identifier of the agent.
            - `toolbox` (`AgentToolbox`): The toolbox of the agent.
            - `memory` (`Memory`): The memory of the agent.

        - **Description**:
            - Initializes the NBSAgent with the provided parameters and sets up necessary internal states.
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
        self.num_labor_hours = 168
        self.productivity_per_labor = 1
        self.price = 1

    async def reset(self):
        """Reset the NBSAgent."""
        pass

    async def month_trigger(self):
        """Check if a monthly cycle should be triggered based on simulation time.

        Returns:
            True if monthly interval has passed since last trigger, False otherwise
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
        """Collect messages from specified agents and extract content.

        Args:
            agent_ids: List of agent identifiers to query
            target: Message content field to retrieve

        Returns:
            List of message contents from target agents
        """
        infos = await super().gather_messages(agent_ids, target)
        return [info["content"] for info in infos]

    async def forward(self):
        """Execute monthly economic data collection and update cycle.

        Performs:
        1. Real GDP calculation
        2. Labor statistics aggregation
        3. Price level monitoring
        4. Citizen welfare metrics collection
        5. Economic indicator updates
        """
        if await self.month_trigger():
            # TODO: fix bug here, what is the t_now ??
            get_logger().debug(f"Agent {self.id}: Start main workflow - nbs forward")
            t_now = str(self.environment.get_tick())
            nbs_id = self.id
            await self.environment.economy_client.calculate_real_gdp(nbs_id)
            citizens_ids = await self.memory.status.get("citizen_ids")
            work_propensity = await self.gather_messages(
                citizens_ids, "work_propensity"
            )
            if sum(work_propensity) == 0.0:
                working_hours = 0.0
            else:
                working_hours = np.mean(work_propensity) * self.num_labor_hours
            await self.environment.economy_client.update(
                nbs_id, "working_hours", {t_now: working_hours}, mode="merge"
            )
            firms_id = await self.environment.economy_client.get_firm_ids()
            prices = await self.environment.economy_client.get(firms_id, "price")

            await self.environment.economy_client.update(
                nbs_id, "prices", {t_now: float(np.mean(prices))}, mode="merge"
            )
            depression = await self.gather_messages(citizens_ids, "depression")
            if sum(depression) == 0.0:
                depression = 0.0
            else:
                depression = np.mean(depression)
            await self.environment.economy_client.update(
                nbs_id, "depression", {t_now: depression}, mode="merge"
            )
            consumption_currency = await self.environment.economy_client.get(
                citizens_ids, "consumption"
            )
            if sum(consumption_currency) == 0.0:
                consumption_currency = 0.0
            else:
                consumption_currency = np.mean(consumption_currency)
            await self.environment.economy_client.update(
                nbs_id,
                "consumption_currency",
                {t_now: consumption_currency},
                mode="merge",
            )
            income_currency = await self.environment.economy_client.get(
                citizens_ids, "income"
            )
            if sum(income_currency) == 0.0:
                income_currency = 0.0
            else:
                income_currency = np.mean(income_currency)
            await self.environment.economy_client.update(
                nbs_id, "income_currency", {t_now: income_currency}, mode="merge"
            )
            get_logger().debug(f"Agent {self.id}: Finished main workflow - nbs forward")
            self.forward_times += 1
            await self.memory.status.update("forward_times", self.forward_times)
