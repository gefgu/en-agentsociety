# /mnt/raid5/gustavo/citysim/packages/agentsociety/agentsociety/cityagent/blocks/daily_schedule_block.py

from typing import Any, Optional
import json_repair

from ...agent import AgentToolbox, Block, Agent
from ...logger import get_logger
from ...memory import Memory
from .utils import clean_json_response


class DailyScheduleBlock(Block):
    """
    Generates and manages value-driven daily schedules using recursive time-block decomposition.

    Schedules are created once per day with:
    1. Mandatory high-priority tasks (sleep, work)
    2. Medium-priority tasks (meals, hygiene)
    3. [EMPTY] blocks filled at execution time via value-driven planning
    """

    name = "DailyScheduleBlock"
    description = "Generates value-driven daily schedules"
    NeedAgent = True

    def __init__(
        self,
        agent: Agent,
        toolbox: AgentToolbox,
        agent_memory: Memory,
    ):
        super().__init__(toolbox=toolbox, agent_memory=agent_memory)
        self.set_agent(agent)
        self.daily_schedule_prompt_name = "daily_schedule_generation"
        self.empty_block_prompt_name = "empty_block_filling"

    async def _generate_daily_schedule(self, day: int) -> Optional[dict]:
        """
        Generate a complete daily schedule for the given day.

        Returns:
            dict with structure: {"day": int, "blocks": [...], "generated_at": str}
        """
        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        _, current_time = self.environment.get_datetime(format_time=True)

        required_fields = self.prompt_manager.get_required_fields(
            self.daily_schedule_prompt_name
        )
        state_dict = await self.prompt_manager.build_agent_state(
            required_fields=required_fields,
            context={
                "day": day,
                "current_time": current_time,
            },
            memory=self.memory,
        )
        dialog = self.prompt_manager.format_prompt_to_dialog(
            self.daily_schedule_prompt_name, state_dict
        )

        schedule = {}
        retry = 3
        while retry > 0:
            try:
                get_logger().info(
                    f"Agent {self.agent.id}: Requesting daily schedule generation for day {day}"
                )
                response = await self.llm.atext_request(
                    dialog,
                    response_format={"type": "json_object"},
                    context={
                        "block_name": self.name,
                        "func_name": "generate_daily_schedule",
                        "agent_id": self.agent.id,
                    },
                )

                result: Any = json_repair.loads(clean_json_response(response))
                if "blocks" not in result or not isinstance(result["blocks"], list):
                    raise ValueError("Invalid daily schedule format - missing blocks")

                for block in result["blocks"]:
                    if not all(
                        k in block for k in ["start_time", "duration", "activity"]
                    ):
                        raise ValueError(
                            "Each block must have start_time, duration, and activity"
                        )

                schedule = {
                    "day": day,
                    "blocks": result["blocks"],
                    "generated_at": current_time,
                }

                get_logger().debug(
                    f"Agent {self.agent.id}: Generated daily schedule for day {day} with {len(result['blocks'])} blocks"
                )
                retry = 0

            except Exception as e:
                get_logger().warning(
                    f"Error parsing daily schedule response: {str(e)}, retry={retry}"
                )
                retry -= 1

        return schedule

    async def _fill_empty_block(self, block: dict) -> Optional[dict]:
        """
        Fill an [EMPTY] block with value-driven activity selection.

        Args:
            block: The empty block to fill (with start_time, duration, description)

        Returns:
            dict with selected activity details
        """
        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        # Get current location
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

        _, current_time = self.environment.get_datetime(format_time=True)

        required_fields = self.prompt_manager.get_required_fields(
            self.empty_block_prompt_name
        )
        state_dict = await self.prompt_manager.build_agent_state(
            required_fields=required_fields,
            context={
                "current_time": current_time,
                "current_location": current_location,
                "block_start_time": block.get("start_time", ""),
                "block_duration": block.get("duration", 60),
                "block_description": block.get("description", ""),
            },
            memory=self.memory,
        )
        dialog = self.prompt_manager.format_prompt_to_dialog(
            self.empty_block_prompt_name, state_dict
        )

        response = await self.llm.atext_request(
            dialog,
            response_format={"type": "json_object"},
            context={
                "block_name": self.name,
                "func_name": "_fill_empty_block",
                "agent_id": self.agent.id,
            },
        )

        retry = 3
        while retry > 0:
            try:
                result: Any = json_repair.loads(clean_json_response(response))
                if "selected" not in result or "activity" not in result["selected"]:
                    raise ValueError("Invalid empty block fill format")

                return result["selected"]

            except Exception as e:
                get_logger().warning(
                    f"Error parsing empty block fill response: {str(e)}, retry={retry}"
                )
                retry -= 1

        return None

    async def get_current_scheduled_block(self) -> Optional[dict]:
        """
        Get the scheduled block for the current time.

        Returns:
            The block that matches current time, or None if no schedule exists
        """
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

    async def forward(self) -> Optional[str]:
        """
        Main entry point: Generate daily schedule once per day, check if regeneration is needed.

        Returns:
            Cognition string if schedule was generated, None otherwise
        """
        day, _ = self.environment.get_datetime(format_time=False)
        daily_schedule = await self.memory.status.get("daily_schedule", {})

        # Check if we need to generate a new schedule for today
        if daily_schedule is None or daily_schedule.get("day", -99) != day:
            get_logger().info(
                f"Agent {self.agent.id}: Generating daily schedule for day {day}"
            )
            new_schedule = await self._generate_daily_schedule(day)

            if new_schedule:
                await self.memory.status.update("daily_schedule", new_schedule)

                # Count empty blocks
                empty_count = sum(
                    1 for b in new_schedule["blocks"] if b["activity"] == "[EMPTY]"
                )
                total_count = len(new_schedule["blocks"])

                cognition = f"I planned my day with {total_count} time blocks ({empty_count} flexible blocks for spontaneous activities)"
                await self.memory.stream.add(
                    topic="cognition",
                    description=cognition,
                )
                return cognition

        return None
