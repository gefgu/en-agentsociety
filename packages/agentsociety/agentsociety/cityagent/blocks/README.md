# `cityagent/blocks/` — SocietyAgent Behavioral Blocks

This directory contains the composed behavioral blocks used by `SocietyAgent` and other city agents. Each block is an independently testable unit of agent behavior.

---

## Files

| File | Block Class | Purpose |
|---|---|---|
| `cognition_block.py` | `CognitionBlock` | Environmental reflection, emotion updates, Big Five personality init, hobbies/goals generation |
| `needs_block.py` | `NeedsBlock` | Evaluates the most pressing Maslow-hierarchy need |
| `plan_block.py` | `PlanBlock` | High-level daily activity plan based on current need + personality |
| `daily_schedule_block.py` | `DailyScheduleBlock` | Generates hour-by-hour schedule of activities and destinations |
| `mobility_block.py` | `MobilityBlock` | Selects movement destination and executes travel via mobility simulator |
| `economy_block.py` | `EconomyBlock` | Economic decisions: shopping, wage collection, spending |
| `social_block.py` | `SocialBlock` | Social interactions: chat, help requests, information sharing |
| `other_block.py` | `OtherBlock` | Miscellaneous behaviors not covered by the above |
| `utils.py` | — | JSON response cleaning, formatting helpers shared by blocks |

---

## Block Execution Flow

```
SocietyAgent.forward()
    │
    ├─► NeedsBlock         → sets current_need
    ├─► PlanBlock          → sets daily_plan
    ├─► DailyScheduleBlock → sets today_schedule
    │
    └─► BlockDispatcher routes to:
            MobilityBlock  │  EconomyBlock  │  SocialBlock  │  CognitionBlock
```

---

## `CognitionBlock`

The most complex block. Handles:

1. **Initialization** (first tick only):
   - Generates Big Five personality scores (`openness`, `conscientiousness`, `extraversion`, `agreeableness`, `neuroticism`) via LLM from demographic profile.
   - Generates hobby list (2–5 items) consistent with personality and demographics.
   - Determines life stage and household type.
   - Sets initial goals.

2. **Ongoing reflection** (every tick):
   - Parses local area information from the environment.
   - Generates an emotional reaction to the environment.
   - Updates the 6-dimensional emotion model.
   - Updates the agent's internal `thought`.

---

## `NeedsBlock`

Implements a simplified Maslow hierarchy:

```
physiological (hunger, energy) > safety > social > self-actualization
```

Reads all current satisfaction scores and returns the most-urgent need as `current_need`.

---

## Writing a Custom Block

```python
from agentsociety.agent import Block, BlockOutput
from agentsociety.cityagent.sharing_params import SocietyAgentBlockOutput

class MyCustomBlock(Block):
    name = "my_custom_block"
    description = "Handles X when the agent wants to do Y"
    OutputType = SocietyAgentBlockOutput

    async def forward(self, context) -> SocietyAgentBlockOutput:
        # Your logic here
        return SocietyAgentBlockOutput(action="did X")
```

Then register it in `AgentConfig`:

```python
AgentConfig(
    agent_class=SocietyAgent,
    number=100,
    blocks=[MyCustomBlock, PlanBlock, MobilityBlock],
)
```
