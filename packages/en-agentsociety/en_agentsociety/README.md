# AgentSociety — CitySim Fork

> A city-scale and task-solving multi-agent simulation framework built on top of the original [AgentSociety](https://github.com/tsinghua-fib-lab/agentsociety) project.

---

## What Is This?

**AgentSociety** is a research framework for simulating large populations of LLM-powered agents inside a realistic city environment. Each agent perceives its environment, reasons with an LLM, moves through a mobility simulator, participates in an economic system, and communicates with other agents.

This fork (`citysim`) extends the original project with:

| Addition | Description |
|---|---|
| `IndividualEngine` | New execution mode for single-agent task-solving workflows (no city required) |
| `CatBoost` need-adjustment | ML-based replacement for LLM calls when adjusting agent need-satisfaction scores |
| `ModernBERT` actor | (Experimental / commented out) TransformerBERT regression backend for need adjustment |
| `CustomTool` + `AgentToolbox` | Extensible tool system allowing arbitrary callables to be injected into agents |
| `TaskLoader` | PyTorch `DataLoader`–style abstraction for loading and assigning tasks to agents |
| `BlockDispatcher` | LLM-based router that selects the appropriate `Block` for a given agent intention |
| `register_get` / `param_docs` | Decorators for exposing agent getter functions and documenting their parameters |
| `DotDict` context | Attribute-style (dot-notation) access to agent and block contexts |
| `Commercial` module | SaaS-layer with authentication, billing, and hosted executor support |
| `Performance` stack | Prometheus + Grafana + ClickHouse + Loki observability via Docker Compose |
| Hugging Face mirror | Automatic fallback to `hf-mirror.com` for users without direct HF access |
| HF `SparseTextEmbedding` | Uses `fastembed` for efficient sparse embeddings throughout the memory system |

See [CHANGES.md](CHANGES.md) for a detailed comparison with the upstream project and [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md) for a developer guide on building custom agent workflows.

---

## Directory Structure

```
agentsociety/
├── agent/          # Agent base class, Block, Dispatcher, Toolbox, Decorators, Context
├── catboost/       # CatBoost ML actors for need-satisfaction adjustment
├── cityagent/      # Default city-simulation agent implementations (SocietyAgent, BankAgent, …)
├── cli/            # Command-line interface entry points
├── commercial/     # (Optional) SaaS layer: auth, billing, hosted executor
├── configs/        # Pydantic config models for the entire simulation
├── environment/    # City environment: mobility sim client, economic sim client, map data
├── executor/       # Multi-process execution helpers
├── filesystem/     # Abstract filesystem client (local / S3)
├── llm/            # LLM adapter (OpenAI API compatible, round-robin, token tracking)
├── logger/         # Structured logger with optional OTLP exporter
├── memory/         # Agent memory: KV store, stream memory, spatial memory, vector store
├── message/        # Ray-based message bus and interceptor
├── modernbert/     # (Experimental) ModernBERT regression actor
├── performance/    # Prometheus / Grafana / ClickHouse / Loki monitoring stack
├── s3/             # S3 client wrapper
├── simulation/     # Core runtime: SimulationEngine, IndividualEngine, AgentSociety factory
├── storage/        # SQLite / PostgreSQL persistence layer
├── survey/         # Survey manager and models
├── taskloader/     # Task loading and assignment system
├── utils/          # Shared utility decorators
├── vectorstore/    # Sparse vector store backed by fastembed
└── webapi/         # FastAPI web backend and REST API
```

---

## Quick Start

### City Simulation

```python
from en_agentsociety import AgentSociety
from en_agentsociety.configs import Config, AgentConfig, EnvConfig, WorkflowStepConfig, WorkflowType
from en_agentsociety.cityagent import SocietyAgent

config = Config(
    name="my_simulation",
    agents=AgentsConfig(
        citizens=[AgentConfig(agent_class=SocietyAgent, number=100)],
    ),
    env=EnvConfig(...),
    workflow=[
        WorkflowStepConfig(type=WorkflowType.RUN, days=1),
    ],
)

engine = AgentSociety.create(config)
await engine.run()
```

### Individual Task-Solving

```python
from en_agentsociety import AgentSociety
from en_agentsociety.configs import IndividualConfig

config = IndividualConfig(...)
engine = AgentSociety.create(config)
await engine.run()
```

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                    AgentSociety                       │
│               (Factory / entry-point)                 │
└──────────┬─────────────────────────┬─────────────────┘
           │                         │
    ┌──────▼──────┐           ┌──────▼──────────┐
    │Simulation   │           │ IndividualEngine │
    │Engine       │           │ (task solving)   │
    └──────┬──────┘           └──────┬───────────┘
           │                         │
    ┌──────▼───────────────────────────────────────┐
    │   Agent Runtime (Ray-distributed workers)     │
    │  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
    │  │  Agent   │  │  Block   │  │ Dispatcher │  │
    │  │  (LLM)   │  │ (logic)  │  │  (routing) │  │
    │  └──────────┘  └──────────┘  └────────────┘  │
    └───────────────────┬──────────────────────────┘
                        │
    ┌───────────────────▼──────────────────────────┐
    │              Support Services                  │
    │  Memory │ Environment │ LLM │ Message │ Storage│
    └───────────────────────────────────────────────┘
```

---

## Key Design Principles

1. **Block = Layer**: A `Block` is the fundamental unit of agent behavior, analogous to a `Layer` in PyTorch. Complex agents are assembled from composable blocks.
2. **Config-driven**: The entire simulation is described by a single Pydantic `Config` object.
3. **Ray-parallel**: All agents run as Ray remote actors, enabling transparent scale-out.
4. **Workflow steps**: Experiments are defined as ordered `WorkflowStepConfig` lists, supporting steps, daily runs, interventions, surveys, and custom code.
5. **Dual-mode**: The same framework supports city-scale population simulation (`SimulationEngine`) and individual task-solving pipelines (`IndividualEngine`).
