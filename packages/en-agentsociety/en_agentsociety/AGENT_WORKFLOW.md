# Agent Workflow Developer Guide

This guide explains how to build custom agents and agent workflows using the code-based API. It is intended for developers who want to extend AgentSociety with their own agents, blocks, and simulation workflows.

---

## Table of Contents

1. [Core Concepts](#1-core-concepts)
2. [Building a Custom Block](#2-building-a-custom-block)
3. [Building a Custom Agent](#3-building-a-custom-agent)
4. [Registering Getter Functions](#4-registering-getter-functions)
5. [Using the BlockDispatcher](#5-using-the-blockdispatcher)
6. [Memory: Reading and Writing State](#6-memory-reading-and-writing-state)
7. [Prompts and FormatPrompt](#7-prompts-and-formatprompt)
8. [Context and DotDict](#8-context-and-dotdict)
9. [Custom Tools](#9-custom-tools)
10. [Task-Solving Workflows (IndividualEngine)](#10-task-solving-workflows-individualengine)
11. [City Simulation Workflow](#11-city-simulation-workflow)
12. [Workflow Step Types](#12-workflow-step-types)
13. [Full Example: Custom Agent](#13-full-example-custom-agent)

---

## 1. Core Concepts

```
Agent
  ├── Memory          (persistent state: profile, status, stream memory)
  ├── Toolbox         (LLM, Environment, Messager, DatabaseWriter, custom tools)
  ├── Blocks[]        (composable behavior units)
  │     └── Block
  │           ├── FormatPrompt  (template-based LLM calls)
  │           └── Context       (local per-execution state)
  └── BlockDispatcher (routes intention → block via LLM function calling)
```

An **Agent** owns a **Memory** (what the agent knows and feels) and a set of **Blocks** (what the agent can do). A **Block** is the smallest independently-testable behavior unit, analogous to a `Layer` in PyTorch. The **BlockDispatcher** routes the agent's current intention to the best-matching Block.

---

## 2. Building a Custom Block

```python
from pydantic import BaseModel
from en_agentsociety.agent import Block, BlockParams, BlockOutput, FormatPrompt

# 1. Define the block's output schema
class MyBlockOutput(BlockOutput):
    result: str = ""

# 2. (Optional) Define block-level configuration
class MyBlockParams(BlockParams):
    temperature: float = 0.7

# 3. Implement the block
class MyBlock(Block):
    name = "my_block"
    description = "Does something useful based on the agent's intention"
    OutputType = MyBlockOutput         # declare output type
    ParamsType = MyBlockParams         # declare params type

    PROMPT = """
    You are a helpful agent.
    Current task: ${context.current_task}
    Agent profile: ${profile.occupation}, age ${profile.age}
    
    Please respond with a short action summary.
    """

    def __init__(self, toolbox, agent_memory=None, block_params=None):
        super().__init__(toolbox, agent_memory, block_params)
        self._prompt = FormatPrompt(self.PROMPT, memory=agent_memory)

    async def forward(self, context) -> MyBlockOutput:
        # Fill prompt variables from memory + context
        prompt_str = await self._prompt.format(context)
        
        # Call the LLM
        response = await self.llm.atext_request(
            [{"role": "user", "content": prompt_str}]
        )
        
        # Persist something to memory
        await self.memory.status.update("last_action", response)
        
        return MyBlockOutput(result=response)
```

### Key Block Rules

- `forward(context)` must be `async` and return an instance of `OutputType`.
- Access `self.llm`, `self.memory`, `self.environment`, `self.toolbox` inside blocks.
- Set `NeedAgent = True` if your block needs access to the parent `Agent` instance (`self.agent`).

---

## 3. Building a Custom Agent

```python
from en_agentsociety.agent import (
    Agent, AgentParams, AgentType, AgentToolbox,
    CitizenAgentBase, MemoryAttribute
)
from en_agentsociety.memory import Memory

class MyAgentParams(AgentParams):
    verbose: bool = False

class MyAgent(CitizenAgentBase):           # or Agent, IndividualAgentBase
    description = "A demo citizen agent"
    ParamsType = MyAgentParams
    BlockOutputType = MyBlockOutput

    # Declare memory fields managed by the framework
    StatusAttributes = [
        MemoryAttribute(
            name="energy",
            type=float,
            default_or_value=1.0,
            description="How energetic the agent feels (0–1)",
        ),
    ]

    def __init__(self, id, name, type, toolbox, memory, agent_params=None, blocks=None):
        super().__init__(id, name, type, toolbox, memory, agent_params, blocks)

    async def forward(self):
        """Main decision loop called every simulation tick."""
        # Example: delegate to the dispatcher
        output = await self.dispatcher.dispatch(self.context)
        return output
```

### Agent Base Classes

| Class | Purpose |
|---|---|
| `Agent` | Abstract base — implement `forward()` |
| `CitizenAgentBase` | Adds mobility helpers for city agents |
| `IndividualAgentBase` | Adds task-solving helpers (`get_task`, `submit_result`) |
| `SupervisorBase` | Oversight agent with message interception capabilities |
| `FirmAgentBase` | Institution-type: firm/company |
| `BankAgentBase` | Institution-type: bank |
| `GovernmentAgentBase` | Institution-type: government |
| `NBSAgentBase` | Institution-type: national bureau of statistics |

---

## 4. Registering Getter Functions

Use `@register_get` to expose memory fields in a queryable, discoverable way. The simulation engine uses `get_functions` to gather data from agents.

```python
from en_agentsociety.agent import register_get

class MyAgent(CitizenAgentBase):

    @register_get("Returns the agent's current energy level")
    async def get_energy(self) -> float:
        return await self.memory.status.get("energy")

    @register_get("Returns the agent's current location as (lat, lng)")
    async def get_location(self) -> tuple:
        return await self.memory.status.get("location")
```

The `register_get` decorator stores function metadata in `cls.get_functions`, which is inherited and can be called by the framework to gather data across all agents.

---

## 5. Using the BlockDispatcher

The `BlockDispatcher` is created automatically for every `Agent`. It uses LLM function-calling to route the agent's `current_intention` to the best-matching block.

### Setup

```python
from en_agentsociety.agent import Block

class PlanBlock(Block):
    name = "plan_block"
    description = "Creates a daily activity plan for the agent"
    ...

class SocialBlock(Block):
    name = "social_block"
    description = "Handles social interactions: chat, help, share information"
    ...

# When creating the agent, pass blocks
agent = MyAgent(
    id=1, name="Alice", type=AgentType.Citizen,
    toolbox=toolbox, memory=memory,
    blocks=[PlanBlock(toolbox, memory), SocialBlock(toolbox, memory)]
)
```

### Usage inside `forward()`

```python
async def forward(self):
    # Set the current intention in context
    self.context.current_intention = "I want to chat with my neighbor"
    
    # Dispatcher selects the right block and calls its forward()
    block, output = await self.dispatcher.dispatch(self.context)
    return output
```

### Custom Dispatcher Prompt

```python
agent.dispatcher.register_dispatcher_prompt("""
Your task is to select the best module for the agent's current goal.

Agent goal: ${context.current_intention}
Agent mood: ${status.emotion}
""")
```

---

## 6. Memory: Reading and Writing State

Every agent has a `Memory` object with three sub-stores:

| Store | API | Contents |
|---|---|---|
| `memory.status` | `get(key)` / `update(key, value)` | Numeric / categorical state (needs, emotions, location) |
| `memory.profile` | `get(key)` / `update(key, value)` | Demographic profile (age, occupation, income, …) |
| `memory.stream` | `add(event)` / `get_recent(n)` | Time-ordered event log (observations, decisions) |

```python
# Read
energy = await self.memory.status.get("energy")
occupation = await self.memory.profile.get("occupation")
recent_events = await self.memory.stream.get_recent(5)

# Write
await self.memory.status.update("energy", energy - 0.1)
await self.memory.stream.add({
    "type": "action",
    "description": "Went to the park",
    "timestamp": ...,
})
```

### Declaring Memory Fields

In your Agent class, list `MemoryAttribute` entries in `StatusAttributes`:

```python
class MyAgent(CitizenAgentBase):
    StatusAttributes = [
        MemoryAttribute(
            name="stress",
            type=float,
            default_or_value=0.3,
            description="Stress level of the agent (0–1)",
        ),
        MemoryAttribute(
            name="current_goal",
            type=str,
            default_or_value="none",
            description="The agent's active goal",
        ),
    ]
```

These are automatically initialized for every agent instance.

---

## 7. Prompts and FormatPrompt

`FormatPrompt` is a template engine that fills placeholders from memory and context at runtime.

### Template Syntax

| Placeholder | Source |
|---|---|
| `${profile.occupation}` | Agent profile memory |
| `${status.energy}` | Agent status memory |
| `${context.current_task}` | Context DotDict |
| `{variable}` | Named variable passed to `format()` |

```python
PLAN_PROMPT = """
You are a {occupation} aged {age}.
Your current energy level is ${status.energy}.
Recent events: ${stream.recent}

What are you going to do today?
"""

prompt = FormatPrompt(PLAN_PROMPT, memory=self.memory)
filled = await prompt.format(context, occupation="engineer", age=35)

response = await self.llm.atext_request([
    {"role": "system", "content": "You are a city simulation agent."},
    {"role": "user",   "content": filled},
])
```

### System Prompts

```python
prompt = FormatPrompt(
    template="...",
    system_prompt="You are simulating a realistic city resident.",
    memory=self.memory,
)
```

---

## 8. Context and DotDict

`Context` carries per-step ephemeral state that is passed down from `Agent.forward()` into each `Block.forward()`.

```python
# Agent context (lives on self.context)
self.context.current_intention = "find food"
self.context.step_count += 1

# Block context (local to the block)
context.selected_action = "walk to restaurant"
context.confidence = 0.85

# Dot-notation access on any DotDict
print(context.selected_action)   # "walk to restaurant"
print(context["confidence"])     # 0.85  — both work
```

### Defining a Typed Context

```python
from pydantic import BaseModel
from en_agentsociety.agent import AgentContext, context_to_dot_dict

class MyAgentContext(AgentContext):
    current_intention: str = ""
    selected_block: str = ""
    step_count: int = 0

class MyAgent(CitizenAgentBase):
    Context = MyAgentContext     # framework will auto-convert to DotDict
```

---

## 9. Custom Tools

Add arbitrary callables to the agent toolbox and use them from any Block.

```python
from en_agentsociety.agent import CustomTool, AgentToolbox

# Create a tool
def fetch_weather(lat: float, lng: float) -> dict:
    return {"temp": 22, "condition": "sunny"}

weather_tool = CustomTool(
    name="weather",
    tool=fetch_weather,
    description="Fetches current weather for a GPS coordinate",
)

# Register at toolbox level (before creating agents)
toolbox = AgentToolbox(llm=llm, environment=env, messager=msg, database_writer=db)
toolbox.add_tool(weather_tool)

# Use inside a Block
class WeatherBlock(Block):
    async def forward(self, context):
        weather_fn = self.toolbox.get_tool("weather")
        data = weather_fn(lat=39.9, lng=116.4)
        await self.memory.stream.add({"weather": data})
        return MyBlockOutput()
```

---

## 10. Task-Solving Workflows (IndividualEngine)

For agent pipelines that solve structured tasks (e.g., QA, code generation, agentic evaluation):

### Define a Task

```python
from dataclasses import dataclass
from en_agentsociety.taskloader import Task

@dataclass
class QATask(Task):
    question: str = ""
    context_text: str = ""
```

### Create a Task File (`tasks.jsonl`)

```jsonl
{"task_id": 0, "question": "What is the capital of France?", "context_text": "...", "ground_truth": "Paris"}
{"task_id": 1, "question": "Who wrote Hamlet?", "context_text": "...", "ground_truth": "Shakespeare"}
```

### IndividualAgent

```python
from en_agentsociety.agent import IndividualAgentBase

class QAAgent(IndividualAgentBase):
    description = "Answers questions from a dataset"

    async def forward(self):
        task = await self.get_task()          # pops the next assigned task
        if task is None:
            return

        question = task.question
        answer = await self.llm.atext_request([
            {"role": "user", "content": question}
        ])
        task.set_result(answer)
        await self.submit_result(task)
```

### IndividualConfig

```python
from en_agentsociety.configs import IndividualConfig, TaskLoaderConfig

config = IndividualConfig(
    name="qa_eval",
    llm=[LLMConfig(...)],
    individual=IndividualAgentConfig(
        agent_class=QAAgent,
        number=4,           # number of parallel agent workers
    ),
    task_loader=TaskLoaderConfig(
        task_class=QATask,
        task_file="tasks.jsonl",
    ),
)

engine = AgentSociety.create(config)
await engine.run()
```

---

## 11. City Simulation Workflow

For city-scale population simulations:

```python
from en_agentsociety.configs import (
    Config, AgentsConfig, AgentConfig, EnvConfig, ExpConfig,
    WorkflowStepConfig, WorkflowType
)
from en_agentsociety.cityagent import SocietyAgent

config = Config(
    name="city_sim_demo",
    agents=AgentsConfig(
        citizens=[
            AgentConfig(agent_class=SocietyAgent, number=500),
        ],
    ),
    env=EnvConfig(
        db=...,   # database connection
    ),
    exp=ExpConfig(
        environment=EnvironmentConfig(work_start_time=8, work_end_time=18),
        workflow=[
            WorkflowStepConfig(type=WorkflowType.RUN, days=3),
            WorkflowStepConfig(type=WorkflowType.SURVEY, survey=my_survey),
            WorkflowStepConfig(type=WorkflowType.RUN, days=1),
        ],
    ),
)

engine = AgentSociety.create(config)
await engine.run()
```

---

## 12. Workflow Step Types

| `WorkflowType` | Description |
|---|---|
| `RUN` | Simulate `days` calendar days (uses `ticks_per_step` ticks) |
| `STEP` | Execute exactly `steps` ticks |
| `INTERVIEW` | Send a free-text question to filtered agents and collect responses |
| `SURVEY` | Send a structured `Survey` questionnaire to filtered agents |
| `UPDATE_STATE` | Directly write to agent memory fields |
| `MESSAGE` | Inject a message into agent inboxes |
| `ENVIRONMENT` | Change global environment variables / prompts |
| `DELETE_AGENT` | Remove agents from the simulation |
| `NEXT_ROUND` | Reset agents to initial positions but preserve memory |
| `SAVE_CONTEXT` | Snapshot agent context to storage |
| `FUNCTION` | Call an arbitrary Python coroutine `async def step(engine): ...` |
| `INTERVENE` | Generic code-driven intervention |

### Example: Direct State Update

```python
WorkflowStepConfig(
    type=WorkflowType.UPDATE_STATE,
    agent_filter=AgentFilterConfig(agent_class=[SocietyAgent]),
    data={"hunger_satisfaction": 0.2},   # force all agents to be hungry
)
```

### Example: FUNCTION Step

```python
async def inject_crisis(engine):
    await engine.update_environment({"crisis": "economic recession started"})
    engine.logger.info("Crisis injected!")

WorkflowStepConfig(type=WorkflowType.FUNCTION, func=inject_crisis)
```

---

## 13. Full Example: Custom Agent

```python
"""
A minimal but complete custom agent that:
 - Has a 'fatigue' status field
 - Has two blocks: RestBlock and WorkBlock
 - Uses the BlockDispatcher to route between them
"""

from pydantic import BaseModel
from en_agentsociety.agent import (
    Agent, AgentParams, AgentType, CitizenAgentBase,
    Block, BlockOutput, MemoryAttribute, register_get,
    FormatPrompt, AgentContext, context_to_dot_dict,
)

# === Blocks ===

class SimpleOutput(BlockOutput):
    action: str = ""

class RestBlock(Block):
    name = "rest_block"
    description = "Agent rests to recover energy when tired"
    OutputType = SimpleOutput

    async def forward(self, context) -> SimpleOutput:
        fatigue = await self.memory.status.get("fatigue")
        await self.memory.status.update("fatigue", max(0.0, fatigue - 0.3))
        await self.memory.stream.add({"event": "rested"})
        return SimpleOutput(action="rested")

class WorkBlock(Block):
    name = "work_block"
    description = "Agent performs productive work when energized"
    OutputType = SimpleOutput

    PROMPT = "You are ${profile.occupation}. Describe one work task you do today."

    def __init__(self, toolbox, agent_memory=None, block_params=None):
        super().__init__(toolbox, agent_memory, block_params)
        self._prompt = FormatPrompt(self.PROMPT, memory=agent_memory)

    async def forward(self, context) -> SimpleOutput:
        filled = await self._prompt.format(context)
        response = await self.llm.atext_request([{"role": "user", "content": filled}])
        fatigue = await self.memory.status.get("fatigue")
        await self.memory.status.update("fatigue", min(1.0, fatigue + 0.2))
        return SimpleOutput(action=response)

# === Agent ===

class WorkerAgentContext(AgentContext):
    current_intention: str = "decide what to do"

class WorkerAgent(CitizenAgentBase):
    description = "A simple worker agent that balances rest and work"
    BlockOutputType = SimpleOutput
    Context = WorkerAgentContext

    StatusAttributes = [
        MemoryAttribute(
            name="fatigue",
            type=float,
            default_or_value=0.2,
            description="Agent fatigue level (0=fresh, 1=exhausted)",
        ),
    ]

    @register_get("Returns current fatigue level")
    async def get_fatigue(self) -> float:
        return await self.memory.status.get("fatigue")

    async def forward(self):
        fatigue = await self.memory.status.get("fatigue")

        # Decide intention based on fatigue
        if fatigue > 0.7:
            self.context.current_intention = "I am very tired and need to rest"
        else:
            self.context.current_intention = "I feel energetic and want to be productive"

        # Delegate to the dispatcher → RestBlock or WorkBlock
        return await self.dispatcher.dispatch(self.context)

# === Wiring it up ===

from en_agentsociety import AgentSociety
from en_agentsociety.configs import Config, AgentsConfig, AgentConfig, EnvConfig, ExpConfig
from en_agentsociety.configs import WorkflowStepConfig, WorkflowType

config = Config(
    name="worker_demo",
    agents=AgentsConfig(
        citizens=[
            AgentConfig(
                agent_class=WorkerAgent,
                number=10,
                blocks=[RestBlock, WorkBlock],   # passed as classes, instantiated per-agent
            ),
        ],
    ),
    env=EnvConfig(db=...),
    exp=ExpConfig(
        workflow=[WorkflowStepConfig(type=WorkflowType.RUN, days=2)],
    ),
)

engine = AgentSociety.create(config)
await engine.run()
```
