# AgentManager Integration Guide

## Overview

The `AgentManager` class is a dedicated agent management system that handles:
- **Agent Creation**: Instantiating agents from configurations
- **Execution**: Running agents in simulation steps
- **Memory Management**: Storage and retrieval of agent memory
- **Lifecycle**: Initialization, reset, and cleanup of agents

This guide explains how to integrate it into your `SimulationEngine`.

---

## Architecture

### Current Structure (Before)
```
SimulationEngine
├── Agent Creation (_prepare_agents, _init_agent_class)
├── Agent Initialization (_initialize_agents, _init_supervisor_from_memory_file)
├── Agent Execution (_id2agent storage, run() calls)
├── Memory Management (agent memory updates)
└── Filtering & Queries (filter, gather)
```

### New Structure (After)
```
SimulationEngine
├── Core Initialization
├── Environment & LLM Setup
└── Workflow Execution
    └── AgentManager (All agent operations)
        ├── Agent Creation
        ├── Initialization
        ├── Execution
        ├── Memory Management
        └── Filtering & Queries
```

---

## Integration Steps

### Step 1: Add AgentManager Import

In `simulationengine.py`, add:
```python
from .agentmanager import AgentManager
```

### Step 2: Initialize AgentManager in __init__

Add to `SimulationEngine.__init__()`:
```python
self._agent_manager: Optional[AgentManager] = None
```

### Step 3: Create AgentManager Instance in init()

Replace the agent initialization logic with:
```python
# Initialize agent manager
self._agent_manager = AgentManager(
    config=self._config,
    llm=self._llm,
    environment=self._environment,
    messager=self._messager,
    embedding=self._embedding,
    database_writer=self._database_writer,
    db_actor=self._db_actor,
    exp_id=self.exp_id,
)

# Create toolbox
await self._agent_manager.create_toolbox()

# Prepare and initialize agents
agents = await self._agent_manager.prepare_agents(
    self._config.agents, 
    resume_state=self._resume_state
)
self._agent_manager._validate_resume_agent_count(agents, self._resume_state)
await self._agent_manager.initialize_agents(agents, self._resume_state)
```

### Step 4: Replace Agent Iteration with AgentManager Calls

**Before**:
```python
tasks = [agent.run() for agent in self._id2agent.values()]
agent_time_log = await asyncio.gather(*tasks)
```

**After**:
```python
agent_time_log = await self._agent_manager.run_all_agents()
```

### Step 5: Update Agent Access Methods

**Before**:
```python
# Direct dictionary access
filtered_ids = [id for id, agent in self._id2agent.items()]

# Filter agents
filtered = [agent for agent in self._id2agent.values() if ...]
```

**After**:
```python
# Use AgentManager methods
filtered_ids = await self._agent_manager.filter_agents(types=AgentTypes)
filtered_ids = await self._agent_manager.filter_agents(filter_str="...")

# Access agents
agents = self._agent_manager.agents  # All agents
agent = self._agent_manager.get_agent(agent_id)
```

### Step 6: Update Memory Operations

**Before**:
```python
for agent_id in target_agent_ids:
    agent = self._id2agent[agent_id]
    await agent.status.update(key, content)
```

**After**:
```python
await self._agent_manager.update_agent_memory(target_agent_ids, key, content)
```

### Step 7: Update Gather Operations

**Before**:
```python
results = {}
for agent in self._id2agent.values():
    if agent.id in target_agent_ids:
        results[agent.id] = await agent.status.get(content)
```

**After**:
```python
results = await self._agent_manager.gather_from_agents(
    content, 
    agent_ids=target_agent_ids,
    flatten=False,
    keep_id=True
)
```

### Step 8: Update Agent Deletion

**Before**:
```python
tasks = []
for agent_id in target_agent_ids:
    agent = self._id2agent[agent_id]
    tasks.append(agent.close())
await asyncio.gather(*tasks)
for agent_id in target_agent_ids:
    del self._id2agent[agent_id]
```

**After**:
```python
await self._agent_manager.delete_agents(target_agent_ids)
```

### Step 9: Update Agent Reset

**Before**:
```python
tasks = []
for agent in self._id2agent.values():
    tasks.append(agent.reset())
await asyncio.gather(*tasks)
```

**After**:
```python
await self._agent_manager.reset_all_agents()
```

### Step 10: Update Cleanup

**Before**:
```python
close_tasks = []
for agent in self._id2agent.values():
    close_tasks.append(agent.close())
await asyncio.gather(*close_tasks)
```

**After**:
```python
await self._agent_manager.close_all_agents()
```

---

## Key Properties & Methods

### Properties
```python
manager.agents              # Get all agents (dict)
manager.agent_ids          # Get all agent IDs (list)
manager.get_agent(id)      # Get specific agent
```

### Agent Execution
```python
await manager.run_all_agents()              # Execute one step for all agents
await manager.reset_all_agents()            # Reset agents for next round
```

### Agent Management
```python
await manager.initialize_agents(agents)     # Initialize agents
await manager.delete_agents(agent_ids)      # Delete specific agents
await manager.close_all_agents()            # Cleanup all agents
```

### Memory Operations
```python
await manager.update_agent_memory(agent_ids, key, content)
await manager.gather_from_agents(content, agent_ids)
await manager.save_agent_static_info(step)
```

### Filtering
```python
await manager.filter_agents(types=(CitizenAgent,))
await manager.filter_agents(filter_str="${profile.age} > 18")
```

---

## Benefits of Integration

1. **Reduced Complexity**: SimulationEngine becomes more focused and readable
2. **Better Maintainability**: Agent logic is centralized and easier to modify
3. **Enhanced Testability**: AgentManager can be tested independently
4. **Improved Reusability**: AgentManager can be used in other simulation contexts
5. **Scalability**: Easier to add new agent features without bloating SimulationEngine
6. **Separation of Concerns**: Clear boundaries between simulation logic and agent management

---

## Complete Integration Checklist

- [ ] Add AgentManager import to simulationengine.py
- [ ] Add `_agent_manager` field to SimulationEngine.__init__
- [ ] Create AgentManager instance in `init()` method
- [ ] Replace `_prepare_agents()` calls with AgentManager
- [ ] Replace `_initialize_agents()` calls with AgentManager
- [ ] Replace agent iteration with AgentManager.run_all_agents()
- [ ] Replace agent access with AgentManager properties
- [ ] Replace memory updates with AgentManager.update_agent_memory()
- [ ] Replace gather operations with AgentManager.gather_from_agents()
- [ ] Replace delete operations with AgentManager.delete_agents()
- [ ] Replace reset operations with AgentManager.reset_all_agents()
- [ ] Replace close operations with AgentManager.close_all_agents()
- [ ] Remove redundant agent management code from SimulationEngine
- [ ] Update all agent filtering calls to use AgentManager.filter_agents()
- [ ] Test the refactored code thoroughly

---

## Example: Before and After

### Before (Mixed Responsibility)
```python
class SimulationEngine:
    async def step(self):
        # ... many other things ...
        
        # Agent execution mixed in
        tasks = [agent.run() for agent in self._id2agent.values()]
        agent_time_log = await asyncio.gather(*tasks)
        
        # Agent memory operations mixed in
        for agent in self._id2agent.values():
            if isinstance(agent, CitizenAgentBase):
                position = await agent.status.get("position")
                # ... process position ...
        
        # Agent filtering mixed in
        filtered = [a for a, (cls, _) in self._filter_base.items() 
                   if issubclass(cls, CitizenAgentBase)]
```

### After (Separated Responsibility)
```python
class SimulationEngine:
    async def step(self):
        # ... many other things ...
        
        # Clean agent execution
        agent_time_log = await self._agent_manager.run_all_agents()
        
        # Clean memory operations
        await self._agent_manager.update_agent_memory(
            agent_ids, "status", new_status
        )
        
        # Clean filtering
        citizen_ids = await self._agent_manager.filter_agents(
            types=(CitizenAgentBase,)
        )
```

---

## Notes

- AgentManager maintains backward compatibility with existing code
- All methods are async for consistency with SimulationEngine
- The refactoring is incremental - you can integrate step by step
- Tests should be updated to use AgentManager directly
- Documentation should reflect the new architecture

