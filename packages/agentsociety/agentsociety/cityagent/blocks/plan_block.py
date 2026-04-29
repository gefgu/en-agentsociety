from typing import Optional, Tuple

from ...agent import AgentToolbox, Agent, Block, DotDict, ResponseMode
from ...logger import get_logger
from ...memory import Memory


class PlanBlock(Block):
    """A block for generating and managing execution plans through LLM-guided decision making.

    Attributes:
        configurable_fields: List of configurable parameter names
        default_values: Default values for configurable parameters
        fields_description: Human-readable descriptions for configurable parameters
        guidance_options: Predefined options mapped to specific needs
        max_plan_steps: Maximum allowed steps in generated plans (configurable)
    """

    name = "PlanBlock"

    def __init__(
        self,
        agent: Agent,
        toolbox: AgentToolbox,
        agent_memory: Memory,
        agent_context: DotDict,
        max_plan_steps: int = 6,
    ):
        """Initialize PlanBlock with required components.

        Args:
            llm: Language Model interface for decision making
            environment: Environment for contextual data
            memory: Agent's memory storage for status tracking
        """
        super().__init__(toolbox=toolbox, agent_memory=agent_memory)
        self.set_agent(agent)
        self.context = agent_context
        self.guidance_prompt_name = "plan_guidance_selection"
        self.detail_prompt_name = "plan_detailed_generation"
        self.trigger_time = 0
        self.token_consumption = 0
        self.guidance_options = {
            "hungry": ["Eat at home", "Eat outside", "Eat at current location"],
            "tired": ["Sleep at home"],
            "safe": ["Work", "Shopping"],
            "social": ["Contact with friends"],
            "whatever": ["leisure and entertainment", "other", "stay at home"],
        }

        self.context["max_plan_steps"] = max_plan_steps

    async def select_guidance(self, current_need: str, scheduled_block: Optional[dict] = None) -> Optional[Tuple[dict, str]]:
        """Select optimal guidance option using Theory of Planned Behavior evaluation.

        Args:
            current_need: The agent's current need to fulfill
            scheduled_block: The currently scheduled block from daily schedule (if any)

        Returns:
            Optional[tuple[dict, str]]: Selected option with TPB evaluation scores and reasoning. None if no guidance option is selected by bad response from LLM.
        """
        cognition = None
        status_values = await self.memory.status.get_many(
            {
                "position": None,
                "home": None,
                "work": None,
                "location_knowledge": None,
                "consumption": None,
            }
        )
        position_now = status_values["position"]
        home_location = status_values["home"]
        work_location = status_values["work"]
        location_knowledge = status_values["location_knowledge"]
        known_locations = [item["id"] for item in location_knowledge.values()]
        id_to_name = {
            info["id"]: f"{name}({info['description']})"
            for name, info in location_knowledge.items()
        }
        current_location = "Outside"
        if (
            "aoi_position" in position_now
            and position_now["aoi_position"] == home_location["aoi_position"]
        ):
            current_location = "At home"
        elif (
            "aoi_position" in position_now
            and position_now["aoi_position"] == work_location["aoi_position"]
        ):
            current_location = "At workplace"
        elif (
            "aoi_position" in position_now
            and position_now["aoi_position"] in known_locations
        ):
            current_location = id_to_name[position_now["aoi_position"]]
        day, current_time = self.environment.get_datetime(format_time=True)
        options = self.guidance_options.get(current_need, [])
        if len(options) == 0:
            options = "Do things that can satisfy your needs or actions."

        # **NEW: Add scheduled activity to options if exists**
        schedule_context = ""
        if scheduled_block:
            activity = scheduled_block.get("activity", "")
            if activity == "[EMPTY]":
                schedule_context = f"\nScheduled: Flexible time block - '{scheduled_block.get('description', '')}' (fill with activity that best satisfies your needs)"
            else:
                schedule_context = f"\nScheduled: {activity} - {scheduled_block.get('description', '')} (consider following schedule)"
                # Add scheduled activity as a high-priority option
                if isinstance(options, list):
                    options = [f"{activity} (scheduled)"] + options

        def validate_guidance(parsed):
            if "selected_option" not in parsed or "evaluation" not in parsed:
                return False
            eval_keys = {"attitude", "subjective_norm", "perceived_control", "reasoning"}
            return eval_keys.issubset(parsed["evaluation"].keys())

        result = await self.execute_prompt(
            self.guidance_prompt_name,
            {
                "current_need": current_need,
                "weather": self.environment.sense("weather"),
                "temperature": self.environment.sense("temperature"),
                "other_info": self.environment.sense("other_information") + schedule_context,
                "options": options,
                "current_location": current_location,
                "current_time": current_time,
                "consumption_level": status_values["consumption"],
            },
            func_name="select_guidance",
            max_retries=2,
            validate=validate_guidance,
        )

        if not result.success:
            get_logger().warning(f"PlanBlock: Guidance selection failed: {result.error}")
            return None

        cognition = f"I choose to {result.parsed['selected_option']} because {result.parsed['evaluation']['reasoning']}"
        return result.parsed, cognition

    async def generate_detailed_plan(self) -> Optional[dict]:
        """Generate executable steps for selected guidance option.

        Returns:
            dict: Structured plan with target and typed execution steps. None if no plan is generated by bad response from LLM.
        """
        def validate_plan(parsed):
            if "plan" not in parsed or "steps" not in parsed["plan"]:
                return False
            return all(
                "intention" in step and "type" in step
                for step in parsed["plan"]["steps"]
            )

        result = await self.execute_prompt(
            self.detail_prompt_name,
            {
                **dict(self.context),
                "weather": self.context.get("weather", self.environment.sense("weather")),
                "temperature": self.context.get("temperature", self.environment.sense("temperature")),
                "other_information": self.context.get("other_information", self.environment.sense("other_information")),
                "current_position": self.context.get("current_position", "unknown"),
                "current_time": self.context.get("current_time", self.environment.get_datetime(format_time=True)[1]),
                "current_thought": self.context.get("current_thought", await self.memory.status.get("thought", "")),
                "plan_target": self.context.get("plan_target", "unknown"),
                "max_plan_steps": self.context.get("max_plan_steps", 6),
            },
            func_name="generate_detailed_plan",
            response_mode=ResponseMode.EXTRACT_JSON,
            max_retries=2,
            validate=validate_plan,
        )

        if not result.success:
            get_logger().warning(f"PlanBlock: Detailed plan generation failed: {result.error}")
            return None

        # Normalise: ensure "target" exists (some LLMs omit it)
        result.parsed["plan"].setdefault("target", "")
        return result.parsed

    async def _get_scheduled_block_for_current_time(self) -> Optional[dict]:
        """Get the currently scheduled block from daily schedule."""
        day, time_seconds = self.environment.get_datetime(format_time=False)
        daily_schedule = await self.memory.status.get("daily_schedule")
        
        if not daily_schedule or daily_schedule.get("day") != day:
            return None
        
        # Convert current time to minutes since midnight
        current_minutes = time_seconds // 60
        
        # Find matching block
        for block in daily_schedule.get("blocks", []):
            start_time_str = block.get("start_time", "")
            try:
                # Parse HH:MM format
                hours, minutes = map(int, start_time_str.split(":"))
                block_start_minutes = hours * 60 + minutes
                block_duration = block.get("duration", 0)
                block_end_minutes = block_start_minutes + block_duration
                
                # Check if current time falls within this block
                if block_start_minutes <= current_minutes < block_end_minutes:
                    return block
            except Exception as e:
                get_logger().warning(f"Error parsing block time {start_time_str}: {e}")
                continue
        
        return None

    async def forward(self):
        """Main workflow: Guidance selection -> Plan generation -> Memory update"""
        cognition = None
        
        # **NEW: Check daily schedule for guidance**
        current_scheduled_block = await self._get_scheduled_block_for_current_time()
        
        # Step 1: Select guidance plan
        current_need = await self.memory.status.get("current_need")
        select_guidance = await self.select_guidance(current_need, current_scheduled_block)  # Pass schedule context
        if not select_guidance:
            return None
        guidance_result, cognition = select_guidance
        self.context["plan_target"] = guidance_result["selected_option"]

        # Step 2: Generate detailed plan
        detailed_plan = await self.generate_detailed_plan()

        if not detailed_plan:
            await self.memory.status.update("current_plan", None)
            return None

        # Step 3: Update plan and current step
        steps = detailed_plan["plan"]["steps"]
        for step in steps:
            step["evaluation"] = {"status": "pending", "details": ""}

        plan = {
            "target": detailed_plan["plan"]["target"],
            "steps": steps,
            "index": 0,
            "completed": False,
            "failed": False,
            "stream_nodes": [],
            "guidance": guidance_result,  # Save the evaluation result of the plan selection
        }
        formated_steps = "\n".join(
            [f"{i}. {step['intention']}" for i, step in enumerate(plan["steps"], 1)]
        )
        formated_plan = f"""
Overall Target: {plan['target']}
Execution Steps: \n{formated_steps}
        """
        _, plan["start_time"] = self.environment.get_datetime(format_time=True)
        await self.memory.status.update_many(
            {
                "current_plan": plan,
                "execution_context": {"plan": formated_plan},
            }
        )
        await self.memory.stream.add(
            topic="cognition",
            description=cognition,
        )
        return cognition
