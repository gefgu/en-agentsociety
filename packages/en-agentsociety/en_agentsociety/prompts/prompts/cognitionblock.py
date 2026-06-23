"""Python prompt classes for CognitionBlock.

Contains:
- CognitionAttitudeUpdateAgentsociety / Citysim
- CognitionEmotionUpdateAgentsociety / Citysim
- CognitionThoughtUpdateAgentsociety / Citysim
- CognitionInitializeBig5Citysim (citysim-only)
- CognitionInitializeHobbiesCitysim (citysim-only)
- CognitionInitializePreferencesCitysim (citysim-only)
"""
from __future__ import annotations

from typing import Any, ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..base import BasePrompt


def _s(v: object, d: str = "unknown") -> object:
    """Return *v* if not None, else *d*."""
    return v if v is not None else d


# ---------------------------------------------------------------------------
# cognition_attitude_update
# ---------------------------------------------------------------------------

class CognitionAttitudeUpdateAgentsociety(BasePrompt):
    """Update topic attitude based on profile, emotions, and incidents — agentsociety origin."""

    name: ClassVar[str] = "cognition_attitude_update"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Update topic attitude based on profile, emotions, and incidents"

    gender: Optional[str] = Field(None, description="Gender input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    race: Optional[str] = Field(None, description="Race input value used by this prompt.")
    religion: Optional[str] = Field(None, description="Religion input value used by this prompt.")
    marriage_status: Optional[str] = Field(None, description="Marriage status input value used by this prompt.")
    residence: Optional[str] = Field(None, description="Residence input value used by this prompt.")
    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    education: Optional[str] = Field(None, description="Education input value used by this prompt.")
    personality: Optional[str] = Field(None, description="Personality input value used by this prompt.")
    consumption: Optional[float] = Field(None, description="Consumption input value used by this prompt.")
    family_consumption: Optional[str] = Field(None, description="Family consumption input value used by this prompt.")
    income: Optional[str] = Field(None, description="Income input value used by this prompt.")
    skill: Optional[str] = Field(None, description="Skill input value used by this prompt.")
    thought: Optional[str] = Field(None, description="Thought input value used by this prompt.")
    emotion_types: Optional[str] = Field(None, description="Emotion types input value used by this prompt.")
    sadness: Optional[str] = Field(None, description="Sadness input value used by this prompt.")
    joy: Optional[str] = Field(None, description="Joy input value used by this prompt.")
    fear: Optional[str] = Field(None, description="Fear input value used by this prompt.")
    disgust: Optional[str] = Field(None, description="Disgust input value used by this prompt.")
    anger: Optional[str] = Field(None, description="Anger input value used by this prompt.")
    surprise: Optional[str] = Field(None, description="Surprise input value used by this prompt.")
    topic: Optional[str] = Field(None, description="Topic input value used by this prompt.")
    previous_attitude: Optional[str] = Field(None, description="Previous attitude input value used by this prompt.")
    incident_text: Optional[str] = Field(None, description="Incident text input value used by this prompt.")
    # Big Five used in template even for agentsociety origin (fallback to "unknown" if not set)
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")

    class Output(BaseModel):
        attitude: int = Field(description="Updated attitude score in range 0-10.")

    def format_prompt(self) -> str:
        return f"""You are a {_s(self.gender)}, aged {_s(self.age)}, belonging to the {_s(self.race)} race and identifying as {_s(self.religion)}.
Your marital status is {_s(self.marriage_status)}, and you currently reside in a {_s(self.residence)} area.
Your occupation is {_s(self.occupation)}, and your education level is {_s(self.education)}.
You are {_s(self.personality)}, with a consumption level of {_s(self.consumption)} and a family consumption level of {_s(self.family_consumption)}.
Your income is {_s(self.income)}, and you are skilled in {_s(self.skill)}.

My current emotion intensities are (0 meaning not at all, 10 meaning very much):
sadness: {_s(self.sadness)}, joy: {_s(self.joy)}, fear: {_s(self.fear)}, disgust: {_s(self.disgust)}, anger: {_s(self.anger)}, surprise: {_s(self.surprise)}.

Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {_s(self.openness)}, conscientiousness: {_s(self.conscientiousness)}, extraversion: {_s(self.extraversion)}, agreeableness: {_s(self.agreeableness)}, neuroticism: {_s(self.neuroticism)}.

You have the following thoughts: {_s(self.thought)}.
In the following 21 words, I have chosen {_s(self.emotion_types)} to represent your current status:
Joy, Distress, Resentment, Pity, Hope, Fear, Satisfaction, Relief, Disappointment, Pride, Admiration, Shame, Reproach, Liking, Disliking, Gratitude, Anger, Gratification, Remorse, Love, Hate.

{_s(self.incident_text)}

You need to decide your attitude towards topic: {_s(self.topic)}, which you previously rated as: {_s(self.previous_attitude)} (0 meaning oppose, 10 meaning support).
Please return a new attitude rating (0-10, smaller meaning oppose, larger meaning support) in JSON format, e.g. {{"attitude": 5}}.

Return JSON only, without any extra text."""


class CognitionAttitudeUpdateCitysim(CognitionAttitudeUpdateAgentsociety):
    """Update topic attitude — citysim origin (Big Five explicitly declared in inputs)."""

    origin: ClassVar[str] = "citysim"
    # Template and fields are identical; citysim just ensures Big Five is resolved from memory.
    # format_prompt() is inherited.


# ---------------------------------------------------------------------------
# cognition_emotion_update
# ---------------------------------------------------------------------------

class CognitionEmotionUpdateAgentsociety(BasePrompt):
    """Update emotion intensities from incident context — agentsociety origin."""

    name: ClassVar[str] = "cognition_emotion_update"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Update emotion intensities from incident context"

    gender: Optional[str] = Field(None, description="Gender input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    race: Optional[str] = Field(None, description="Race input value used by this prompt.")
    religion: Optional[str] = Field(None, description="Religion input value used by this prompt.")
    marriage_status: Optional[str] = Field(None, description="Marriage status input value used by this prompt.")
    residence: Optional[str] = Field(None, description="Residence input value used by this prompt.")
    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    education: Optional[str] = Field(None, description="Education input value used by this prompt.")
    personality: Optional[str] = Field(None, description="Personality input value used by this prompt.")
    consumption: Optional[float] = Field(None, description="Consumption input value used by this prompt.")
    family_consumption: Optional[str] = Field(None, description="Family consumption input value used by this prompt.")
    income: Optional[str] = Field(None, description="Income input value used by this prompt.")
    skill: Optional[str] = Field(None, description="Skill input value used by this prompt.")
    thought: Optional[str] = Field(None, description="Thought input value used by this prompt.")
    sadness: Optional[str] = Field(None, description="Sadness input value used by this prompt.")
    joy: Optional[str] = Field(None, description="Joy input value used by this prompt.")
    fear: Optional[str] = Field(None, description="Fear input value used by this prompt.")
    disgust: Optional[str] = Field(None, description="Disgust input value used by this prompt.")
    anger: Optional[str] = Field(None, description="Anger input value used by this prompt.")
    surprise: Optional[str] = Field(None, description="Surprise input value used by this prompt.")
    incident_text: Optional[str] = Field(None, description="Incident text input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")

    class Output(BaseModel):
        word: str = Field(description="Dominant emotion keyword.")
        sadness: int = Field(description="Updated sadness score.")
        joy: int = Field(description="Updated joy score.")
        fear: int = Field(description="Updated fear score.")
        disgust: int = Field(description="Updated disgust score.")
        anger: int = Field(description="Updated anger score.")
        surprise: int = Field(description="Updated surprise score.")
        conclusion: str = Field(description="Free-text conclusion for emotion update.")

    def format_prompt(self) -> str:
        return f"""You are a {_s(self.gender)}, aged {_s(self.age)}, belonging to the {_s(self.race)} race and identifying as {_s(self.religion)}.
Your marital status is {_s(self.marriage_status)}, and you currently reside in a {_s(self.residence)} area.
Your occupation is {_s(self.occupation)}, and your education level is {_s(self.education)}.
You are {_s(self.personality)}, with a consumption level of {_s(self.consumption)} and a family consumption level of {_s(self.family_consumption)}.
Your income is {_s(self.income)}, and you are skilled in {_s(self.skill)}.

My current emotion intensities are (0 meaning not at all, 10 meaning very much):
sadness: {_s(self.sadness)}, joy: {_s(self.joy)}, fear: {_s(self.fear)}, disgust: {_s(self.disgust)}, anger: {_s(self.anger)}, surprise: {_s(self.surprise)}.

Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {_s(self.openness)}, conscientiousness: {_s(self.conscientiousness)}, extraversion: {_s(self.extraversion)}, agreeableness: {_s(self.agreeableness)}, neuroticism: {_s(self.neuroticism)}.

You have the following thoughts: {_s(self.thought)}.
In the following 21 words, choose one word to represent your current status:
[Joy, Distress, Resentment, Pity, Hope, Fear, Satisfaction, Relief, Disappointment, Pride, Admiration, Shame, Reproach, Liking, Disliking, Gratitude, Anger, Gratification, Remorse, Love, Hate].

Incident:
{_s(self.incident_text)}

Please reconsider your emotion intensities: sadness, joy, fear, disgust, anger, surprise (0 meaning not at all, 10 meaning very much).
Return in JSON format, e.g. {{"sadness": 5, "joy": 5, "fear": 5, "disgust": 5, "anger": 5, "surprise": 5, "conclusion": "I feel ...", "word": "Relief"}}.

Return JSON only, without any extra text."""


class CognitionEmotionUpdateCitysim(CognitionEmotionUpdateAgentsociety):
    """Update emotion intensities — citysim origin (Big Five explicitly in inputs)."""

    origin: ClassVar[str] = "citysim"
    # Template and fields are identical; format_prompt() is inherited.


# ---------------------------------------------------------------------------
# cognition_thought_update
# ---------------------------------------------------------------------------

class CognitionThoughtUpdateAgentsociety(BasePrompt):
    """Generate daily reflection thought from profile, emotions, and incidents — agentsociety origin."""

    name: ClassVar[str] = "cognition_thought_update"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Generate daily reflection thought from profile, emotions, and incidents"

    gender: Optional[str] = Field(None, description="Gender input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    race: Optional[str] = Field(None, description="Race input value used by this prompt.")
    religion: Optional[str] = Field(None, description="Religion input value used by this prompt.")
    marriage_status: Optional[str] = Field(None, description="Marriage status input value used by this prompt.")
    residence: Optional[str] = Field(None, description="Residence input value used by this prompt.")
    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    education: Optional[str] = Field(None, description="Education input value used by this prompt.")
    personality: Optional[str] = Field(None, description="Personality input value used by this prompt.")
    consumption: Optional[float] = Field(None, description="Consumption input value used by this prompt.")
    family_consumption: Optional[str] = Field(None, description="Family consumption input value used by this prompt.")
    income: Optional[str] = Field(None, description="Income input value used by this prompt.")
    skill: Optional[str] = Field(None, description="Skill input value used by this prompt.")
    thought: Optional[str] = Field(None, description="Thought input value used by this prompt.")
    emotion_types: Optional[str] = Field(None, description="Emotion types input value used by this prompt.")
    sadness: Optional[str] = Field(None, description="Sadness input value used by this prompt.")
    joy: Optional[str] = Field(None, description="Joy input value used by this prompt.")
    fear: Optional[str] = Field(None, description="Fear input value used by this prompt.")
    disgust: Optional[str] = Field(None, description="Disgust input value used by this prompt.")
    anger: Optional[str] = Field(None, description="Anger input value used by this prompt.")
    surprise: Optional[str] = Field(None, description="Surprise input value used by this prompt.")
    incident_text: Optional[str] = Field(None, description="Incident text input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")

    class Output(BaseModel):
        thought: str = Field(description="Generated daily thought summary.")

    def format_prompt(self) -> str:
        return f"""You are a {_s(self.gender)}, aged {_s(self.age)}, belonging to the {_s(self.race)} race and identifying as {_s(self.religion)}.
Your marital status is {_s(self.marriage_status)}, and you currently reside in a {_s(self.residence)} area.
Your occupation is {_s(self.occupation)}, and your education level is {_s(self.education)}.
You are {_s(self.personality)}, with a consumption level of {_s(self.consumption)} and a family consumption level of {_s(self.family_consumption)}.
Your income is {_s(self.income)}, and you are skilled in {_s(self.skill)}.

My current emotion intensities are (0 meaning not at all, 10 meaning very much):
sadness: {_s(self.sadness)}, joy: {_s(self.joy)}, fear: {_s(self.fear)}, disgust: {_s(self.disgust)}, anger: {_s(self.anger)}, surprise: {_s(self.surprise)}.

Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {_s(self.openness)}, conscientiousness: {_s(self.conscientiousness)}, extraversion: {_s(self.extraversion)}, agreeableness: {_s(self.agreeableness)}, neuroticism: {_s(self.neuroticism)}.

You have the following thoughts: {_s(self.thought)}.
In the following 21 words, I have chosen {_s(self.emotion_types)} to represent your current status:
Joy, Distress, Resentment, Pity, Hope, Fear, Satisfaction, Relief, Disappointment, Pride, Admiration, Shame, Reproach, Liking, Disliking, Gratitude, Anger, Gratification, Remorse, Love, Hate.

{_s(self.incident_text)}

Please review what happened today and share your thoughts and feelings about it.
Consider your current emotional state and experiences, then:
1. Summarize your thoughts and reflections on today's events.
2. Choose one word that best describes your current emotional state from: Joy, Distress, Resentment, Pity, Hope, Fear, Satisfaction, Relief, Disappointment, Pride, Admiration, Shame, Reproach, Liking, Disliking, Gratitude, Anger, Gratification, Remorse, Love, Hate.

Return in JSON format, e.g. {{"thought": "Currently nothing good or bad is happening, I think ..."}}.

Return JSON only, without any extra text."""


class CognitionThoughtUpdateCitysim(CognitionThoughtUpdateAgentsociety):
    """Generate daily reflection thought — citysim origin (Big Five explicitly in inputs)."""

    origin: ClassVar[str] = "citysim"
    # Template and fields are identical; format_prompt() is inherited.


# ---------------------------------------------------------------------------
# cognition_initialize_big5 (citysim-only)
# ---------------------------------------------------------------------------

class CognitionInitializeBig5Citysim(BasePrompt):
    """Initialize Big Five psychographic traits from profile — citysim origin."""

    name: ClassVar[str] = "cognition_initialize_big5"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "citysim"
    description: ClassVar[str] = "Initialize Big Five psychographic traits from profile"

    gender: Optional[str] = Field(None, description="Gender input value used by this prompt.")
    education: Optional[str] = Field(None, description="Education input value used by this prompt.")
    consumption: Optional[float] = Field(None, description="Consumption input value used by this prompt.")
    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    income: Optional[str] = Field(None, description="Income input value used by this prompt.")
    background_story: Optional[str] = Field(None, description="Background story input value used by this prompt.")

    class Output(BaseModel):
        psychographic_traits: dict[str, int] = Field(description="Big Five trait values (each 1–3).")

    def format_prompt(self) -> str:
        return f"""You are an intelligent agent psychographic initialization system. Based on the profile information below, please help initialize the agent's Big Five personality traits.

Profile Information:
- Gender: {_s(self.gender)}
- Education Level: {_s(self.education)}
- Consumption Level: {_s(self.consumption)}
- Occupation: {_s(self.occupation)}
- Age: {_s(self.age)}
- Monthly Income: {_s(self.income)}
- Background Story: {_s(self.background_story)}

Please initialize the agent's Big Five personality traits based on the profile above. Consider generally accepted associations between the provided demographic/socioeconomic factors and personality (e.g., occupation requirements, age maturity principles).

Return the values in JSON format with the following structure:

Psychographic Traits (Integer values 1-3, where 1=Low, 2=Medium, 3=High):
- openness: Openness to experience (creativity, curiosity, preference for novelty)
- conscientiousness: Conscientiousness (discipline, organization, dependability)
- extraversion: Extraversion (sociability, energy, assertiveness)
- agreeableness: Agreeableness (compassion, cooperativeness, trust)
- neuroticism: Neuroticism (emotional instability, anxiety, moodiness)

Please response in json format, example:
{{
  "psychographic_traits": {{
    "openness": 2,
    "conscientiousness": 3,
    "extraversion": 2,
    "agreeableness": 2,
    "neuroticism": 1
  }}
}}
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.

Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# cognition_initialize_hobbies (citysim-only)
# ---------------------------------------------------------------------------

class CognitionInitializeHobbiesCitysim(BasePrompt):
    """Initialize hobbies from profile and psychographic traits — citysim origin."""

    name: ClassVar[str] = "cognition_initialize_hobbies"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "citysim"
    description: ClassVar[str] = "Initialize hobbies from profile and psychographic traits"

    gender: Optional[str] = Field(None, description="Gender input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    income: Optional[str] = Field(None, description="Income input value used by this prompt.")
    education: Optional[str] = Field(None, description="Education input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")

    class Output(BaseModel):
        hobbies: list[str] = Field(description="List of hobby names.")

    def format_prompt(self) -> str:
        return f"""You are an intelligent agent profile generator. Based on the demographic and psychographic information below, please generate a list of suitable hobbies for this agent.

Profile Information:
- Gender: {_s(self.gender)}
- Age: {_s(self.age)}
- Occupation: {_s(self.occupation)}
- Income: {_s(self.income)}
- Education: {_s(self.education)}
- Household type: {_s(self.household)}
- Life stage: {_s(self.life_stage)}

Psychographic Traits (1-3 scale):
- Openness: {_s(self.openness)}
- Conscientiousness: {_s(self.conscientiousness)}
- Extraversion: {_s(self.extraversion)}
- Agreeableness: {_s(self.agreeableness)}
- Neuroticism: {_s(self.neuroticism)}

Please generate a list of 2-5 hobbies.
- Ensure the hobbies fit the agent's income level and age (e.g., "Golf" for higher income, "Video Games" for younger cohorts).
- Ensure the hobbies reflect their Big 5 personality (e.g., High Extraversion -> Team Sports; High Openness -> Painting/Travel; High Conscientiousness -> Gardening/Chess).
- These hobbies will be used to determine the agent's daily locations and routines.

Return the values in JSON format with the following structure:

{{
    "hobbies": [
        "Hobby Name 1",
        "Hobby Name 2",
        "Hobby Name 3"
    ]
}}

Example Response:
{{
    "hobbies": [
        "Photography",
        "Hiking",
        "Reading Sci-Fi"
    ]
}}

DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.

Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# cognition_initialize_preferences (citysim-only)
# ---------------------------------------------------------------------------

class CognitionInitializePreferencesCitysim(BasePrompt):
    """Initialize behavioral preferences from profile and psychographics — citysim origin."""

    name: ClassVar[str] = "cognition_initialize_preferences"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "citysim"
    description: ClassVar[str] = "Initialize behavioral preferences from profile and psychographics"

    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    income: Optional[str] = Field(None, description="Income input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")

    class Output(BaseModel):
        preferences: dict[str, Any] = Field(description="Initialized behavioral preferences (chronotype, risk_tolerance, etc.).")

    def format_prompt(self) -> str:
        return f"""You are an intelligent agent behavioral analyst. Based on the demographic and psychographic profile below, please initialize the agent's daily habits and behavioral preferences.

Profile Information:
- Age: {_s(self.age)}
- Occupation: {_s(self.occupation)}
- Income: {_s(self.income)}
- Household Composition: {_s(self.household)}

Psychographic Traits (1-3 scale):
- Openness: {_s(self.openness)}
- Conscientiousness: {_s(self.conscientiousness)}
- Extraversion: {_s(self.extraversion)}
- Agreeableness: {_s(self.agreeableness)}
- Neuroticism: {_s(self.neuroticism)}

Please generate specific behavioral parameters. Use the personality traits to guide these values (e.g., High Conscientiousness = Early Riser, Low Consumption; High Extraversion = High Social Frequency).

Return the values in JSON format with the following structure:

- chronotype: "early_bird" (wakes ~6am), "night_owl" (wakes ~10am), or "standard" (wakes ~7-8am).
- risk_tolerance: Float 0.0-1.0 (propensity to take financial or physical risks).
- spending_tendency: Float 0.0-1.0 (0=Frugal/Saver, 1=Impulsive/Spender).
- social_frequency: Float 0.0-1.0 (desired probability of initiating social interactions per day).
- work_ethic: Float 0.0-1.0 (tendency to work overtime or prioritize work tasks).
- leisure_preference: "outdoor", "indoor", "social", or "solitary" (dominant preference for free time).

Example Response:
{{
  "preferences": {{
    "chronotype": "night_owl",
    "risk_tolerance": 0.7,
    "spending_tendency": 0.8,
    "social_frequency": 0.9,
    "work_ethic": 0.3,
    "leisure_preference": "social"
  }}
}}

DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.

Return JSON only, without any extra text."""
