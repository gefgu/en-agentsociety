import asyncio
import logging
from typing import Optional, cast

import numpy as np
import pycityproto.city.economy.v2.economy_pb2 as economyv2

from agentsociety import InstitutionAgent, Simulator
from agentsociety.environment import EconomyClient
from agentsociety.llm import LLM
from agentsociety.memory import Memory
from agentsociety.message import Messager

logger = logging.getLogger("agentsociety")


class NBSAgent(InstitutionAgent):
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
        name: str,
        llm_client: Optional[LLM] = None,
        simulator: Optional[Simulator] = None,
        memory: Optional[Memory] = None,
        economy_client: Optional[EconomyClient] = None,
        messager: Optional[Messager] = None,  # type:ignore
        avro_file: Optional[dict] = None,
    ) -> None:
        """Initialize NBSAgent with dependencies and configuration.
        
        Args:
            name: Unique identifier for the agent
            llm_client: Language model client for decision-making (optional)
            simulator: Time management and simulation control
            memory: Persistent storage for agent state and historical data
            economy_client: Client to interact with economic simulation services
            messager: Communication interface with other agents
            avro_file: Schema configuration for data serialization (optional)
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
        self.num_labor_hours = 168
        self.productivity_per_labor = 1
        self.price = 1

    async def month_trigger(self):
        """Check if a monthly cycle should be triggered based on simulation time.
        
        Returns:
            True if monthly interval has passed since last trigger, False otherwise
        """
        now_time = await self.simulator.get_time()
        now_time = cast(int, now_time)
        if self.last_time_trigger is None:
            self.last_time_trigger = now_time
            return False
        if now_time - self.last_time_trigger >= self.time_diff:
            self.last_time_trigger = now_time
            return True
        return False

    async def gather_messages(self, agent_ids, content):  # type:ignore
        """Collect messages from specified agents and extract content.
        
        Args:
            agent_ids: List of agent identifiers to query
            content: Message content field to retrieve
            
        Returns:
            List of message contents from target agents
        """
        infos = await super().gather_messages(agent_ids, content)
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
            print("nbs forward")
            t_now = str(await self.simulator.get_time())
            nbs_id = self._agent_id
            await self.economy_client.calculate_real_gdp(nbs_id)
            citizens_ids = await self.memory.status.get("citizen_ids")
            work_propensity = await self.gather_messages(
                citizens_ids, "work_propensity"
            )
            if sum(work_propensity) == 0.0:
                working_hours = 0.0
            else:
                working_hours = np.mean(work_propensity) * self.num_labor_hours
            await self.economy_client.update(
                nbs_id, "working_hours", {t_now: working_hours}, mode="merge"
            )
            firms_id = await self.economy_client.get_firm_ids()
            prices = await self.economy_client.get(firms_id, "price")

            await self.economy_client.update(
                nbs_id, "prices", {t_now: float(np.mean(prices))}, mode="merge"
            )
            depression = await self.gather_messages(citizens_ids, "depression")
            if sum(depression) == 0.0:
                depression = 0.0
            else:
                depression = np.mean(depression)
            await self.economy_client.update(
                nbs_id, "depression", {t_now: depression}, mode="merge"
            )
            consumption_currency = await self.economy_client.get(
                citizens_ids, "consumption"
            )
            if sum(consumption_currency) == 0.0:
                consumption_currency = 0.0
            else:
                consumption_currency = np.mean(consumption_currency)
            await self.economy_client.update(
                nbs_id,
                "consumption_currency",
                {t_now: consumption_currency},
                mode="merge",
            )
            income_currency = await self.economy_client.get(citizens_ids, "income")
            if sum(income_currency) == 0.0:
                income_currency = 0.0
            else:
                income_currency = np.mean(income_currency)
            await self.economy_client.update(
                nbs_id, "income_currency", {t_now: income_currency}, mode="merge"
            )
            print("nbs forward end")
            self.forward_times += 1
            await self.memory.status.update("forward_times", self.forward_times)
