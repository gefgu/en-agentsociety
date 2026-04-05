# `memory/` — Agent Memory System

This package implements the multi-layered memory system used by every agent.

---

## Files

| File | Purpose |
|---|---|
| `memory.py` | `Memory` orchestrator class |
| `kv_memory.py` | `KVMemory` |
| `stream_memory.py` | `MemoryNode`, `StreamMemory` |
| `spatial_memory.py` | `SpatialMemoryNode`, `SpatialMemory` |
| `const.py` | Memory-related constants |

---

## Memory Architecture

Every agent has a `Memory` object that bundles three specialized stores:

```
Memory
├── status:  KVMemory    — numeric/categorical state (hunger, energy, location, …)
├── profile: KVMemory    — demographic profile (age, occupation, income, …)
└── stream:  StreamMemory — time-ordered event log
```

An optional `SpatialMemory` is available for location-aware agents.

---

## `KVMemory`

Key-value store with optional semantic search via `SparseTextEmbedding`.

```python
# Read
value = await agent.memory.status.get("hunger_satisfaction")
all_status = await agent.memory.status.get_all()

# Write
await agent.memory.status.update("hunger_satisfaction", 0.7)
await agent.memory.status.batch_update({"hunger": 0.7, "energy": 0.9})

# Semantic search
results = await agent.memory.status.search("I am feeling tired", top_k=3)
```

### Initialization

`KVMemory` is configured via `MemoryConfig` (a list of `MemoryAttribute` objects). The framework populates these from `Agent.StatusAttributes` at agent creation time.

### Embedding (optional)

Fields with an `embedding_template` are automatically embedded on first initialization, enabling semantic retrieval via `SparseTextEmbedding` (fastembed BM25).

---

## `StreamMemory`

Ordered log of events, observations, and decisions.

```python
# Append event
await agent.memory.stream.add({
    "type": "observation",
    "description": "Saw a crowded park",
    "timestamp": 1234567890,
})

# Retrieve recent N events
events = await agent.memory.stream.get_recent(10)

# Semantic search over stream
results = await agent.memory.stream.search("park", top_k=5)
```

---

## `SpatialMemory`

Tracks location history and known places.

```python
# Record a visited location
await agent.memory.spatial.add_visit(lat=39.9, lng=116.4, place_name="Tiantan Park")

# Retrieve frequently visited places
frequent = await agent.memory.spatial.get_frequent(top_k=5)
```

---

## `MemoryAttribute`

Declares a typed memory field with a default value:

```python
MemoryAttribute(
    name="hunger_satisfaction",
    type=float,
    default_or_value=0.9,
    description="Agent hunger satisfaction (0–1)",
    embedding_template="My hunger level is {}",   # optional: enables semantic search
)
```

---

## Thread Safety

All `KVMemory` and `StreamMemory` operations are protected by `asyncio.Lock` so concurrent agent tasks do not corrupt memory state.

---

## Integration with FormatPrompt

Memory fields are accessible in `FormatPrompt` templates via `${status.field}`, `${profile.field}`, etc. The prompt engine reads directly from the `KVMemory` at format time.
