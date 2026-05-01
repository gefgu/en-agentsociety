"""Python prompt classes for PlanBlock (guidance selection + detailed generation)."""
from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from ..base import BasePrompt


def _s(v: object, d: str = "unknown") -> object:
    """Return *v* if not None, else *d*."""
    return v if v is not None else d


# ---------------------------------------------------------------------------
# plan_guidance_selection
# ---------------------------------------------------------------------------

class PlanGuidanceSelectionAgentsociety(BasePrompt):
    """Select best guidance option for current need using TPB evaluation — agentsociety origin."""

    name: ClassVar[str] = "plan_guidance_selection"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Select best guidance option for current need using TPB evaluation"

    weather: Optional[str] = Field(None, description="Weather input value used by this prompt.")
    temperature: Optional[float] = Field(None, description="Current temperature context value.")
    other_info: Optional[str] = Field(None, description="Other info input value used by this prompt.")
    current_need: Optional[str] = Field(None, description="Current need input value used by this prompt.")
    current_location: Optional[str] = Field(None, description="Current location input value used by this prompt.")
    current_time: Optional[str] = Field(None, description="Current simulation time (HH:MM).")
    consumption_level: Optional[str] = Field(None, description="Consumption level input value used by this prompt.")
    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    emotion_types: Optional[str] = Field(None, description="Emotion types input value used by this prompt.")
    thought: Optional[str] = Field(None, description="Thought input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    options: Optional[str] = Field(None, description="Options input value used by this prompt.")

    class Output(BaseModel):
        selected_option: str = Field(description="Selected guidance option.")
        evaluation: str = Field(description="JSON evaluation object for TPB scores and reasoning.")

    def format_prompt(self) -> str:
        return f"""As an intelligent agent's decision system, please help me determine a suitable option to satisfy my current need.
The Environment will influence the choice of steps.

Current weather: {_s(self.weather)}
Current temperature: {_s(self.temperature)}
Other information:
-------------------------
{_s(self.other_info)}
-------------------------

Current need: Need to satisfy {_s(self.current_need)}
Current location: {_s(self.current_location)}
Current time: {_s(self.current_time)}
My income/consumption level: {_s(self.consumption_level)}
My occupation: {_s(self.occupation)}
My age: {_s(self.age)}
My emotion: {_s(self.emotion_types)}
My thought: {_s(self.thought)}
Household type: {_s(self.household)}

Guidance Options:
-------------------------
{_s(self.options)}
-------------------------

Please evaluate and select the most appropriate option based on these three dimensions:
1. Attitude: Personal preference and evaluation of the option
2. Subjective Norm: Social environment and others' views on this behavior
3. Perceived Control: Difficulty and controllability of executing this option

Please response in json format (Do not return any other text), example:
{{
    "selected_option": "Select the most suitable option from Guidance Options and extent the option if necessary (or do things that can satisfy your needs or actions unless there is no specific options)",
    "evaluation": {{
        "attitude": "Attitude score for the option (0-1)",
        "subjective_norm": "Subjective norm score (0-1)",
        "perceived_control": "Perceived control score (0-1)",
        "reasoning": "Specific reasons for selecting this option"
    }}
}}

Return JSON only, without any extra text."""


class PlanGuidanceSelectionCitysim(PlanGuidanceSelectionAgentsociety):
    """Select best guidance option for current need using TPB evaluation — citysim origin (adds Big Five + lifestyle fields)."""

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
        return f"""As an intelligent agent's decision system, please help me determine a suitable option to satisfy my current need.
The Environment will influence the choice of steps.

Current weather: {_s(self.weather)}
Current temperature: {_s(self.temperature)}
Other information:
-------------------------
{_s(self.other_info)}
-------------------------

Current need: Need to satisfy {_s(self.current_need)}
Current location: {_s(self.current_location)}
Current time: {_s(self.current_time)}
My income/consumption level: {_s(self.consumption_level)}
My occupation: {_s(self.occupation)}
My age: {_s(self.age)}
My emotion: {_s(self.emotion_types)}
My thought: {_s(self.thought)}
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
- Chronotype: {_s(self.chronotype)} (early_bird/standard/night_owl - affects timing preferences)
- Work Ethic: {_s(self.work_ethic)} (0.0=Low work priority, 1.0=High work priority/workaholic)
- Social Frequency: {_s(self.social_frequency)} (0.0=Prefers solitude, 1.0=Seeks frequent social interaction)
- Leisure Preference: {_s(self.leisure_preference)} (outdoor/indoor/social/solitary)

Guidance Options:
-------------------------
{_s(self.options)}
-------------------------

Please evaluate and select the most appropriate option based on these three dimensions:
1. Attitude: Personal preference and evaluation of the option
2. Subjective Norm: Social environment and others' views on this behavior
3. Perceived Control: Difficulty and controllability of executing this option

Please response in json format (Do not return any other text), example:
{{
    "selected_option": "Select the most suitable option from Guidance Options and extent the option if necessary (or do things that can satisfy your needs or actions unless there is no specific options)",
    "evaluation": {{
        "attitude": "Attitude score for the option (0-1)",
        "subjective_norm": "Subjective norm score (0-1)",
        "perceived_control": "Perceived control score (0-1)",
        "reasoning": "Specific reasons for selecting this option"
    }}
}}

Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# plan_detailed_generation
# ---------------------------------------------------------------------------

class PlanDetailedGenerationAgentsociety(BasePrompt):
    """Generate detailed executable plan steps from selected guidance — agentsociety origin."""

    name: ClassVar[str] = "plan_detailed_generation"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Generate detailed executable plan steps from selected guidance"

    weather: Optional[str] = Field(None, description="Weather input value used by this prompt.")
    temperature: Optional[float] = Field(None, description="Current temperature context value.")
    other_information: Optional[str] = Field(None, description="Other information input value used by this prompt.")
    plan_target: Optional[str] = Field(None, description="Plan target input value used by this prompt.")
    current_position: Optional[str] = Field(None, description="Current position input value used by this prompt.")
    current_time: Optional[str] = Field(None, description="Current simulation time (HH:MM).")
    consumption_level: Optional[str] = Field(None, description="Consumption level input value used by this prompt.")
    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    emotion_types: Optional[str] = Field(None, description="Emotion types input value used by this prompt.")
    current_thought: Optional[str] = Field(None, description="Current thought input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    max_plan_steps: Optional[int] = Field(None, description="Maximum number of actionable steps allowed in the generated plan.")

    class Output(BaseModel):
        plan: str = Field(..., description="JSON plan object containing target and executable steps.")

    def format_prompt(self) -> str:
        return f"""As an intelligent agent's plan system, please help me generate specific execution steps based on the selected guidance plan.
The Environment will influence the choice of steps.

Current weather: {_s(self.weather)}
Current temperature: {_s(self.temperature)}
Other information:
-------------------------
{_s(self.other_information)}
-------------------------

Plan target: {_s(self.plan_target)}
Current location: {_s(self.current_position)}
Current time: {_s(self.current_time)}
My income/consumption level: {_s(self.consumption_level)}
My occupation: {_s(self.occupation)}
My age: {_s(self.age)}
My emotion: {_s(self.emotion_types)}
My thought: {_s(self.current_thought)}
Household type: {_s(self.household)}

Notes:
1. type can only be one of these four: mobility, social, economy, other
   1.1 mobility: Decisions or behaviors related to large-scale spatial movement, such as location selection, going to a place, etc.
   1.2 social: Decisions or behaviors related to social interaction, such as finding contacts, chatting with friends, etc.
   1.3 economy: Decisions or behaviors related to shopping, work, etc.
   1.4 other: Other types of decisions or behaviors, such as small-scale activities, learning, resting, entertainment, etc.
2. steps should only include steps necessary to fulfill the target (limited to {_s(self.max_plan_steps)} steps)
3. intention in each step should be concise and clear

Please response in json format (Do not return any other text), example:
{{
    "plan": {{
        "target": "Eat at home",
        "steps": [
            {{
                "intention": "Return home from current location",
                "type": "mobility"
            }},
            {{
                "intention": "Cook food",
                "type": "other"
            }},
            {{
                "intention": "Have meal",
                "type": "other"
            }}
        ]
    }}
}}
Return JSON only, without any extra text."""


class PlanDetailedGenerationCitysim(PlanDetailedGenerationAgentsociety):
    """Generate detailed executable plan steps — citysim origin (adds Big Five + lifestyle + behavioral prefs)."""

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
        return f"""As an intelligent agent's plan system, please help me generate specific execution steps based on the selected guidance plan.
The Environment will influence the choice of steps.

Current weather: {_s(self.weather)}
Current temperature: {_s(self.temperature)}
Other information:
-------------------------
{_s(self.other_information)}
-------------------------

Plan target: {_s(self.plan_target)}
Current location: {_s(self.current_position)}
Current time: {_s(self.current_time)}
My income/consumption level: {_s(self.consumption_level)}
My occupation: {_s(self.occupation)}
My age: {_s(self.age)}
My emotion: {_s(self.emotion_types)}
My thought: {_s(self.current_thought)}
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
- Chronotype: {_s(self.chronotype)} (early_bird/standard/night_owl - affects timing preferences)
- Work Ethic: {_s(self.work_ethic)} (0.0=Low work priority, 1.0=High work priority/workaholic)
- Social Frequency: {_s(self.social_frequency)} (0.0=Prefers solitude, 1.0=Seeks frequent social interaction)
- Leisure Preference: {_s(self.leisure_preference)} (outdoor/indoor/social/solitary)

Notes:
1. type can only be one of these four: mobility, social, economy, other
   1.1 mobility: Decisions or behaviors related to large-scale spatial movement, such as location selection, going to a place, etc.
   1.2 social: Decisions or behaviors related to social interaction, such as finding contacts, chatting with friends, etc.
   1.3 economy: Decisions or behaviors related to shopping, work, etc.
   1.4 other: Other types of decisions or behaviors, such as small-scale activities, learning, resting, entertainment, etc.
2. steps should only include steps necessary to fulfill the target (limited to {_s(self.max_plan_steps)} steps)
3. intention in each step should be concise and clear

Please response in json format (Do not return any other text), example:
{{
    "plan": {{
        "target": "Eat at home",
        "steps": [
            {{
                "intention": "Return home from current location",
                "type": "mobility"
            }},
            {{
                "intention": "Cook food",
                "type": "other"
            }},
            {{
                "intention": "Have meal",
                "type": "other"
            }}
        ]
    }}
}}
Return JSON only, without any extra text."""
