# AgentManager Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       SimulationEngine                          │
│  (Orchestrates workflow, environment, experiments, messaging)   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │ Delegates Agent Management   │
        ▼                               │
┌──────────────────────────────────────┴──────────────────────────┐
│                       AgentManager                              │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Agent Storage                                          │    │
│  │ ┌─────────────────┐         ┌──────────────────────┐  │    │
│  │ │  _id2agent      │         │    _filter_base      │  │    │
│  │ │                 │         │                      │  │    │
│  │ │ 1 → Agent       │         │ 1 → (Class, Config)  │  │    │
│  │ │ 2 → Agent       │         │ 2 → (Class, Config)  │  │    │
│  │ │ 3 → Agent       │         │ 3 → (Class, Config)  │  │    │
│  │ └─────────────────┘         └──────────────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Operations                                             │    │
│  │                                                        │    │
│  │ Initialization        Execution      Lifecycle        │    │
│  │ ├─ create_toolbox    ├─ run_all     ├─ close_all     │    │
│  │ ├─ prepare_agents    │  _agents()   ├─ delete_agents │    │
│  │ └─ init_agents       │               └─ reset_all     │    │
│  │                      │                                │    │
│  │ Memory Ops           Querying                         │    │
│  │ ├─ update_agent     ├─ filter_agents                 │    │
│  │ │  _memory()        ├─ get_agent()                   │    │
│  │ └─ gather_from      └─ agent_ids, agents             │    │
│  │    _agents()                                          │    │
│  │                                                        │    │
│  │ Persistence                                           │    │
│  │ └─ save_agent_static_info()                           │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Dependencies (Injected)                                │    │
│  │ ├─ config           ├─ embedding                      │    │
│  │ ├─ llm              ├─ database_writer                │    │
│  │ ├─ environment      └─ db_actor                       │    │
│  │ └─ messager                                           │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
         │                  │                    │
         ▼                  ▼                    ▼
    ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐
    │   Agents    │  │  Database   │  │  Environment &   │
    │ (Instances) │  │   Systems   │  │  LLM Services    │
    └─────────────┘  └─────────────┘  └──────────────────┘
```

## Data Flow

### Agent Creation Flow

```
AgentConfig
    │
    └──> prepare_agents()
         │
         ├──> Generate agent tuples
         ├──> Assign unique IDs
         ├──> Create MemoryConfigGenerator
         │
         └──> Return agent tuples
              │
              └──> initialize_agents()
                   │
                   ├──> Create Memory instances
                   ├──> Create block components
                   ├──> Instantiate agent classes
                   ├──> Run agent.init() hooks
                   ├──> Export profiles
                   ├──> Initialize embeddings
                   │
                   └──> Agents ready to run
```

### Execution Flow (Each Step)

```
SimulationEngine.step()
    │
    └──> run_all_agents()
         │
         ├──> [Agent 1].run() ──┐
         ├──> [Agent 2].run() ──┤
         ├──> [Agent 3].run() ──┼──> asyncio.gather() ──> [time_logs]
         ├──> [Agent N].run() ──┤
         │                       │
         └─────────────────────┬─┘
              Returns in parallel
```

### Memory Operation Flow

```
update_agent_memory([1, 2, 3], "status", "active")
    │
    └──> For each agent ID:
         │
         ├──> agent.status.update("status", "active") ──┐
         │                                                ├──> asyncio.gather()
         └──> (parallel for all agents) ───────────────┘
```

### Filtering Flow

```
filter_agents(
    types=(CitizenAgent,),
    filter_str="${profile.age} > 18"
)
    │
    ├──> Type filtering (O(n))
    │    └──> Keep agents matching types
    │
    └──> Property filtering (O(m))
         └──> Keep agents matching filter_str
              │
              └──> evaluate_filter()
                   └──> Check ${profile} expressions
```

## Component Interaction

```
┌──────────────────────────────────────────────────────────────┐
│                    AgentManager Instance                     │
└──────────────────────────────────────────────────────────────┘
         │                                                       │
         │ Dependencies                                         │ Methods
         │                                                       │
    ┌────┴────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
    │ config  │ │   llm    │ │   env    │ │messager  │         │
    └────┬────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘         │
         │           │            │            │              │
         └───────────┬────────────┬────────────┘              │
                     │            │                           │
              ┌──────▼────────────▼──────────┐              │
              │  _agent_toolbox created     │              │
              │  (passed to all agents)     │              │
              └──────┬─────────────────────┘              │
                     │                                     │
                     ▼                                     ▼
              Every Agent gets:          Operation Methods:
              ├─ toolbox                 ├─ Initialize
              ├─ memory                  ├─ Execute
              ├─ blocks                  ├─ Update
              └─ parameters              ├─ Query
                                         └─ Cleanup
```

## Class Responsibilities

```
AgentManager
├── Storage Management
│   ├── _id2agent: dict[int, Agent]
│   ├── _filter_base: dict[int, tuple]
│   └── Properties: agents, agent_ids
│
├── Agent Lifecycle
│   ├── Initialization
│   │   ├── create_toolbox()
│   │   ├── prepare_agents()
│   │   └── initialize_agents()
│   │
│   ├── Execution
│   │   └── run_all_agents()
│   │
│   └── Cleanup
│       ├── close_all_agents()
│       ├── delete_agents()
│       └── reset_all_agents()
│
├── Memory & State
│   ├── update_agent_memory()
│   ├── gather_from_agents()
│   └── save_agent_static_info()
│
└── Queries & Filtering
    ├── filter_agents()
    ├── get_agent()
    └── Metadata: agent_ids, agents
```

## Type Hierarchy

```
Agent (Base Class)
├── CitizenAgentBase
│   └── Used for citizen simulations
├── FirmAgentBase
│   └── Used for firm simulations
├── BankAgentBase
│   └── Used for banking simulations
├── NBSAgentBase
│   └── Used for national bureau of statistics
├── GovernmentAgentBase
│   └── Used for government agencies
└── SupervisorBase
    └── Used for supervision/monitoring
```

## State Diagram

```
                    Created
                       │
                       ▼
    ┌──────────────────────────────────────┐
    │      Not Initialized                 │
    │ (AgentManager exists, no agents)     │
    └──────────┬───────────────────────────┘
               │ prepare_agents() +
               │ initialize_agents()
               ▼
    ┌──────────────────────────────────────┐
    │           Initialized                │
    │ (Agents created, ready to run)       │
    └──────────┬───────────────────────────┘
               │ run_all_agents()
               ▼
    ┌──────────────────────────────────────┐
    │            Running                   │
    │ (Agents executing each step)         │◄─┐
    │ (Can update memory, gather data)     │  │
    └──────────┬───────────────────────────┘  │
               │                               │
        ┌──────┴─────┐                        │
        │             │                        │
        │ reset_all   │ continue               │
        │ _agents()   │ steps ─────────────────┘
        │             │
        ▼             ▼
    ┌────────┐   ┌──────────────────┐
    │ Reset  │   │ Running          │
    │        │   │ (Next round)     │
    └────────┘   └──────────────────┘
        │
        └──> back to Running or Cleanup
        
               delete_agents() or
               close_all_agents()
               ▼
    ┌──────────────────────────────────────┐
    │         Cleaning Up                  │
    │ (Agents being closed)                │
    └──────────┬───────────────────────────┘
               ▼
    ┌──────────────────────────────────────┐
    │         Cleaned Up                   │
    │ (Resources released)                 │
    └──────────────────────────────────────┘
```

## Integration Points

```
SimulationEngine
    │
    ├─ Initializes (calls init())
    │  ├─ Create AgentManager
    │  ├─ Create toolbox
    │  ├─ Prepare agents
    │  └─ Initialize agents
    │
    ├─ Executes steps (calls step())
    │  ├─ Run agents
    │  ├─ Update memory
    │  ├─ Gather data
    │  └─ Save state
    │
    ├─ Handles workflows
    │  ├─ Filter agents
    │  ├─ Update state
    │  └─ Interview agents
    │
    └─ Cleanup (calls close())
       └─ Close all agents
```

## Performance Characteristics

```
Operation              Time Complexity    Space Complexity
─────────────────────  ────────────────   ────────────────
get_agent(id)          O(1)               O(1)
filter_agents(types)   O(n)               O(m) where m = matches
filter_agents(str)     O(m)               O(k) where k = filtered
run_all_agents()       O(n) parallel      O(1) per step
gather_from_agents()   O(n) parallel      O(n)
update_memory()        O(n) parallel      O(1)
save_static_info()     O(c) where c =     O(c)
                       citizens

n = total agents
m = agents of specific type
c = citizen agents
k = temporary space for filter evaluation
```

---

This architecture provides a clean separation of concerns while maintaining efficient operations for large numbers of agents.
