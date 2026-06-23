# `survey/` — Survey System

This package provides survey design and management for collecting structured data from agents during a simulation.

---

## Files

| File | Purpose |
|---|---|
| `manager.py` | `SurveyManager` — sends surveys and collects responses |
| `models.py` | `Survey`, `Question`, and response type models |

---

## Survey Structure

A `Survey` consists of one or more `Question` items:

```python
from en_agentsociety.survey.models import Survey, Question, QuestionType

survey = Survey(
    name="Wellbeing Check",
    description="Measuring agent wellbeing at end of day",
    questions=[
        Question(
            id="q1",
            type=QuestionType.SINGLE_CHOICE,
            text="How satisfied are you with your life today?",
            options=["Very dissatisfied", "Dissatisfied", "Neutral", "Satisfied", "Very satisfied"],
        ),
        Question(
            id="q2",
            type=QuestionType.OPEN_ENDED,
            text="What was the most significant event for you today?",
        ),
        Question(
            id="q3",
            type=QuestionType.RATING,
            text="Rate your energy level from 1 to 10.",
            min_value=1,
            max_value=10,
        ),
    ],
)
```

---

## Question Types

| `QuestionType` | Description |
|---|---|
| `SINGLE_CHOICE` | One answer from a list of options |
| `MULTIPLE_CHOICE` | Multiple answers from a list |
| `OPEN_ENDED` | Free-text response |
| `RATING` | Numeric score within a range |

---

## Using Surveys in Workflows

```python
from en_agentsociety.configs import WorkflowStepConfig, WorkflowType, AgentFilterConfig
from en_agentsociety.cityagent import SocietyAgent

WorkflowStepConfig(
    type=WorkflowType.SURVEY,
    survey=survey,
    agent_filter=AgentFilterConfig(agent_class=[SocietyAgent]),
)
```

The `SimulationEngine` sends the survey to all matching agents. Each agent uses its LLM to fill out the answers based on its current memory and context. Responses are stored in `StoragePendingSurvey` and marked complete when the agent responds.

---

## `SurveyManager`

```python
manager = SurveyManager(llm=llm, database_writer=writer)

# Dispatch survey to a list of agent IDs
await manager.send_survey(survey, agent_ids=[1, 2, 3])

# Retrieve completed responses
responses = await manager.get_responses(survey_name="Wellbeing Check")
```

---

## Survey Results

Results are stored in the database and accessible via the web API at `GET /api/experiments/{exp_id}/surveys`.
