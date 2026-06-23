"""Python prompt classes for SocialBlock (time estimation + message generation).

Contains:
- SocialTimeEstimateAgentsociety / SocialTimeEstimateCitysim
- SocialMessageGenerationAgentsociety / SocialMessageGenerationCitysim
"""
from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from ..base import BasePrompt


def _s(v: object, d: str = "unknown") -> object:
    """Return *v* if not None, else *d*."""
    return v if v is not None else d


# ---------------------------------------------------------------------------
# social_time_estimate
# ---------------------------------------------------------------------------

class SocialTimeEstimateAgentsociety(BasePrompt):
    """Estimate time for generic social actions — agentsociety origin."""

    name: ClassVar[str] = "social_time_estimate"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Estimate time for generic social actions when no specific social sub-action is selected"

    plan: Optional[str] = Field(None, description="Plan input value used by this prompt.")
    intention: Optional[str] = Field(None, description="Intention input value used by this prompt.")
    emotion_types: Optional[str] = Field(None, description="Emotion types input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")

    class Output(BaseModel):
        time: int = Field(description="Estimated minutes for the social action.")

    def format_prompt(self) -> str:
        return f"""As an intelligent agent's time estimation system, please estimate the time needed to complete the current action based on the overall plan and current intention.

Overall plan:
{_s(self.plan)}

Current action: {_s(self.intention)}

Current emotion: {_s(self.emotion_types)}

Household type: {_s(self.household)}

Examples:
- "Chat with a friend": {{"time": 20}}
- "Join a group activity": {{"time": 90}}
- "Call family": {{"time": 30}}
- "Browse social media": {{"time": 25}}

Please return the result in JSON format (Do not return any other text), the time unit is [minute], example:
{{
    "time": 10
}}

Return JSON only, without any extra text."""


class SocialTimeEstimateCitysim(SocialTimeEstimateAgentsociety):
    """Estimate time for generic social actions — citysim origin."""

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
- "Chat with a friend": {{"time": 20}}
- "Join a group activity": {{"time": 90}}
- "Call family": {{"time": 30}}
- "Browse social media": {{"time": 25}}

Please return the result in JSON format (Do not return any other text), the time unit is [minute], example:
{{
    "time": 10
}}

Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# social_message_generation
# ---------------------------------------------------------------------------

class SocialMessageGenerationAgentsociety(BasePrompt):
    """Generate a context-aware social message to a selected target — agentsociety origin."""

    name: ClassVar[str] = "social_message_generation"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Generate a context-aware social message to a selected target"

    # NOTE: 'name' is a ClassVar on BasePrompt; use 'agent_name' for the agent's own name.
    agent_name: Optional[str] = Field(None, description="Name input value used by this prompt.")
    gender: Optional[str] = Field(None, description="Gender input value used by this prompt.")
    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    education: Optional[str] = Field(None, description="Education input value used by this prompt.")
    personality: Optional[str] = Field(None, description="Personality input value used by this prompt.")
    emotion_types: Optional[str] = Field(None, description="Emotion types input value used by this prompt.")
    thought: Optional[str] = Field(None, description="Thought input value used by this prompt.")
    background_story: Optional[str] = Field(None, description="Background story input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    relationship_type: Optional[str] = Field(None, description="Relationship type input value used by this prompt.")
    relationship_strength: Optional[float] = Field(None, description="Relationship strength score (0.0=weak, 1.0=strong).")
    chat_history: Optional[str] = Field(None, description="Chat history input value used by this prompt.")
    intention: Optional[str] = Field(None, description="Intention input value used by this prompt.")
    environment_info: Optional[str] = Field(None, description="Environment info input value used by this prompt.")
    discussion_constraint: Optional[str] = Field(None, description="Discussion constraint input value used by this prompt.")

    class Output(BaseModel):
        message: str = Field(description="Generated social message content.")

    def format_prompt(self) -> str:
        return f"""My name is {_s(self.agent_name)}, I am a {_s(self.gender)}
My occupation is {_s(self.occupation)}.
My education level is {_s(self.education)}.
My personality is {_s(self.personality)}.
My current emotion is: {_s(self.emotion_types)}.
My current thought is: {_s(self.thought)}.
My background story is: {_s(self.background_story)}.
Household type: {_s(self.household)}

Now, I want to generate a social message to a target, my relationship with him/her:
Our relationship type is: {_s(self.relationship_type)}
Our relationship strength: {_s(self.relationship_strength)} (0-1, higher is stronger)
My previous chat history with him/her is:
{_s(self.chat_history)}

My intention is: {_s(self.intention)}.

Environment Information:
{_s(self.environment_info)}

Please generate a natural and contextually appropriate message.
Keep it under 100 characters.
The message should reflect my personality and background.

{_s(self.discussion_constraint)}

Please output the message from a first-person perspective, without any other text

Return JSON only, without any extra text."""


class SocialMessageGenerationCitysim(SocialMessageGenerationAgentsociety):
    """Generate a context-aware social message to a selected target — citysim origin (adds Big Five + lifestyle fields)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")
    hobbies: Optional[str] = Field(None, description="Hobbies input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")

    def format_prompt(self) -> str:
        return f"""My name is {_s(self.agent_name)}, I am a {_s(self.gender)}
My occupation is {_s(self.occupation)}.
My education level is {_s(self.education)}.
My personality is {_s(self.personality)}.
My current emotion is: {_s(self.emotion_types)}.
My current thought is: {_s(self.thought)}.
My background story is: {_s(self.background_story)}.
Household type: {_s(self.household)}
Life stage: {_s(self.life_stage)}
Hobbies: {_s(self.hobbies)}

Big Five Personality Traits (1=Low, 2=Medium, 3=High):
- Openness: {_s(self.openness)}
- Conscientiousness: {_s(self.conscientiousness)}
- Extraversion: {_s(self.extraversion)}
- Agreeableness: {_s(self.agreeableness)}
- Neuroticism: {_s(self.neuroticism)}

Now, I want to generate a social message to a target, my relationship with him/her:
Our relationship type is: {_s(self.relationship_type)}
Our relationship strength: {_s(self.relationship_strength)} (0-1, higher is stronger)
My previous chat history with him/her is:
{_s(self.chat_history)}

My intention is: {_s(self.intention)}.

Environment Information:
{_s(self.environment_info)}

Please generate a natural and contextually appropriate message.
Keep it under 100 characters.
The message should reflect my personality and background.

{_s(self.discussion_constraint)}

Please output the message from a first-person perspective, without any other text

Return JSON only, without any extra text."""
