import logging
from typing import Optional, cast

import numpy as np

from agentsociety import InstitutionAgent, Simulator
from agentsociety.environment import EconomyClient
from agentsociety.llm import LLM
from agentsociety.memory import Memory
from agentsociety.message import Messager

logger = logging.getLogger("agentsociety")


class FirmAgent(InstitutionAgent):
    """Agent representing a firm in an economic simulation.

    Manages economic activities including price adjustments, wage policies,
    inventory control, and employee skill development.
    Inherits from InstitutionAgent and extends its economic behaviors.
    """

    configurable_fields = ["time_diff", "max_price_inflation", "max_wage_inflation"]
    default_values = {
        "time_diff": 30 * 24 * 60 * 60,
        "max_price_inflation": 0.05,
        "max_wage_inflation": 0.05,
    }
    fields_description = {
        "time_diff": "Time difference between each forward, day * hour * minute * second",
        "max_price_inflation": "Maximum price inflation rate",
        "max_wage_inflation": "Maximum wage inflation rate",
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
        """Initialize a FirmAgent with essential components for economic simulation.

        Args:
            name: Unique identifier for the agent
            llm_client: Language model client for decision-making (optional)
            simulator: Simulation controller (optional)
            memory: Agent's memory system (optional)
            economy_client: Client for economic data operations (optional)
            messager: Communication handler (optional)
            avro_file: Configuration file in Avro format (optional)
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
        self.forward_times = 0
        self.time_diff = 30 * 24 * 60 * 60
        self.max_price_inflation = 0.05
        self.max_wage_inflation = 0.05

    async def month_trigger(self):
        """Check if monthly adjustment should be triggered.

        Compares current simulation time with last trigger time.
        Returns:
            True if time_diff has passed since last trigger, False otherwise
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
        """Collect messages from specified agents.

        Args:
            agent_ids: List of agent identifiers to gather from
            content: Message content template
        Returns:
            List of message contents from target agents
        """
        infos = await super().gather_messages(agent_ids, content)
        return [info["content"] for info in infos]

    async def forward(self):
        """Execute monthly economic adjustments.

        Performs:
        - Employee skill adjustments based on market conditions
        - Price adjustments based on inventory/demand balance
        - Economic metrics reset (demand/sales tracking)
        """
        if await self.month_trigger():
            firm_id = self._agent_id
            print("firm forward")
            employees, total_demand, goods_consumption, inventory, skills, price = (
                await self.economy_client.get(
                    firm_id,
                    ["employees", "demand", "sales", "inventory", "skill", "price"],
                )
            )
            last_inventory = goods_consumption + inventory
            max_change_rate = (total_demand - last_inventory) / (
                max(total_demand, last_inventory) + 1e-8
            )
            skills = np.array(skills)
            skill_change_ratio = np.random.uniform(
                0, max_change_rate * self.max_wage_inflation
            )
            await self.economy_client.update(
                employees,
                "skill",
                list(np.maximum(skills * (1 + skill_change_ratio), 1)),
            )
            await self.economy_client.update(
                firm_id,
                "price",
                max(
                    price
                    * (
                        1
                        + np.random.uniform(
                            0, max_change_rate * self.max_price_inflation
                        )
                    ),
                    1,
                ),
            )
            await self.economy_client.update(firm_id, "demand", 0)
            await self.economy_client.update(firm_id, "sales", 0)
            print("firm forward end")
