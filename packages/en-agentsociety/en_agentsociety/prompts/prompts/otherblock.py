"""Python prompt classes for OtherBlock (sleep + generic time estimation)."""
from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from ..base import BasePrompt


def _s(v: object, d: str = "unknown") -> object:
    """Return *v* if not None, else *d*."""
    return v if v is not None else d


# ---------------------------------------------------------------------------
# other_sleep_time_estimate
# ---------------------------------------------------------------------------

class OtherSleepTimeEstimateAgentsociety(BasePrompt):
    """Estimate sleep action duration — agentsociety origin."""

    name: ClassVar[str] = "other_sleep_time_estimate"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Estimate sleep action duration from plan, intention, and persona"

    plan: Optional[str] = Field(None, description="Plan input value used by this prompt.")
    intention: Optional[str] = Field(None, description="Intention input value used by this prompt.")
    emotion_types: Optional[str] = Field(None, description="Emotion types input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")

    class Output(BaseModel):
        time: int = Field(description="Estimated minutes for the sleep action.")

    def format_prompt(self) -> str:
        return f"""As an intelligent agent's time estimation system, please estimate the time needed to complete the current action based on the overall plan and current intention.

Overall plan:
{_s(self.plan)}

Current action: {_s(self.intention)}

Current emotion: {_s(self.emotion_types)}

Household type: {_s(self.household)}

Examples:
- "Learn programming": {{"time": 120}}
- "Watch a movie": {{"time": 150}}
- "Play mobile games": {{"time": 60}}
- "Read a book": {{"time": 90}}
- "Exercise": {{"time": 45}}

Please return the result in JSON format (Do not return any other text), the time unit is [minute], example:
{{
    "time": 10
}}

Return JSON only, without any extra text."""


class OtherSleepTimeEstimateCitysim(OtherSleepTimeEstimateAgentsociety):
    """Estimate sleep action duration — citysim origin (adds Big Five + lifestyle fields)."""

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
    leisure_preference: Optional[str] = Field(None, description="Leisure preference input value used by this prompt.")

    def format_prompt(self) -> str:
        return f"""As an intelligent agent's time estimation system, please estimate the time needed to complete the current action based on the overall plan and current intention.

Overall plan:
{_s(self.plan)}

Current action: {_s(self.intention)}

Current emotion: {_s(self.emotion_types)}

Household type: {_s(self.household)}
Life stage: {_s(self.life_stage)}
Hobbies: {_s(self.hobbies)}
Goals: {_s(self.goals)}

Big Five Personality Traits (1=Low, 2=Medium, 3=High):
- Openness: {_s(self.openness)}
- Conscientiousness: {_s(self.conscientiousness)}
- Extraversion: {_s(self.extraversion)}
- Agreeableness: {_s(self.agreeableness)}
- Neuroticism: {_s(self.neuroticism)}

Behavioral Preferences:
- Chronotype: {_s(self.chronotype)} (early_bird: wakes ~6am and goes to bed early, standard: wakes ~7-8am, night_owl: wakes ~10am and stays up late)
- Leisure Preference: {_s(self.leisure_preference)} (outdoor/indoor/social/solitary - affects activity duration)

Examples:
- "Learn programming": {{"time": 120}}
- "Watch a movie": {{"time": 150}}
- "Play mobile games": {{"time": 60}}
- "Read a book": {{"time": 90}}
- "Exercise": {{"time": 45}}

Please return the result in JSON format (Do not return any other text), the time unit is [minute], example:
{{
    "time": 10
}}

Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# other_time_estimate
# ---------------------------------------------------------------------------

class OtherTimeEstimateAgentsociety(BasePrompt):
    """Estimate time for generic non-sleep other actions — agentsociety origin."""

    name: ClassVar[str] = "other_time_estimate"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Estimate time for generic non-sleep other actions"

    plan: Optional[str] = Field(None, description="Plan input value used by this prompt.")
    intention: Optional[str] = Field(None, description="Intention input value used by this prompt.")
    emotion_types: Optional[str] = Field(None, description="Emotion types input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")

    class Output(BaseModel):
        time: int = Field(description="Estimated minutes for the generic action.")

    def format_prompt(self) -> str:
        return f"""As an intelligent agent's time estimation system, please estimate the time needed to complete the current action based on the overall plan and current intention.

Overall plan:
{_s(self.plan)}

Current action: {_s(self.intention)}

Current emotion: {_s(self.emotion_types)}

Household type: {_s(self.household)}

Examples:
- "Learn programming": {{"time": 120}}
- "Watch a movie": {{"time": 150}}
- "Play mobile games": {{"time": 60}}
- "Read a book": {{"time": 90}}
- "Exercise": {{"time": 45}}

Please return the result in JSON format (Do not return any other text), the time unit is [minute], example:
{{
    "time": 10
}}

Return JSON only, without any extra text."""


class OtherTimeEstimateCitysim(OtherTimeEstimateAgentsociety):
    """Estimate time for generic non-sleep other actions — citysim origin."""

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
    leisure_preference: Optional[str] = Field(None, description="Leisure preference input value used by this prompt.")

    def format_prompt(self) -> str:
        return f"""As an intelligent agent's time estimation system, please estimate the time needed to complete the current action based on the overall plan and current intention.

Overall plan:
{_s(self.plan)}

Current action: {_s(self.intention)}

Current emotion: {_s(self.emotion_types)}

Household type: {_s(self.household)}
Life stage: {_s(self.life_stage)}
Hobbies: {_s(self.hobbies)}
Goals: {_s(self.goals)}

Big Five Personality Traits (1=Low, 2=Medium, 3=High):
- Openness: {_s(self.openness)}
- Conscientiousness: {_s(self.conscientiousness)}
- Extraversion: {_s(self.extraversion)}
- Agreeableness: {_s(self.agreeableness)}
- Neuroticism: {_s(self.neuroticism)}

Behavioral Preferences:
- Chronotype: {_s(self.chronotype)} (early_bird: wakes ~6am, standard: wakes ~7-8am, night_owl: wakes ~10am)
- Work Ethic: {_s(self.work_ethic)} (0.0=Low priority on work, 1.0=High priority, tends to work overtime)
- Leisure Preference: {_s(self.leisure_preference)} (outdoor/indoor/social/solitary)

Examples:
- "Learn programming": {{"time": 120}}
- "Watch a movie": {{"time": 150}}
- "Play mobile games": {{"time": 60}}
- "Read a book": {{"time": 90}}
- "Exercise": {{"time": 45}}

Please return the result in JSON format (Do not return any other text), the time unit is [minute], example:
{{
    "time": 10
}}

Return JSON only, without any extra text."""
