from typing import Any
import time
import json_repair
import os
import json

from ...agent import AgentToolbox, Block, FormatPrompt, DotDict
from ...logger import get_logger
from ...memory import Memory
from .utils import clean_json_response
from ...catboost import catboost_adjust_needs


INITIAL_NEEDS_PROMPT = """You are an intelligent agent satisfaction initialization system. Based on the profile information below, please help initialize the agent's satisfaction levels and related parameters.

Profile Information:
- Gender: ${profile.gender}
- Education Level: ${profile.education} 
- Consumption Level: ${profile.consumption}
- Occupation: ${profile.occupation}
- Age: ${profile.age}
- Monthly Income: ${profile.income}
- Household type: {household}
- Life stage: {life_stage}
- Hobbies: {hobbies}
- Goals: {goals}
- Big Five Personality Traits (1=Low, 2=Medium, 3=High):
  - Openness: {openness}
  - Conscientiousness: {conscientiousness}
  - Extraversion: {extraversion}
  - Agreeableness: {agreeableness}
  - Neuroticism: {neuroticism}
- Behavioral Preferences:
  - Social Frequency: {social_frequency} (0.0=Rarely initiates social contact, 1.0=Frequently seeks social interaction)

Current Time: ${context.current_time}

Please initialize the agent's satisfaction levels and parameters based on the profile above. Return the values in JSON format with the following structure:

Current satisfaction levels (0-1 float values, lower means less satisfied):
- hunger_satisfaction: Hunger satisfaction level (Normally, the agent will be less satisfied with hunger at eating time)
- energy_satisfaction: Energy satisfaction level (Normally, at night, the agent will be less satisfied with energy)
- safety_satisfaction: Safety satisfaction level (Normally, the agent will be more satisfied with safety when they have high income and currency)
- social_satisfaction: Social satisfaction level (Consider social_frequency: higher value means more need for social interaction)

Please response in json format, example:
{{
    "current_satisfaction": {{
        "hunger_satisfaction": 0.8,
        "energy_satisfaction": 0.7,
        "safety_satisfaction": 0.9,
        "social_satisfaction": 0.6
    }}
}}
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
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
- Social Frequency: {social_frequency} (0.0=Rarely initiates social contact, 1.0=Frequently seeks social interaction)

Please evaluate and adjust the value of {current_need} satisfaction based on the execution results above.

Notes:
1. Satisfaction values range from 0-1, where:
   - 1 means the need is fully satisfied
   - 0 means the need is completely unsatisfied 
   - Higher values indicate greater need satisfaction
2. If the current need is not "whatever", only return the new value for the current need. Otherwise, return both safe and social need values.
3. Consider social_frequency when evaluating social satisfaction: higher social_frequency means social activities have greater impact.
4. Ensure the return value is in valid JSON format, examples below:

Please response in json format for specific need (hungry here) adjustment (Do not return any other text), example:
{{
    "hunger_satisfaction": new_hunger_satisfaction_value
}}

Please response in json format for whatever need adjustment (Do not return any other text), example:
{{
    "safety_satisfaction": new_safety_satisfaction_value,
    "social_satisfaction": new_social_satisfaction_value
}}
"""

REFLECTION_PROMPT = """You are an intelligent agent reflection system. Based on the intervention message below, please help to rebuild the satisfaction levels of the agent.

The agent has received/sense the following intervention message:
--------------------------------
{intervention_message}
--------------------------------

And the agent's current needs are:
- hunger_satisfaction: {hunger_satisfaction}
- energy_satisfaction: {energy_satisfaction}
- safety_satisfaction: {safety_satisfaction}
- social_satisfaction: {social_satisfaction}

Household type: {household}
Life stage: {life_stage}
Hobbies: {hobbies}

Big Five Personality Traits (1=Low, 2=Medium, 3=High):
- Openness: {openness}
- Conscientiousness: {conscientiousness}
- Extraversion: {extraversion}
- Agreeableness: {agreeableness}
- Neuroticism: {neuroticism}

Behavioral Preferences:
- Social Frequency: {social_frequency} (0.0=Rarely initiates social contact, 1.0=Frequently seeks social interaction)

The agent's current action is:
--------------------------------
{current_action}
--------------------------------

Please response in json format, example:
{{
    "hunger_satisfaction": new_hunger_satisfaction_value,
    "energy_satisfaction": new_energy_satisfaction_value,
    "safety_satisfaction": new_safety_satisfaction_value,
    "social_satisfaction": new_social_satisfaction_value,
}}
If you think the agent has to stop the current action and do something to satisfy the needs, please response in json format, example:
{{
    "do_something": True,
    "description": "Go to the hospital"
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

    name = "NeedsBlock"
    description = "Manages agent's dynamic needs system"
    NeedAgent = True

    def __init__(
        self,
        id: str,
        toolbox: AgentToolbox,
        agent_memory: Memory,
        agent_context: DotDict,
        evaluation_prompt: str = EVALUATION_PROMPT,
        reflection_prompt: str = REFLECTION_PROMPT,
        initial_prompt: str = INITIAL_NEEDS_PROMPT,
    ):
        """
        Initialize needs management system.

        Args:
            llm: Language model instance for processing prompts
            environment: Simulation environment controller
            agent_memory: Agent's memory storage interface

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
        super().__init__(toolbox=toolbox, agent_memory=agent_memory)
        self.context = agent_context
        self.evaluation_prompt = FormatPrompt(template=evaluation_prompt)
        self.initial_prompt = FormatPrompt(template=initial_prompt, memory=agent_memory)
        self.reflection_prompt = FormatPrompt(template=reflection_prompt)
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
        # intervention need
        self._need_to_do = None
        # determine if the intervention need has been checked
        self._need_to_do_checked = False
        self.id = id
        self._last_tick_time = 0

    async def reset(self):
        """Reset the needs block."""
        self._need_to_do = None
        self._need_to_do_checked = False
        self.initialized = False
        await self.memory.status.update("need_fulfillment", 0)

    async def initialize(self):
        """
        Initialize agent's satisfaction levels using profile data.
        - Runs once per simulation day
        - Collects demographic data from memory
        - Generates initial satisfaction values via LLM
        - Handles JSON parsing and validation
        """
        day, t = self.environment.get_datetime()

        if day != self.now_day and t >= 7 * 60 * 60:
            self.now_day = day

            await self.update_need_fulfillment()
            workday = self.environment.sense("workday")
            if workday:
                self.need_work = True
            else:
                self.need_work = False

        if not self.initialized:
            # Get Big Five personality traits
            big5 = await self.memory.status.get("big5", {})

            # Get household and life stage
            household = await self.memory.status.get("household", "unknown")
            life_stage = await self.memory.status.get("life_stage", "unknown")
            hobbies = await self.memory.status.get("hobbies", [])
            hobbies_str = (
                ", ".join(hobbies) if isinstance(hobbies, list) else str(hobbies)
            )
            goals = await self.memory.status.get("goals", [])
            goals_str = ", ".join(goals) if isinstance(goals, list) else str(goals)

            # Get preferences
            preferences = await self.memory.status.get("preferences", {})
            social_frequency = preferences.get("social_frequency", 0.5)

            await self.initial_prompt.format(
                context=self.context,
                household=household,
                life_stage=life_stage,
                hobbies=hobbies_str,
                goals=goals_str,
                openness=big5.get("openness", 2),
                conscientiousness=big5.get("conscientiousness", 2),
                extraversion=big5.get("extraversion", 2),
                agreeableness=big5.get("agreeableness", 2),
                neuroticism=big5.get("neuroticism", 2),
                social_frequency=social_frequency,
            )
            response = await self.llm.atext_request(
                self.initial_prompt.to_dialog(),
                response_format={"type": "json_object"},
                context={
                    "block_name": "NeedsBlock",
                    "func_name": "initialize",
                    "agent_id": self.id,
                },
            )
            response = clean_json_response(response)
            retry = 3
            while retry > 0:
                try:
                    satisfaction: Any = json_repair.loads(response)
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
                except Exception as e:
                    get_logger().warning(f"Initial response error: {e}")
                    retry -= 1

            current_plan = await self.memory.status.get("current_plan", False)
            if current_plan:
                history = await self.memory.status.get("plan_history")
                history.append(current_plan)
                await self.memory.status.update("plan_history", history)
                await self.memory.status.update("current_plan", None)
                await self.memory.status.update("execution_context", {})
            self.initialized = True

    async def reflect_to_intervention(self, intervention: str):
        # rebuild needs for intervention
        current_plan = await self.memory.status.get("current_plan", False)
        if not current_plan:
            return
        step_index = current_plan.get("index", 0)
        current_action = current_plan.get("steps", [{"intention": "", "type": ""}])[
            step_index
        ]
        action_message = (
            f"{current_action['intention']} ({current_action['type']})"
            if current_action["intention"] != ""
            else "None"
        )

        # Get Big Five personality traits
        big5 = await self.memory.status.get("big5", {})

        # Get household and life stage
        household = await self.memory.status.get("household", "unknown")
        life_stage = await self.memory.status.get("life_stage", "unknown")
        hobbies = await self.memory.status.get("hobbies", [])
        hobbies_str = ", ".join(hobbies) if isinstance(hobbies, list) else str(hobbies)

        # Get preferences
        preferences = await self.memory.status.get("preferences", {})
        social_frequency = preferences.get("social_frequency", 0.5)

        await self.reflection_prompt.format(
            intervention_message=intervention,
            current_action=action_message,
            hunger_satisfaction=await self.memory.status.get("hunger_satisfaction"),
            energy_satisfaction=await self.memory.status.get("energy_satisfaction"),
            safety_satisfaction=await self.memory.status.get("safety_satisfaction"),
            social_satisfaction=await self.memory.status.get("social_satisfaction"),
            household=household,
            life_stage=life_stage,
            hobbies=hobbies_str,
            openness=big5.get("openness", 2),
            conscientiousness=big5.get("conscientiousness", 2),
            extraversion=big5.get("extraversion", 2),
            agreeableness=big5.get("agreeableness", 2),
            neuroticism=big5.get("neuroticism", 2),
            social_frequency=social_frequency,
        )
        response = await self.llm.atext_request(
            self.reflection_prompt.to_dialog(),
            response_format={"type": "json_object"},
            context={
                "block_name": "NeedsBlock",
                "func_name": "reflect_to_intervention",
                "agent_id": self.id,
            },
        )
        try:
            reflection: Any = json_repair.loads(clean_json_response(response))
            if "do_something" in reflection:
                self._need_to_do = reflection["description"]
            else:
                # update satisfaction
                for need_type, new_value in reflection.items():
                    if need_type in [
                        "hunger_satisfaction",
                        "energy_satisfaction",
                        "safety_satisfaction",
                        "social_satisfaction",
                    ]:
                        await self.memory.status.update(need_type, new_value)
        except Exception as e:
            get_logger().warning(f"Error processing reflection response: {str(e)}")
            get_logger().warning(f"Original response: {response}")
            return None

    async def time_decay(self):
        """
        Apply time-based decay to satisfaction values.
        - Calculates hours since last update
        - Applies exponential decay to each satisfaction dimension
        - Ensures values stay within [0,1] range
        """
        # calculate time diff
        tick_now = self.environment.get_tick()
        if self.last_evaluation_time is None:
            self.last_evaluation_time = tick_now
            return
        else:
            time_diff = (tick_now - self.last_evaluation_time) / 3600
            self.last_evaluation_time = tick_now

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
            pre_need = await self.memory.status.get("current_need")
            # evaluate plan execution and adjust needs
            await self.evaluate_and_adjust_needs(current_plan)
            # add completed plan to history
            history = await self.memory.status.get("plan_history")
            history.append(current_plan)
            await self.memory.status.update("plan_history", history)
            await self.memory.status.update("current_plan", None)
            await self.memory.status.update("execution_context", {})
            if pre_need == self._need_to_do:
                self._need_to_do = None
                self._need_to_do_checked = False

    async def determine_current_need(self):
        """
        Determine agent's current dominant need based on:
        - Satisfaction thresholds
        - Need priority hierarchy (hungry > tired > safe > social)
        - Workday requirements
        - Ongoing plan interruptions
        """
        cognition = None
        hunger_satisfaction = await self.memory.status.get("hunger_satisfaction")
        energy_satisfaction = await self.memory.status.get("energy_satisfaction")
        safety_satisfaction = await self.memory.status.get("safety_satisfaction")
        social_satisfaction = await self.memory.status.get("social_satisfaction")

        # If needs adjustment is required, update current need
        # The adjustment scheme is to adjust the need if the current need is empty, or a higher priority need appears
        current_plan = await self.memory.status.get("current_plan")
        current_need = await self.memory.status.get("current_need")

        # When there's no plan, get all satisfaction values and check each need against its threshold based on priority
        if not current_plan:
            # check needs in priority order
            if self._need_to_do:
                await self.memory.status.update("current_need", self._need_to_do)
                self.context.current_intention = self._need_to_do
                await self.memory.stream.add(
                    topic="cognition", description=f"I need to do: {self._need_to_do}"
                )
                cognition = f"I need to do: {self._need_to_do}"
                self._need_to_do_checked = True
            elif hunger_satisfaction <= self.T_H:
                await self.memory.status.update("current_need", "hungry")
                self.context.current_intention = "hungry"
                await self.memory.stream.add(
                    topic="cognition", description="I feel hungry"
                )
                cognition = "I feel hungry"
            elif energy_satisfaction <= self.T_D:
                await self.memory.status.update("current_need", "tired")
                self.context.current_intention = "tired"
                await self.memory.stream.add(
                    topic="cognition", description="I feel tired"
                )
                cognition = "I feel tired"
            elif self.need_work:
                await self.memory.status.update("current_need", "safe")
                self.context.current_intention = "safe"
                await self.memory.stream.add(
                    topic="cognition", description="I need to work"
                )
                cognition = "I need to work"
                self.need_work = False
            elif safety_satisfaction <= self.T_P:
                await self.memory.status.update("current_need", "safe")
                self.context.current_intention = "safe"
                await self.memory.stream.add(
                    topic="cognition", description="I have safe needs right now"
                )
                cognition = "I have safe needs right now"
            elif social_satisfaction <= self.T_C:
                await self.memory.status.update("current_need", "social")
                self.context.current_intention = "social"
                await self.memory.stream.add(
                    topic="cognition", description="I have social needs right now"
                )
                cognition = "I have social needs right now"
            else:
                await self.memory.status.update("current_need", "whatever")
                self.context.current_intention = "whatever"
                await self.memory.stream.add(
                    topic="cognition", description="I have no specific needs right now"
                )
                cognition = "I have no specific needs right now"

        else:
            # While there is an ongoing plan, only adjust for higher priority needs
            needs_changed = False
            new_need = None
            if self._need_to_do:
                if not self._need_to_do_checked:
                    new_need = self._need_to_do
                    needs_changed = True
                    self._need_to_do_checked = True
                    cognition = f"I need to change my plan, as {self._need_to_do} is more important than {current_need}"
                else:
                    cognition = f"I still need to concentrate on {self._need_to_do}"
                    pass  # still concentrate on the emergency need
            elif hunger_satisfaction <= self.T_H and current_need not in [
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
                await self.memory.stream.add(
                    topic="cognition",
                    description=f"I need to change my plan because the need of [{new_need}] is more important than [{current_need}]",
                )
                cognition = f"I need to change my plan because the need of [{new_need}] is more important than [{current_need}]"
                await self.memory.status.update("current_need", new_need)
                self.context.current_intention = new_need
                await self.memory.status.update("plan_history", history)
                await self.memory.status.update("current_plan", None)
                await self.memory.status.update("execution_context", {})

        date, t = self.environment.get_datetime()

        delta_t = t - self._last_tick_time
        self._last_tick_time = t
        is_satisfied = (
            hunger_satisfaction > self.T_H
            and energy_satisfaction > self.T_D
            and safety_satisfaction > self.T_P
            and social_satisfaction > self.T_C
        )

        if is_satisfied and delta_t > 0:
            # Convert seconds to proportion of 24h day (86400s)
            fulfillment_increment = delta_t / 86400.0

            current_fulfillment = await self.memory.status.get("need_fulfillment", 0)
            await self.memory.status.update(
                "need_fulfillment", current_fulfillment + fulfillment_increment
            )

        return cognition

    async def _save_finetuning_data(
        self, prompt_dialog: str, response: str, metadata: dict
    ):
        """Save finetuning data to the specified directory."""
        finetune_data_dir = self.toolbox.finetune_data_dir
        if not finetune_data_dir:
            return

        os.makedirs(f"{finetune_data_dir}/adjust_needs/", exist_ok=True)
        timestamp = int(time.time() * 1000)
        filename = f"{self.id}_{timestamp}.json"
        filepath = os.path.join(f"{finetune_data_dir}/adjust_needs/", filename)

        finetune_entry = {
            "prompt": prompt_dialog,
            "response": response,
            **metadata,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json.dumps(finetune_entry, ensure_ascii=False) + "\n")

    async def evaluate_and_adjust_needs(self, completed_plan):
        """
        Evaluate plan execution results and adjust satisfaction values.
        - Extracts step evaluations from completed plan
        - Constructs evaluation prompt for LLM
        - Processes LLM response and updates satisfaction values
        - Implements retry logic for invalid responses
        """
        metrics_tool = self.toolbox.get_tool("metrics_actor")
        modernbert_tool = self.toolbox.get_tool("modernbert_regression_actor")
        catboost_tool = self.toolbox.get_tool("catboost_adjust_needs_actor")
        db_tool = self.toolbox.get_tool("db_actor")

        # Retrieve the executed plan and evaluation results
        evaluation_results = []
        for step in completed_plan["steps"]:
            if "evaluation" in step["evaluation"]:
                eva_ = step["evaluation"]["evaluation"]
            else:
                eva_ = "Plan failed or skipped, not completed"
            evaluation_results.append(f"- {step['intention']} ({step['type']}): {eva_}")
        evaluation_results = "\n".join(evaluation_results)

        # Use LLM for evaluation
        current_need = await self.memory.status.get("current_need")
        current_hunger = await self.memory.status.get("hunger_satisfaction")
        current_energy = await self.memory.status.get("energy_satisfaction")
        current_safety = await self.memory.status.get("safety_satisfaction")
        current_social = await self.memory.status.get("social_satisfaction")

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
        social_frequency = preferences.get("social_frequency", 0.5)

        await self.evaluation_prompt.format(
            current_need=current_need,
            plan_target=completed_plan["target"],
            evaluation_results=evaluation_results,
            hunger_satisfaction=current_hunger,
            energy_satisfaction=current_energy,
            safety_satisfaction=current_safety,
            social_satisfaction=current_social,
            household=household,
            life_stage=life_stage,
            hobbies=hobbies_str,
            goals=goals_str,
            openness=big5.get("openness", 2),
            conscientiousness=big5.get("conscientiousness", 2),
            extraversion=big5.get("extraversion", 2),
            agreeableness=big5.get("agreeableness", 2),
            neuroticism=big5.get("neuroticism", 2),
            social_frequency=social_frequency,
        )

        if catboost_tool:
            try:
                start_time = time.perf_counter()
                context_text = self.evaluation_prompt.to_dialog()[0]["content"]

                (
                    should_use,
                    response_list,
                ) = await catboost_tool.get_tool().predict.remote(
                    prompt=context_text,
                    current_need=current_need,
                    current_hunger=current_hunger,
                    current_energy=current_energy,
                    current_safety=current_safety,
                    current_social=current_social,
                )
                # --- MEASUREMENT END ---
                end_time = time.perf_counter()
                duration = end_time - start_time

                if should_use and response_list is not None:
                    if metrics_tool:
                        metrics_tool.get_tool().record_block_performance.remote(
                            block_name="NeedsBlock",
                            func_name="evaluate_and_adjust_needs",
                            actor="catboost",
                            agent_id=self.id,
                            duration=round(duration, 4),
                            token_input=len(context_text.split()),
                            token_output=0,
                        )

                        metrics_tool.get_tool().record_routing.remote(
                            block_name="NeedsBlock",
                            func_name="evaluate_and_adjust_needs",
                            agent_id=self.id,
                            routed=False,
                        )

                    try:
                        new_satisfaction: Any = response_list
                        # Update values of all needs
                        for need_type, new_value in new_satisfaction.items():
                            if need_type in [
                                "hunger_satisfaction",
                                "energy_satisfaction",
                                "safety_satisfaction",
                                "social_satisfaction",
                            ]:
                                await self.memory.status.update(need_type, new_value)

                        if db_tool:
                            db_tool.get_tool().insert_adjust_needs_record.remote(
                                {
                                    "agent_id": self.id,
                                    "prompt": catboost_adjust_needs.format_prompt(
                                        context_text, current_need
                                    ),
                                    "current_need": current_need,
                                    "current_hunger": current_hunger,
                                    "current_energy": current_energy,
                                    "current_safety": current_safety,
                                    "current_social": current_social,
                                    "new_hunger": new_satisfaction.get(
                                        "hunger_satisfaction", current_hunger
                                    ),
                                    "new_energy": new_satisfaction.get(
                                        "energy_satisfaction", current_energy
                                    ),
                                    "new_safety": new_satisfaction.get(
                                        "safety_satisfaction", current_safety
                                    ),
                                    "new_social": new_satisfaction.get(
                                        "social_satisfaction", current_social
                                    ),
                                    "timestamp": int(time.time()),
                                    "actor": "catboost",
                                }
                            )

                        return
                    except Exception as e:
                        get_logger().warning(
                            f"Error processing evaluation response: {str(e)}"
                        )
                        get_logger().warning(f"Original response: {response_list}")

                else:
                    metrics_tool.get_tool().record_routing.remote(
                        block_name="NeedsBlock",
                        func_name="evaluate_and_adjust_needs",
                        agent_id=self.id,
                        routed=True,
                    )

            except Exception as e:
                get_logger().warning(f"CatBoost evaluation failed: {str(e)}")
                # Fallback to original LLM evaluation

        if modernbert_tool:
            try:
                start_time = time.perf_counter()
                context_text = self.evaluation_prompt.to_dialog()[0]["content"]

                modernbert_pool = modernbert_tool.get_tool()
                response_dict = await modernbert_pool.predict.remote(context_text)
                # --- MEASUREMENT END ---
                end_time = time.perf_counter()
                duration = end_time - start_time

                if metrics_tool:
                    metrics_tool.get_tool().record_performance.remote(
                        block_name="NeedsBlock",
                        func_name="evaluate_and_adjust_needs_modernbert",
                        actor="modernbert",
                        agent_id=self.id,
                        duration=round(duration, 4),
                        token_input=len(context_text.split()),
                        token_output=0,
                    )

                try:
                    # print(self.evaluation_prompt.to_dialog())
                    # print(response)

                    new_satisfaction: Any = response_dict
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
                except Exception as e:
                    get_logger().warning(
                        f"Error processing evaluation response: {str(e)}"
                    )
                    get_logger().warning(f"Original response: {response_dict}")

            except Exception as e:
                get_logger().warning(f"ModernBERT evaluation failed: {str(e)}")
                # Fallback to original LLM evaluation

        retry = 3
        while retry > 0:

            response = await self.llm.atext_request(
                self.evaluation_prompt.to_dialog(),
                response_format={"type": "json_object"},
                context={
                    "block_name": "NeedsBlock",
                    "func_name": "evaluate_and_adjust_needs",
                    "agent_id": self.id,
                },
            )

            if self.toolbox.finetune_data_dir:
                try:
                    await self._save_finetuning_data(
                        prompt_dialog=self.evaluation_prompt.to_dialog()[0]["content"],
                        response=response,
                        metadata={
                            "agent_id": self.id,
                            "current_need": current_need,
                            "timestamp": time.time(),
                        },
                    )
                except Exception as e:
                    get_logger().warning(
                        f"Failed to save finetuning data in needs_block: {str(e)}"
                    )

            try:
                # print(self.evaluation_prompt.to_dialog())
                # print(response)

                new_satisfaction: Any = json_repair.loads(clean_json_response(response))  # type: ignore
                # Update values of all needs
                for need_type, new_value in new_satisfaction.items():
                    if need_type in [
                        "hunger_satisfaction",
                        "energy_satisfaction",
                        "safety_satisfaction",
                        "social_satisfaction",
                    ]:
                        await self.memory.status.update(need_type, new_value)

                if db_tool:
                    record = {
                        "agent_id": self.id,
                        "prompt": self.evaluation_prompt.to_dialog()[0]["content"],
                        "current_need": current_need,
                        "current_hunger": current_hunger,
                        "current_energy": current_energy,
                        "current_safety": current_safety,
                        "current_social": current_social,
                        "new_hunger": new_satisfaction.get(
                            "hunger_satisfaction", current_hunger
                        ),
                        "new_energy": new_satisfaction.get(
                            "energy_satisfaction", current_energy
                        ),
                        "new_safety": new_satisfaction.get(
                            "safety_satisfaction", current_safety
                        ),
                        "new_social": new_satisfaction.get(
                            "social_satisfaction", current_social
                        ),
                        "timestamp": int(time.time()),
                        "actor": "llm",
                    }
                    db_tool.get_tool().insert_adjust_needs_record.remote(record)
                return
            except Exception as e:
                get_logger().warning(f"Error processing evaluation response: {str(e)}")
                get_logger().warning(f"Original response: {response}")
                retry -= 1

    async def update_need_fulfillment(self):
        """Only called in new days"""
        day, t = self.environment.get_datetime()
        current_fulfillment = await self.memory.status.get("need_fulfillment", 0)
        mean_need_fulfillment = await self.memory.status.get("mean_need_fulfillment", 0)

        new_mean_fulfillment = (mean_need_fulfillment * day + current_fulfillment) / (
            day + 1
        )

        await self.memory.status.update("mean_need_fulfillment", new_mean_fulfillment)
        await self.memory.status.update("need_fulfillment", 0)

    async def forward(self):
        """
        Main execution flow for needs management:
        1. Initialize satisfaction values (if needed)
        2. Apply time-based decay
        3. Handle completed plans
        4. Determine current dominant need
        """
        cognition = None

        await self.initialize()

        # satisfaction decay with time
        await self.time_decay()

        # update when plan completed
        await self.update_when_plan_completed()

        # determine current need
        cognition = await self.determine_current_need()

        return cognition


# [
#     {
#         "role": "user",
#         "content": 'You are an evaluation system for an intelligent agent. The agent has performed the following actions to satisfy the whatever need:\n\nGoal: other\nExecution situation:\n- Continue with work tasks (economy): work: Continue with work tasks\n- Take a short break for relaxation (other): Finished executing Take a short break for relaxation\n- Review patient records for accuracy (economy): Finished executing Review patient records for accuracy\n- Prepare for upcoming appointments or surgeries (economy): Failed to complete social interaction with default behavior: Prepare for upcoming appointments or surgeries\n- Check in with colleagues about any urgent matters (social): Plan failed or skipped, not completed\n- Enjoy a light lunch if time allows (other): Plan failed or skipped, not completed\n\nCurrent satisfaction: \n- hunger_satisfaction: 0.6\n- energy_satisfaction: 0.4933333333333337\n- safety_satisfaction: 0.45833333333333326\n- social_satisfaction: 0.31666666666666654\n\nPlease evaluate and adjust the value of whatever satisfaction based on the execution results above.\n\nNotes:\n1. Satisfaction values range from 0-1, where:\n   - 1 means the need is fully satisfied\n   - 0 means the need is completely unsatisfied \n   - Higher values indicate greater need satisfaction\n2. If the current need is not "whatever", only return the new value for the current need. Otherwise, return both safe and social need values.\n3. Ensure the return value is in valid JSON format, examples below:\n\nPlease response in json format for specific need (hungry here) adjustment (Do not return any other text), example:\n{\n    "hunger_satisfaction": new_hunger_satisfaction_value\n}\n\nPlease response in json format for whatever need adjustment (Do not return any other text), example:\n{\n    "safety_satisfaction": new_safety_satisfaction_value,\n    "social_satisfaction": new_social_satisfaction_value\n}\n',
#     }
# ]
# {"safety_satisfaction": 0.45833333333333326, "social_satisfaction": 0.21666666666666654}
