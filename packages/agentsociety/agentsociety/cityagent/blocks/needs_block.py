from typing import Any
import time
import json_repair
import os
import json

from ...agent import AgentToolbox, Block, FormatPrompt, DotDict
from ...logger import get_logger
from ...memory import Memory
from .utils import clean_json_response


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


POI_OBSERVATION_PROMPT = """You are a Spatial Memory Observation Encoder. Your task is to quantify the agent's experience at a Point of Interest (POI) into a numerical observation vector.

This vector will be fed into a Kalman filter to update the agent's long-term memory.

**Profile Information:**
- Gender: {gender}
- Age: {age}
- Income: {income}
- User Big Five Personality Traits: (1=Low, 2=Medium, 3=High)
  - Openness: {openness}
  - Conscientiousness: {conscientiousness}
  - Extraversion: {extraversion}
  - Agreeableness: {agreeableness}
  - Neuroticism: {neuroticism}
- Hobbies: {hobbies}

**Context:**
- POI Name: {poi_name}
- POI Category: {poi_category}

**Interaction/Observation Log:**
--------------------------------
{observation}
--------------------------------

**Task:**
Analyze the interaction log and the agent's profile to generate a quantitative score (0.0 to 1.0) for the following four dimensions based *only* on this specific visit.

**Scoring Guidelines (1.0 is always POSITIVE/GOOD, 0.0 is NEGATIVE/BAD):**

1. **price**: Evaluate the affordability/value.
   - 1.0 = Very Cheap / Excellent Value (Positive)
   - 0.0 = Very Expensive / Overpriced (Negative)
   
2. **atmosphere**: Evaluate the environment/vibe.
   - 1.0 = Excellent, Pleasant, Welcoming
   - 0.0 = Hostile, Dirty, Unpleasant

3. **satisfaction**: Evaluate the agent's overall fulfillment.
   - 1.0 = Highly Satisfied, Needs met perfectly
   - 0.0 = Unsatisfied, Regretful

4. **convenience**: Evaluate ease of access or service.
   - 1.0 = Very Convenient, Fast, Accessible
   - 0.0 = Inconvenient, Slow, Hard to find

**Response Format:**
Return ONLY valid JSON.

Example:
{{
    "price": 0.8,
    "atmosphere": 0.9,
    "satisfaction": 0.7,
    "convenience": 0.5
}}

DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
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
        poi_belief_update_prompt: str = POI_OBSERVATION_PROMPT,
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
        self.poi_belief_update_prompt = FormatPrompt(template=poi_belief_update_prompt)
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
            await self.update_poi_beliefs_from_plan(current_plan)

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

    async def update_poi_beliefs_from_plan(self, plan):
        """
        Update POI beliefs based on actually executed steps.
        Only processes steps that have non-pending evaluation status.
        Only processes steps with poi_id (excludes home and workplace).
        """

        # Debug Plan
        get_logger().debug(
            f"Updating POI beliefs from plan: {plan}", extra={"agent_id": self.id}
        )

        for step in plan.get("steps", []):
            evaluation = step.get("evaluation", {})
            if evaluation.get("status") == "pending" or not evaluation.get(
                "success", False
            ):
                get_logger().debug(
                    f"Agent {self.id}: Skipping step with pending or failed evaluation. Step: {step}, Evaluation: {evaluation}",
                    extra={"agent_id": self.id},
                )
                continue  # Skip pending steps

            # Only process steps with valid poi_id (POI visits)
            if "poi_id" not in step or step["poi_id"] is None:
                get_logger().debug(
                    f"Agent {self.id}: Skipping step without valid poi_id (not a POI visit or selection failed): {step.get('intention', 'unknown')}",
                    extra={"agent_id": self.id},
                )
                continue

            poi_id = step["poi_id"]
            intention = step.get("intention", "")
            step_type = step.get("type", "")
            details = evaluation.get("details", "")

            poi_category = step.get("next_place_type", "unknown")

            get_logger().info(
                f"Agent {self.id}: Updating beliefs for POI {poi_id}. Intention: {intention}, Type: {step_type}, Category: {poi_category}, Details: {details}",
                extra={"agent_id": self.id},
            )

            await self.update_location_belief(
                poi_id, poi_category, intention, step_type, details
            )

    async def update_location_belief(
        self, location_id, location_category, intention, step_type, details
    ):
        """
        Update beliefs about a location based on step evaluation.
        - Retrieves existing belief for the location
        - Updates belief attributes based on intention, type, and evaluation details
        - Handles different types of intentions (e.g., mobility, economy) and their impact on beliefs
        """

        gender = await self.memory.status.get("gender", "unknown")
        age = await self.memory.status.get("age", "unknown")
        income = await self.memory.status.get("income", "unknown")
        big5 = await self.memory.status.get("big5", {})
        openness = big5.get("openness", 2)
        conscientiousness = big5.get("conscientiousness", 2)
        extraversion = big5.get("extraversion", 2)
        agreeableness = big5.get("agreeableness", 2)
        neuroticism = big5.get("neuroticism", 2)
        hobbies = await self.memory.status.get("hobbies", [])
        hobbies_str = ", ".join(hobbies) if isinstance(hobbies, list) else str(hobbies)
        observation = f"Based on my recent experience of {intention} at {location_category} (ID: {location_id}), I have the following details: {details}."

        await self.poi_belief_update_prompt.format(
            gender=gender,
            age=age,
            income=income,
            openness=openness,
            conscientiousness=conscientiousness,
            extraversion=extraversion,
            agreeableness=agreeableness,
            neuroticism=neuroticism,
            hobbies=hobbies_str,
            observation=observation,
            poi_name=location_id,
            poi_category=location_category,
        )

        retry = 3
        while retry > 0:
            try:
                response = await self.llm.atext_request(
                    self.poi_belief_update_prompt.to_dialog(),
                    response_format={"type": "json_object"},
                    context={
                        "block_name": "NeedsBlock",
                        "func_name": "update_location_belief",
                        "agent_id": self.id,
                    },
                )
                belief_update: Any = json_repair.loads(clean_json_response(response))
                new_price = belief_update.get("price", 0.5)
                new_atmosphere = belief_update.get("atmosphere", 0.5)
                new_satisfaction = belief_update.get("satisfaction", 0.5)
                new_convenience = belief_update.get("convenience", 0.5)
                await self.memory.spatial.update_belief_location(
                    location_id,
                    new_price,
                    new_atmosphere,
                    new_satisfaction,
                    new_convenience,
                )
                get_logger().info(
                    f"Belief updated for location {location_id} with data: {belief_update}"
                )
                break
            except Exception as e:
                get_logger().warning(
                    f"Error updating beliefs from plan evaluation: {str(e)}"
                )
                get_logger().warning(f"Original response: {response}")
                retry -= 1

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

    async def evaluate_and_adjust_needs(self, completed_plan):
        """
        Evaluate plan execution results and adjust satisfaction values.
        - Extracts step evaluations from completed plan
        - Constructs evaluation prompt for LLM
        - Processes LLM response and updates satisfaction values
        - Implements retry logic for invalid responses
        """
        metrics_tool = self.toolbox.get_tool("metrics_actor")
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
