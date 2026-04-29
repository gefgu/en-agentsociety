from typing import Any
import time

from ...agent import AgentToolbox, Block, DotDict
from ...logger import get_logger
from ...memory import Memory


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

            satisfaction_keys = (
                "hunger_satisfaction", "energy_satisfaction",
                "safety_satisfaction", "social_satisfaction",
            )

            def _has_satisfaction_keys(parsed: Any) -> bool:
                if not isinstance(parsed, dict):
                    return False
                # Accept if at least 1 key is present at top level (partial responses are ok)
                if any(k in parsed for k in satisfaction_keys):
                    return True
                # Search any nested dict — handles typos like "current_satisfation"
                # and partial responses (missing 1-2 keys)
                for v in parsed.values():
                    if isinstance(v, dict) and any(k in v for k in satisfaction_keys):
                        return True
                return False

            def _find_satisfaction_dict(parsed: dict) -> dict:
                """Return the dict holding the 4 keys (top-level or any nested dict)."""
                if all(k in parsed for k in satisfaction_keys):
                    return parsed
                for v in parsed.values():
                    if isinstance(v, dict) and all(k in v for k in satisfaction_keys):
                        return v
                return parsed

            result = await self.execute_prompt(
                self.initial_prompt_name,
                {"current_time": current_time},
                func_name="initialize",
                max_retries=2,
                validate=_has_satisfaction_keys,
            )
            if result.success:
                sat = _find_satisfaction_dict(result.parsed)
                await self.memory.status.update_many(
                    {
                        "hunger_satisfaction": float(
                            sat.get("hunger_satisfaction", 0.9)
                        ),
                        "energy_satisfaction": float(
                            sat.get("energy_satisfaction", 0.9)
                        ),
                        "safety_satisfaction": float(
                            sat.get("safety_satisfaction", 0.4)
                        ),
                        "social_satisfaction": float(
                            sat.get("social_satisfaction", 0.6)
                        ),
                    }
                )
            else:
                get_logger().warning(f"NeedsBlock.initialize failed: {result.error}")

            current_plan = await self.memory.status.get("current_plan", False)
            if current_plan:
                history = await self.memory.status.get("plan_history")
                history.append(current_plan)
                await self.memory.status.update_many(
                    {
                        "plan_history": history,
                        "current_plan": None,
                        "execution_context": {},
                    }
                )
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
            satisfaction_keys = {
                "hunger_satisfaction", "energy_satisfaction",
                "safety_satisfaction", "social_satisfaction",
            }
            updates = {
                need_type: new_value
                for need_type, new_value in reflection.items()
                if need_type in satisfaction_keys
            }
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

        satisfaction = await self.memory.status.get_many(
            {
                "hunger_satisfaction": None,
                "energy_satisfaction": None,
                "safety_satisfaction": None,
                "social_satisfaction": None,
            }
        )
        hunger_satisfaction = satisfaction["hunger_satisfaction"]
        energy_satisfaction = satisfaction["energy_satisfaction"]
        safety_satisfaction = satisfaction["safety_satisfaction"]
        social_satisfaction = satisfaction["social_satisfaction"]

        hunger_satisfaction = self._ensure_float(
            hunger_satisfaction, "hunger_satisfaction"
        )
        energy_satisfaction = self._ensure_float(
            energy_satisfaction, "energy_satisfaction"
        )
        safety_satisfaction = self._ensure_float(
            safety_satisfaction, "safety_satisfaction"
        )
        social_satisfaction = self._ensure_float(
            social_satisfaction, "social_satisfaction"
        )

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
        status_values = await self.memory.status.get_many(
            {
                "hunger_satisfaction": None,
                "energy_satisfaction": None,
                "safety_satisfaction": None,
                "social_satisfaction": None,
                "current_plan": None,
                "current_need": None,
            }
        )
        hunger_satisfaction = status_values["hunger_satisfaction"]
        energy_satisfaction = status_values["energy_satisfaction"]
        safety_satisfaction = status_values["safety_satisfaction"]
        social_satisfaction = status_values["social_satisfaction"]

        hunger_satisfaction = self._ensure_float(
            hunger_satisfaction, "hunger_satisfaction"
        )
        energy_satisfaction = self._ensure_float(
            energy_satisfaction, "energy_satisfaction"
        )
        safety_satisfaction = self._ensure_float(
            safety_satisfaction, "safety_satisfaction"
        )
        social_satisfaction = self._ensure_float(
            social_satisfaction, "social_satisfaction"
        )

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

        status_values = await self.memory.status.get_many(
            {
                "current_need": None,
                "hunger_satisfaction": None,
                "energy_satisfaction": None,
                "safety_satisfaction": None,
                "social_satisfaction": None,
            }
        )
        current_need = status_values["current_need"]
        current_hunger = self._ensure_float(
            status_values["hunger_satisfaction"], "hunger_satisfaction"
        )
        current_energy = self._ensure_float(
            status_values["energy_satisfaction"], "energy_satisfaction"
        )
        current_safety = self._ensure_float(
            status_values["safety_satisfaction"], "safety_satisfaction"
        )
        current_social = self._ensure_float(
            status_values["social_satisfaction"], "social_satisfaction"
        )

        satisfaction_keys = {
            "hunger_satisfaction", "energy_satisfaction",
            "safety_satisfaction", "social_satisfaction",
        }

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
            validate=lambda p: isinstance(p, dict) and any(k in p for k in satisfaction_keys),
        )
        if not result.success:
            get_logger().warning(f"NeedsBlock.evaluate_and_adjust_needs failed: {result.error}")
            return

        new_satisfaction = result.parsed
        updates = {
            need_type: new_value
            for need_type, new_value in new_satisfaction.items()
            if need_type in satisfaction_keys
        }
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
                "new_hunger": new_satisfaction.get("hunger_satisfaction", current_hunger),
                "new_energy": new_satisfaction.get("energy_satisfaction", current_energy),
                "new_safety": new_satisfaction.get("safety_satisfaction", current_safety),
                "new_social": new_satisfaction.get("social_satisfaction", current_social),
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
