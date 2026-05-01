"""Python prompt classes for SocietyAgent-level prompts.

Contains:
- SocietyAgentEnvironmentReflectionAgentsociety / Citysim
- SocietyAgentStatusSummaryAgentsociety / Citysim
- SocietyAgentChatResponseDecisionAgentsociety / Citysim
- SocietyAgentChatBeliefUpdateAgentsociety / Citysim
"""
from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from ..base import BasePrompt


def _s(v: object, d: str = "unknown") -> object:
    """Return *v* if not None, else *d*."""
    return v if v is not None else d


# ---------------------------------------------------------------------------
# societyagent_environment_reflection
# ---------------------------------------------------------------------------

class SocietyAgentEnvironmentReflectionAgentsociety(BasePrompt):
    """Generate the agent's reflection about current environmental information — agentsociety origin."""

    name: ClassVar[str] = "societyagent_environment_reflection"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Generate the agent's reflection about current environmental information"

    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    emotion_types: Optional[str] = Field(None, description="Emotion types input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    area_information: Optional[str] = Field(None, description="Area information input value used by this prompt.")

    class Output(BaseModel):
        reflection: str = Field(..., description="Generated free-text reflection about current environment.")

    def format_prompt(self) -> str:
        return f"""You are a citizen of the city.
Your occupation: {_s(self.occupation)}
Your age: {_s(self.age)}
Your current emotion: {_s(self.emotion_types)}
Household type: {_s(self.household)}

In your current location, you can sense the following information:
{_s(self.area_information)}

What's your feeling about those environmental information?
Return JSON only, without any extra text."""


class SocietyAgentEnvironmentReflectionCitysim(SocietyAgentEnvironmentReflectionAgentsociety):
    """Environment reflection — citysim origin (adds Big Five + lifestyle fields)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")
    hobbies: Optional[str] = Field(None, description="Hobbies input value used by this prompt.")
    goals: Optional[str] = Field(None, description="Goals input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")

    def format_prompt(self) -> str:
        return f"""You are a citizen of the city.
Your occupation: {_s(self.occupation)}
Your age: {_s(self.age)}
Your current emotion: {_s(self.emotion_types)}
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

In your current location, you can sense the following information:
{_s(self.area_information)}

What's your feeling about those environmental information?
Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# societyagent_status_summary
# ---------------------------------------------------------------------------

class SocietyAgentStatusSummaryAgentsociety(BasePrompt):
    """Generate a concise first-person summary of current agent status — agentsociety origin."""

    name: ClassVar[str] = "societyagent_status_summary"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Generate a concise first-person summary of current agent status"

    agent_name: Optional[str] = Field(None, alias="name", description="Agent name input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    gender: Optional[str] = Field(None, description="Gender input value used by this prompt.")
    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    education: Optional[str] = Field(None, description="Education input value used by this prompt.")
    personality: Optional[str] = Field(None, description="Personality input value used by this prompt.")
    background_story: Optional[str] = Field(None, description="Background story input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    # Big Five used in template (not listed in agentsociety TOML inputs, but template references them)
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    current_time: Optional[str] = Field(None, description="Current simulation time (HH:MM).")
    weather: Optional[str] = Field(None, description="Weather input value used by this prompt.")
    temperature: Optional[float] = Field(None, description="Current temperature context value.")
    current_location: Optional[str] = Field(None, description="Current location input value used by this prompt.")
    other_information: Optional[str] = Field(None, description="Other information input value used by this prompt.")
    current_need: Optional[str] = Field(None, description="Current need input value used by this prompt.")
    current_plan_target: Optional[str] = Field(None, description="Current plan target input value used by this prompt.")
    current_intention: Optional[str] = Field(None, description="Current intention input value used by this prompt.")
    current_emotion: Optional[str] = Field(None, description="Current emotion input value used by this prompt.")
    current_thought: Optional[str] = Field(None, description="Current thought input value used by this prompt.")

    class Output(BaseModel):
        summary: str = Field(..., description="Generated agent status summary text.")

    def format_prompt(self) -> str:
        return f"""Based on the following information, provide a concise 1-2 sentence description of the agent's current status:

Agent Profile:
- Name: {_s(self.agent_name)}
- Age: {_s(self.age)}
- Gender: {_s(self.gender)}
- Occupation: {_s(self.occupation)}
- Education: {_s(self.education)}
- Personality: {_s(self.personality)}
- Background: {_s(self.background_story)}
- Household type: {_s(self.household)}
-
  - Openness: {_s(self.openness)}
  - Conscientiousness: {_s(self.conscientiousness)}
  - Extraversion: {_s(self.extraversion)}
  - Agreeableness: {_s(self.agreeableness)}
  - Neuroticism: {_s(self.neuroticism)}

Current Environment:
- Time: {_s(self.current_time)}
- Weather: {_s(self.weather)}
- Temperature: {_s(self.temperature)}
- Location: {_s(self.current_location)}
- Other Information: {_s(self.other_information)}

Current Status:
- Current Need: {_s(self.current_need)}
- Plan Target: {_s(self.current_plan_target)}
- Current Intention: {_s(self.current_intention)}
- Emotion: {_s(self.current_emotion)}
- Thought: {_s(self.current_thought)}

Please provide a natural, human-like description of what the agent is currently doing and feeling, considering their personality, current situation, and environment. Focus on the most relevant aspects that define their current state.

Response format: 1-2 sentences describing the agent's current status from a first-person perspective.

Example:
I am working at the office, the work is not too busy, but I am a bit tired."""


class SocietyAgentStatusSummaryCitysim(SocietyAgentStatusSummaryAgentsociety):
    """Agent status summary — citysim origin (adds life_stage, hobbies, goals)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")
    hobbies: Optional[str] = Field(None, description="Hobbies input value used by this prompt.")
    goals: Optional[str] = Field(None, description="Goals input value used by this prompt.")

    def format_prompt(self) -> str:
        return f"""Based on the following information, provide a concise 1-2 sentence description of the agent's current status:

Agent Profile:
- Name: {_s(self.agent_name)}
- Age: {_s(self.age)}
- Gender: {_s(self.gender)}
- Occupation: {_s(self.occupation)}
- Education: {_s(self.education)}
- Personality: {_s(self.personality)}
- Background: {_s(self.background_story)}
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

Current Environment:
- Time: {_s(self.current_time)}
- Weather: {_s(self.weather)}
- Temperature: {_s(self.temperature)}
- Location: {_s(self.current_location)}
- Other Information: {_s(self.other_information)}

Current Status:
- Current Need: {_s(self.current_need)}
- Plan Target: {_s(self.current_plan_target)}
- Current Intention: {_s(self.current_intention)}
- Emotion: {_s(self.current_emotion)}
- Thought: {_s(self.current_thought)}

Please provide a natural, human-like description of what the agent is currently doing and feeling, considering their personality, current situation, and environment. Focus on the most relevant aspects that define their current state.


Response format: 1-2 sentences describing the agent's current status from a first-person perspective.

Example:
I am working at the office, the work is not too busy, but I am a bit tired."""


# ---------------------------------------------------------------------------
# societyagent_chat_response_decision
# ---------------------------------------------------------------------------

class SocietyAgentChatResponseDecisionAgentsociety(BasePrompt):
    """Decide whether to respond to an incoming social message — agentsociety origin."""

    name: ClassVar[str] = "societyagent_chat_response_decision"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Decide whether to respond to an incoming social message and draft response content"

    current_intention: Optional[str] = Field(None, description="Current intention input value used by this prompt.")
    gender: Optional[str] = Field(None, description="Gender input value used by this prompt.")
    education: Optional[str] = Field(None, description="Education input value used by this prompt.")
    personality: Optional[str] = Field(None, description="Personality input value used by this prompt.")
    occupation: Optional[str] = Field(None, description="Occupation input value used by this prompt.")
    background_story: Optional[str] = Field(None, description="Background story input value used by this prompt.")
    emotion_types: Optional[str] = Field(None, description="Emotion types input value used by this prompt.")
    # Call-site fields (social block passes these in context)
    content: Optional[str] = Field(None, description="Content input value used by this prompt.")
    relationship_strength: Optional[float] = Field(None, description="Relationship strength score (0.0=weak, 1.0=strong).")
    relationship_type: Optional[str] = Field(None, description="Relationship type input value used by this prompt.")
    recent_chat_history: Optional[str] = Field(None, description="Recent chat history input value used by this prompt.")

    class Output(BaseModel):
        should_respond: str = Field(..., description="Whether the agent should respond to the message.")
        response_content: Optional[str] = Field(None, description="Response message content when a reply is needed.")

    def format_prompt(self) -> str:
        return f"""My current action/intention is: {_s(self.current_intention)}
My profile:
    - gender: {_s(self.gender)}
    - education: {_s(self.education)}
    - personality: {_s(self.personality)}
    - occupation: {_s(self.occupation)}
    - background_story: {_s(self.background_story)}
My current emotion: {_s(self.emotion_types)}

I received a message:{_s(self.content)}
    - My relationship strength with him/her: {_s(self.relationship_strength)}
    - Our relationship type: {_s(self.relationship_type)}
    - Recent chat history: {_s(self.recent_chat_history)}

Based on the above all information, should I respond to this message? If I should respond, what should I say?
1. Is this a message that needs/deserves a response?
2. If you think the conversation should end, you should not respond or end quick and say goodbye.
3. If I should respond, what should I say? (only output the response content from a first person perspective, no other text)
4. If I am busy, I should not respond or tell him/her that I am busy.
5. The length of the social message should be less than 20 characters.
6. If I need to respond, I should respond in a natural way, not like a robot, talk in the point but not nonsense.

Answer only YES or NO, in JSON format, e.g. {{"should_respond": "YES", "response_content": "Hello, how are you?(optional)"}}
Return JSON only, without any extra text."""


class SocietyAgentChatResponseDecisionCitysim(SocietyAgentChatResponseDecisionAgentsociety):
    """Chat response decision — citysim origin (identical template, different origin label)."""

    origin: ClassVar[str] = "citysim"


# ---------------------------------------------------------------------------
# societyagent_chat_belief_update
# ---------------------------------------------------------------------------

class SocietyAgentChatBeliefUpdateAgentsociety(BasePrompt):
    """Update belief attributes for a social contact after receiving a message — agentsociety origin."""

    name: ClassVar[str] = "societyagent_chat_belief_update"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Update belief attributes for a social contact after receiving a message"

    # Call-site fields (social block passes these in context)
    content: Optional[str] = Field(None, description="Content input value used by this prompt.")
    sender_id: Optional[str] = Field(None, description="Sender id input value used by this prompt.")
    relationship_type: Optional[str] = Field(None, description="Relationship type input value used by this prompt.")
    relationship_strength: Optional[float] = Field(None, description="Relationship strength score (0.0=weak, 1.0=strong).")

    class Output(BaseModel):
        affinity: float = Field(..., description="Updated affinity score (0.0 to 1.0).")
        trust: float = Field(..., description="Updated trust score (0.0 to 1.0).")
        familiarity: float = Field(..., description="Updated familiarity score (0.0 to 1.0).")

    def format_prompt(self) -> str:
        return f"""You have received a message: {_s(self.content)}
Based on this message, update your beliefs about the sender (ID: {_s(self.sender_id)}) in your social network.
Consider their personality, intentions, and any relevant context from your past interactions, and the current beliefs.
Current belief about the sender: {_s(self.relationship_type)} with {_s(self.relationship_strength)}.
Provide a brief update to your beliefs about this sender.

Return new affinity, trust, and familiarity values (0-1 scale) in JSON format:
{{"affinity": float, "trust": float, "familiarity": float}}
Return JSON only, without any extra text."""


class SocietyAgentChatBeliefUpdateCitysim(SocietyAgentChatBeliefUpdateAgentsociety):
    """Chat belief update — citysim origin (identical template, different origin label)."""

    origin: ClassVar[str] = "citysim"
