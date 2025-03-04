import asyncio
import logging
from typing import Optional, cast

import numpy as np
import pycityproto.city.economy.v2.economy_pb2 as economyv2

from agentsociety import InstitutionAgent, Simulator
from agentsociety.environment import EconomyClient
from agentsociety.llm.llm import LLM
from agentsociety.memory import Memory
from agentsociety.message import Messager

logger = logging.getLogger("agentsociety")


def calculate_inflation(prices):
    """
    Calculate annual inflation rates based on historical price data.

    Args:
        prices (list/np.array): A list of monthly price values

    Returns:
        list: Annual inflation rates in percentages. Returns empty list if
              insufficient data (less than 2 full years of data).

    Logic:
        1. Truncates input to full years of data (multiples of 12 months)
        2. Reshapes monthly data into yearly groups
        3. Computes average price per year
        4. Calculates year-over-year inflation rates
    """
    # Make sure the length of price data is a multiple of 12
    length = len(prices)
    months_in_year = 12
    full_years = length // months_in_year  # Calculate number of complete years

    # Remaining data not used in calculation
    prices = prices[: full_years * months_in_year]

    # Group by year, calculate average price for each year
    annual_avg_prices = np.mean(np.reshape(prices, (-1, months_in_year)), axis=1)

    # Calculate annual inflation rates
    inflation_rates = []
    for i in range(1, full_years):
        inflation_rate = (
            (annual_avg_prices[i] - annual_avg_prices[i - 1]) / annual_avg_prices[i - 1]
        ) * 100
        inflation_rates.append(inflation_rate)

    return inflation_rates


class BankAgent(InstitutionAgent):
    """
    A central banking agent that manages monetary policy in the simulation.

    Key Responsibilities:
    1. Adjusts interest rates based on inflation trends (Taylor Rule implementation)
    2. Applies interest to citizens' savings periodically
    3. Interacts with economic simulation components via EconomyClient

    Configurable Parameters:
    - time_diff: Frequency of policy updates in simulation seconds (default: 30 days)
    """

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
        Initialize the banking agent.

        Args:
            name: Unique identifier for the agent
            llm_client: Language model client for decision-making (unused in current implementation)
            simulator: Simulation time controller
            memory: Agent memory system (unused in current implementation)
            economy_client: Interface for economic data operations
            messager: Communication subsystem (unused in current implementation)
            avro_file: Data schema configuration (unused in current implementation)
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
        Check if monthly policy update should be triggered.

        Returns:
            bool: True if required time interval has passed since last update

        Note:
            Uses simulation time rather than real-world time
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
        """
        Collect messages from other agents.

        Returns:
            list: Message contents stripped of metadata
        """
        infos = await super().gather_messages(agent_ids, content)
        return [info["content"] for info in infos]

    async def forward(self):
        """
        Execute monthly policy update cycle.

        Performs two main actions:
        1. Applies interest to citizens' savings
        2. Adjusts interest rate based on inflation (Taylor Rule)
        """
        if await self.month_trigger():
            bank_id = self._agent_id
            print("bank forward")
            interest_rate, citizens = await self.economy_client.get(
                bank_id,
                ["interest_rate", "citizens"],
            )
            currencies = await self.economy_client.get(citizens, "currency")
            # update currency with interest
            for citizen, wealth in zip(citizens, currencies):
                await self.economy_client.delta_update_agents(
                    citizen, delta_currency=interest_rate * wealth
                )
            nbs_id = await self.economy_client.get_nbs_ids()
            nbs_id = nbs_id[0]
            prices = await self.economy_client.get(nbs_id, "prices")
            prices = list(prices.values())
            inflations = calculate_inflation(prices)
            natural_interest_rate = 0.01
            target_inflation = 0.02
            if len(inflations) > 0:
                # natural_unemployment_rate = 0.04
                inflation_coeff, unemployment_coeff = 0.5, 0.5
                tao = 1
                avg_inflation = np.mean(inflations[-tao:])
                interest_rate = (
                    natural_interest_rate
                    + target_inflation
                    + inflation_coeff * (avg_inflation - target_inflation)
                )
            else:
                interest_rate = natural_interest_rate + target_inflation
            await self.economy_client.update(bank_id, "interest_rate", interest_rate)
            print("bank forward end")
