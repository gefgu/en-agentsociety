"""Python prompt classes for MobilityBlock.

Contains:
- MobilityAoiAreaSelectionAgentsociety / Citysim
- MobilityNeighborhoodSelectionAgentsociety / Citysim
- MobilityPlaceAnalysisAgentsociety / Citysim
- MobilityPlaceTypeSelectionAgentsociety / Citysim
- MobilityPlaceSecondTypeSelectionAgentsociety / Citysim
- MobilityRadiusSelectionAgentsociety / Citysim
- MobilityTransportModeSelectionCitysim (citysim-only)
"""
from __future__ import annotations

from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field

from ..base import BasePrompt


def _s(v: object, d: str = "unknown") -> object:
    """Return *v* if not None, else *d*."""
    return v if v is not None else d


# ---------------------------------------------------------------------------
# mobility_aoi_area_selection
# ---------------------------------------------------------------------------

class MobilityAoiAreaSelectionAgentsociety(BasePrompt):
    """Select candidate AOI areas for place search — agentsociety origin."""

    name: ClassVar[str] = "mobility_aoi_area_selection"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Select candidate AOI areas for place search"

    plan: Optional[str] = Field(None, description="Plan input value used by this prompt.")
    intention: Optional[str] = Field(None, description="Intention input value used by this prompt.")
    emotion_types: Optional[str] = Field(None, description="Current emotion state (mapped from emotion_types).")
    thought: Optional[str] = Field(None, description="Thought input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    visit_history: Optional[str] = Field(None, description="Visit history input value used by this prompt.")
    ranked_areas: Optional[str] = Field(None, description="Ranked areas input value used by this prompt.")
    # Big Five used in template even for agentsociety origin
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")

    class Output(BaseModel):
        selected_area_ids: str = Field(description="Selected AOI area id list in JSON array form.")
        reasoning: str = Field(description="Reasoning for AOI area selection.")

    def format_prompt(self) -> str:
        return f"""As an intelligent decision system, please select 3-5 areas (AOIs) where the agent should look for places to visit.

Agent State:
- Current Plan: {_s(self.plan)}
- Current Intention: {_s(self.intention)}
- Current Emotion: {_s(self.emotion_types)}
- Current Thought: {_s(self.thought)}
- Household: {_s(self.household)}
Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {_s(self.openness)}, conscientiousness: {_s(self.conscientiousness)}, extraversion: {_s(self.extraversion)}, agreeableness: {_s(self.agreeableness)}, neuroticism: {_s(self.neuroticism)}.

Recent Visit History (last 7 days):
{_s(self.visit_history)}

Candidate Areas (ranked by distance and popularity):
{_s(self.ranked_areas)}

Please select 3-5 area IDs that best match the agent's intention, emotional state, and preferences.
Consider:
1. Distance (closer is generally better)
2. Popularity (more POIs = more options)
3. Past visit patterns
4. Current emotional state and intention

Please response in json format (Do not return any other text), example:
{{
    "selected_area_ids": [123, 456, 789],
    "reasoning": "Selected areas close to home with high popularity for shopping"
}}

Return JSON only, without any extra text."""


class MobilityAoiAreaSelectionCitysim(MobilityAoiAreaSelectionAgentsociety):
    """Select candidate AOI areas — citysim origin (adds life_stage + explicit Big Five)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")

    def format_prompt(self) -> str:
        return f"""As an intelligent decision system, please select 3-5 areas (AOIs) where the agent should look for places to visit.

Agent State:
- Current Plan: {_s(self.plan)}
- Current Intention: {_s(self.intention)}
- Current Emotion: {_s(self.emotion_types)}
- Current Thought: {_s(self.thought)}
- Household: {_s(self.household)}
- Life Stage: {_s(self.life_stage)}
Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {_s(self.openness)}, conscientiousness: {_s(self.conscientiousness)}, extraversion: {_s(self.extraversion)}, agreeableness: {_s(self.agreeableness)}, neuroticism: {_s(self.neuroticism)}.

Recent Visit History (last 7 days):
{_s(self.visit_history)}

Candidate Areas (ranked by distance and popularity):
{_s(self.ranked_areas)}

Please select 3-5 area IDs that best match the agent's intention, emotional state, and preferences.
Consider:
1. Distance (closer is generally better)
2. Popularity (more POIs = more options)
3. Past visit patterns
4. Current emotional state and intention

Please response in json format (Do not return any other text), example:
{{
    "selected_area_ids": [123, 456, 789],
    "reasoning": "Selected areas close to home with high popularity for shopping"
}}

Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# mobility_neighborhood_selection
# ---------------------------------------------------------------------------

class MobilityNeighborhoodSelectionAgentsociety(BasePrompt):
    """Select candidate neighborhoods for place search — agentsociety origin."""

    name: ClassVar[str] = "mobility_neighborhood_selection"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Select candidate neighborhoods for place search"

    plan: Optional[str] = Field(None, description="Plan input value used by this prompt.")
    intention: Optional[str] = Field(None, description="Intention input value used by this prompt.")
    emotion_types: Optional[str] = Field(None, description="Current emotion state (mapped from emotion_types).")
    thought: Optional[str] = Field(None, description="Thought input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    visit_history: Optional[str] = Field(None, description="Visit history input value used by this prompt.")
    candidate_neighborhoods: Optional[str] = Field(None, description="Candidate neighborhoods input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")

    class Output(BaseModel):
        selected_neighborhood_ids: str = Field(description="Selected neighborhood id list in JSON array form.")
        reasoning: str = Field(description="Reasoning for neighborhood selection.")

    def format_prompt(self) -> str:
        return f"""As an intelligent decision system, please select 3-5 neighborhoods where the agent should look for places to visit.

Agent State:
- Current Plan: {_s(self.plan)}
- Current Intention: {_s(self.intention)}
- Current Emotion: {_s(self.emotion_types)}
- Current Thought: {_s(self.thought)}
- Household: {_s(self.household)}
Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {_s(self.openness)}, conscientiousness: {_s(self.conscientiousness)}, extraversion: {_s(self.extraversion)}, agreeableness: {_s(self.agreeableness)}, neuroticism: {_s(self.neuroticism)}.

Recent Visit History (last 7 days):
{_s(self.visit_history)}

Candidate Neighborhoods (ranked by matching POI count):
{_s(self.candidate_neighborhoods)}

Please select 3-5 neighborhood IDs that best match the agent's intention, emotional state, and preferences.

Please response in json format (Do not return any other text), example:
{{
    "selected_neighborhood_ids": [123, 456, 789],
    "reasoning": "Selected neighborhoods with enough matching options"
}}

Return JSON only, without any extra text."""


class MobilityNeighborhoodSelectionCitysim(MobilityNeighborhoodSelectionAgentsociety):
    """Select candidate neighborhoods — citysim origin (adds life_stage)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")

    def format_prompt(self) -> str:
        return f"""As an intelligent decision system, please select 3-5 neighborhoods where the agent should look for places to visit.

Agent State:
- Current Plan: {_s(self.plan)}
- Current Intention: {_s(self.intention)}
- Current Emotion: {_s(self.emotion_types)}
- Current Thought: {_s(self.thought)}
- Household: {_s(self.household)}
- Life Stage: {_s(self.life_stage)}
Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {_s(self.openness)}, conscientiousness: {_s(self.conscientiousness)}, extraversion: {_s(self.extraversion)}, agreeableness: {_s(self.agreeableness)}, neuroticism: {_s(self.neuroticism)}.

Recent Visit History (last 7 days):
{_s(self.visit_history)}

Candidate Neighborhoods (ranked by matching POI count):
{_s(self.candidate_neighborhoods)}

Please select 3-5 neighborhood IDs that best match the agent's intention, emotional state, and preferences.

Please response in json format (Do not return any other text), example:
{{
    "selected_neighborhood_ids": [123, 456, 789],
    "reasoning": "Selected neighborhoods with enough matching options"
}}

Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# mobility_place_analysis
# ---------------------------------------------------------------------------

class MobilityPlaceAnalysisAgentsociety(BasePrompt):
    """Decide whether to go home, workplace, known place, or other — agentsociety origin."""

    name: ClassVar[str] = "mobility_place_analysis"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Decide whether to go home, workplace, known place, or other"

    plan: Optional[str] = Field(None, description="Plan input value used by this prompt.")
    intention: Optional[str] = Field(None, description="Intention input value used by this prompt.")
    place_list: Optional[Any] = Field(None, description="Place list input value used by this prompt.")
    other_info: Optional[str] = Field(None, description="Other info input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    leisure_preference: Optional[str] = Field(None, description="Leisure preference (outdoor/indoor/social/solitary).")
    risk_tolerance: Optional[float] = Field(None, description="Risk tolerance for uncertain or unfamiliar options (0.0 to 1.0).")

    class Output(BaseModel):
        place_type: str = Field(description="Selected destination category.")

    def format_prompt(self) -> str:
        return f"""As an intelligent analysis system, please determine the type of place the user needs to visit based on their input requirement.
User Plan: {_s(self.plan)}
User requirement: {_s(self.intention)}
Household type: {_s(self.household)}
Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {_s(self.openness)}, conscientiousness: {_s(self.conscientiousness)}, extraversion: {_s(self.extraversion)}, agreeableness: {_s(self.agreeableness)}, neuroticism: {_s(self.neuroticism)}.
Your behavioral preferences are:
- Leisure Preference: {_s(self.leisure_preference)} (outdoor/indoor/social/solitary preference for free time)
- Risk Tolerance: {_s(self.risk_tolerance)} (0.0=Risk-averse, 1.0=Risk-seeking for new/unfamiliar places)
Other information:
-------------------------
{_s(self.other_info)}
-------------------------

Your output must be a single selection from {_s(self.place_list)} without any additional text or explanation.

Please response in json format (Do not return any other text), example:
{{
    "place_type": "home"
}}

Return JSON only, without any extra text."""


class MobilityPlaceAnalysisCitysim(MobilityPlaceAnalysisAgentsociety):
    """Decide whether to go home, workplace, etc. — citysim origin (adds Big Five + lifestyle)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")
    hobbies: Optional[str] = Field(None, description="Hobbies input value used by this prompt.")
    goals: Optional[str] = Field(None, description="Goals input value used by this prompt.")

    def format_prompt(self) -> str:
        return f"""As an intelligent analysis system, please determine the type of place the user needs to visit based on their input requirement.
User Plan: {_s(self.plan)}
User requirement: {_s(self.intention)}
Household type: {_s(self.household)}
Life stage: {_s(self.life_stage)}
Hobbies: {_s(self.hobbies)}
Goals: {_s(self.goals)}
Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {_s(self.openness)}, conscientiousness: {_s(self.conscientiousness)}, extraversion: {_s(self.extraversion)}, agreeableness: {_s(self.agreeableness)}, neuroticism: {_s(self.neuroticism)}.
Your behavioral preferences are:
- Leisure Preference: {_s(self.leisure_preference)} (outdoor/indoor/social/solitary preference for free time)
- Risk Tolerance: {_s(self.risk_tolerance)} (0.0=Risk-averse, 1.0=Risk-seeking for new/unfamiliar places)
Other information:
-------------------------
{_s(self.other_info)}
-------------------------

Your output must be a single selection from {_s(self.place_list)} without any additional text or explanation.

Please response in json format (Do not return any other text), example:
{{
    "place_type": "home"
}}

Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# mobility_place_type_selection
# ---------------------------------------------------------------------------

class MobilityPlaceTypeSelectionAgentsociety(BasePrompt):
    """Select primary POI category for mobility destination — agentsociety origin."""

    name: ClassVar[str] = "mobility_place_type_selection"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Select primary POI category for mobility destination"

    plan: Optional[str] = Field(None, description="Plan input value used by this prompt.")
    intention: Optional[str] = Field(None, description="Intention input value used by this prompt.")
    poi_category: Optional[Any] = Field(None, description="POI category input value used by this prompt.")
    other_info: Optional[str] = Field(None, description="Other info input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    leisure_preference: Optional[str] = Field(None, description="Leisure preference (outdoor/indoor/social/solitary).")
    risk_tolerance: Optional[float] = Field(None, description="Risk tolerance (0.0 to 1.0).")

    class Output(BaseModel):
        place_type: str = Field(description="Selected primary place type.")

    def format_prompt(self) -> str:
        return f"""As an intelligent decision system, please determine the type of place the user needs to visit based on their input requirement.
User Plan: {_s(self.plan)}
User requirement: {_s(self.intention)}
Household type: {_s(self.household)}
Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {_s(self.openness)}, conscientiousness: {_s(self.conscientiousness)}, extraversion: {_s(self.extraversion)}, agreeableness: {_s(self.agreeableness)}, neuroticism: {_s(self.neuroticism)}.
Your behavioral preferences are:
- Leisure Preference: {_s(self.leisure_preference)} (outdoor/indoor/social/solitary preference for free time)
- Risk Tolerance: {_s(self.risk_tolerance)} (0.0=Risk-averse, 1.0=Risk-seeking for new/unfamiliar places)
Other information:
-------------------------
{_s(self.other_info)}
-------------------------
Your output must be a single selection from {_s(self.poi_category)} without any additional text or explanation.

Please response in json format (Do not return any other text), example:
{{
    "place_type": "shopping"
}}

Return JSON only, without any extra text."""


class MobilityPlaceTypeSelectionCitysim(MobilityPlaceTypeSelectionAgentsociety):
    """Select primary POI category — citysim origin (adds Big Five + lifestyle)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")
    hobbies: Optional[str] = Field(None, description="Hobbies input value used by this prompt.")
    goals: Optional[str] = Field(None, description="Goals input value used by this prompt.")

    def format_prompt(self) -> str:
        return f"""As an intelligent decision system, please determine the type of place the user needs to visit based on their input requirement.
User Plan: {_s(self.plan)}
User requirement: {_s(self.intention)}
Household type: {_s(self.household)}
Life stage: {_s(self.life_stage)}
Hobbies: {_s(self.hobbies)}
Goals: {_s(self.goals)}
Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {_s(self.openness)}, conscientiousness: {_s(self.conscientiousness)}, extraversion: {_s(self.extraversion)}, agreeableness: {_s(self.agreeableness)}, neuroticism: {_s(self.neuroticism)}.
Your behavioral preferences are:
- Leisure Preference: {_s(self.leisure_preference)} (outdoor/indoor/social/solitary preference for free time)
- Risk Tolerance: {_s(self.risk_tolerance)} (0.0=Risk-averse, 1.0=Risk-seeking for new/unfamiliar places)
Other information:
-------------------------
{_s(self.other_info)}
-------------------------
Your output must be a single selection from {_s(self.poi_category)} without any additional text or explanation.

Please response in json format (Do not return any other text), example:
{{
    "place_type": "shopping"
}}

Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# mobility_place_second_type_selection
# ---------------------------------------------------------------------------

class MobilityPlaceSecondTypeSelectionAgentsociety(BasePrompt):
    """Select secondary POI category for mobility destination — agentsociety origin."""

    name: ClassVar[str] = "mobility_place_second_type_selection"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Select secondary POI category for mobility destination"

    plan: Optional[str] = Field(None, description="Plan input value used by this prompt.")
    intention: Optional[str] = Field(None, description="Intention input value used by this prompt.")
    poi_category: Optional[Any] = Field(None, description="POI category input value used by this prompt.")
    other_info: Optional[str] = Field(None, description="Other info input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    leisure_preference: Optional[str] = Field(None, description="Leisure preference (outdoor/indoor/social/solitary).")
    risk_tolerance: Optional[float] = Field(None, description="Risk tolerance (0.0 to 1.0).")

    class Output(BaseModel):
        place_type: str = Field(description="Selected secondary place type.")

    def format_prompt(self) -> str:
        return f"""As an intelligent decision system, please determine the type of place the user needs to visit based on their input requirement.
User Plan: {_s(self.plan)}
User requirement: {_s(self.intention)}
Household type: {_s(self.household)}
Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {_s(self.openness)}, conscientiousness: {_s(self.conscientiousness)}, extraversion: {_s(self.extraversion)}, agreeableness: {_s(self.agreeableness)}, neuroticism: {_s(self.neuroticism)}.
Your behavioral preferences are:
- Leisure Preference: {_s(self.leisure_preference)} (outdoor/indoor/social/solitary preference for free time)
- Risk Tolerance: {_s(self.risk_tolerance)} (0.0=Risk-averse, 1.0=Risk-seeking for new/unfamiliar places)
Other information:
-------------------------
{_s(self.other_info)}
-------------------------

Your output must be a single selection from {_s(self.poi_category)} without any additional text or explanation.

Please response in json format (Do not return any other text), example:
{{
    "place_type": "shopping"
}}

Return JSON only, without any extra text."""


class MobilityPlaceSecondTypeSelectionCitysim(MobilityPlaceSecondTypeSelectionAgentsociety):
    """Select secondary POI category — citysim origin (adds Big Five + lifestyle)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")
    hobbies: Optional[str] = Field(None, description="Hobbies input value used by this prompt.")
    goals: Optional[str] = Field(None, description="Goals input value used by this prompt.")

    def format_prompt(self) -> str:
        return f"""As an intelligent decision system, please determine the type of place the user needs to visit based on their input requirement.
User Plan: {_s(self.plan)}
User requirement: {_s(self.intention)}
Household type: {_s(self.household)}
Life stage: {_s(self.life_stage)}
Hobbies: {_s(self.hobbies)}
Goals: {_s(self.goals)}
Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {_s(self.openness)}, conscientiousness: {_s(self.conscientiousness)}, extraversion: {_s(self.extraversion)}, agreeableness: {_s(self.agreeableness)}, neuroticism: {_s(self.neuroticism)}.
Your behavioral preferences are:
- Leisure Preference: {_s(self.leisure_preference)} (outdoor/indoor/social/solitary preference for free time)
- Risk Tolerance: {_s(self.risk_tolerance)} (0.0=Risk-averse, 1.0=Risk-seeking for new/unfamiliar places)
Other information:
-------------------------
{_s(self.other_info)}
-------------------------

Your output must be a single selection from {_s(self.poi_category)} without any additional text or explanation.

Please response in json format (Do not return any other text), example:
{{
    "place_type": "shopping"
}}

Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# mobility_radius_selection
# ---------------------------------------------------------------------------

class MobilityRadiusSelectionAgentsociety(BasePrompt):
    """Determine mobility travel radius from current state — agentsociety origin."""

    name: ClassVar[str] = "mobility_radius_selection"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Determine mobility travel radius from current state"

    weather: Optional[str] = Field(None, description="Weather input value used by this prompt.")
    temperature: Optional[float] = Field(None, description="Current temperature context value.")
    current_emotion: Optional[str] = Field(None, description="Current emotion input value used by this prompt.")
    current_thought: Optional[str] = Field(None, description="Current thought input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    other_information: Optional[str] = Field(None, description="Other information input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    risk_tolerance: Optional[float] = Field(None, description="Risk tolerance (0.0 to 1.0).")

    class Output(BaseModel):
        radius: int = Field(description="Selected mobility search radius in meters.")

    def format_prompt(self) -> str:
        return f"""As an intelligent decision system, please determine the maximum travel radius (in meters) based on the current emotional state.

Current weather: {_s(self.weather)}
Current temperature: {_s(self.temperature)}
Your current emotion: {_s(self.current_emotion)}
Your current thought: {_s(self.current_thought)}
Household type: {_s(self.household)}
Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {_s(self.openness)}, conscientiousness: {_s(self.conscientiousness)}, extraversion: {_s(self.extraversion)}, agreeableness: {_s(self.agreeableness)}, neuroticism: {_s(self.neuroticism)}.
Your behavioral preferences:
- Risk Tolerance: {_s(self.risk_tolerance)} (0.0=Risk-averse/prefers nearby, 1.0=Risk-seeking/willing to travel far)
Other information:
-------------------------
{_s(self.other_information)}
-------------------------

Please analyze how these emotions and preferences would affect travel willingness and return only a single integer number between 3000-200000 representing the maximum travel radius in meters. A more positive emotional state and higher risk tolerance generally lead to greater willingness to travel further.

Please response in json format (Do not return any other text), example:
{{
    "radius": 10000
}}

Return JSON only, without any extra text."""


class MobilityRadiusSelectionCitysim(MobilityRadiusSelectionAgentsociety):
    """Determine mobility travel radius — citysim origin (adds life_stage + hobbies)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")
    hobbies: Optional[str] = Field(None, description="Hobbies input value used by this prompt.")

    # Template is identical to agentsociety; format_prompt() is inherited.


# ---------------------------------------------------------------------------
# mobility_transport_mode_selection (citysim-only)
# ---------------------------------------------------------------------------

class MobilityTransportModeSelectionCitysim(BasePrompt):
    """Select transport mode from trip and persona context — citysim origin."""

    name: ClassVar[str] = "mobility_transport_mode_selection"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "citysim"
    description: ClassVar[str] = "Select transport mode from trip and persona context"

    distance: Optional[float] = Field(None, description="Travel distance value used for decision-making.")
    time: Optional[Any] = Field(None, description="Estimated duration in minutes.")
    month: Optional[str] = Field(None, description="Month input value used by this prompt.")
    weather: Optional[str] = Field(None, description="Weather input value used by this prompt.")
    temperature: Optional[float] = Field(None, description="Current temperature context value.")
    persona: Optional[str] = Field(None, description="Persona input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")
    hobbies: Optional[str] = Field(None, description="Hobbies input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    risk_tolerance: Optional[float] = Field(None, description="Risk tolerance (0.0 to 1.0).")
    emotion_types: Optional[str] = Field(None, description="Current emotion/thought state.")
    available_modes: Optional[str] = Field(None, description="Available modes input value used by this prompt.")

    class Output(BaseModel):
        mode: str = Field(description="Selected transport mode.")
        reason: str = Field(description="Reasoning for selecting transport mode.")

    def format_prompt(self) -> str:
        return f"""As an intelligent transport decision system, please select the most appropriate transport mode for the user based on the current context and their persona.
You are approximating a utility function where you maximize the user's comfort, efficiency, and preference.

Context:
- Trip Distance: {_s(self.distance)} meters
- Current Time: {_s(self.time)}
- Month: {_s(self.month)}
- Weather: {_s(self.weather)}
- Temperature: {_s(self.temperature)}
- User Persona: {_s(self.persona)}
- Household type: {_s(self.household)}
- Life stage: {_s(self.life_stage)}
- Hobbies: {_s(self.hobbies)}
- User Big Five Personality Traits: (1=Low, 2=Medium, 3=High)
  - Openness: {_s(self.openness)}
  - Conscientiousness: {_s(self.conscientiousness)}
  - Extraversion: {_s(self.extraversion)}
  - Agreeableness: {_s(self.agreeableness)}
  - Neuroticism: {_s(self.neuroticism)}
- User Behavioral Preferences:
  - Risk Tolerance: {_s(self.risk_tolerance)} (0.0=Prefers safe/familiar modes, 1.0=Open to new/adventurous modes)
- User Current Emotion/Thought: {_s(self.emotion_types)}

Available Transport Modes:
{_s(self.available_modes)}

Please analyze the utility of each mode given the weather (e.g., avoid walking in heavy rain), distance (e.g., avoid walking for >2km), persona, and risk tolerance.
Select one mode and provide a brief reason.

Please response in json format (Do not return any other text), example:
{{
    "mode": "TRIP_MODE_DRIVE_ONLY",
    "reason": "Given the heavy rain and the 5km distance, driving is the most comfortable option despite the traffic."
}}

Return JSON only, without any extra text."""
