import json
import numbers
import random
from typing import Any, Optional

import json_repair
import numpy as np
from pydantic import Field

from ...agent import (
    AgentToolbox,
    Block,
    BlockParams,
    BlockDispatcher,
    DotDict,
    BlockContext,
)
from ...logger import get_logger
from ...memory import Memory
from ..sharing_params import SocietyAgentBlockOutput
from .utils import clean_json_response, prettify_document
from .utils import extract_dict_from_string

def softmax(x, gamma=1.0):
    """Compute softmax values with temperature scaling.

    Args:
        x: Input values (array or list)
        gamma: Temperature parameter (higher values make distribution sharper)

    Returns:
        Probability distribution over input values
    """
    if not isinstance(x, np.ndarray):
        x = np.array(x)
    x *= gamma
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=-1, keepdims=True)


class WorkBlock(Block):
    """Handles work-related economic activities and time tracking.

    Attributes:
        guidance_prompt: Template for time estimation queries
    """

    name = "WorkBlock"
    description = "Handles work-related economic activities and time tracking"
    NeedAgent = True

    def __init__(
        self,
        toolbox: AgentToolbox,
        agent_memory: Memory,
    ):
        """Initialize with dependencies.

        Args:
            llm: Language model for time estimation
            environment: Time tracking environment
            memory: Agent's memory system
        """
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )
        self.prompt_name = "worktime_estimate"

    async def forward(self, context: DotDict):
        """Process work task and track time expenditure.

        Workflow:
            1. Format prompt with work context
            2. Request time estimation from LLM
            3. Record work experience in memory
            4. Fallback to random time on parsing failures

        Returns:
            Execution result with time consumption details
        """
        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        required_fields = self.prompt_manager.get_required_fields(self.prompt_name)
        state_dict = await self.prompt_manager.build_agent_state(
            required_fields, context, self.memory
        )
        final_prompt = self.prompt_manager.format_prompt_to_dialog(
            self.prompt_name, state_dict
        )
        result = await self.llm.atext_request(
            final_prompt,
            response_format={"type": "json_object"},
            context={
                "block_name": self.name,
                "func_name": "forward",
                "agent_id": self.agent.id,
            },
        )
        result = clean_json_response(result)
        try:
            result: Any = json_repair.loads(result)
            time = result["time"]
            day, start_time = self.environment.get_datetime(format_time=True)
            await self.memory.status.update(
                "working_experience",
                [
                    f"Start from {start_time}, worked {time} minutes on {context['current_step']['intention']}"
                ],
                mode="merge",
            )
            work_hour_finish = await self.memory.status.get("work_hour_finish")
            work_hour_finish += float(time / 60)
            node_id = await self.memory.stream.add(
                topic="economy",
                description=f"I worked {time} minutes on {context['current_step']['intention']}",
            )
            await self.memory.status.update("work_hour_finish", work_hour_finish)
            return {
                "success": True,
                "evaluation": f'work: {context["current_step"]["intention"]}',
                "consumed_time": time,
                "node_id": node_id,
            }
        except Exception as e:
            get_logger().warning(f"Error in parsing: {str(e)}, raw: {result}")
            time = random.randint(1, 3) * 60
            day, start_time = self.environment.get_datetime(format_time=True)
            await self.memory.status.update(
                "working_experience",
                [
                    f"Start from {start_time}, worked {time} minutes on {context['current_step']['intention']}"
                ],
                mode="merge",
            )
            work_hour_finish = await self.memory.status.get("work_hour_finish")
            node_id = await self.memory.stream.add(
                topic="economy",
                description=f"I worked {time} minutes on {context['current_step']['intention']}",
            )
            work_hour_finish += float(time / 60)
            await self.memory.status.update("work_hour_finish", work_hour_finish)
            return {
                "success": True,
                "evaluation": f'work: {context["current_step"]["intention"]}',
                "consumed_time": time,
                "node_id": node_id,
            }


class ConsumptionBlock(Block):
    """Manages consumption behavior and budget constraints.

    Attributes:
        economy_client: Interface to economic simulation
        forward_times: Counter for execution attempts
    """

    name = "ConsumptionBlock"
    description = "Used to determine the consumption amount, and items"
    NeedAgent = True

    def __init__(
        self,
        toolbox: AgentToolbox,
        agent_memory: Memory,
    ):
        """Initialize consumption processor.

        Args:
            economy_client: Client for economic system interactions
        """
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )
        self.forward_times = 0

    async def forward(self, context: DotDict):
        """Execute consumption decision-making.

        Workflow:
            1. Check monthly consumption limits
            2. Calculate price-weighted demand distribution
            3. Execute transactions through economy client
            4. Record consumption in memory stream

        Returns:
            Consumption evaluation with financial details
        """
        self.forward_times += 1
        agent_id = await self.memory.status.get("id")  # agent_id
        firms_id = await self.environment.economy_client.get_firm_ids()
        intention = context["current_step"]["intention"]
        month_consumption = await self.memory.status.get("to_consumption_currency")
        consumption_currency = await self.environment.economy_client.get(
            agent_id, "consumption"
        )
        if consumption_currency >= month_consumption:
            node_id = await self.memory.stream.add(
                topic="economy",
                description="I have passed the monthly consumption limit, so I will not consume.",
            )
            return {
                "success": False,
                "evaluation": "I have passed the monthly consumption limit, so I will not consume.",
                "consumed_time": 0,
                "node_id": node_id,
            }
        consumption = min(
            month_consumption / 1, month_consumption - consumption_currency
        )
        prices = await self.environment.economy_client.get(firms_id, "price")
        consumption_each_firm = consumption * softmax(prices, gamma=-0.01)
        demand_each_firm = []
        for i in range(len(firms_id)):
            demand_each_firm.append(int(consumption_each_firm[i] // prices[i]))
        real_consumption = await self.environment.economy_client.calculate_consumption(
            firms_id, agent_id, demand_each_firm
        )
        node_id = await self.memory.stream.add(
            topic="economy",
            description=f"I bought some goods, and spent {real_consumption:.1f} on {intention}",
        )
        evaluation = {
            "success": True,
            "evaluation": f"I bought some goods, and spent {real_consumption:.1f} on {intention}",
            "consumed_time": 20,
            "node_id": node_id,
        }
        return evaluation

class EconomyNoneBlock(Block):
    """
    Fallback block for non-economic/non-specified activities.
    """

    name = "EconomyNoneBlock"
    description = "Fallback block for other activities"

    def __init__(self, toolbox: AgentToolbox, agent_memory: Memory):
        super().__init__(toolbox=toolbox, agent_memory=agent_memory)

    async def forward(self, context: DotDict):
        """Log generic activities in economy stream."""
        node_id = await self.memory.stream.add(
            topic="economy", description=f"I {context['current_step']['intention']}"
        )
        return {
            "success": True,
            "evaluation": f'Finished{context["current_step"]["intention"]}',
            "consumed_time": 0,
            "node_id": node_id,
        }

class EconomyBlockParams(BlockParams):
    UBI: float = Field(default=0, description="Universal Basic Income")
    num_labor_hours: int = Field(
        default=168, description="Number of labor hours per month"
    )
    productivity_per_labor: float = Field(
        default=1, description="Productivity per labor hour"
    )
    time_diff: int = Field(
        default=30 * 24 * 60 * 60, description="Time difference between two triggers"
    )


class EconomyBlockContext(BlockContext): ...


class EconomyBlock(Block):
    """Orchestrates economic activities through specialized sub-blocks.

    Attributes:
        dispatcher: Routes tasks to appropriate sub-blocks
        work_block: Work activity handler
        consumption_block: Consumption manager
        none_block: Fallback activities
    """

    ParamsType = EconomyBlockParams
    OutputType = SocietyAgentBlockOutput
    ContextType = EconomyBlockContext
    NeedAgent = True
    name = "EconomyBlock"
    description = "Work, shopping, consume, and other economic activities."
    actions = {
        "work": "Support the work action",
        "consume": "Support the consume action",
        "economy_none": "Support other economic operations",
    }

    def __init__(
        self,
        toolbox: AgentToolbox,
        agent_memory: Memory,
        block_params: Optional[EconomyBlockParams] = None,
    ):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
            block_params=block_params,
        )
        self.month_plan_block = MonthEconomyPlanBlock(
            toolbox=toolbox,
            agent_memory=agent_memory,
            ubi=self.params.UBI,
            num_labor_hours=self.params.num_labor_hours,
            productivity_per_labor=self.params.productivity_per_labor,
            time_diff=self.params.time_diff,
        )
        self.work_block = WorkBlock(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )
        self.consumption_block = ConsumptionBlock(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )
        self.none_block = EconomyNoneBlock(toolbox=toolbox, agent_memory=agent_memory)
        self.trigger_time = 0
        self.token_consumption = 0
        self.dispatcher = BlockDispatcher(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )
        self.dispatcher.register_blocks(
            [self.work_block, self.consumption_block, self.none_block]
        )

    def set_agent(self, agent: Any):
        super().set_agent(agent)
        self.month_plan_block.set_agent(agent)
        self.work_block.set_agent(agent)
        self.consumption_block.set_agent(agent)
        self.none_block.set_agent(agent)

    async def before_forward(self):
        try:
            await self.month_plan_block.forward()
        except Exception as e:
            get_logger().warning(f"EconomyBlock MonthPlanBlock: {e}")
            pass

    async def forward(self, agent_context: DotDict) -> SocietyAgentBlockOutput:
        """Coordinate economic activity execution.

        Workflow:
            1. Use dispatcher to select appropriate handler
            2. Delegate execution to selected block
        """
        try:
            self.trigger_time += 1
            context = agent_context | self.context
            intention = context["current_step"]["intention"]
            selected_block = await self.dispatcher.dispatch(context)
            if selected_block is None:
                return self.OutputType(
                    success=False,
                    evaluation=f"Failed to {intention}",
                    consumed_time=0,
                    node_id=None,
                )
            result = await selected_block.forward(context)
            return self.OutputType(**result)
        except Exception as e:
            get_logger().error(f"EconomyBlock: Error in forward: {e}")
            return self.OutputType(
                success=False,
                evaluation="Failed to forward",
                consumed_time=0,
                node_id=None,
            )

class MonthEconomyPlanBlock(Block):
    """Manages monthly economic planning and mental health assessment.

    Attributes:
        configurable_fields: Economic policy parameters
        economy_client: Interface to economic system
        llm_error: Counter for LLM failures
    """

    name = "MonthEconomyPlanBlock"
    description = "Handles monthly economic planning and mental health assessment"

    def __init__(
        self,
        toolbox: AgentToolbox,
        agent_memory: Memory,
        ubi: float = 0,
        num_labor_hours: int = 168,
        productivity_per_labor: float = 1,
        time_diff: int = 30 * 24 * 60 * 60,
    ):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )
        self.llm_error = 0
        self.last_time_trigger = None
        self.forward_times = 0
        self.ubi = ubi
        self.num_labor_hours = num_labor_hours
        self.productivity_per_labor = productivity_per_labor
        self.time_diff = time_diff
        self.month_plan_prompt_name = "month_plan_observation"
        self.mental_health_prompt_name = "month_plan_mental_health_assessment"
        self.goal_creation_prompt_name = "month_plan_goal_creation"

    async def month_trigger(self):
        """Check if monthly planning cycle should activate."""
        now_tick = self.environment.get_tick()
        if (
            self.last_time_trigger is None
            or now_tick - self.last_time_trigger >= self.time_diff
        ):
            self.last_time_trigger = now_tick
            return True
        return False

    def _format_prompt(self, prompt_name: str, state_dict: dict[str, Any]) -> str:
        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")
        return prettify_document(self.prompt_manager.format_prompt(prompt_name, state_dict))
    
    def _get_number_of_contacts_in_last_7_days(self) -> int:
        # TODO: IMPLEMENT
        return 0

    async def forward(self):
        """Execute monthly planning workflow.

        Workflow:
            1. Collect economic indicators
            2. Generate LLM prompts for work/consumption propensity
            3. Update agent's economic status
            4. Periodically conduct mental health assessments
            5. Handle UBI policy evaluations
        """
        if await self.month_trigger():
            agent_id = await self.memory.status.get("id")
            firms_id = await self.environment.economy_client.get_firm_ids()
            firm_id = await self.memory.status.get("firm_id")
            bank_id = await self.environment.economy_client.get_bank_ids()
            bank_id = bank_id[0]
            skill, consumption, wealth = await self.environment.economy_client.get(
                agent_id, ["skill", "consumption", "currency"]
            )
            get_logger().debug(f"type of skill: {type(skill)}, value: {skill}")
            if self.prompt_manager is None:
                raise RuntimeError("PromptManager is not initialized")

            obs_required_fields = self.prompt_manager.get_required_fields(
                self.month_plan_prompt_name
            )
            obs_context: dict[str, Any] = {
                "skill": f"{skill:.2f}",
                "wealth": f"{wealth:.2f}",
            }

            if "consumption_summary" in obs_required_fields:
                consumption_propensity = await self.memory.status.get(
                    "consumption_propensity"
                )
                if (consumption <= 0) and (consumption_propensity > 0):
                    obs_context["consumption_summary"] = (
                        "Besides, you had no consumption due to shortage of goods."
                    )
                else:
                    obs_context["consumption_summary"] = (
                        f"Besides, your consumption was ${consumption:.2f}."
                    )

            if "tax_summary" in obs_required_fields:
                tax_paid = await self.memory.status.get("tax_paid")
                tax_summary = (
                    f"Your tax deduction amounted to ${tax_paid:.2f}, and the government "
                    "uses the tax revenue to provide social services to all citizens."
                )
                if self.ubi and self.forward_times >= 96:
                    tax_summary = (
                        f"{tax_summary} Specifically, the government directly provides "
                        f"${self.ubi} per capita in each month."
                    )
                obs_context["tax_summary"] = tax_summary

            if "price" in obs_required_fields:
                prices = await self.environment.economy_client.get(firms_id, "price")
                obs_context["price"] = f"{np.mean(prices):.2f}"

            if "interest_rate_pct" in obs_required_fields:
                interest_rate = await self.environment.economy_client.get(
                    bank_id, "interest_rate"
                )
                obs_context["interest_rate_pct"] = f"{interest_rate*100:.2f}"

            obs_state = await self.prompt_manager.build_agent_state(
                obs_required_fields, obs_context, self.memory
            )
            obs_prompt = self._format_prompt(self.month_plan_prompt_name, obs_state)
            try:
                await self.memory.status.update(
                    "dialog_queue",
                    [{"role": "user", "content": obs_prompt}],
                    mode="merge",
                )
                dialog_queue = await self.memory.status.get("dialog_queue")
                content = await self.llm.atext_request(
                    list(dialog_queue),
                    timeout=300,
                    context={
                        "block_name": self.name,
                        "func_name": "forward",
                        "agent_id": agent_id,
                    },
                )
                await self.memory.status.update(
                    "dialog_queue",
                    [{"role": "assistant", "content": content}],
                    mode="merge",
                )
                propensity_dict = extract_dict_from_string(content)[0]
                work_propensity, consumption_propensity = (
                    propensity_dict["work"],
                    propensity_dict["consumption"],
                )
                if isinstance(work_propensity, numbers.Number) and isinstance(
                    consumption_propensity, numbers.Number
                ):
                    await self.memory.status.update("work_propensity", work_propensity)
                    await self.memory.status.update(
                        "consumption_propensity", consumption_propensity
                    )
                else:
                    self.llm_error += 1
            except Exception:
                self.llm_error += 1

            work_skill = await self.environment.economy_client.get(agent_id, "skill")
            work_propensity = await self.memory.status.get("work_propensity")
            consumption_propensity = await self.memory.status.get(
                "consumption_propensity"
            )
            work_hours = work_propensity * self.num_labor_hours
            # income = await self.economy_client.get(agent_id, 'income')
            income = work_hours * work_skill

            wealth = await self.environment.economy_client.get(agent_id, "currency")
            wealth += work_hours * work_skill
            await self.environment.economy_client.update(agent_id, "currency", wealth)
            await self.environment.economy_client.delta_update_firms(
                firm_id, delta_inventory=int(work_hours * self.productivity_per_labor)
            )

            if self.ubi and self.forward_times >= 96:
                income += self.ubi
                wealth += self.ubi

            await self.memory.status.update(
                "to_consumption_currency", consumption_propensity * wealth
            )

            await self.environment.economy_client.update(agent_id, "consumption", 0)
            await self.environment.economy_client.update(agent_id, "income", income)
            await self.environment.economy_client.update(agent_id, "currency", wealth)

            if self.forward_times % 3 == 0:
                mental_required_fields = self.prompt_manager.get_required_fields(
                    self.mental_health_prompt_name
                )
                mental_context = dict(obs_context)
                mental_context["wealth"] = f"{wealth:.2f}"
                mental_state = await self.prompt_manager.build_agent_state(
                    mental_required_fields, mental_context, self.memory
                )
                obs_prompt = self._format_prompt(
                    self.mental_health_prompt_name, mental_state
                )
                content = await self.llm.atext_request(
                    [{"role": "user", "content": obs_prompt}],
                    timeout=300,
                    context={
                        "block_name": self.name,
                        "func_name": "forward",
                        "agent_id": agent_id,
                    },
                )
                inverse_score_items = [3, 8, 12, 16]
                category2score = {"rarely": 0, "some": 1, "occasionally": 2, "most": 3}
                try:
                    content = extract_dict_from_string(content)[0]
                    for k in content:
                        if k in inverse_score_items:
                            content[k] = 3 - category2score[content[k].lower()]
                        else:
                            content[k] = category2score[content[k].lower()]
                    depression = sum(list(content.values()))
                    await self.memory.status.update("depression", depression)
                except Exception:
                    self.llm_error += 1

            # Goal Creation
            goals_required_fields = self.prompt_manager.get_required_fields(
                self.goal_creation_prompt_name
            )
            goals_context: dict[str, Any] = {
                "income": f"{income:.2f}",
                "consumption": f"{consumption:.2f}",
                "wealth": f"{wealth:.2f}",
            }

            if "financial_stress" in goals_required_fields:
                financial_stress = income < (0.9 * consumption)
                goals_context["financial_stress"] = (
                    "Yes" if financial_stress else "No"
                )

            if "need_fulfillment" in goals_required_fields:
                need_fulfillment = await self.memory.status.get(
                    "mean_need_fulfillment", 0.5
                )
                goals_context["need_fulfillment"] = f"{need_fulfillment:.2f}"

            if "social_isolation" in goals_required_fields:
                social_isolation = (
                    self._get_number_of_contacts_in_last_7_days()
                ) < 3
                goals_context["social_isolation"] = (
                    "Yes" if social_isolation else "No"
                )

            if "interest" in goals_required_fields:
                interest = await self.memory.spatial.get_interest()
                goals_context["interest"] = f"{interest:.2f}"

            if "major_events_memories" in goals_required_fields:
                major_events_memories = await self.memory.stream.search(
                    query="major_event", top_k=5
                )
                goals_context["major_events_memories"] = str(major_events_memories)

            goals_state = await self.prompt_manager.build_agent_state(
                goals_required_fields, goals_context, self.memory
            )
            GOALS_PROMPT = self._format_prompt(
                self.goal_creation_prompt_name, goals_state
            )
            content = await self.llm.atext_request(
                [{"role": "user", "content": GOALS_PROMPT}],
                timeout=300,
                context={
                    "block_name": self.name,
                    "func_name": "forward_goal_creation",
                    "agent_id": agent_id,
                },
            )

            try:
                goals = json_repair.loads(content)
            except Exception as e:
                get_logger().warning(
                    f"Error in parsing goals: {str(e)}, raw: {content}"
                )
                goals = []

            await self.memory.status.update("goals", goals)

            self.forward_times += 1
