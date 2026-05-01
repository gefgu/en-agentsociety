"""Python prompt classes for NeedsBlock.

Contains:
- NeedsEvaluationAgentsociety / Citysim
- NeedsInitializeAgentsociety / Citysim
- NeedsPoiObservationCitysim (citysim-only)
- NeedsReflectionAgentsociety / Citysim
"""
from __future__ import annotations

from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field

from ..base import BasePrompt


def _s(v: object, d: str = "unknown") -> object:
    """Return *v* if not None, else *d*."""
    return v if v is not None else d


# ---------------------------------------------------------------------------
# needs_evaluation
# ---------------------------------------------------------------------------

class NeedsEvaluationAgentsociety(BasePrompt):
    """Evaluate completed plan results and adjust need satisfaction — agentsociety origin."""

    name: ClassVar[str] = "needs_evaluation"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Evaluate completed plan results and adjust need satisfaction"

    current_need: Optional[str] = Field(None, description="The current need to evaluate (e.g., hunger, energy, safety, social, whatever).")
    plan_target: Optional[str] = Field(None, description="The goal the agent attempted to complete for the current need.")
    evaluation_results: Optional[str] = Field(None, description="Execution outcome and observed results for the completed actions.")
    hunger_satisfaction: Optional[float] = Field(None, description="Current hunger satisfaction level (0.0 to 1.0).")
    energy_satisfaction: Optional[float] = Field(None, description="Current energy satisfaction level (0.0 to 1.0).")
    safety_satisfaction: Optional[float] = Field(None, description="Current safety satisfaction level (0.0 to 1.0).")
    social_satisfaction: Optional[float] = Field(None, description="Current social satisfaction level (0.0 to 1.0).")
    household: Optional[str] = Field(None, description="Description of the agent's household composition.")

    class Output(BaseModel):
        hunger_satisfaction: Optional[float] = Field(None, description="Updated hunger satisfaction level (0.0 to 1.0).")
        energy_satisfaction: Optional[float] = Field(None, description="Updated energy satisfaction level (0.0 to 1.0).")
        safety_satisfaction: Optional[float] = Field(None, description="Updated safety satisfaction level (0.0 to 1.0).")
        social_satisfaction: Optional[float] = Field(None, description="Updated social satisfaction level (0.0 to 1.0).")

    def format_prompt(self) -> str:
        return f"""You are an evaluation system for an intelligent agent. The agent has performed the following actions to satisfy the {_s(self.current_need)} need:

Goal: {_s(self.plan_target)}
Execution situation:
{_s(self.evaluation_results)}

Current satisfaction:
- hunger_satisfaction: {_s(self.hunger_satisfaction)}
- energy_satisfaction: {_s(self.energy_satisfaction)}
- safety_satisfaction: {_s(self.safety_satisfaction)}
- social_satisfaction: {_s(self.social_satisfaction)}

Household type: {_s(self.household)}

Please evaluate and adjust the value of {_s(self.current_need)} satisfaction based on the execution results above.

Notes:
1. Satisfaction values range from 0-1, where:
   - 1 means the need is fully satisfied
   - 0 means the need is completely unsatisfied
   - Higher values indicate greater need satisfaction
2. Consider social_frequency when evaluating social satisfaction: higher social_frequency means social activities have greater impact.

Return JSON only, without any extra text.

If current_need is not "whatever", return only the updated value for that need, for example:
{{
    "hunger_satisfaction": new_hunger_satisfaction_value
}}

If current_need is "whatever", return both safety and social satisfaction values, for example:
{{
    "safety_satisfaction": new_safety_satisfaction_value,
    "social_satisfaction": new_social_satisfaction_value
}}"""


class NeedsEvaluationCitysim(NeedsEvaluationAgentsociety):
    """Evaluate completed plan results — citysim origin (adds Big Five + lifestyle fields)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="The agent's current stage of life (e.g., Young adulthood, Mid-life).")
    hobbies: Optional[str] = Field(None, description="Interests and activities the agent enjoys.")
    goals: Optional[str] = Field(None, description="The agent's short-term or long-term objectives.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    social_frequency: Optional[float] = Field(None, description="Frequency of seeking social interaction (0.0 to 1.0).")

    def format_prompt(self) -> str:
        return f"""You are an evaluation system for an intelligent agent. The agent has performed the following actions to satisfy the {_s(self.current_need)} need:

Goal: {_s(self.plan_target)}
Execution situation:
{_s(self.evaluation_results)}

Current satisfaction:
- hunger_satisfaction: {_s(self.hunger_satisfaction)}
- energy_satisfaction: {_s(self.energy_satisfaction)}
- safety_satisfaction: {_s(self.safety_satisfaction)}
- social_satisfaction: {_s(self.social_satisfaction)}

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
- Social Frequency: {_s(self.social_frequency)} (0.0=Rarely initiates social contact, 1.0=Frequently seeks social interaction)

Please evaluate and adjust the value of {_s(self.current_need)} satisfaction based on the execution results above.

Notes:
1. Satisfaction values range from 0-1, where:
   - 1 means the need is fully satisfied
   - 0 means the need is completely unsatisfied
   - Higher values indicate greater need satisfaction
2. Consider social_frequency when evaluating social satisfaction: higher social_frequency means social activities have greater impact.

Return JSON only, without any extra text.

If current_need is not "whatever", return only the updated value for that need, for example:
{{
    "hunger_satisfaction": new_hunger_satisfaction_value
}}

If current_need is "whatever", return both safety and social satisfaction values, for example:
{{
    "safety_satisfaction": new_safety_satisfaction_value,
    "social_satisfaction": new_social_satisfaction_value
}}"""


# ---------------------------------------------------------------------------
# needs_initialize
# ---------------------------------------------------------------------------

class NeedsInitializeAgentsociety(BasePrompt):
    """Initialize satisfaction levels from profile and traits — agentsociety origin."""

    name: ClassVar[str] = "needs_initialize"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Initialize satisfaction levels from profile and traits"

    gender: Optional[str] = Field(None, description="Gender input value used by this prompt.")
    education: Optional[str] = Field(None, description="Education input value used by this prompt.")
    consumption: Optional[float] = Field(None, description="Consumption input value used by this prompt.")
    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    income: Optional[str] = Field(None, description="Income input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    current_time: Optional[str] = Field(None, description="Current simulation time (HH:MM).")
    # Used in template even in agentsociety origin
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    social_frequency: Optional[float] = Field(None, description="Frequency of seeking social interaction (0.0 to 1.0).")

    class Output(BaseModel):
        current_satisfaction: Any = Field(description="JSON object containing initialized satisfaction values.")

    def format_prompt(self) -> str:
        return f"""You are an intelligent agent satisfaction initialization system. Based on the profile information below, please help initialize the agent's satisfaction levels and related parameters.

Profile Information:
- Gender: {_s(self.gender)}
- Education Level: {_s(self.education)}
- Consumption Level: {_s(self.consumption)}
- Occupation: {_s(self.occupation)}
- Age: {_s(self.age)}
- Monthly Income: {_s(self.income)}
- Household type: {_s(self.household)}
-
  - Openness: {_s(self.openness)}
  - Conscientiousness: {_s(self.conscientiousness)}
  - Extraversion: {_s(self.extraversion)}
  - Agreeableness: {_s(self.agreeableness)}
  - Neuroticism: {_s(self.neuroticism)}
-
  - Social Frequency: {_s(self.social_frequency)} (0.0=Rarely initiates social contact, 1.0=Frequently seeks social interaction)

Current Time: {_s(self.current_time)}

Please initialize the agent's satisfaction levels and parameters based on the profile above. Return the values in JSON format with the following structure:

Current satisfaction levels (0-1 float values, lower means less satisfied):
- hunger_satisfaction: Hunger satisfaction level (Normally, the agent will be less satisfied with hunger at eating time)
- energy_satisfaction: Energy satisfaction level (Normally, at night, the agent will be less satisfied with energy)
- safety_satisfaction: Safety satisfaction level (Normally, the agent will be more satisfied with safety when they have high income and currency)
- social_satisfaction: Social satisfaction level (Consider social_frequency: higher value means more need for social interaction)

Please response in json format, example:
{{
    "current_satisfaction": {{
        "hunger_satisfaction": 0.8,
        "energy_satisfaction": 0.7,
        "safety_satisfaction": 0.9,
        "social_satisfaction": 0.6
    }}
}}
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.

Return JSON only, without any extra text."""


class NeedsInitializeCitysim(NeedsInitializeAgentsociety):
    """Initialize satisfaction levels — citysim origin (adds life_stage, hobbies, goals)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")
    hobbies: Optional[str] = Field(None, description="Hobbies input value used by this prompt.")
    goals: Optional[str] = Field(None, description="Goals input value used by this prompt.")

    def format_prompt(self) -> str:
        return f"""You are an intelligent agent satisfaction initialization system. Based on the profile information below, please help initialize the agent's satisfaction levels and related parameters.

Profile Information:
- Gender: {_s(self.gender)}
- Education Level: {_s(self.education)}
- Consumption Level: {_s(self.consumption)}
- Occupation: {_s(self.occupation)}
- Age: {_s(self.age)}
- Monthly Income: {_s(self.income)}
- Household type: {_s(self.household)}
- Life stage: {_s(self.life_stage)}
- Hobbies: {_s(self.hobbies)}
- Goals: {_s(self.goals)}
- Big Five Personality Traits (1=Low, 2=Medium, 3=High):
  - Openness: {_s(self.openness)}
  - Conscientiousness: {_s(self.conscientiousness)}
  - Extraversion: {_s(self.extraversion)}
  - Agreeableness: {_s(self.agreeableness)}
  - Neuroticism: {_s(self.neuroticism)}
- Behavioral Preferences:
  - Social Frequency: {_s(self.social_frequency)} (0.0=Rarely initiates social contact, 1.0=Frequently seeks social interaction)

Current Time: {_s(self.current_time)}

Please initialize the agent's satisfaction levels and parameters based on the profile above. Return the values in JSON format with the following structure:

Current satisfaction levels (0-1 float values, lower means less satisfied):
- hunger_satisfaction: Hunger satisfaction level (Normally, the agent will be less satisfied with hunger at eating time)
- energy_satisfaction: Energy satisfaction level (Normally, at night, the agent will be less satisfied with energy)
- safety_satisfaction: Safety satisfaction level (Normally, the agent will be more satisfied with safety when they have high income and currency)
- social_satisfaction: Social satisfaction level (Consider social_frequency: higher value means more need for social interaction)

Please response in json format, example:
{{
    "current_satisfaction": {{
        "hunger_satisfaction": 0.8,
        "energy_satisfaction": 0.7,
        "safety_satisfaction": 0.9,
        "social_satisfaction": 0.6
    }}
}}
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.

Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# needs_poi_observation (citysim-only)
# ---------------------------------------------------------------------------

class NeedsPoiObservationCitysim(BasePrompt):
    """Encode POI interaction into belief observation vector — citysim origin."""

    name: ClassVar[str] = "needs_poi_observation"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "citysim"
    description: ClassVar[str] = "Encode POI interaction into belief observation vector"

    gender: Optional[str] = Field(None, description="Gender input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    income: Optional[str] = Field(None, description="Income input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    hobbies: Optional[str] = Field(None, description="Hobbies input value used by this prompt.")
    poi_name: Optional[str] = Field(None, description="POI name input value used by this prompt.")
    poi_category: Optional[str] = Field(None, description="POI category input value used by this prompt.")
    observation: Optional[str] = Field(None, description="Observation input value used by this prompt.")

    class Output(BaseModel):
        price: float = Field(description="Updated belief about price for this POI.")
        atmosphere: float = Field(description="Updated belief about atmosphere for this POI.")
        satisfaction: float = Field(description="Updated belief about expected satisfaction for this POI.")
        convenience: float = Field(description="Updated belief about convenience for this POI.")

    def format_prompt(self) -> str:
        return f"""You are a Spatial Memory Observation Encoder. Your task is to quantify the agent's experience at a Point of Interest (POI) into a numerical observation vector.

This vector will be fed into a Kalman filter to update the agent's long-term memory.

Profile Information:
- Gender: {_s(self.gender)}
- Age: {_s(self.age)}
- Income: {_s(self.income)}
- User Big Five Personality Traits: (1=Low, 2=Medium, 3=High)
  - Openness: {_s(self.openness)}
  - Conscientiousness: {_s(self.conscientiousness)}
  - Extraversion: {_s(self.extraversion)}
  - Agreeableness: {_s(self.agreeableness)}
  - Neuroticism: {_s(self.neuroticism)}
- Hobbies: {_s(self.hobbies)}

Context:
- POI Name: {_s(self.poi_name)}
- POI Category: {_s(self.poi_category)}

Interaction/Observation Log:
--------------------------------
{_s(self.observation)}
--------------------------------

Task:
Analyze the interaction log and the agent's profile to generate a quantitative score (0.0 to 1.0) for the following four dimensions based only on this specific visit.

Scoring Guidelines (1.0 is always POSITIVE/GOOD, 0.0 is NEGATIVE/BAD):

1. price: Evaluate the affordability/value.
   - 1.0 = Very Cheap / Excellent Value (Positive)
   - 0.0 = Very Expensive / Overpriced (Negative)

2. atmosphere: Evaluate the environment/vibe.
   - 1.0 = Excellent, Pleasant, Welcoming
   - 0.0 = Hostile, Dirty, Unpleasant

3. satisfaction: Evaluate the agent's overall fulfillment.
   - 1.0 = Highly Satisfied, Needs met perfectly
   - 0.0 = Unsatisfied, Regretful

4. convenience: Evaluate ease of access or service.
   - 1.0 = Very Convenient, Fast, Accessible
   - 0.0 = Inconvenient, Slow, Hard to find

Response Format:
Return ONLY valid JSON.

Example:
{{
    "price": 0.8,
    "atmosphere": 0.9,
    "satisfaction": 0.7,
    "convenience": 0.5
}}

DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.

Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# needs_reflection
# ---------------------------------------------------------------------------

class NeedsReflectionAgentsociety(BasePrompt):
    """Reflect intervention impact and rebuild needs — agentsociety origin."""

    name: ClassVar[str] = "needs_reflection"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Reflect intervention impact and rebuild needs"

    intervention_message: Optional[str] = Field(None, description="Intervention message input value used by this prompt.")
    current_action: Optional[str] = Field(None, description="Current action input value used by this prompt.")
    hunger_satisfaction: Optional[float] = Field(None, description="Current hunger satisfaction level (0.0 to 1.0).")
    energy_satisfaction: Optional[float] = Field(None, description="Current energy satisfaction level (0.0 to 1.0).")
    safety_satisfaction: Optional[float] = Field(None, description="Current safety satisfaction level (0.0 to 1.0).")
    social_satisfaction: Optional[float] = Field(None, description="Current social satisfaction level (0.0 to 1.0).")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")

    class Output(BaseModel):
        do_something: Optional[str] = Field(None, description="Whether intervention requires an explicit action.")
        description: Optional[str] = Field(None, description="Intervention action description when do_something is yes.")
        hunger_satisfaction: Optional[float] = Field(None, description="Updated hunger satisfaction level.")
        energy_satisfaction: Optional[float] = Field(None, description="Updated energy satisfaction level.")
        safety_satisfaction: Optional[float] = Field(None, description="Updated safety satisfaction level.")
        social_satisfaction: Optional[float] = Field(None, description="Updated social satisfaction level.")

    def format_prompt(self) -> str:
        return f"""You are an intelligent agent reflection system. Based on the intervention message below, please help to rebuild the satisfaction levels of the agent.

The agent has received/sense the following intervention message:
--------------------------------
{_s(self.intervention_message)}
--------------------------------

And the agent's current needs are:
- hunger_satisfaction: {_s(self.hunger_satisfaction)}
- energy_satisfaction: {_s(self.energy_satisfaction)}
- safety_satisfaction: {_s(self.safety_satisfaction)}
- social_satisfaction: {_s(self.social_satisfaction)}

Household type: {_s(self.household)}

The agent's current action is:
--------------------------------
{_s(self.current_action)}
--------------------------------

Please response in json format, example:
{{
    "hunger_satisfaction": new_hunger_satisfaction_value,
    "energy_satisfaction": new_energy_satisfaction_value,
    "safety_satisfaction": new_safety_satisfaction_value,
    "social_satisfaction": new_social_satisfaction_value
}}
If you think the agent has to stop the current action and do something to satisfy the needs, please response in json format, example:
{{
    "do_something": true,
    "description": "Go to the hospital"
}}

Return JSON only, without any extra text."""


class NeedsReflectionCitysim(NeedsReflectionAgentsociety):
    """Reflect intervention impact — citysim origin (adds Big Five + lifestyle fields)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")
    hobbies: Optional[str] = Field(None, description="Hobbies input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    social_frequency: Optional[float] = Field(None, description="Frequency of seeking social interaction (0.0 to 1.0).")

    def format_prompt(self) -> str:
        return f"""You are an intelligent agent reflection system. Based on the intervention message below, please help to rebuild the satisfaction levels of the agent.

The agent has received/sense the following intervention message:
--------------------------------
{_s(self.intervention_message)}
--------------------------------

And the agent's current needs are:
- hunger_satisfaction: {_s(self.hunger_satisfaction)}
- energy_satisfaction: {_s(self.energy_satisfaction)}
- safety_satisfaction: {_s(self.safety_satisfaction)}
- social_satisfaction: {_s(self.social_satisfaction)}

Household type: {_s(self.household)}
Life stage: {_s(self.life_stage)}
Hobbies: {_s(self.hobbies)}

Big Five Personality Traits (1=Low, 2=Medium, 3=High):
- Openness: {_s(self.openness)}
- Conscientiousness: {_s(self.conscientiousness)}
- Extraversion: {_s(self.extraversion)}
- Agreeableness: {_s(self.agreeableness)}
- Neuroticism: {_s(self.neuroticism)}

Behavioral Preferences:
- Social Frequency: {_s(self.social_frequency)} (0.0=Rarely initiates social contact, 1.0=Frequently seeks social interaction)

The agent's current action is:
--------------------------------
{_s(self.current_action)}
--------------------------------

Please response in json format, example:
{{
    "hunger_satisfaction": new_hunger_satisfaction_value,
    "energy_satisfaction": new_energy_satisfaction_value,
    "safety_satisfaction": new_safety_satisfaction_value,
    "social_satisfaction": new_social_satisfaction_value
}}
If you think the agent has to stop the current action and do something to satisfy the needs, please response in json format, example:
{{
    "do_something": true,
    "description": "Go to the hospital"
}}

Return JSON only, without any extra text."""
