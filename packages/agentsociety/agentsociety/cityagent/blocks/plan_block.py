import time
from typing import Any, Optional, Tuple


import json_repair

from ...agent import AgentToolbox, Agent, Block, DotDict
from ...logger import get_logger
from ...memory import Memory
from .utils import clean_json_response


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
        position_now = await self.memory.status.get("position")
        home_location = await self.memory.status.get("home")
        work_location = await self.memory.status.get("work")
        location_knowledge = await self.memory.status.get("location_knowledge")
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

        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        required_fields = self.prompt_manager.get_required_fields(
            self.guidance_prompt_name
        )
        state_dict = await self.prompt_manager.build_agent_state(
            required_fields=required_fields,
            context={
                "current_need": current_need,
                "weather": self.environment.sense("weather"),
                "temperature": self.environment.sense("temperature"),
                "other_info": self.environment.sense("other_information") + schedule_context,
                "options": options,
                "current_location": current_location,
                "current_time": current_time,
                "consumption_level": await self.memory.status.get("consumption"),
            },
            memory=self.memory,
        )
        dialog = self.prompt_manager.format_prompt_to_dialog(
            self.guidance_prompt_name, state_dict
        )

        response = await self.llm.atext_request(
            dialog,
            response_format={"type": "json_object"},
            context={
                "block_name": self.name,
                "func_name": "select_guidance",
                "agent_id": self.agent.id,
            },
        )

        retry = 3
        while retry > 0:
            try:
                result: Any = json_repair.loads(clean_json_response(response))
                if "selected_option" not in result or "evaluation" not in result:
                    raise ValueError("Invalid guidance selection format")
                if (
                    "attitude" not in result["evaluation"]
                    or "subjective_norm" not in result["evaluation"]
                    or "perceived_control" not in result["evaluation"]
                    or "reasoning" not in result["evaluation"]
                ):
                    raise ValueError(
                        "Evaluation must include attitude, subjective_norm, perceived_control, and reasoning"
                    )
                cognition = f"I choose to {result['selected_option']} because {result['evaluation']['reasoning']}"
                return result, cognition
            except Exception as e:
                get_logger().warning(
                    f"Error parsing guidance selection response: {str(e)}"
                )
                retry -= 1
        return None

    async def generate_detailed_plan(self) -> Optional[dict]:
        """Generate executable steps for selected guidance option.

        Args:
            plan_target: The target of the plan

        Returns:
            dict: Structured plan with target and typed execution steps. None if no plan is generated by bad response from LLM.
        """
        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        required_fields = self.prompt_manager.get_required_fields(self.detail_prompt_name)
        state_dict = await self.prompt_manager.build_agent_state(
            required_fields=required_fields,
            context={
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
            memory=self.memory,
        )
        dialog = self.prompt_manager.format_prompt_to_dialog(
            self.detail_prompt_name, state_dict
        )

        response = await self.llm.atext_request(
            dialog,
            context={
                "block_name": self.name,
                "func_name": "generate_detailed_plan",
                "agent_id": self.agent.id,
            },
        )

        retry = 3
        while retry > 0:
            try:
                result: Any = json_repair.loads(clean_json_response(response))
                if (
                    "plan" not in result
                    or "target" not in result["plan"]
                    or "steps" not in result["plan"]
                ):
                    raise ValueError("Invalid plan format")
                for step in result["plan"]["steps"]:
                    if "intention" not in step or "type" not in step:
                        raise ValueError("Each step must have an intention and a type")
                return result
            except Exception as e:
                get_logger().warning(
                    f"Error parsing detailed plan: {str(e)} with response={response}"
                )
                retry -= 1
        return None

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
        await self.memory.status.update("current_plan", plan)
        await self.memory.status.update("execution_context", {"plan": formated_plan})
        await self.memory.stream.add(
            topic="cognition",
            description=cognition,
        )
        return cognition
