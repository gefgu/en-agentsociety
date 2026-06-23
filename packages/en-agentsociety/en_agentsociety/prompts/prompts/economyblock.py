"""Python prompt classes for EconomyBlock (worktime estimate + monthly plan prompts)."""
from __future__ import annotations

from typing import Any, ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..base import BasePrompt


def _s(v: object, d: str = "unknown") -> object:
    """Return *v* if not None, else *d*."""
    return v if v is not None else d


# ---------------------------------------------------------------------------
# worktime_estimate
# ---------------------------------------------------------------------------

class WorktimeEstimateAgentsociety(BasePrompt):
    """Estimate time for work actions — agentsociety origin."""

    name: ClassVar[str] = "worktime_estimate"
    version: ClassVar[str] = "1.1.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "A prompt for estimating the time needed to complete an action based on the overall plan"

    plan: Optional[str] = Field(None, description="Plan input value used by this prompt.")
    current_intention: Optional[str] = Field(None, description="Current intention input value used by this prompt.")
    emotion_types: Optional[str] = Field(None, description="Emotion types input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")

    class Output(BaseModel):
        time: int = Field(description="Estimated minutes required for the work action.")

    def format_prompt(self) -> str:
        return f"""As an intelligent agent's time estimation system, please estimate the time needed to complete the current action based on the overall plan and current intention.

Overall plan:
{_s(self.plan)}

Current action: {_s(self.current_intention)}

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


class WorktimeEstimateCitysim(WorktimeEstimateAgentsociety):
    """Estimate time for work actions — citysim origin (adds Big Five + lifestyle fields)."""

    origin: ClassVar[str] = "citysim"

    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")
    hobbies: Optional[str] = Field(None, description="Hobbies input value used by this prompt.")
    goals: Optional[str] = Field(None, description="Goals input value used by this prompt.")
    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    work_ethic: Optional[float] = Field(None, description="Work-priority preference (0.0=Low work priority, 1.0=High work priority).")

    def format_prompt(self) -> str:
        return f"""As an intelligent agent's time estimation system, please estimate the time needed to complete the current action based on the overall plan and current intention.

Overall plan:
{_s(self.plan)}

Current action: {_s(self.current_intention)}

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
- Work Ethic: {_s(self.work_ethic)} (0.0=Low work priority/minimal hours, 1.0=High work priority/tends to work overtime)

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
# month_plan_goal_creation
# ---------------------------------------------------------------------------

class MonthPlanGoalCreationAgentsociety(BasePrompt):
    """Monthly SMART goal creation from economic and social context — agentsociety origin."""

    name: ClassVar[str] = "month_plan_goal_creation"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Monthly SMART goal creation prompt from economic and social context"

    # Call-site fields (passed in context dict by EconomyBlock)
    income: Optional[str] = Field(None, description="Income input value used by this prompt.")
    consumption: Optional[float] = Field(None, description="Consumption input value used by this prompt.")
    wealth: Optional[str] = Field(None, description="Wealth input value used by this prompt.")
    financial_stress: Optional[str] = Field(None, description="Financial stress input value used by this prompt.")
    need_fulfillment: Optional[str] = Field(None, description="Need fulfillment input value used by this prompt.")
    social_isolation: Optional[str] = Field(None, description="Social isolation input value used by this prompt.")
    interest: Optional[str] = Field(None, description="Interest input value used by this prompt.")
    major_events_memories: Optional[str] = Field(None, description="Major events memories input value used by this prompt.")

    class Output(BaseModel):
        goals: list[str] = Field(default_factory=list, description="Goal list generated for the next month.")

    def format_prompt(self) -> str:
        return f"""Given the following economic and social context, please create 3 to 5 goals that I can achieve in the next month. These goals should be specific, measurable, achievable, relevant, and time-bound (SMART).

Economic Context:
- Income: ${_s(self.income)} per month
- Consumption: ${_s(self.consumption)} per month
- Wealth: ${_s(self.wealth)}
- Financial Stress: {_s(self.financial_stress)}
- Need Fulfillment: {_s(self.need_fulfillment)} (0 to 1 scale)
- Social Isolation: {_s(self.social_isolation)}
- Interest in New Experiences: {_s(self.interest)} (0 to 1 scale)

Recent Major Events:
{_s(self.major_events_memories)}

Please generate goals that can help improve my economic situation, mental well-being, and social connections based on the above context.

Output requirements:
- Return exactly one JSON object with a "goals" field.
- "goals" must be an array of 3 to 5 strings.
- Each array item must be a plain goal description string, not an object.
- Do not use keys such as "description", "goalDescription", "title", or "reason".
- Do not include markdown, comments, explanations, or any text outside the JSON object.

Correct format:
{{
    "goals": [
        "Find a part-time job in retail to increase my monthly income.",
        "Reduce my monthly consumption by 20% by cooking at home more often.",
        "Save at least $100 from my income by cutting unnecessary expenses.",
        "Engage in a new hobby or activity to increase my interest in new experiences.",
        "Reconnect with an old friend to reduce social isolation."
    ]
}}

Incorrect format:
{{
    "goals": [
        {{"description": "Find a part-time job in retail to increase my monthly income."}}
    ]
}}
Return JSON only, without any extra text."""


class MonthPlanGoalCreationCitysim(MonthPlanGoalCreationAgentsociety):
    """Monthly SMART goal creation — citysim origin (identical template, different origin label)."""

    origin: ClassVar[str] = "citysim"


# ---------------------------------------------------------------------------
# month_plan_mental_health_assessment
# ---------------------------------------------------------------------------

class MonthPlanMentalHealthAssessmentAgentsociety(BasePrompt):
    """Monthly mental health assessment conditioned on economic context — agentsociety origin."""

    name: ClassVar[str] = "month_plan_mental_health_assessment"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Monthly mental health assessment prompt conditioned on economic context"

    name_field: Optional[str] = Field(None, alias="name", description="Name input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    city: Optional[str] = Field(None, description="City input value used by this prompt.")
    job: Optional[str] = Field(None, description="Job input value used by this prompt.")
    skill: Optional[str] = Field(None, description="Skill input value used by this prompt.")
    consumption_summary: Optional[str] = Field(None, description="Consumption summary input value used by this prompt.")
    tax_summary: Optional[str] = Field(None, description="Tax summary input value used by this prompt.")
    price: Optional[str] = Field(None, description="Price input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    wealth: Optional[str] = Field(None, description="Wealth input value used by this prompt.")
    interest_rate_pct: Optional[float] = Field(None, description="Current interest rate percentage context.")

    class Output(BaseModel):
        model_config = ConfigDict(extra="allow")

    def format_prompt(self) -> str:
        return f"""You're {_s(self.name_field)}, a {_s(self.age)}-year-old individual living in {_s(self.city)}. As with all Americans, a portion of your monthly income is taxed by the federal government. This taxation system is tiered, income is taxed cumulatively within defined brackets, combined with a redistributive policy: after collection, the government evenly redistributes the tax revenue back to all citizens, irrespective of their earnings.

In the previous month, you worked as a(an) {_s(self.job)}. If you continue working this month, your expected hourly income will be ${_s(self.skill)}.

{_s(self.consumption_summary)}
{_s(self.tax_summary)}
Meanwhile, in the consumption market, the average price of essential goods is now at ${_s(self.price)}.

Your current savings account balance is ${_s(self.wealth)}. Interest rates, as set by your bank, stand at {_s(self.interest_rate_pct)}%.

Please fill in the following questionnaire:
Indicate how often you have felt this way during the last week by choosing one of the following options:
"Rarely" means Rarely or none of the time (less than 1 day),
"Some" means Some or a little of the time (1-2 days),
"Occasionally" means Occasionally or a moderate amount of the time (3-4 days),
"Most" means Most or all of the time (5-7 days).
Statement 1: I was bothered by things that usually don't bother me.
Statement 2: I did not feel like eating; my appetite was poor.
Statement 3: I felt that I could not shake off the blues even with help from my family or friends.
Statement 4: I felt that I was just as good as other people.
Statement 5: I had trouble keeping my mind on what I was doing.
Statement 6: I felt depressed.
Statement 7: I felt that everything I did was an effort.
Statement 8: I felt hopeful about the future.
Statement 9: I thought my life had been a failure.
Statement 10: I felt fearful.
Statement 11: My sleep was restless.
Statement 12: I was happy.
Statement 13: I talked less than usual.
Statement 14: I felt lonely.
Statement 15: People were unfriendly.
Statement 16: I enjoyed life.
Statement 17: I had crying spells.
Statement 18: I felt sad.
Statement 19: I felt that people disliked me.
Statement 20: I could not get "going".

Please response with json format with keys being numbers 1-20 and values being one of "Rarely", "Some", "Occasionally", "Most".
Any other output words are NOT allowed.
Return JSON only, without any extra text."""


class MonthPlanMentalHealthAssessmentCitysim(MonthPlanMentalHealthAssessmentAgentsociety):
    """Monthly mental health assessment — citysim origin (adds Big Five + life_stage; different template)."""

    origin: ClassVar[str] = "citysim"

    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")

    def format_prompt(self) -> str:
        return f"""You're {_s(self.name_field)}, a {_s(self.age)}-year-old individual living in {_s(self.city)}. As with all Americans, a portion of your monthly income is taxed by the federal government. This taxation system is tiered, income is taxed cumulatively within defined brackets, combined with a redistributive policy: after collection, the government evenly redistributes the tax revenue back to all citizens, irrespective of their earnings.

In the previous month, you worked as a(an) {_s(self.job)}. If you continue working this month, your expected hourly income will be ${_s(self.skill)}.

{_s(self.consumption_summary)}
{_s(self.tax_summary)}
Meanwhile, in the consumption market, the average price of essential goods is now at ${_s(self.price)}.

Your personality traits are as follows: openness {_s(self.openness)}, conscientiousness {_s(self.conscientiousness)}, extraversion {_s(self.extraversion)}, agreeableness {_s(self.agreeableness)}, and neuroticism {_s(self.neuroticism)}. Your household type is {_s(self.household)} and your life stage is {_s(self.life_stage)}.

Your current savings account balance is ${_s(self.wealth)}. Interest rates, as set by your bank, stand at {_s(self.interest_rate_pct)}%.

Please fill in the following questionnaire:
Indicate how often you have felt this way during the last week by choosing one of the following options:
"Rarely" means Rarely or none of the time (less than 1 day),
"Some" means Some or a little of the time (1-2 days),
"Occasionally" means Occasionally or a moderate amount of the time (3-4 days),
"Most" means Most or all of the time (5-7 days).
Statement 1: I was bothered by things that usually don't bother me.
Statement 2: I did not feel like eating; my appetite was poor.
Statement 3: I felt that I could not shake off the blues even with help from my family or friends.
Statement 4: I felt that I was just as good as other people.
Statement 5: I had trouble keeping my mind on what I was doing.
Statement 6: I felt depressed.
Statement 7: I felt that everything I did was an effort.
Statement 8: I felt hopeful about the future.
Statement 9: I thought my life had been a failure.
Statement 10: I felt fearful.
Statement 11: My sleep was restless.
Statement 12: I was happy.
Statement 13: I talked less than usual.
Statement 14: I felt lonely.
Statement 15: People were unfriendly.
Statement 16: I enjoyed life.
Statement 17: I had crying spells.
Statement 18: I felt sad.
Statement 19: I felt that people disliked me.
Statement 20: I could not get "going".

Please response with json format with keys being numbers 1-20 and values being one of "Rarely", "Some", "Occasionally", "Most".
Any other output words are NOT allowed.
Return JSON only, without any extra text."""


# ---------------------------------------------------------------------------
# month_plan_observation
# ---------------------------------------------------------------------------

class MonthPlanObservationAgentsociety(BasePrompt):
    """Monthly economic observation for work and consumption propensity decisions — agentsociety origin."""

    name: ClassVar[str] = "month_plan_observation"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = "Monthly economic observation prompt for work and consumption propensity decisions"

    name_field: Optional[str] = Field(None, alias="name", description="Name input value used by this prompt.")
    age: Optional[int] = Field(None, description="Age input value used by this prompt.")
    city: Optional[str] = Field(None, description="City input value used by this prompt.")
    job: Optional[str] = Field(None, description="Job input value used by this prompt.")
    skill: Optional[str] = Field(None, description="Skill input value used by this prompt.")
    consumption_summary: Optional[str] = Field(None, description="Consumption summary input value used by this prompt.")
    tax_summary: Optional[str] = Field(None, description="Tax summary input value used by this prompt.")
    price: Optional[str] = Field(None, description="Price input value used by this prompt.")
    household: Optional[str] = Field(None, description="Household input value used by this prompt.")
    wealth: Optional[str] = Field(None, description="Wealth input value used by this prompt.")
    interest_rate_pct: Optional[float] = Field(None, description="Current interest rate percentage context.")

    class Output(BaseModel):
        work: float = Field(..., description="Work propensity score.")
        consumption: float = Field(..., description="Consumption propensity score.")

    def format_prompt(self) -> str:
        return f"""You're {_s(self.name_field)}, a {_s(self.age)}-year-old individual living in {_s(self.city)}. As with all Americans, a portion of your monthly income is taxed by the federal government. This taxation system is tiered, income is taxed cumulatively within defined brackets, combined with a redistributive policy: after collection, the government evenly redistributes the tax revenue back to all citizens, irrespective of their earnings.

In the previous month, you worked as a(an) {_s(self.job)}. If you continue working this month, your expected hourly income will be ${_s(self.skill)}.

{_s(self.consumption_summary)}
{_s(self.tax_summary)}
Meanwhile, in the consumption market, the average price of essential goods is now at ${_s(self.price)}.

Your current savings account balance is ${_s(self.wealth)}. Interest rates, as set by your bank, stand at {_s(self.interest_rate_pct)}%.

Your goal is to maximize your utility by deciding how much to work and how much to consume. Your utility is determined by your consumption, income, saving, social service recieved and leisure time. You will spend the time you do not work on leisure activities.

With all these factors in play, and considering aspects like your living costs, any future aspirations, and the broader economic trends, how is your willingness to work this month? Furthermore, how would you plan your expenditures on essential goods, keeping in mind good price?

Please share your decisions in a JSON format as follows:
{{
    "work": a value between 0 and 1, indicating the propensity to work,
    "consumption": a value between 0 and 1, indicating the proportion of all your savings and income you intend to spend on essential goods
}}
Any other output words are NOT allowed.
Return JSON only, without any extra text."""


class MonthPlanObservationCitysim(MonthPlanObservationAgentsociety):
    """Monthly economic observation — citysim origin (adds Big Five + life_stage; different template)."""

    origin: ClassVar[str] = "citysim"

    openness: Optional[int] = Field(None, description="Big Five trait: Openness (1=Low, 2=Medium, 3=High).")
    conscientiousness: Optional[int] = Field(None, description="Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High).")
    extraversion: Optional[int] = Field(None, description="Big Five trait: Extraversion (1=Low, 2=Medium, 3=High).")
    agreeableness: Optional[int] = Field(None, description="Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High).")
    neuroticism: Optional[int] = Field(None, description="Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High).")
    life_stage: Optional[str] = Field(None, description="Life stage input value used by this prompt.")

    def format_prompt(self) -> str:
        return f"""You're {_s(self.name_field)}, a {_s(self.age)}-year-old individual living in {_s(self.city)}. As with all Americans, a portion of your monthly income is taxed by the federal government. This taxation system is tiered, income is taxed cumulatively within defined brackets, combined with a redistributive policy: after collection, the government evenly redistributes the tax revenue back to all citizens, irrespective of their earnings.

In the previous month, you worked as a(an) {_s(self.job)}. If you continue working this month, your expected hourly income will be ${_s(self.skill)}.

{_s(self.consumption_summary)}
{_s(self.tax_summary)}
Meanwhile, in the consumption market, the average price of essential goods is now at ${_s(self.price)}.

Your personality traits are as follows: openness {_s(self.openness)}, conscientiousness {_s(self.conscientiousness)}, extraversion {_s(self.extraversion)}, agreeableness {_s(self.agreeableness)}, and neuroticism {_s(self.neuroticism)}. Your household type is {_s(self.household)} and your life stage is {_s(self.life_stage)}.

Your current savings account balance is ${_s(self.wealth)}. Interest rates, as set by your bank, stand at {_s(self.interest_rate_pct)}%.

Your goal is to maximize your utility by deciding how much to work and how much to consume. Your utility is determined by your consumption, income, saving, social service recieved and leisure time. You will spend the time you do not work on leisure activities.

With all these factors in play, and considering aspects like your living costs, any future aspirations, and the broader economic trends, how is your willingness to work this month? Furthermore, how would you plan your expenditures on essential goods, keeping in mind good price?

Please share your decisions in a JSON format as follows:
{{
    "work": a value between 0 and 1, indicating the propensity to work,
    "consumption": a value between 0 and 1, indicating the proportion of all your savings and income you intend to spend on essential goods
}}
Any other output words are NOT allowed.
Return JSON only, without any extra text."""
