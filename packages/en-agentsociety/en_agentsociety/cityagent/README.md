# `cityagent/` — Default City-Simulation Agent Implementations

This package provides ready-to-use agent implementations for city-scale social simulation. These agents model citizens and institutions within a city.

---

## Files

| File | Purpose |
|---|---|
| `societyagent.py` | `SocietyAgent` — the primary citizen agent |
| `bankagent.py` | `BankAgent` — financial institution agent |
| `firmagent.py` | `FirmAgent` — company/employer agent |
| `governmentagent.py` | `GovernmentAgent` — government institution agent |
| `nbsagent.py` | `NBSAgent` — national bureau of statistics agent |
| `initial.py` | Population initialization helpers (profile generation from distributions) |
| `memory_config.py` | Default memory configs for citizen and institution agents |
| `sharing_params.py` | Shared config classes: `SocietyAgentConfig`, `SocietyAgentBlockOutput`, `SocietyAgentContext` |

---

## SocietyAgent

The main citizen agent. It models a realistic urban resident with:

### Internal State (StatusAttributes)

| Field | Type | Description |
|---|---|---|
| `hunger_satisfaction` | float (0–1) | How fed the agent is |
| `energy_satisfaction` | float (0–1) | How rested the agent is |
| `safety_satisfaction` | float (0–1) | Sense of personal safety |
| `social_satisfaction` | float (0–1) | Social connection level |
| `current_need` | str | Active need being pursued |
| `emotion` | dict | 6-dimensional emotion (sadness, joy, fear, disgust, anger, surprise), each 0–10 |
| `thought` | str | Current internal monologue |
| `openness` | int (1–3) | Big Five: Openness to experience |
| `conscientiousness` | int (1–3) | Big Five: Conscientiousness |
| `extraversion` | int (1–3) | Big Five: Extraversion |
| `agreeableness` | int (1–3) | Big Five: Agreeableness |
| `neuroticism` | int (1–3) | Big Five: Neuroticism |
| `hobbies` | list[str] | Agent hobbies (influences daily destinations) |
| `goals` | str | Long-term life goals |
| `life_stage` | str | E.g. "young adult", "parent", "retiree" |
| `household` | str | Household type |

### Profile Attributes (from demographics)

Age, gender, occupation, income, education, consumption level, background story.

### Behavioral Blocks

The `SocietyAgent` uses these blocks (from `cityagent/blocks/`):

| Block | Purpose |
|---|---|
| `NeedsBlock` | Evaluates the most pressing need and sets `current_need` |
| `PlanBlock` | Creates a daily activity plan based on need and personality |
| `DailyScheduleBlock` | Generates time-specific activities for the day |
| `CognitionBlock` | Environmental reflection, emotion update, thought generation |
| `MobilityBlock` | Movement decisions (where to go) |
| `EconomyBlock` | Economic transactions (shopping, wages) |
| `SocialBlock` | Social interactions with other agents |

---

## `blocks/` Sub-package

| Block File | Description |
|---|---|
| `cognition_block.py` | Environment perception, Big Five initialization, emotion updates |
| `needs_block.py` | Maslow hierarchy need evaluation |
| `plan_block.py` | High-level daily activity planning |
| `daily_schedule_block.py` | Hour-by-hour schedule generation |
| `mobility_block.py` | Destination selection and movement |
| `economy_block.py` | Economic decision-making (spending, work) |
| `social_block.py` | Social interaction (chat, help, influence) |
| `other_block.py` | Miscellaneous behaviors |
| `utils.py` | JSON cleaning, formatting helpers |

---

## Institution Agents

| Agent | Role in City |
|---|---|
| `BankAgent` | Provides loans, sets interest rates, manages deposits |
| `FirmAgent` | Employs citizens, produces goods/services, pays wages |
| `GovernmentAgent` | Sets taxes, redistributes income, enforces regulations |
| `NBSAgent` | Collects statistical data from other agents |

---

## Quick Start

```python
from en_agentsociety.cityagent import SocietyAgent
from en_agentsociety.configs import AgentsConfig, AgentConfig

agents_config = AgentsConfig(
    citizens=[
        AgentConfig(agent_class=SocietyAgent, number=200),
    ],
)
```

The `initial.py` module handles population initialization, sampling attributes from statistical distributions defined in the `Config`.
