"""Python prompt classes for DailyScheduleBlock.

Contains:
- DailyScheduleGenerationAgentsociety / Citysim
- EmptyBlockFillingAgentsociety / Citysim
"""
from __future__ import annotations

from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field

from ..base import BasePrompt


def _s(v: object, d: str = "unknown") -> object:
    """Return *v* if not None, else *d*."""
    return v if v is not None else d


# ---------------------------------------------------------------------------
# daily_schedule_generation
# ---------------------------------------------------------------------------

class DailyScheduleGenerationAgentsociety(BasePrompt):
    """Generate a value-driven daily schedule with mandatory and flexible time blocks — agentsociety origin."""

    name: ClassVar[str] = "daily_schedule_generation"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Generate a value-driven daily schedule with mandatory and flexible time blocks"

    day: Optional[str] = Field(None, description="Day input value used by this prompt.")
    current_time: Optional[str] = Field(None, description="Current simulation time (HH:MM).")
    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    income: Optional[str] = Field(None, description="Income input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    hunger_satisfaction: Optional[float] = Field(None, description="Current hunger satisfaction level (0.0 to 1.0).")
    energy_satisfaction: Optional[float] = Field(None, description="Current energy satisfaction level (0.0 to 1.0).")
    safety_satisfaction: Optional[float] = Field(None, description="Current safety satisfaction level (0.0 to 1.0).")
    social_satisfaction: Optional[float] = Field(None, description="Current social satisfaction level (0.0 to 1.0).")

    class Output(BaseModel):
        blocks: list[Any] = Field(default_factory=list, description="Generated daily schedule blocks.")

    def format_prompt(self) -> str:
        return f"""You are an intelligent agent's daily schedule system. Generate a complete daily schedule using recursive time-block decomposition.

Current day: {_s(self.day)}
Current time: {_s(self.current_time)}

Profile Information:
- Occupation: {_s(self.occupation)}
- Age: {_s(self.age)}
- Income: {_s(self.income)}
- Household type: {_s(self.household)}

Current Needs (0-1, lower = more urgent):
- Hunger: {_s(self.hunger_satisfaction)}
- Energy: {_s(self.energy_satisfaction)}
- Safety: {_s(self.safety_satisfaction)}
- Social: {_s(self.social_satisfaction)}

Instructions:
1. Start with MANDATORY high-priority activities (sleep, work) based on chronotype, work_ethic, and occupation.
2. Recursively fill time blocks with MEDIUM-priority tasks (meals, hygiene).
3. Leave some blocks as [EMPTY] for value-driven planning at execution time (leisure, hobbies, socializing).
4. Each block must have: start_time (HH:MM), duration (minutes), activity, description.
5. If an activity does not fill the entire block, subdivide it.
6. Consider current needs when scheduling. Lower satisfaction means higher priority.

Activity Types:
- "sleep": Sleep/rest at home
- "work": Work-related activities
- "meal": Eating (breakfast/lunch/dinner)
- "hygiene": Personal care activities
- "[EMPTY]": Unfilled block for runtime value-driven planning

Response Format (JSON only):
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
Return JSON only, without any extra text."""


class DailyScheduleGenerationCitysim(DailyScheduleGenerationAgentsociety):
    """Generate a value-driven daily schedule — citysim origin (adds Big Five + lifestyle fields)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")
    hobbies: Optional[str] = Field(None, description="Hobbies input value used by this prompt.")
    goals: Optional[str] = Field(None, description="Goals input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    chronotype: Optional[str] = Field(None, description="Chronotype input value used by this prompt.")
    work_ethic: Optional[float] = Field(None, description="Work-priority preference (0.0=Low work priority, 1.0=High work priority).")
    social_frequency: Optional[float] = Field(None, description="Frequency of seeking social interaction (0.0 to 1.0).")
    leisure_preference: Optional[str] = Field(None, description="Leisure preference input value used by this prompt.")

    def format_prompt(self) -> str:
        return f"""You are an intelligent agent's daily schedule system. Generate a complete daily schedule using recursive time-block decomposition.

Current day: {_s(self.day)}
Current time: {_s(self.current_time)}

Profile Information:
- Occupation: {_s(self.occupation)}
- Age: {_s(self.age)}
- Income: {_s(self.income)}
- Household type: {_s(self.household)}
- Life stage: {_s(self.life_stage)}
- Hobbies: {_s(self.hobbies)}
- Goals: {_s(self.goals)}

Big Five Personality Traits (1=Low, 2=Medium, 3=High):
- Openness: {_s(self.openness)}
- Conscientiousness: {_s(self.conscientiousness)}
- Extraversion: {_s(self.extraversion)}
- Agreeableness: {_s(self.agreeableness)}
- Neuroticism: {_s(self.neuroticism)}

Behavioral Preferences:
- Chronotype: {_s(self.chronotype)} (early_bird: wakes ~6am, standard: ~7-8am, night_owl: ~10am)
- Work Ethic: {_s(self.work_ethic)} (0.0=Low work priority, 1.0=High work priority/workaholic)
- Social Frequency: {_s(self.social_frequency)} (0.0=Prefers solitude, 1.0=Seeks frequent social interaction)
- Leisure Preference: {_s(self.leisure_preference)} (outdoor/indoor/social/solitary)

Current Needs (0-1, lower = more urgent):
- Hunger: {_s(self.hunger_satisfaction)}
- Energy: {_s(self.energy_satisfaction)}
- Safety: {_s(self.safety_satisfaction)}
- Social: {_s(self.social_satisfaction)}

Instructions:
1. Start with MANDATORY high-priority activities (sleep, work) based on chronotype, work_ethic, and occupation.
2. Recursively fill time blocks with MEDIUM-priority tasks (meals, hygiene).
3. Leave some blocks as [EMPTY] for value-driven planning at execution time (leisure, hobbies, socializing).
4. Each block must have: start_time (HH:MM), duration (minutes), activity, description.
5. If an activity does not fill the entire block, subdivide it.
6. Consider current needs when scheduling. Lower satisfaction means higher priority.

Activity Types:
- "sleep": Sleep/rest at home
- "work": Work-related activities
- "meal": Eating (breakfast/lunch/dinner)
- "hygiene": Personal care activities
- "[EMPTY]": Unfilled block for runtime value-driven planning

Response Format (JSON only):
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
Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# empty_block_filling
# ---------------------------------------------------------------------------

class EmptyBlockFillingAgentsociety(BasePrompt):
    """Select the best value-driven activity for an empty schedule block — agentsociety origin."""

    name: ClassVar[str] = "empty_block_filling"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Select the best value-driven activity for an empty schedule block"

    current_time: Optional[str] = Field(None, description="Current simulation time (HH:MM).")
    current_location: Optional[str] = Field(None, description="Current location input value used by this prompt.")
    emotion_types: Optional[str] = Field(None, description="Emotion types input value used by this prompt.")
    thought: Optional[str] = Field(None, description="Thought input value used by this prompt.")
    block_start_time: Optional[str] = Field(None, description="Start time of the schedule block (HH:MM).")
    block_duration: Optional[int] = Field(None, description="Duration of the schedule block in minutes.")
    block_description: Optional[str] = Field(None, description="Block description input value used by this prompt.")
    hunger_satisfaction: Optional[float] = Field(None, description="Current hunger satisfaction level (0.0 to 1.0).")
    energy_satisfaction: Optional[float] = Field(None, description="Current energy satisfaction level (0.0 to 1.0).")
    safety_satisfaction: Optional[float] = Field(None, description="Current safety satisfaction level (0.0 to 1.0).")
    social_satisfaction: Optional[float] = Field(None, description="Current social satisfaction level (0.0 to 1.0).")
    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")

    class Output(BaseModel):
        selected: Any = Field(default=None, description="Selected activity object (activity, type, reasoning).")
        candidates: Optional[list[Any]] = Field(default=None, description="Candidate activities evaluated before selection.")

    def format_prompt(self) -> str:
        return f"""You are an intelligent agent's value-driven activity planner. Fill this [EMPTY] time block with the best activity to satisfy your intrinsic desires.

Current Context:
- Current time: {_s(self.current_time)}
- Current location: {_s(self.current_location)}
- Current emotion: {_s(self.emotion_types)}
- Current thought: {_s(self.thought)}

Available Empty Block:
- Start time: {_s(self.block_start_time)}
- Duration: {_s(self.block_duration)} minutes
- Original description: {_s(self.block_description)}

Current Needs (0-1, lower = more urgent):
- Hunger: {_s(self.hunger_satisfaction)}
- Energy: {_s(self.energy_satisfaction)}
- Safety: {_s(self.safety_satisfaction)}
- Social: {_s(self.social_satisfaction)}

Profile:
- Occupation: {_s(self.occupation)}
- Age: {_s(self.age)}
- Household: {_s(self.household)}

Task:
Generate and evaluate multiple candidate activities (2-4 options). Select the one that best satisfies your intrinsic desires according to Maslow's Hierarchy.

Consider:
1. Most urgent needs (lowest satisfaction scores).
2. Your personality traits and preferences.
3. Current location and time constraints.
4. Your hobbies and goals.

Response Format (JSON only):
{{
    "candidates": [
        {{"activity": "Contact friends", "expected_need": "social", "expected_satisfaction_gain": 0.3, "reasoning": "Low social satisfaction"}},
        {{"activity": "Practice photography (hobby)", "expected_need": "safety", "expected_satisfaction_gain": 0.2, "reasoning": "Aligns with hobbies and goals"}},
        {{"activity": "Exercise at park", "expected_need": "energy", "expected_satisfaction_gain": 0.15, "reasoning": "Outdoor leisure preference"}}
    ],
    "selected": {{
        "activity": "Contact friends",
        "type": "social",
        "reasoning": "Social need is most urgent and this activity is expected to provide the highest satisfaction gain"
    }}
}}

DO NOT INCLUDE COMMENTS. RETURN ONLY VALID JSON.
Return JSON only, without any extra text."""


class EmptyBlockFillingCitysim(EmptyBlockFillingAgentsociety):
    """Select the best value-driven activity for an empty schedule block — citysim origin (adds Big Five + lifestyle fields)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")
    hobbies: Optional[str] = Field(None, description="Hobbies input value used by this prompt.")
    goals: Optional[str] = Field(None, description="Goals input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    social_frequency: Optional[float] = Field(None, description="Frequency of seeking social interaction (0.0 to 1.0).")
    leisure_preference: Optional[str] = Field(None, description="Leisure preference input value used by this prompt.")

    def format_prompt(self) -> str:
        return f"""You are an intelligent agent's value-driven activity planner. Fill this [EMPTY] time block with the best activity to satisfy your intrinsic desires.

Current Context:
- Current time: {_s(self.current_time)}
- Current location: {_s(self.current_location)}
- Current emotion: {_s(self.emotion_types)}
- Current thought: {_s(self.thought)}

Available Empty Block:
- Start time: {_s(self.block_start_time)}
- Duration: {_s(self.block_duration)} minutes
- Original description: {_s(self.block_description)}

Current Needs (0-1, lower = more urgent):
- Hunger: {_s(self.hunger_satisfaction)}
- Energy: {_s(self.energy_satisfaction)}
- Safety: {_s(self.safety_satisfaction)}
- Social: {_s(self.social_satisfaction)}

Profile:
- Occupation: {_s(self.occupation)}
- Age: {_s(self.age)}
- Household: {_s(self.household)}
- Life stage: {_s(self.life_stage)}
- Hobbies: {_s(self.hobbies)}
- Goals: {_s(self.goals)}

Big Five Personality Traits (1=Low, 2=Medium, 3=High):
- Openness: {_s(self.openness)}
- Conscientiousness: {_s(self.conscientiousness)}
- Extraversion: {_s(self.extraversion)}
- Agreeableness: {_s(self.agreeableness)}
- Neuroticism: {_s(self.neuroticism)}

Behavioral Preferences:
- Social Frequency: {_s(self.social_frequency)}
- Leisure Preference: {_s(self.leisure_preference)}

Task:
Generate and evaluate multiple candidate activities (2-4 options). Select the one that best satisfies your intrinsic desires according to Maslow's Hierarchy.

Consider:
1. Most urgent needs (lowest satisfaction scores).
2. Your personality traits and preferences.
3. Current location and time constraints.
4. Your hobbies and goals.

Response Format (JSON only):
{{
    "candidates": [
        {{"activity": "Contact friends", "expected_need": "social", "expected_satisfaction_gain": 0.3, "reasoning": "Low social satisfaction"}},
        {{"activity": "Practice photography (hobby)", "expected_need": "safety", "expected_satisfaction_gain": 0.2, "reasoning": "Aligns with hobbies and goals"}},
        {{"activity": "Exercise at park", "expected_need": "energy", "expected_satisfaction_gain": 0.15, "reasoning": "Outdoor leisure preference"}}
    ],
    "selected": {{
        "activity": "Contact friends",
        "type": "social",
        "reasoning": "Social need is most urgent and this activity is expected to provide the highest satisfaction gain"
    }}
}}

DO NOT INCLUDE COMMENTS. RETURN ONLY VALID JSON.
Return JSON only, without any extra text."""
