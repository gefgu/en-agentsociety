# `configs/` — Configuration Models

This package defines all Pydantic configuration models used to set up a simulation. A `Config` or `IndividualConfig` object is the **single entry point** for the entire framework.

---

## Files

| File | Purpose |
|---|---|
| `__init__.py` | Top-level exports: `Config`, `IndividualConfig`, `AgentsConfig`, etc. |
| `agent.py` | `AgentConfig`, `InstitutionAgentClass` |
| `env.py` | `EnvConfig` — database and S3 configuration |
| `exp.py` | `ExpConfig`, `WorkflowStepConfig`, `WorkflowType`, `AgentFilterConfig` |
| `social_network.py` | Social network graph configuration |
| `utils.py` | `load_config_from_file` — YAML/JSON loader |

---

## Top-Level Config Schemas

### `Config` — City Simulation

```python
class Config(BaseModel):
    id: str                          # experiment ID (auto-generated UUID)
    name: str                        # experiment name
    llm: list[LLMConfig]             # LLM provider configs (round-robin)
    agents: AgentsConfig             # citizen + institution agent configs
    env: EnvConfig                   # database, S3, map configs
    exp: ExpConfig                   # workflow, environment overrides
    logging_level: str = "INFO"
```

### `IndividualConfig` — Task-Solving Pipeline

```python
class IndividualConfig(BaseModel):
    id: str
    name: str
    llm: list[LLMConfig]
    individual: IndividualAgentConfig  # single agent type + number
    task_loader: TaskLoaderConfig      # task source
    env: EnvConfig
    logging_level: str = "INFO"
```

---

## `AgentsConfig`

```python
class AgentsConfig(BaseModel):
    citizens: list[AgentConfig]       # required, min 1
    firms: list[AgentConfig] = []
    banks: list[AgentConfig] = []
    nbs: list[AgentConfig] = []
    governments: list[AgentConfig] = []
    supervisor: Optional[AgentConfig] = None
    init_funcs: list[Callable] = []   # async callables run before simulation starts
```

---

## `AgentConfig`

```python
class AgentConfig(BaseModel):
    agent_class: type[Agent]
    number: int
    blocks: list[type[Block]] = []          # block classes to instantiate
    memory_config_func: Optional[Callable]  # custom memory setup function
    agent_params: Optional[AgentParams]
    distribution: Optional[DistributionConfig]  # for sampling demographics
```

---

## `ExpConfig`

```python
class ExpConfig(BaseModel):
    workflow: list[WorkflowStepConfig]   # ordered simulation steps
    environment: EnvironmentConfig       # city environment parameters
```

---

## `WorkflowStepConfig`

```python
class WorkflowStepConfig(BaseModel):
    type: WorkflowType
    days: float = 1                        # for RUN
    steps: int = 1                         # for STEP
    ticks_per_step: int = 300
    func: Optional[Callable]               # for FUNCTION
    agent_filter: Optional[AgentFilterConfig]
    data: Optional[dict]                   # for UPDATE_STATE
    message: Optional[str]                 # for MESSAGE_INTERVENE
    survey: Optional[Survey]              # for SURVEY
    interview_message: Optional[str]       # for INTERVIEW
```

---

## Loading from File

```python
from en_agentsociety.configs import load_config_from_file

config = load_config_from_file("my_experiment.yaml")
```

YAML and JSON formats are both supported.

---

## `WorkflowType` Reference

```python
class WorkflowType(str, Enum):
    STEP = "step"
    RUN = "run"
    INTERVIEW = "interview"
    SURVEY = "survey"
    UPDATE_STATE = "update_state"
    MESSAGE = "message"
    DELETE_AGENT = "delete_agent"
    ENVIRONMENT = "environment"
    NEXT_ROUND = "next_round"
    SAVE_CONTEXT = "save_context"
    INTERVENE = "other"
    FUNCTION = "function"
```
