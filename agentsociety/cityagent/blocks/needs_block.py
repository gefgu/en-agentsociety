import json
import logging
from typing import cast

from agentsociety import Simulator
from agentsociety.llm import LLM
from agentsociety.memory import Memory
from agentsociety.workflow import Block, FormatPrompt

from .utils import clean_json_response

logger = logging.getLogger("agentsociety")

INITIAL_NEEDS_PROMPT = """You are an intelligent agent satisfaction initialization system. Based on the profile information below, please help initialize the agent's satisfaction levels and related parameters.

Profile Information:
- Gender: {gender}
- Education Level: {education} 
- Consumption Level: {consumption}
- Occupation: {occupation}
- Age: {age}
- Monthly Income: {income}

Current Time: {now_time}

Please initialize the agent's satisfaction levels and parameters based on the profile above. Return the values in JSON format with the following structure:

Current satisfaction levels (0-1 float values, lower means less satisfied):
- hunger_satisfaction: Hunger satisfaction level (Normally, the agent will be less satisfied with hunger at eating time)
- energy_satisfaction: Energy satisfaction level (Normally, at night, the agent will be less satisfied with energy)
- safety_satisfaction: Safety satisfaction level (Normally, the agent will be more satisfied with safety when they have high income and currency)
- social_satisfaction: Social satisfaction level

Please response in json format (Do not return any other text), example:
{{
    "current_satisfaction": {{
        "hunger_satisfaction": 0.8,
        "energy_satisfaction": 0.7,
        "safety_satisfaction": 0.9,
        "social_satisfaction": 0.6
    }}
}}
"""

EVALUATION_PROMPT = """You are an evaluation system for an intelligent agent. The agent has performed the following actions to satisfy the {current_need} need:

Goal: {plan_target}
Execution situation:
{evaluation_results}

Current satisfaction: 
- hunger_satisfaction: {hunger_satisfaction}
- energy_satisfaction: {energy_satisfaction}
- safety_satisfaction: {safety_satisfaction}
- social_satisfaction: {social_satisfaction}

Please evaluate and adjust the value of {current_need} satisfaction based on the execution results above.

Notes:
1. Satisfaction values range from 0-1, where:
   - 1 means the need is fully satisfied
   - 0 means the need is completely unsatisfied 
   - Higher values indicate greater need satisfaction
2. If the current need is not "whatever", only return the new value for the current need. Otherwise, return both safe and social need values.
3. Ensure the return value is in valid JSON format, examples below:

Please response in json format for specific need (hungry here) adjustment (Do not return any other text), example:
{{
    "hunger_satisfaction": new_need_value
}}

Please response in json format for whatever need adjustment (Do not return any other text), example:
{{
    "safety_satisfaction": new_safe_value,
    "social_satisfaction": new_social_value
}}
"""


class NeedsBlock(Block):
    """
    Manages agent's dynamic needs system including:
    - Initializing satisfaction levels
    - Time-based decay of satisfaction values
    - Need prioritization based on thresholds
    - Plan execution evaluation and satisfaction adjustments
    """

    def __init__(self, llm: LLM, memory: Memory, simulator: Simulator):
        """
        Initialize needs management system.

        Args:
            llm: Language model instance for processing prompts
            memory: Agent's memory storage interface
            simulator: Simulation environment controller

        Configuration Parameters:
            alpha_H: Hunger satisfaction decay rate per hour (default: 0.15)
            alpha_D: Energy satisfaction decay rate per hour (default: 0.08)
            alpha_P: Safety satisfaction decay rate per hour (default: 0.05)
            alpha_C: Social satisfaction decay rate per hour (default: 0.1)
            T_H: Hunger threshold for triggering need (default: 0.2)
            T_D: Energy threshold for triggering need (default: 0.2)
            T_P: Safety threshold for triggering need (default: 0.2)
            T_C: Social threshold for triggering need (default: 0.3)
        """
        super().__init__("NeedsBlock", llm=llm, memory=memory, simulator=simulator)
        self.evaluation_prompt = FormatPrompt(EVALUATION_PROMPT)
        self.initial_prompt = FormatPrompt(INITIAL_NEEDS_PROMPT)
        self.need_work = True
        self.now_day = -1
        self.last_evaluation_time = None
        self.trigger_time = 0
        self.token_consumption = 0
        self.initialized = False
        self.alpha_H, self.alpha_D, self.alpha_P, self.alpha_C = (
            0.15,
            0.08,
            0.05,
            0.1,
        )  # Hunger decay rate, Energy decay rate, Safety decay rate, Social decay rate
        self.T_H, self.T_D, self.T_P, self.T_C = (
            0.2,
            0.2,
            0.2,
            0.3,
        )  # Hunger threshold, Energy threshold, Safety threshold, Social threshold

    async def initialize(self):
        """
        Initialize agent's satisfaction levels using profile data.
        - Runs once per simulation day
        - Collects demographic data from memory
        - Generates initial satisfaction values via LLM
        - Handles JSON parsing and validation
        """
        day = await self.simulator.get_simulator_day()
        if day != self.now_day:
            self.now_day = day
            workday = self.simulator.sence("day")
            if workday == "Workday":
                self.need_work = True
            else:
                self.need_work = False

        if not self.initialized:
            self.initial_prompt.format(
                gender=await self.memory.status.get("gender"),
                education=await self.memory.status.get("education"),
                consumption=await self.memory.status.get("consumption"),
                occupation=await self.memory.status.get("occupation"),
                age=await self.memory.status.get("age"),
                income=await self.memory.status.get("income"),
                now_time=await self.simulator.get_time(format_time=True),
            )
            response = await self.llm.atext_request(
                self.initial_prompt.to_dialog(), response_format={"type": "json_object"}
            )
            response = clean_json_response(response)  # type:ignore
            retry = 3
            while retry > 0:
                try:
                    satisfaction = json.loads(response)
                    satisfactions = satisfaction["current_satisfaction"]
                    await self.memory.status.update(
                        "hunger_satisfaction", satisfactions["hunger_satisfaction"]
                    )
                    await self.memory.status.update(
                        "energy_satisfaction", satisfactions["energy_satisfaction"]
                    )
                    await self.memory.status.update(
                        "safety_satisfaction", satisfactions["safety_satisfaction"]
                    )
                    await self.memory.status.update(
                        "social_satisfaction", satisfactions["social_satisfaction"]
                    )
                    break
                except json.JSONDecodeError:
                    logger.warning(f"初始化响应不是有效的JSON格式: {response}")
                    retry -= 1

            current_plan = await self.memory.status.get("current_plan")
            history = await self.memory.status.get("plan_history")
            history.append(current_plan)
            await self.memory.status.update("plan_history", history)
            await self.memory.status.update("current_plan", None)
            await self.memory.status.update(
                "current_step", {"intention": "", "type": ""}
            )
            await self.memory.status.update("execution_context", {})
            self.initialized = True

    async def time_decay(self):
        """
        Apply time-based decay to satisfaction values.
        - Calculates hours since last update
        - Applies exponential decay to each satisfaction dimension
        - Ensures values stay within [0,1] range
        """
        # calculate time diff
        time_now = await self.simulator.get_time()
        time_now = cast(int, time_now)
        if self.last_evaluation_time is None:
            self.last_evaluation_time = time_now
            time_diff = 0
        else:
            time_diff = (time_now - self.last_evaluation_time) / 3600
            self.last_evaluation_time = time_now

        # acquire current satisfaction
        hunger_satisfaction = await self.memory.status.get("hunger_satisfaction")
        energy_satisfaction = await self.memory.status.get("energy_satisfaction")
        safety_satisfaction = await self.memory.status.get("safety_satisfaction")
        social_satisfaction = await self.memory.status.get("social_satisfaction")

        # calculates hunger and fatigue decay based on elapsed time
        hungry_decay = self.alpha_H * time_diff
        energy_decay = self.alpha_D * time_diff
        safety_decay = self.alpha_P * time_diff
        social_decay = self.alpha_C * time_diff
        hunger_satisfaction = max(0, hunger_satisfaction - hungry_decay)
        energy_satisfaction = max(0, energy_satisfaction - energy_decay)
        safety_satisfaction = max(0, safety_satisfaction - safety_decay)
        social_satisfaction = max(0, social_satisfaction - social_decay)

        # update satisfaction
        await self.memory.status.update("hunger_satisfaction", hunger_satisfaction)
        await self.memory.status.update("energy_satisfaction", energy_satisfaction)
        await self.memory.status.update("safety_satisfaction", safety_satisfaction)
        await self.memory.status.update("social_satisfaction", social_satisfaction)

    async def update_when_plan_completed(self):
        # Check if there is any ongoing plan
        current_plan = await self.memory.status.get("current_plan")
        if current_plan and (
            current_plan.get("completed") or current_plan.get("failed")
        ):
            # Evaluate the execution process of the plan and adjust needs
            await self.evaluate_and_adjust_needs(current_plan)
            # Add the completed plan to history
            history = await self.memory.status.get("plan_history")
            history.append(current_plan)
            await self.memory.status.update("plan_history", history)
            await self.memory.status.update("current_plan", None)
            await self.memory.status.update(
                "current_step", {"intention": "", "type": ""}
            )
            await self.memory.status.update("execution_context", {})

    async def determine_current_need(self):
        """
        Determine agent's current dominant need based on:
        - Satisfaction thresholds
        - Need priority hierarchy (hungry > tired > safe > social)
        - Workday requirements
        - Ongoing plan interruptions
        """
        hunger_satisfaction = await self.memory.status.get("hunger_satisfaction")
        energy_satisfaction = await self.memory.status.get("energy_satisfaction")
        safety_satisfaction = await self.memory.status.get("safety_satisfaction")
        social_satisfaction = await self.memory.status.get("social_satisfaction")

        # If needs adjustment is required, update current need
        # The adjustment scheme is to adjust the need if the current need is empty, or a higher priority need appears
        current_plan = await self.memory.status.get("current_plan")
        current_need = await self.memory.status.get("current_need")

        # When there's no plan or the plan has been completed, get all satisfaction values and check each need against its threshold based on priority
        if not current_plan or current_plan.get("completed"):
            # Check needs in order of priority
            if hunger_satisfaction <= self.T_H:
                await self.memory.status.update("current_need", "hungry")
            elif energy_satisfaction <= self.T_D:
                await self.memory.status.update("current_need", "tired")
            elif self.need_work:
                await self.memory.status.update("current_need", "safe")
                self.need_work = False
            elif safety_satisfaction <= self.T_P:
                await self.memory.status.update("current_need", "safe")
            elif social_satisfaction <= self.T_C:
                await self.memory.status.update("current_need", "social")
            else:
                await self.memory.status.update("current_need", "whatever")
        else:
            # While there is an ongoing plan, only adjust for higher priority needs
            needs_changed = False
            new_need = None
            if hunger_satisfaction <= self.T_H and current_need not in [
                "hungry",
                "tired",
            ]:
                new_need = "hungry"
                needs_changed = True
            elif energy_satisfaction <= self.T_D and current_need not in [
                "hungry",
                "tired",
            ]:
                new_need = "tired"
                needs_changed = True
            elif safety_satisfaction <= self.T_P and current_need not in [
                "hungry",
                "tired",
                "safe",
            ]:
                new_need = "safe"
                needs_changed = True
            elif social_satisfaction <= self.T_C and current_need not in [
                "hungry",
                "tired",
                "safe",
                "social",
            ]:
                new_need = "social"
                needs_changed = True

            # If needs have changed, interrupt the current plan
            if needs_changed:
                await self.evaluate_and_adjust_needs(current_plan)
                history = await self.memory.status.get("plan_history")
                history.append(current_plan)
                await self.memory.status.update("current_need", new_need)
                await self.memory.status.update("plan_history", history)
                await self.memory.status.update("current_plan", None)
                await self.memory.status.update(
                    "current_step", {"intention": "", "type": ""}
                )
                await self.memory.status.update("execution_context", {})

    async def evaluate_and_adjust_needs(self, completed_plan):
        """
        Evaluate plan execution results and adjust satisfaction values.
        - Extracts step evaluations from completed plan
        - Constructs evaluation prompt for LLM
        - Processes LLM response and updates satisfaction values
        - Implements retry logic for invalid responses
        """
        # Retrieve the executed plan and evaluation results
        evaluation_results = []
        for step in completed_plan["steps"]:
            if "evaluation" in step["evaluation"]:
                eva_ = step["evaluation"]["evaluation"]
            else:
                eva_ = "Plan failed, not completed"
            evaluation_results.append(f"- {step['intention']} ({step['type']}): {eva_}")
        evaluation_results = "\n".join(evaluation_results)

        # Use LLM for evaluation
        current_need = await self.memory.status.get("current_need")
        self.evaluation_prompt.format(
            current_need=current_need,
            plan_target=completed_plan["target"],
            evaluation_results=evaluation_results,
            hunger_satisfaction=await self.memory.status.get("hunger_satisfaction"),
            energy_satisfaction=await self.memory.status.get("energy_satisfaction"),
            safety_satisfaction=await self.memory.status.get("safety_satisfaction"),
            social_satisfaction=await self.memory.status.get("social_satisfaction"),
        )

        retry = 3
        while retry > 0:
            response = await self.llm.atext_request(
                self.evaluation_prompt.to_dialog(),
                response_format={"type": "json_object"},
            )
            try:
                new_satisfaction = json.loads(clean_json_response(response))  # type: ignore
                # Update values of all needs
                for need_type, new_value in new_satisfaction.items():
                    if need_type in [
                        "hunger_satisfaction",
                        "energy_satisfaction",
                        "safety_satisfaction",
                        "social_satisfaction",
                    ]:
                        await self.memory.status.update(need_type, new_value)
                        return
            except json.JSONDecodeError:
                logger.warning(
                    f"Evaluation response is not a valid JSON format: {response}"
                )
                retry -= 1
            except Exception as e:
                logger.warning(f"Error processing evaluation response: {str(e)}")
                logger.warning(f"Original response: {response}")
                retry -= 1

    async def forward(self):
        """
        Main execution flow for needs management:
        1. Initialize satisfaction values (if needed)
        2. Apply time-based decay
        3. Handle completed plans
        4. Determine current dominant need
        """
        await self.initialize()

        # satisfaction decay with time
        await self.time_decay()

        # update when plan completed
        await self.update_when_plan_completed()

        # determine current need
        await self.determine_current_need()
