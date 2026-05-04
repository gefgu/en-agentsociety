from collections.abc import Mapping
from typing import Any
import time

import json_repair
from pydantic import BaseModel

from ...agent import AgentToolbox, Block, DotDict
from ...logger import get_logger
from ...memory import Memory


SATISFACTION_KEYS = (
    "hunger_satisfaction",
    "energy_satisfaction",
    "safety_satisfaction",
    "social_satisfaction",
)

SATISFACTION_DEFAULTS = {
    "hunger_satisfaction": 0.9,
    "energy_satisfaction": 0.9,
    "safety_satisfaction": 0.4,
    "social_satisfaction": 0.6,
}


def _coerce_satisfaction_value(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        coerced = float(value)
    except (TypeError, ValueError):
        return None
    if 0 <= coerced <= 1:
        return coerced
    return None


def _as_mapping(value: Any) -> dict[str, Any] | None:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str) and "{" in value and "}" in value:
        try:
            repaired = json_repair.loads(value)
        except Exception:
            return None
        if isinstance(repaired, Mapping):
            return dict(repaired)
    return None


def _find_complete_satisfaction_dict(parsed: Any) -> dict[str, float] | None:
    """Find a complete satisfaction dict in top-level or nested LLM output."""
    parsed_mapping = _as_mapping(parsed)
    if parsed_mapping is None:
        return None

    if all(key in parsed_mapping for key in SATISFACTION_KEYS):
        coerced = {
            key: _coerce_satisfaction_value(parsed_mapping.get(key))
            for key in SATISFACTION_KEYS
        }
        if all(value is not None for value in coerced.values()):
            return {key: float(value) for key, value in coerced.items()}

    for value in parsed_mapping.values():
        candidate = _find_complete_satisfaction_dict(value)
        if candidate is not None:
            return candidate

    return None


def _has_complete_satisfaction_dict(parsed: Any) -> bool:
    return _find_complete_satisfaction_dict(parsed) is not None


def _extract_valid_satisfaction_updates(parsed: Any) -> dict[str, float]:
    parsed_mapping = _as_mapping(parsed)
    if parsed_mapping is None:
        return {}

    updates: dict[str, float] = {}
    for field_name in SATISFACTION_KEYS:
        if field_name not in parsed_mapping:
            continue
        value = _coerce_satisfaction_value(parsed_mapping.get(field_name))
        if value is not None:
            updates[field_name] = value
    return updates


def _has_valid_satisfaction_update(parsed: Any) -> bool:
    return bool(_extract_valid_satisfaction_updates(parsed))


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
        self.evaluation_prompt_name = "needs_evaluation"
        self.initial_prompt_name = "needs_initialize"
        self.reflection_prompt_name = "needs_reflection"
        self.poi_belief_update_prompt_name = "needs_poi_observation"
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

    def _ensure_float(self, value, field_name: str) -> float:
        if value is None:
            get_logger().warning(f"{field_name} is None, using default 0.5")
            return 0.5
        if isinstance(value, str):
            try:
                get_logger().warning(
                    f"{field_name} came back as string '{value}' from memory, converting to float"
                )
                return float(value)
            except (ValueError, TypeError):
                get_logger().warning(
                    f"Failed to convert {field_name}='{value}' to float, using default 0.5"
                )
                return 0.5
        if isinstance(value, (int, float)):
            return float(value)
        get_logger().warning(
            f"{field_name} has unexpected type {type(value)}, using default 0.5"
        )
        return 0.5

    async def _get_normalized_satisfaction(self) -> dict[str, float]:
        raw_values = await self.memory.status.get_many(SATISFACTION_DEFAULTS)
        normalized: dict[str, float] = {}
        repaired_fields: list[str] = []

        for field_name, default_value in SATISFACTION_DEFAULTS.items():
            raw_value = raw_values.get(field_name)
            normalized_value = _coerce_satisfaction_value(raw_value)
            if normalized_value is None:
                normalized_value = default_value
            normalized[field_name] = normalized_value
            if raw_value != normalized_value:
                repaired_fields.append(field_name)

        if repaired_fields:
            await self.memory.status.update_many(normalized)
            get_logger().warning(
                "Repaired satisfaction memory values for fields: "
                f"{', '.join(repaired_fields)}"
            )

        return normalized

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
            _, current_time = self.environment.get_datetime(format_time=True)

            result = await self.execute_prompt(
                self.initial_prompt_name,
                {"current_time": current_time},
                func_name="initialize",
                max_retries=2,
                validate=_has_complete_satisfaction_dict,
            )
            initialized_successfully = False
            if result.success:
                sat = _find_complete_satisfaction_dict(result.parsed)
                if sat is None:
                    get_logger().warning(
                        "NeedsBlock.initialize returned success without complete satisfaction values"
                    )
                else:
                    await self.memory.status.update_many(sat)
                    initialized_successfully = True
            else:
                get_logger().warning(f"NeedsBlock.initialize failed: {result.error}")

            current_plan = await self.memory.status.get("current_plan", False)
            if current_plan:
                history = await self.memory.status.get("plan_history")
                if not isinstance(history, list):
                    get_logger().warning(f"plan_history is not a list ({type(history).__name__}), resetting to []")
                    history = []
                history.append(current_plan)
                await self.memory.status.update_many(
                    {
                        "plan_history": history,
                        "current_plan": None,
                        "execution_context": {},
                    }
                )
            self.initialized = initialized_successfully

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

        result = await self.execute_prompt(
            self.reflection_prompt_name,
            {"intervention_message": intervention, "current_action": action_message},
            func_name="reflect_to_intervention",
        )
        if not result.success:
            get_logger().warning(f"NeedsBlock.reflect_to_intervention failed: {result.error}")
            return None
        reflection = result.parsed
        if "do_something" in reflection:
            self._need_to_do = reflection.get("description")
        else:
            updates = _extract_valid_satisfaction_updates(reflection)
            if updates:
                await self.memory.status.update_many(updates)

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

        satisfaction = await self._get_normalized_satisfaction()
        hunger_satisfaction = satisfaction["hunger_satisfaction"]
        energy_satisfaction = satisfaction["energy_satisfaction"]
        safety_satisfaction = satisfaction["safety_satisfaction"]
        social_satisfaction = satisfaction["social_satisfaction"]

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
        await self.memory.status.update_many(
            {
                "hunger_satisfaction": hunger_satisfaction,
                "energy_satisfaction": energy_satisfaction,
                "safety_satisfaction": safety_satisfaction,
                "social_satisfaction": social_satisfaction,
            }
        )

    async def update_when_plan_completed(self):
        # Check if there is any ongoing plan
        current_plan = await self.memory.status.get("current_plan")
        if current_plan and (
            current_plan.get("completed") or current_plan.get("failed")
        ):
            if self.agent.params.simulation_mode == "citysim":
                await self.update_poi_beliefs_from_plan(current_plan)

            # Evaluate the execution process of the plan and adjust needs
            status_values = await self.memory.status.get_many(
                {
                    "current_need": None,
                    "plan_history": None,
                }
            )
            pre_need = status_values["current_need"]
            # evaluate plan execution and adjust needs
            await self.evaluate_and_adjust_needs(current_plan)
            # add completed plan to history
            history = status_values["plan_history"]
            history.append(current_plan)
            await self.memory.status.update_many(
                {
                    "plan_history": history,
                    "current_plan": None,
                    "execution_context": {},
                }
            )
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

        observation = f"Based on my recent experience of {intention} at {location_category} (ID: {location_id}), I have the following details: {details}."

        result = await self.execute_prompt(
            self.poi_belief_update_prompt_name,
            {
                "observation": observation,
                "poi_name": location_id,
                "poi_category": location_category,
            },
            func_name="update_location_belief",
            max_retries=2,
            validate=lambda p: isinstance(p, dict) and any(
                k in p for k in ("price", "atmosphere", "satisfaction", "convenience")
            ),
        )
        if result.success:
            b = result.parsed
            await self.memory.spatial.update_belief_location(
                location_id,
                b.get("price", 0.5),
                b.get("atmosphere", 0.5),
                b.get("satisfaction", 0.5),
                b.get("convenience", 0.5),
            )
            get_logger().info(f"Belief updated for location {location_id} with data: {b}")
        else:
            get_logger().warning(f"NeedsBlock.update_location_belief failed: {result.error}")

    async def determine_current_need(self):
        """
        Determine agent's current dominant need based on:
        - Satisfaction thresholds
        - Need priority hierarchy (hungry > tired > safe > social)
        - Workday requirements
        - Ongoing plan interruptions
        """
        cognition = None

        # Get satisfaction values and ensure they are floats (may come as strings from DB)
        satisfaction = await self._get_normalized_satisfaction()
        status_values = await self.memory.status.get_many(
            {
                "current_plan": None,
                "current_need": None,
            }
        )
        hunger_satisfaction = satisfaction["hunger_satisfaction"]
        energy_satisfaction = satisfaction["energy_satisfaction"]
        safety_satisfaction = satisfaction["safety_satisfaction"]
        social_satisfaction = satisfaction["social_satisfaction"]

        # If needs adjustment is required, update current need
        # The adjustment scheme is to adjust the need if the current need is empty, or a higher priority need appears
        current_plan = status_values["current_plan"]
        current_need = status_values["current_need"]

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
                if not isinstance(history, list):
                    get_logger().warning(f"plan_history is not a list ({type(history).__name__}), resetting to []")
                    history = []
                history.append(current_plan)
                await self.memory.stream.add(
                    topic="cognition",
                    description=f"I need to change my plan because the need of [{new_need}] is more important than [{current_need}]",
                )
                cognition = f"I need to change my plan because the need of [{new_need}] is more important than [{current_need}]"
                self.context.current_intention = new_need
                await self.memory.status.update_many(
                    {
                        "current_need": new_need,
                        "plan_history": history,
                        "current_plan": None,
                        "execution_context": {},
                    }
                )

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
        db_tool = self.toolbox.get_tool("db_actor")

        evaluation_results = []
        for step in completed_plan["steps"]:
            if "evaluation" in step["evaluation"]:
                eva_ = step["evaluation"]["evaluation"]
            else:
                eva_ = "Plan failed or skipped, not completed"
            evaluation_results.append(f"- {step['intention']} ({step['type']}): {eva_}")
        evaluation_results_str = "\n".join(evaluation_results)

        current_need = await self.memory.status.get("current_need", None)
        satisfaction = await self._get_normalized_satisfaction()
        current_hunger = satisfaction["hunger_satisfaction"]
        current_energy = satisfaction["energy_satisfaction"]
        current_safety = satisfaction["safety_satisfaction"]
        current_social = satisfaction["social_satisfaction"]

        result = await self.execute_prompt(
            self.evaluation_prompt_name,
            {
                "current_need": current_need,
                "plan_target": completed_plan["target"],
                "evaluation_results": evaluation_results_str,
                "hunger_satisfaction": current_hunger,
                "energy_satisfaction": current_energy,
                "safety_satisfaction": current_safety,
                "social_satisfaction": current_social,
            },
            func_name="evaluate_and_adjust_needs",
            max_retries=2,
            validate=_has_valid_satisfaction_update,
        )
        if not result.success:
            get_logger().warning(f"NeedsBlock.evaluate_and_adjust_needs failed: {result.error}")
            return

        new_satisfaction = result.parsed
        updates = _extract_valid_satisfaction_updates(new_satisfaction)
        if updates:
            await self.memory.status.update_many(updates)

        if db_tool:
            record = {
                "agent_id": self.id,
                "prompt": result.state_dict,
                "current_need": current_need,
                "current_hunger": current_hunger,
                "current_energy": current_energy,
                "current_safety": current_safety,
                "current_social": current_social,
                "new_hunger": updates.get("hunger_satisfaction", current_hunger),
                "new_energy": updates.get("energy_satisfaction", current_energy),
                "new_safety": updates.get("safety_satisfaction", current_safety),
                "new_social": updates.get("social_satisfaction", current_social),
                "timestamp": int(time.time()),
                "actor": "llm",
            }
            db_tool.get_tool().insert_adjust_needs_record.remote(record)

    async def update_need_fulfillment(self):
        """Only called in new days"""
        day, t = self.environment.get_datetime()
        status_values = await self.memory.status.get_many(
            {
                "need_fulfillment": 0,
                "mean_need_fulfillment": 0,
            }
        )
        current_fulfillment = status_values["need_fulfillment"]
        mean_need_fulfillment = status_values["mean_need_fulfillment"]

        new_mean_fulfillment = (mean_need_fulfillment * day + current_fulfillment) / (
            day + 1
        )

        await self.memory.status.update_many(
            {
                "mean_need_fulfillment": new_mean_fulfillment,
                "need_fulfillment": 0,
            }
        )

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
