# Qdrant Cache Performance: Batched Embed Actor
> Introduce a shared `EmbedActor` Ray actor that batches embedding requests from all agent processes into single ONNX inference calls, eliminating the per-request model invocation overhead inside `QdrantCacheActor`.

## Purpose & Motivation

Every LLM cache probe today triggers `QdrantCacheActor._embed_typed_fields`, which calls `fastembed.TextEmbedding.embed([single_text])` once per text field in the prompt's input schema. With 1000 agents running in parallel, each ticking every simulation step, that means hundreds to thousands of single-item embedding calls hitting the model sequentially inside one Ray actor. The embedding model is an ONNX transformer that has non-trivial per-call overhead (tokenization, padding, ONNX session execution) that does not scale linearly — it is materially faster to embed 64 texts in a single batch than to embed them individually.

The `QdrantCacheActor` is a single-process Ray actor. All agents call it via `.remote()`. This actor serializes all embedding work: while it is embedding one agent's cache probe, every other agent's probe waits in the Ray call queue. The model's native `batch_size` parameter is never exploited.

A separate `EmbedActor` with an internal batching loop collapses concurrent single-text requests from many agents into one model inference call, cutting total wall-clock time proportionally to batch size while adding only a bounded wait (10–50 ms) before the batch fires.

Additional bottlenecks identified during the audit are documented under the Audit section below.

## Success Criteria

1. Wall-clock latency per cache probe (measured at `LLM._probe_semantic_cache`, reported via `cache_lookup_duration_seconds{cache_type="qdrant"}`) decreases when the simulation is running 200+ agents.
2. `EmbedActor` emits a `embed_batch_size` histogram metric so batch effectiveness is observable.
3. `QdrantCacheActor` no longer holds a `fastembed.TextEmbedding` instance; all embedding goes through `EmbedActor`.
4. Single-agent benchmarks (1 agent, no contention) show neutral or better performance compared to before (the batching timeout adds at most the configured wait, e.g. 25 ms, in the worst case).
5. Existing e2e test `tests/e2e/006_qdrant_cache.py` passes unchanged.

## Scope

**In scope:**
- New `EmbedActor` Ray remote actor in `agentsociety/llm/cache/embed_actor.py`.
- `EmbedActor` batches requests with a configurable `batch_timeout_ms` and `max_batch_size`.
- `QdrantCacheActor` delegates all `TextEmbedding` calls to `EmbedActor`.
- `InfrastructureManager` creates and passes `EmbedActor` to `QdrantCacheActor`.
- New config knob `embed_batch_timeout_ms` and `embed_max_batch_size` in `QdrantCacheConfig`.
- New Prometheus histogram `embed_batch_size_total` (buckets: 1, 2, 4, 8, 16, 32, 64, 128, 256) exposed via `PrometheusActor`.
- Audit fix A: `_embed_typed_fields` calls `embed` one field at a time; batch all fields for a single prompt together.
- Audit fix B: `_flush_buffer` and `_rebuild_model` block the actor event loop during upsert and KNN rebuild; move them to a thread via `asyncio.to_thread` (actor method changes to async).
- Audit fix C: `_get_tournament_data` fetches up to 5000 vectors from Qdrant at every rebuild; cap it and add a scroll offset so repeated rebuilds see different data.
- Audit fix D: document and enforce that `QdrantCacheConfig.batch_size` default of 1000 means no flush and no rebuild until 1000 cache misses have been recorded; add a `min_batch_size_to_rebuild` config knob so operators can trigger a first rebuild sooner.

**Out of scope:**
- GPU/CUDA acceleration for the embedding model (not available in this deployment).
- Replacing `fastembed.TextEmbedding` with a different model.
- Distributing `EmbedActor` across multiple processes (one actor is sufficient; the bottleneck is serial calls, not CPU capacity).
- Changes to `VectorStore` (uses `SparseTextEmbedding` / BM25, a different model and a different use case).
- `GlobalDispatcherCacheActor` (no embedding; bottleneck is not relevant here).
- Changes to the `QdrantCacheChampionship` KNN logic.

## Constraints

- `EmbedActor` must be a Ray remote actor (`@ray.remote`). Agents run in separate Ray worker processes and cannot share an in-process object. The actor is the only process-safe shared state primitive in this architecture.
- `fastembed.TextEmbedding.embed(documents: list[str])` is a synchronous generator. The actor's event loop must not block while the model is running. The embedding call must be dispatched to a thread via `asyncio.to_thread` or `loop.run_in_executor`.
- Ray actor method calls are serialized by default (Ray's GIL-equivalent). To service concurrent requests while the batch is being filled, `EmbedActor` must use `asyncio` inside the actor and declare `@ray.remote(concurrency_groups={"embed": N})` or use an async gather pattern. The simplest correct pattern: `EmbedActor` methods are `async`, the actor runs with async concurrency, and the batch collector uses `asyncio.Queue`.
- `QdrantCacheActor` must remain the sole owner of the Qdrant `QdrantClient` instance. `EmbedActor` only owns the `TextEmbedding` model.
- The `cache-metrics.md` feature plan (already implemented per `PrometheusActor` at line 94) introduced `record_cache_latency`. The new `embed_batch_size` metric follows the same pattern.
- No breaking changes to `QdrantCacheConfig` public API. New fields must have defaults that reproduce current behavior (`embed_batch_timeout_ms=25`, `embed_max_batch_size=256`).

## Architecture & Integration Points

### Current hot path (cache probe)

```
LLM.atext_request (llm/llm.py:501)
  → LLM._probe_semantic_cache (llm/llm.py:255)
    → QdrantCacheActor.query_and_maybe_serve.remote(...)
      [Ray RPC — crosses process boundary]
      → QdrantCacheActor._embed_typed_fields (llm/cache/ray_actor.py:134)
          for each field:
            text = normalize(value)
            emb = next(self._embedding.embed([text]))  ← single-item ONNX inference
      → MultiFeatureQdrantChampionCache.evaluate (llm/cache/qdrant_cache.py:213)
          → self._query_neighbors (qdrant_cache.py:140)  ← Qdrant ANN query
      ← returns hit/miss + label
    ← returns decoded output or None
  ← LLM returns cached value or continues to live call
```

### After this feature

```
LLM._probe_semantic_cache
  → QdrantCacheActor.query_and_maybe_serve.remote(...)
    [Ray RPC]
    → QdrantCacheActor._embed_typed_fields_via_actor (llm/cache/ray_actor.py)
        texts = [normalize(v) for all text fields]   ← collected first
        embeddings = await EmbedActor.embed_batch.remote(texts)  ← one remote call
        [EmbedActor coalesces with concurrent requests and calls embed(all_texts) once]
    → MultiFeatureQdrantChampionCache.evaluate (unchanged)
```

### Integration points

- `agentsociety/llm/cache/ray_actor.py:63–67` — `QdrantCacheActor.__init__` constructs `TextEmbedding`; this is removed and replaced with an `embed_actor` parameter.
- `agentsociety/llm/cache/ray_actor.py:134–150` — `QdrantCacheActor._embed_typed_fields`: the inner loop calling `next(self._embedding.embed([text]))` becomes a batch call to `EmbedActor`.
- `agentsociety/simulation/infrastructuremanager.py:402–437` — `_init_llm_cache_actor` constructs `QdrantCacheActor.remote(...)`; it must also construct `EmbedActor.remote(...)` and pass it.
- `agentsociety/llm/cache/config.py:6–18` — `QdrantCacheConfig` gets two new optional fields: `embed_batch_timeout_ms` and `embed_max_batch_size`.
- `agentsociety/llm/cache/__init__.py:1–13` — `EmbedActor` added to public re-exports.
- `agentsociety/llm/__init__.py:1–15` — `EmbedActor` re-exported if needed by `infrastructuremanager.py`.
- `agentsociety/performance/MetricsTracker.py` — new `embed_batch_size` histogram added (same pattern as `cache_lookup_duration_seconds` at line 62).
- `agentsociety/performance/prometheusActor.py` — new `record_embed_batch_size` method.

## Similar Patterns & Reuse

- **`LLMActor` with async concurrency**: `agentsociety/llm/llm_actor.py:61` — `@ray.remote(concurrency_groups={"default": 500})`. `EmbedActor` uses the same decorator to allow async concurrency.
- **`GlobalDispatcherCacheActor` shared-actor pattern**: `agentsociety/agent/dispatcher_cache_actor.py:37` — a single Ray actor shared via toolbox. `EmbedActor` follows the same deployment pattern: one actor, passed by reference, never reconstructed per-agent.
- **`PrometheusActor.record_cache_latency`**: `agentsociety/performance/prometheusActor.py:94` — fire-and-forget `.remote()` call from another actor. `EmbedActor` uses the same pattern for its batch-size histogram.
- **`asyncio.to_thread` for blocking work**: Not currently used in this codebase but is the standard Python 3.9+ mechanism for running synchronous blocking code (like ONNX inference) inside an async context without blocking the event loop. The alternative `loop.run_in_executor(None, ...)` is also acceptable.

## Implementation Strategy

### Step 1 — Extend `QdrantCacheConfig`

**Before**: `agentsociety/llm/cache/config.py:6` — `QdrantCacheConfig` has no embed batching fields.

**After**: Add:
```
embed_batch_timeout_ms: int = Field(default=25, ge=1, le=500)
embed_max_batch_size: int = Field(default=256, ge=1)
```
Defaults reproduce current behavior (a single-item batch fires after 25 ms — worst case is 25 ms added latency in low-concurrency scenarios; at high concurrency the batch fills before the timeout fires).

### Step 2 — Create `EmbedActor`

New file: `agentsociety/llm/cache/embed_actor.py`

The actor must:
1. Load `fastembed.TextEmbedding` in `__init__`.
2. Expose one async method: `embed_batch(texts: list[str]) -> list[list[float]]` (a list of embedding vectors as plain Python lists for Ray serialization).
3. Internally, use an `asyncio.Queue` and a background coroutine (started with `asyncio.create_task` in `__init__`) that:
   - Pulls items from the queue with a `asyncio.wait_for(queue.get(), timeout=batch_timeout_s)`.
   - Accumulates items until `max_batch_size` is reached or the timeout fires.
   - Calls `asyncio.to_thread(list, model.embed(texts))` to run ONNX inference off the event loop.
   - Resolves all waiting `asyncio.Future` objects with their respective slice of results.
4. Each call to `embed_batch` puts a `(texts, future)` tuple on the queue and awaits the future.

The actor is declared `@ray.remote` with no extra options (Ray handles concurrency through its own async scheduling when the actor's methods are `async`). It must use Python `asyncio` exclusively for internal coordination — no threads for queue management.

**Embeddings are returned as `list[list[float]]`**, not numpy arrays, because numpy arrays are not efficiently serialized by Ray's default serializer across process boundaries (Ray uses pickle/Arrow; a Python list of floats is lighter for small vectors).

**Before** (`ray_actor.py:148`):
```python
emb = next(self._embedding.embed([text]))
feature_row[key] = np.asarray(emb, dtype=float)
```

**After** (`ray_actor.py`):
```python
# Collect all text fields first
texts_to_embed = [(key, text) for key, text in text_fields.items()]
text_keys = [k for k, _ in texts_to_embed]
text_values = [t for _, t in texts_to_embed]
# One remote call to EmbedActor for all text fields of this probe
raw_vecs = await self._embed_actor.embed_batch.remote(text_values)
for key, vec in zip(text_keys, raw_vecs):
    feature_row[key] = np.asarray(vec, dtype=float)
```

This means `QdrantCacheActor.query_and_maybe_serve` and `record` must become `async def` methods. Ray actors support async methods natively.

### Step 3 — Wire `EmbedActor` in `InfrastructureManager`

**Before**: `agentsociety/simulation/infrastructuremanager.py:418` — `QdrantCacheActor.remote(...)` is constructed with `embedding_model` and `embedding_cache_dir` parameters.

**After**:
1. Construct `EmbedActor.remote(embedding_model=cfg.embedding_model, embedding_cache_dir=..., batch_timeout_ms=cfg.embed_batch_timeout_ms, max_batch_size=cfg.embed_max_batch_size, metrics_actor=self._metrics_actor)` before constructing `QdrantCacheActor`.
2. Remove `embedding_model` and `embedding_cache_dir` from the `QdrantCacheActor.remote(...)` call; pass `embed_actor=self._embed_actor` instead.
3. Add `self._embed_actor: Optional[Any] = None` to `InfrastructureManager.__init__`.
4. In `close()`, call `self._embed_actor.close.remote()` if set (to allow graceful shutdown logging).

### Step 4 — Audit Fix A: batch fields within a single probe

**Before**: `agentsociety/llm/cache/ray_actor.py:134–150` — `_embed_typed_fields` loops over fields and calls `embed([text])` once per text field. If a prompt has 3 text input fields, this makes 3 sequential single-item ONNX calls.

**After**: After the `EmbedActor` refactor in Step 2, all text fields for a given probe are sent as a single list in one `embed_batch.remote(...)` call. This is automatic when Step 2's batch-collection approach is used. No separate change needed.

### Step 5 — Audit Fix B: unblock the actor event loop during flush and rebuild

**Before**: `agentsociety/llm/cache/ray_actor.py:390–408` — `QdrantCacheActor.close()` is synchronous and calls `cache._flush_buffer()` then `cache._rebuild_model()` for every collection. `_flush_buffer` calls `self.client.upsert(...)` (synchronous network I/O to Qdrant). `_rebuild_model` calls `_get_tournament_data` (synchronous Qdrant scroll over up to 5000 points) and then runs KNN scoring in NumPy. Both block the actor process.

During a live simulation, `_drain_one_rebuild` is called inline in `query_and_maybe_serve` and `record` at lines 269, 296, 333 — meaning a rebuild can silently block an arbitrary number of agent cache probes while the KNN tournament runs.

**After**:
1. Make `QdrantCacheActor.query_and_maybe_serve`, `record`, and `close` async.
2. In `_drain_one_rebuild`, wrap `cache._rebuild_model()` in `await asyncio.to_thread(cache._rebuild_model)`.
3. In `_flush_buffer`, wrap `self.client.upsert(...)` in `await asyncio.to_thread(client.upsert, ...)`.
4. In `close`, await `asyncio.to_thread` for each collection's flush + rebuild.

This requires converting `MultiFeatureQdrantChampionCache._flush_buffer` and `_rebuild_model` to accept being called from a thread (they are already pure CPU/IO with no asyncio internal state, so this is safe).

### Step 6 — Audit Fix C: cap tournament data fetch

**Before**: `agentsociety/llm/cache/qdrant_cache.py:259–277` — `_get_tournament_data(sample_size=5000)` scrolls Qdrant for up to 5000 points **with `with_vectors=True`**. At 384-dimensional float vectors, 5000 points = ~7.5 MB fetched per rebuild, per collection, regardless of how large the collection is. For a simulation with 10 prompts, this is 75 MB per rebuild cycle.

**After**: One change:
1. Use a random offset scroll instead of always starting at point 0, so repeated rebuilds see different samples from the collection when the collection is larger than `sample_size`. Qdrant's `scroll` API accepts an `offset` parameter.

## Audit: Other Performance and Correctness Issues Found

### A. Single-item embed calls (addressed by Step 2 above)

`agentsociety/llm/cache/ray_actor.py:148` — `next(self._embedding.embed([text]))` called once per text field per probe. This is the primary bottleneck.

### B. Synchronous Qdrant I/O blocks the actor event loop (addressed by Step 5 above)

`agentsociety/llm/cache/ray_actor.py:269` — `_drain_one_rebuild` is called inline in every probe. `_rebuild_model` at `qdrant_cache.py:190` is a synchronous blocking call that fetches vectors from Qdrant and runs a KNN tournament. Depending on collection size, this takes 10s–1000s of milliseconds and blocks every agent waiting on the cache actor.

### C. Tournament data is always fetched from the start (addressed by Step 6 above)

`agentsociety/llm/cache/qdrant_cache.py:261` — `self.client.scroll(..., limit=sample_size)` with no offset. Large collections waste bandwidth fetching the same stale data.

### D. Correctness: `_collection_exists` called on every `_ensure_collection` invocation

`agentsociety/llm/cache/qdrant_cache.py:88–98` — `_ensure_collection` is called on every `record` and `evaluate` call. The early-return guard `if self.collection_initialized: return` at line 93 works correctly after the first call, but `_collection_exists` at line 95 hits the Qdrant HTTP API on the very first call per collection. This is correct but inefficient at startup: if 100 agents each trigger a probe for the same prompt before the first flush, all 100 will hit `_collection_exists`. This is masked by `QdrantCacheActor` being a single actor (they serialize), but calls still go to Qdrant. No change needed — the serialization means it is a one-time cost per collection, not per probe. Documented for awareness.

### E. Correctness: `_normalize_by_type` and `_encode_numeric_field` called twice (record + evaluate path)

`agentsociety/llm/cache/ray_actor.py:134–150` — `_embed_typed_fields` is called in both `query_and_maybe_serve` (line 277) and `record` (line 328). When a miss occurs, the embedding is computed twice: once in `query_and_maybe_serve` (to evaluate, get a miss) and again in `record` (to store). The vectors are discarded between the two calls.

This is a correctness-neutral but performance-wasteful double embedding. A fix would have `query_and_maybe_serve` return the computed `feature_row` alongside the hit/miss result and pass it through to `record`. However, this requires changing the `LLM._record_cache_miss` call signature at `llm/llm.py:409`, which currently passes only the raw `prompt_inputs`. The fix is worthwhile but is a separate interface change. **Flag this for future work, not this plan.**

### F. Correctness: `_drain_one_rebuild` called twice per `query_and_maybe_serve` on a hit

`agentsociety/llm/cache/ray_actor.py:269, 296` — `_drain_one_rebuild()` is called at the start of `query_and_maybe_serve` and again at the end (line 296), only on a cache hit. This means a rebuild can be triggered, then another one attempted in the same method call if the first one was processed and a new one was queued. This appears to be intentional (drain the queue eagerly), but it is subtle. The logic is correct under the current single-threaded actor model. After Step 5 (async), the dual-drain is still correct because `_drain_one_rebuild` is idempotent when the pending set is empty. No change needed, but it should be commented.

## Trade-Offs

- **Batch timeout adds worst-case latency**: In a single-agent or very-low-concurrency scenario, `embed_batch_timeout_ms=25` means each cache probe waits up to 25 ms before its embedding fires. At high concurrency the batch fills before the timeout, so no penalty. The default of 25 ms is less than typical LLM call latency (~500 ms–2 s) and smaller than the Qdrant ANN query itself, so the absolute impact is minor. The timeout is configurable to 0 ms if needed (effectively disabling batching).
- **`EmbedActor` is another Ray actor**: Adds one more remote object to manage, monitor, and close. Justified because it is the only way to share the embedding model across Ray worker processes.
- **Async `QdrantCacheActor` methods**: Converting `query_and_maybe_serve` and `record` to `async def` requires all callers to `await` them. They are already called with `.remote()` in Ray, so callers are already awaiting `ObjectRef`s. No call-site changes needed — Ray handles this transparently for async actor methods.
- **Double-embedding not fixed here** (Audit item E): The interface change needed to pass `feature_row` from `query_and_maybe_serve` through to `record` via `LLM._record_cache_miss` touches the public `QdrantCacheActor.record()` signature, which could affect hypothetical external users. Fixing it in a separate focused PR preserves the plan's scope.
- **`_rebuild_model` thread safety**: `cache._rebuild_model()` reads and writes `self.championship.active_feature` and `self.championship.max_neighbor_distance`. If `_rebuild_model` runs in a thread while `evaluate` reads these fields synchronously, there is a TOCTOU race. Mitigation: keep the rule that `_drain_one_rebuild` is only called from within `QdrantCacheActor` (single actor, single event loop), so even with `asyncio.to_thread`, only one rebuild runs at a time (guarded by an `asyncio.Lock` in `_drain_one_rebuild`).

## Rejected Approaches

- **Multiple `QdrantCacheActor` instances per node**: Would allow parallel embeddings without a shared actor, but each actor would hold its own Qdrant client and would write to the same on-disk collection concurrently. Qdrant's local client is not safe for concurrent multi-process writes. Rejected.
- **`ThreadPoolExecutor` inside `QdrantCacheActor` for embeddings**: Would allow parallel ONNX inference within one actor. The ONNX runtime's GIL behavior is inconsistent; fastembed's `threads` parameter controls internal ONNX parallelism, not Python-level concurrency. A separate Ray actor is cleaner and consistent with how `LLMActor` handles parallel inference.
- **`batch_size` parameter on `embed([text], batch_size=N)` already batches internally**: Confirmed false — `fastembed.TextEmbedding.embed` accepts a `batch_size` parameter that controls how documents within a single call are chunked before passing to the ONNX session. Calling `embed([one_text])` means one text, one ONNX call, regardless of `batch_size`. The batching we need is across multiple concurrent `.embed()` invocations from different Ray worker processes, not within a single call.
- **Increase `QdrantCacheActor` Ray concurrency group**: Ray actors are single-threaded by default. Increasing the concurrency group allows Ray to interleave multiple async method calls but does not parallelize the synchronous ONNX model. Rejected as insufficient.
- **Replace ONNX model with a simpler TF-IDF or BM25 embedding inside `QdrantCacheActor`**: The existing Qdrant-in-memory memory system already uses BM25 (`SparseTextEmbedding`). The dense `TextEmbedding` model is used specifically because KNN on dense vectors with cosine distance has better semantic generalization for the champion-feature cache. Replacing it would degrade cache accuracy. Rejected.
- **Pre-compute all embeddings at prompt registration time**: The input field values vary per-agent per-tick (they are runtime state: agent emotions, hunger levels, etc.). They cannot be precomputed. Rejected.

## Assumptions & Open Questions

- **Assumption**: `fastembed.TextEmbedding.embed(texts: list[str])` is thread-safe when called from `asyncio.to_thread`. The fastembed library uses ONNX Runtime which is documented as thread-safe for inference. Verify before merging.
- **Assumption**: Ray async actor methods are supported in the project's Ray version. Check `pyproject.toml` for the Ray version constraint.
- **Assumption**: The embedding model (`BAAI/bge-small-en-v1.5`, dimension ~384) produces vectors small enough that batching 256 of them fits in Ray's message buffer (~100 MB default). 256 × 384 × 4 bytes ≈ 393 KB. Well within limits.
- **Open question**: Should `EmbedActor` be co-located on the same node as `QdrantCacheActor`? By default, Ray may schedule them on different nodes in a multi-node cluster. Use `@ray.remote(scheduling_strategy=NodeAffinitySchedulingStrategy(...))` or place both in the same node group if cross-node RPC latency matters.
- **Open question**: Should `embed_batch_timeout_ms=0` be a valid config value meaning "no timeout, only fire when `max_batch_size` is reached"? This would cause unbounded waiting in low-concurrency scenarios. Recommend keeping minimum of 1 ms in the Pydantic validator. ANSWER: KEEP MINIMUM OF 1ms.
- **Open question**: The `QdrantCacheConfig.batch_size` default of 1000 was chosen for large simulations. For small-scale testing, is it acceptable for the model to never rebuild? The proposed `min_rebuild_threshold=50` in Step 7 addresses this but the right default value depends on how many cache misses typically accumulate in a 10-step smoke test. ANSWER: IGNORE THIS FOR NOW.

## Code That Could Be Refactored *(informational)*

- `agentsociety/llm/cache/ray_actor.py:77–80` — `_hit_counts` and `_miss_counts` dicts are maintained in parallel with Prometheus counters (since the `cache-metrics` feature). They are used for the end-of-run JSON stats file. A comment noting this intentional duplication would help future readers.
- `agentsociety/llm/cache/qdrant_cache.py:169–188` — `_flush_buffer` constructs `PointStruct` objects with an explicit `.tolist()` conversion for every vector in every row. This could be extracted into a `_row_to_point` helper for readability.
- `agentsociety/llm/cache/ray_actor.py:252–297` — `query_and_maybe_serve` is 45 lines with three distinct responsibilities: schema caching, embedding, and evaluation. Splitting into `_embed_inputs` and `_evaluate_cache` helpers would improve testability.
- `agentsociety/llm/cache/ray_actor.py:235–246` — `_drain_one_rebuild` silently discards rebuild failures after logging. A rebuild failure counter (even just logged, not a Prometheus metric) would help diagnose when the championship model is stuck.
- `agentsociety/simulation/infrastructuremanager.py:500–535` — `close()` lists its first `get_logger().info` message as "Closing ClickHouse tool..." but then first closes the dispatcher cache actor. Minor misleading log message.

## Proposed Next Steps

1. **Step 1**: Add `embed_batch_timeout_ms` and `embed_max_batch_sisim_bin_nameze` to `agentsociety/llm/cache/config.py`.
2. **Step 2**: Create `agentsociety/llm/cache/embed_actor.py` with `EmbedActor` (async, batch queue, `asyncio.to_thread` for ONNX).
3. **Step 3**: Refactor `QdrantCacheActor.__init__` to accept `embed_actor` instead of `embedding_model`/`embedding_cache_dir`; make `query_and_maybe_serve` and `record` async; update `_embed_typed_fields` to call `EmbedActor`.
4. **Step 4**: Wire `EmbedActor` construction and teardown in `agentsociety/simulation/infrastructuremanager.py:_init_llm_cache_actor` and `close`.
5. **Step 5 (Audit B)**: Wrap `_drain_one_rebuild` and close-path flush/rebuild in `asyncio.to_thread`; add `asyncio.Lock` to prevent concurrent rebuilds.
6. **Step 6 (Audit C)**: Cap tournament data fetch and add random offset to `_get_tournament_data`.
7. **Step 7 (Audit D)**: Add `min_rebuild_threshold` to `QdrantCacheConfig` and `MultiFeatureQdrantChampionCache`.
8. **Step 8**: Add `embed_batch_size` histogram to `MetricsTracker` and expose via `PrometheusActor`.
9. **Step 9**: Update `agentsociety/llm/cache/__init__.py` and `agentsociety/llm/__init__.py` to re-export `EmbedActor`.
10. **Verify**: Run `tests/e2e/006_qdrant_cache.py` via `sh tests/run_e2e_tests.sh`. Confirm stats file is written and no regressions. If monitoring is enabled, confirm `embed_batch_size` histogram appears in Prometheus.
