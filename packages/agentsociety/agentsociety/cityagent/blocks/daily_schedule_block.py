# /mnt/raid5/gustavo/citysim/packages/agentsociety/agentsociety/cityagent/blocks/daily_schedule_block.py

import json
from typing import Any, Optional
import json_repair

from ...agent import AgentToolbox, Block, FormatPrompt, DotDict, Agent
from ...logger import get_logger
from ...memory import Memory
from .utils import clean_json_response


DAILY_SCHEDULE_GENERATION_PROMPT = """You are an intelligent agent's daily schedule system. Generate a complete daily schedule using recursive time-block decomposition.

Current day: {day}
Current time: {current_time}

Profile Information:
- Occupation: {occupation}
- Age: {age}
- Income: {income}
- Household type: {household}
- Life stage: {life_stage}
- Hobbies: {hobbies}
- Goals: {goals}

Big Five Personality Traits (1=Low, 2=Medium, 3=High):
- Openness: {openness}
- Conscientiousness: {conscientiousness}
- Extraversion: {extraversion}
- Agreeableness: {agreeableness}
- Neuroticism: {neuroticism}

Behavioral Preferences:
- Chronotype: {chronotype} (early_bird: wakes ~6am, standard: ~7-8am, night_owl: ~10am)
- Work Ethic: {work_ethic} (0.0=Low work priority, 1.0=High work priority/workaholic)
- Social Frequency: {social_frequency} (0.0=Prefers solitude, 1.0=Seeks frequent social interaction)
- Leisure Preference: {leisure_preference} (outdoor/indoor/social/solitary)

Current Needs (0-1, lower = more urgent):
- Hunger: {hunger_satisfaction}
- Energy: {energy_satisfaction}
- Safety: {safety_satisfaction}
- Social: {social_satisfaction}

**Instructions:**
1. Start with MANDATORY high-priority activities (sleep, work) based on chronotype, work_ethic, and occupation
2. Recursively fill time blocks with MEDIUM-priority tasks (meals, hygiene) 
3. Leave some blocks as [EMPTY] for value-driven planning at execution time (leisure, hobbies, socializing)
4. Each block must have: start_time (HH:MM), duration (minutes), activity/intention
5. If an activity doesn't fill the entire block, subdivide it
6. Consider current needs when scheduling - low satisfaction = higher priority

**Activity Types:**
- "sleep": Sleep/rest at home
- "work": Work-related activities
- "meal": Eating (breakfast/lunch/dinner)
- "hygiene": Personal care activities
- "[EMPTY]": Unfilled block for runtime value-driven planning (will be filled based on state/needs/location)

**Response Format (JSON only):**
{{
    "blocks": [
        {{"start_time": "06:00", "duration": 30, "activity": "hygiene", "description": "Morning routine"}},
        {{"start_time": "06:30", "duration": 30, "activity": "meal", "description": "Breakfast"}},
        {{"start_time": "07:00", "duration": 60, "activity": "[EMPTY]", "description": "Free time before work"}},
        {{"start_time": "08:00", "duration": 480, "activity": "work", "description": "At workplace"}},
        {{"start_time": "16:00", "duration": 60, "activity": "[EMPTY]", "description": "Evening leisure"}},
        {{"start_time": "17:00", "duration": 60, "activity": "meal", "description": "Dinner"}},
        {{"start_time": "18:00", "duration": 120, "activity": "[EMPTY]", "description": "Evening activities"}},
        {{"start_time": "20:00", "duration": 30, "activity": "hygiene", "description": "Evening routine"}},
        {{"start_time": "20:30", "duration": 570, "activity": "sleep", "description": "Night sleep"}}
    ]
}}

DO NOT INCLUDE COMMENTS OR EXTRA TEXT. RETURN ONLY VALID JSON.
"""


EMPTY_BLOCK_FILLING_PROMPT = """You are an intelligent agent's value-driven activity planner. Fill this [EMPTY] time block with the best activity to satisfy your intrinsic desires.

Current Context:
- Current time: {current_time}
- Current location: {current_location}
- Current emotion: {emotion_types}
- Current thought: {thought}

Available Empty Block:
- Start time: {block_start_time}
- Duration: {block_duration} minutes
- Original description: {block_description}

Current Needs (0-1, lower = more urgent):
- Hunger: {hunger_satisfaction}
- Energy: {energy_satisfaction}
- Safety: {safety_satisfaction}
- Social: {social_satisfaction}

Profile:
- Occupation: {occupation}
- Age: {age}
- Household: {household}
- Life stage: {life_stage}
- Hobbies: {hobbies}
- Goals: {goals}

Big Five Personality Traits (1=Low, 2=Medium, 3=High):
- Openness: {openness}
- Conscientiousness: {conscientiousness}
- Extraversion: {extraversion}
- Agreeableness: {agreeableness}
- Neuroticism: {neuroticism}

Behavioral Preferences:
- Social Frequency: {social_frequency}
- Leisure Preference: {leisure_preference}

**Task:**
Generate and evaluate multiple candidate activities (2-4 options). Select the one that best satisfies your intrinsic desires according to Maslow's Hierarchy.

Consider:
1. Most urgent needs (lowest satisfaction scores)
2. Your personality traits and preferences
3. Current location and time constraints
4. Your hobbies and goals

**Response Format (JSON only):**
{{
    "candidates": [
        {{"activity": "Contact friends", "expected_need": "social", "expected_satisfaction_gain": 0.3, "reasoning": "Low social satisfaction"}},
        {{"activity": "Practice photography (hobby)", "expected_need": "safety", "expected_satisfaction_gain": 0.2, "reasoning": "Aligns with hobbies and goals"}},
        {{"activity": "Exercise at park", "expected_need": "energy", "expected_satisfaction_gain": 0.15, "reasoning": "Outdoor leisure preference"}}
    ],
    "selected": {{
        "activity": "Contact friends",
        "type": "social",
        "reasoning": "Social need is most urgent (0.3) and activity expected to provide highest satisfaction gain"
    }}
}}

DO NOT INCLUDE COMMENTS. RETURN ONLY VALID JSON.
"""


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
        daily_schedule_prompt: str = DAILY_SCHEDULE_GENERATION_PROMPT,
        empty_block_prompt: str = EMPTY_BLOCK_FILLING_PROMPT,
    ):
        super().__init__(toolbox=toolbox, agent_memory=agent_memory)
        self.set_agent(agent)
        self.daily_schedule_prompt = FormatPrompt(
            template=daily_schedule_prompt, memory=agent_memory
        )
        self.empty_block_prompt = FormatPrompt(
            template=empty_block_prompt, memory=agent_memory
        )

    async def _generate_daily_schedule(self, day: int) -> Optional[dict]:
        """
        Generate a complete daily schedule for the given day.

        Returns:
            dict with structure: {"day": int, "blocks": [...], "generated_at": str}
        """
        # Get Big Five personality traits
        big5 = await self.memory.status.get("big5", {})

        # Get profile information
        household = await self.memory.status.get("household", "unknown")
        life_stage = await self.memory.status.get("life_stage", "unknown")
        hobbies = await self.memory.status.get("hobbies", [])
        hobbies_str = ", ".join(hobbies) if isinstance(hobbies, list) else str(hobbies)
        goals = await self.memory.status.get("goals", [])
        goals_str = ", ".join(goals) if isinstance(goals, list) else str(goals)

        # Get preferences
        preferences = await self.memory.status.get("preferences", {})
        chronotype = preferences.get("chronotype", "standard")
        work_ethic = preferences.get("work_ethic", 0.5)
        social_frequency = preferences.get("social_frequency", 0.5)
        leisure_preference = preferences.get("leisure_preference", "indoor")

        # Get current needs
        hunger_sat = await self.memory.status.get("hunger_satisfaction", 0.8)
        energy_sat = await self.memory.status.get("energy_satisfaction", 0.8)
        safety_sat = await self.memory.status.get("safety_satisfaction", 0.8)
        social_sat = await self.memory.status.get("social_satisfaction", 0.8)

        # Get current time
        _, current_time = self.environment.get_datetime(format_time=True)

        await self.daily_schedule_prompt.format(
            day=day,
            current_time=current_time,
            occupation=await self.memory.status.get("occupation", "unknown"),
            age=await self.memory.status.get("age", 30),
            income=await self.memory.status.get("income", 0),
            household=household,
            life_stage=life_stage,
            hobbies=hobbies_str,
            goals=goals_str,
            openness=big5.get("openness", 2),
            conscientiousness=big5.get("conscientiousness", 2),
            extraversion=big5.get("extraversion", 2),
            agreeableness=big5.get("agreeableness", 2),
            neuroticism=big5.get("neuroticism", 2),
            chronotype=chronotype,
            work_ethic=work_ethic,
            social_frequency=social_frequency,
            leisure_preference=leisure_preference,
            hunger_satisfaction=hunger_sat,
            energy_satisfaction=energy_sat,
            safety_satisfaction=safety_sat,
            social_satisfaction=social_sat,
        )

        retry = 3
        while retry > 0:
            try:
                get_logger().info(f"Agent {self.agent.id}: Requesting daily schedule generation for day {day}")
                response = await self.llm.atext_request(
                    self.daily_schedule_prompt.to_dialog(),
                    response_format={"type": "json_object"},
                    context={
                        "block_name": self.name,
                        "func_name": "generate_daily_schedule",
                        "agent_id": self.agent.id,
                    },
                )

                schedule = {}

                result: Any = json_repair.loads(clean_json_response(response))
                if "blocks" not in result or not isinstance(result["blocks"], list):
                    raise ValueError("Invalid daily schedule format - missing blocks")

                # Validate each block
                for block in result["blocks"]:
                    if not all(
                        k in block for k in ["start_time", "duration", "activity"]
                    ):
                        raise ValueError(
                            "Each block must have start_time, duration, and activity"
                        )

                # Add metadata
                schedule = {
                    "day": day,
                    "blocks": result["blocks"],
                    "generated_at": current_time,
                }

                get_logger().debug(
                    f"Agent {self.agent.id}: Generated daily schedule for day {day} with {len(result['blocks'])} blocks"
                )
                retry = 0  # success, exit loop

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
        # Get current context
        big5 = await self.memory.status.get("big5", {})
        household = await self.memory.status.get("household", "unknown")
        life_stage = await self.memory.status.get("life_stage", "unknown")
        hobbies = await self.memory.status.get("hobbies", [])
        hobbies_str = ", ".join(hobbies) if isinstance(hobbies, list) else str(hobbies)
        goals = await self.memory.status.get("goals", [])
        goals_str = ", ".join(goals) if isinstance(goals, list) else str(goals)

        preferences = await self.memory.status.get("preferences", {})
        social_frequency = preferences.get("social_frequency", 0.5)
        leisure_preference = preferences.get("leisure_preference", "indoor")

        # Get current needs
        hunger_sat = await self.memory.status.get("hunger_satisfaction", 0.8)
        energy_sat = await self.memory.status.get("energy_satisfaction", 0.8)
        safety_sat = await self.memory.status.get("safety_satisfaction", 0.8)
        social_sat = await self.memory.status.get("social_satisfaction", 0.8)

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

        await self.empty_block_prompt.format(
            current_time=current_time,
            current_location=current_location,
            emotion_types=await self.memory.status.get("emotion_types", "neutral"),
            thought=await self.memory.status.get("thought", ""),
            block_start_time=block.get("start_time", ""),
            block_duration=block.get("duration", 60),
            block_description=block.get("description", ""),
            hunger_satisfaction=hunger_sat,
            energy_satisfaction=energy_sat,
            safety_satisfaction=safety_sat,
            social_satisfaction=social_sat,
            occupation=await self.memory.status.get("occupation", "unknown"),
            age=await self.memory.status.get("age", 30),
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
            leisure_preference=leisure_preference,
        )

        response = await self.llm.atext_request(
            self.empty_block_prompt.to_dialog(),
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
