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
    FormatPrompt,
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

WORKTIME_ESTIMATE_PROMPT = """As an intelligent agent's time estimation system, please estimate the time needed to complete the current action based on the overall plan and current intention.

Overall plan:
${context.plan_context["plan"]}

Current action: ${context.current_step["intention"]}

Current emotion: ${status.emotion_types}

Household type: {household}
Life stage: {life_stage}
Hobbies: {hobbies}
Goals: {goals}

Big Five Personality Traits (1=Low, 2=Medium, 3=High):
- Openness: {openness}
- Conscientiousness: {conscientiousness}
- Extraversion: {extraversion}
- Agreeableness: {agreeableness}
- Neuroticism: {neuroticism}

Behavioral Preferences:
- Work Ethic: {work_ethic} (0.0=Low work priority/minimal hours, 1.0=High work priority/tends to work overtime)

Examples:
- "Learn programming": {{"time": 120}}
- "Watch a movie": {{"time": 150}} 
- "Play mobile games": {{"time": 60}}
- "Read a book": {{"time": 90}}
- "Exercise": {{"time": 45}}

Please return the result in JSON format (Do not return any other text), the time unit is [minute], example:
{{
    "time": 10
}}
"""


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
        worktime_estimation_prompt: str = WORKTIME_ESTIMATE_PROMPT,
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
        self.guidance_prompt = FormatPrompt(
            template=worktime_estimation_prompt,
            memory=agent_memory,
        )

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
        # Get Big Five personality traits
        big5 = await self.memory.status.get("big5", {})

        # Get household and life stage
        household = await self.memory.status.get("household", "unknown")
        life_stage = await self.memory.status.get("life_stage", "unknown")
        hobbies = await self.memory.status.get("hobbies", [])
        hobbies_str = ", ".join(hobbies) if isinstance(hobbies, list) else str(hobbies)
        goals = await self.memory.status.get("goals", [])
        goals_str = ", ".join(goals) if isinstance(goals, list) else str(goals)

        # Get preferences
        preferences = await self.memory.status.get("preferences", {})
        work_ethic = preferences.get("work_ethic", 0.5)

        await self.guidance_prompt.format(
            context=context,
            household=household,
            life_stage=life_stage,
            hobbies=hobbies_str,
            goals=goals_str,
            work_ethic=work_ethic,
            openness=big5.get("openness", 2),
            conscientiousness=big5.get("conscientiousness", 2),
            extraversion=big5.get("extraversion", 2),
            agreeableness=big5.get("agreeableness", 2),
            neuroticism=big5.get("neuroticism", 2),
        )
        result = await self.llm.atext_request(
            self.guidance_prompt.to_dialog(),
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
    worktime_estimation_prompt: str = Field(
        default=WORKTIME_ESTIMATE_PROMPT, description="Used to determine the worktime"
    )
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
            worktime_estimation_prompt=self.params.worktime_estimation_prompt,
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
            name = await self.memory.status.get("name")
            age = await self.memory.status.get("age")
            city = await self.memory.status.get("city")
            job = await self.memory.status.get("occupation")
            skill, consumption, wealth = await self.environment.economy_client.get(
                agent_id, ["skill", "consumption", "currency"]
            )
            get_logger().debug(f"type of skill: {type(skill)}, value: {skill}")
            tax_paid = await self.memory.status.get("tax_paid")
            prices = await self.environment.economy_client.get(firms_id, "price")
            price = np.mean(prices)
            interest_rate = await self.environment.economy_client.get(
                bank_id, "interest_rate"
            )

            problem_prompt = f"""
                    You're {name}, a {age}-year-old individual living in {city}. As with all Americans, a portion of your monthly income is taxed by the federal government. This taxation system is tiered, income is taxed cumulatively within defined brackets, combined with a redistributive policy: after collection, the government evenly redistributes the tax revenue back to all citizens, irrespective of their earnings.
                """
            job_prompt = f"""
                        In the previous month, you worked as a(an) {job}. If you continue working this month, your expected hourly income will be ${skill:.2f}.
                    """
            consumption_propensity = await self.memory.status.get(
                "consumption_propensity"
            )
            if (consumption <= 0) and (consumption_propensity > 0):
                consumption_prompt = """
                            Besides, you had no consumption due to shortage of goods.
                        """
            else:
                consumption_prompt = f"""
                            Besides, your consumption was ${consumption:.2f}.
                        """
            tax_prompt = f"""Your tax deduction amounted to ${tax_paid:.2f}, and the government uses the tax revenue to provide social services to all citizens."""
            if self.ubi and self.forward_times >= 96:
                tax_prompt = f"{tax_prompt} Specifically, the government directly provides ${self.ubi} per capita in each month."
            price_prompt = f"""Meanwhile, in the consumption market, the average price of essential goods is now at ${price:.2f}."""
            job_prompt = prettify_document(job_prompt)

            big5 = await self.memory.status.get("big5", {})
            personality_prompt = f"""Your personality traits are as follows: openness {big5.get("openness", 2)}, conscientiousness {big5.get("conscientiousness", 2)}, extraversion {big5.get("extraversion", 2)}, agreeableness {big5.get("agreeableness", 2)}, and neuroticism {big5.get("neuroticism", 2)}. Your household type is {await self.memory.status.get("household", "unknown")} and your life stage is {await self.memory.status.get("life_stage", "unknown")}."""

            obs_prompt = f"""
                            {problem_prompt} {job_prompt} {consumption_prompt} {tax_prompt} {price_prompt} {personality_prompt}
                            Your current savings account balance is ${wealth:.2f}. Interest rates, as set by your bank, stand at {interest_rate*100:.2f}%. 
                            Your goal is to maximize your utility by deciding how much to work and how much to consume. Your utility is determined by your consumption, income, saving, social service recieved and leisure time. You will spend the time you do not work on leisure activities. 
                            With all these factors in play, and considering aspects like your living costs, any future aspirations, and the broader economic trends, how is your willingness to work this month? Furthermore, how would you plan your expenditures on essential goods, keeping in mind good price?
                            Please share your decisions in a JSON format as follows:
                            {{'work': a value between 0 and 1, indicating the propensity to work,
                            'consumption': a value between 0 and 1, indicating the proportion of all your savings and income you intend to spend on essential goods
                            }}
                            Any other output words are NOT allowed.
                        """
            obs_prompt = prettify_document(obs_prompt)
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
                obs_prompt = f"""
                                {problem_prompt} {job_prompt} {consumption_prompt} {tax_prompt} {price_prompt} {personality_prompt}
                                Your current savings account balance is ${wealth:.2f}. Interest rates, as set by your bank, stand at {interest_rate*100:.2f}%. 
                                Please fill in the following questionnaire:
                                Indicate how often you have felt this way during the last week by choosing one of the following options:
                                "Rarely" means Rarely or none of the time (less than 1 day),
                                "Some" means Some or a little of the time (1-2 days),
                                "Occasionally" means Occasionally or a moderate amount of the time (3-4 days),
                                "Most" means Most or all of the time (5-7 days).
                                Statement 1: I was bothered by things that usually don't bother me.  
                                Statement 2: I did not feel like eating; my appetite was poor.
                                Statement 3: I felt that I could not shake off the blues even with help from my family or friends.
                                Statement 4: I felt that I was just as good as other people.
                                Statement 5: I had trouble keeping my mind on what I was doing.
                                Statement 6: I felt depressed.
                                Statement 7: I felt that everything I did was an effort.
                                Statement 8: I felt hopeful about the future.
                                Statement 9: I thought my life had been a failure.
                                Statement 10: I felt fearful.
                                Statement 11: My sleep was restless.
                                Statement 12: I was happy.
                                Statement 13: I talked less than usual.
                                Statement 14: I felt lonely.
                                Statement 15: People were unfriendly.
                                Statement 16: I enjoyed life.
                                Statement 17: I had crying spells.
                                Statement 18: I felt sad.
                                Statement 19: I felt that people disliked me.
                                Statement 20: I could not get "going".
                                Please response with json format with keys being numbers 1-20 and values being one of "Rarely", "Some", "Occasionally", "Most".
                                Any other output words are NOT allowed.
                            """
                obs_prompt = prettify_document(obs_prompt)
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

            if self.ubi and self.forward_times >= 96 and self.forward_times % 12 == 0:
                obs_prompt = f"""
                                {problem_prompt} {job_prompt} {consumption_prompt} {tax_prompt} {price_prompt}
                                Your current savings account balance is ${wealth:.2f}. Interest rates, as set by your bank, stand at {interest_rate*100:.2f}%. 
                                What's your opinion on the UBI policy, including the advantages and disadvantages?
                            """
                obs_prompt = prettify_document(obs_prompt)
                content = await self.llm.atext_request(
                    [{"role": "user", "content": obs_prompt}],
                    timeout=300,
                    context={
                        "block_name": self.name,
                        "func_name": "forward",
                        "agent_id": agent_id,
                    },
                )
                await self.memory.status.update("ubi_opinion", [content], mode="merge")

            # Goal Creation
            financial_stress = income < (0.9 * consumption)
            need_fulfillment = await self.memory.status.get(
                "mean_need_fulfillment", 0.5
            )

            social_isolation = (
                await self.agent.blocks[1].get_number_of_contacts_in_last_7_days()
            ) < 3 # Block 1 is the social block
            interest = await self.memory.spatial.get_interest()
            major_events_memories = await self.memory.stream.search(
                query="major_event", top_k=5
            )

            GOALS_PROMPT = f"""
                Given the following economic and social context, please create 3 to 5 goals that I can achieve in the next month. These goals should be specific, measurable, achievable, relevant, and time-bound (SMART). 

                Economic Context:
                - Income: ${income:.2f} per month
                - Consumption: ${consumption:.2f} per month
                - Wealth: ${wealth:.2f}
                - Financial Stress: {"Yes" if financial_stress else "No"}
                - Need Fulfillment: {need_fulfillment:.2f} (0 to 1 scale)
                - Social Isolation: {"Yes" if social_isolation else "No"}
                - Interest in New Experiences: {interest:.2f} (0 to 1 scale)

                Recent Major Events:
                {major_events_memories}

                Please generate goals that can help improve my economic situation, mental well-being, and social connections based on the above context.
                Return a JSON array of goal, with just the goal description, without any other text. For example:
                [
                    "Find a part-time job in retail to increase my monthly income.",
                    "Reduce my monthly consumption by 20% by cooking at home more often.",
                    "Save at least $100 from my income by cutting unnecessary expenses.",
                    "Engage in a new hobby or activity to increase my interest in new experiences.",
                    "Reconnect with an old friend to reduce social isolation."
                ]
            """
            GOALS_PROMPT = prettify_document(GOALS_PROMPT)
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
