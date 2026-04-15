# Cache Metrics: Hits, Misses, and Latency
> Expose Prometheus hit/miss counters and latency histograms for both the `QdrantCacheActor` and `GlobalDispatcherCacheActor`, mirroring the pattern already used for LLM block performance.

## Purpose & Motivation

Two cache systems exist in the simulation — the `GlobalDispatcherCacheActor` (block-routing cache) and the `QdrantCacheActor` (LLM semantic cache). The dispatcher cache already reports hits and misses to Prometheus via `PrometheusActor`. The Qdrant cache does not: its `metrics_actor` wiring was never built into `QdrantCacheActor.__init__`, so the `cache_hits_total` / `cache_misses_total` counters in `MetricsTracker` are only populated from the `LLM` layer (hit-only path) and `LLM._record_cache_miss` (miss path). Neither cache system records lookup latency at all.

The goal is to close both gaps cleanly and durably.

## Success Criteria

1. `cache_hits_total{exp_id, prompt_name}` and `cache_misses_total{exp_id, prompt_name}` rise correctly for every Qdrant cache query, visible in Prometheus within one scrape interval.
2. `dispatcher_cache_hits_total{exp_id}` and `dispatcher_cache_misses_total{exp_id}` continue to work as before (no regression).
3. New histogram metric `cache_lookup_duration_seconds{exp_id, cache_type, prompt_name}` is populated on every cache query for both systems.
4. `cache_type="qdrant"` and `cache_type="dispatcher"` distinguish the two in Grafana queries.
5. No code in the existing hit/miss reporting path in `LLM._probe_semantic_cache` and `LLM._record_cache_miss` is removed or duplicated — the `LLM`-layer hit/miss reporting stays as the source of truth for `cache_hits_total` / `cache_misses_total`, and only latency is added there.

## Scope

**In scope:**
- Add `metrics_actor` parameter to `QdrantCacheActor.__init__` and pass it through from `InfrastructureManager._init_llm_cache_actor`.
- Add a `cache_lookup_duration_seconds` Histogram to `MetricsTracker`, with labels `[exp_id, cache_type, prompt_name]`.
- Add `record_cache_latency(cache_type, prompt_name, duration)` to `MetricsTracker` and expose it on `PrometheusActor`.
- Record Qdrant probe latency inside `LLM._probe_semantic_cache` (the timing is already measured at `llm.py:274` — emit to Prometheus alongside it).
- Record dispatcher cache lookup latency inside `GlobalDispatcherCacheActor.check_cache` (requires adding `time` import there).
- Update the Grafana dashboard with new panels for hit-rate and latency histograms.

**Out of scope:**
- Latency for `QdrantCacheActor.record()` (write path) — high-frequency, low-value for dashboards.
- Per-agent-ID breakdown for cache metrics (cardinality explosion risk).
- Qdrant collection-level latency breakdown (collection name as a Prometheus label is too high-cardinality).
- Any changes to the ClickHouse actor or SQLite database path.

## Constraints

- Prometheus label cardinality: `prompt_name` is already a label on `cache_hits_total` and can be reused safely on the latency histogram. Collection names from Qdrant must NOT become labels; `prompt_name` (derived from `prompt_identity[0]`) is the right granularity.
- `QdrantCacheActor` is a Ray remote actor — it cannot call `metrics_actor` synchronously. All calls must be `.remote()` fire-and-forget, exactly as `GlobalDispatcherCacheActor` does at `dispatcher_cache_actor.py:82`.
- `PrometheusActor` is also a Ray actor — all calls to it from other actors must use `.remote()`.
- The `prometheus_client` library is not process-safe across Ray actors. Each Ray actor runs in its own process. `QdrantCacheActor` must NOT instantiate `prometheus_client` counters directly; it must delegate to `PrometheusActor` the same way `GlobalDispatcherCacheActor` does.
- Latency for the Qdrant probe is measured in `LLM._probe_semantic_cache` (a coroutine on the main process/worker). The `LLM` object already holds `self._metrics_actor`. This is the right place to emit Qdrant probe latency — not inside `QdrantCacheActor` (which would require timing its own async remote call, which is not meaningful for wall-clock latency as seen by the LLM caller).
- Dispatcher cache latency is measured inside `GlobalDispatcherCacheActor.check_cache`, which is called via `.remote()`. The latency there measures internal lookup time, which is the correct metric.

## Architecture & Integration Points

### Existing wiring

- `agentsociety/simulation/infrastructuremanager.py:418` — `QdrantCacheActor.remote(...)` is constructed **without** `metrics_actor`; this is root cause of the missing Qdrant metrics.
- `agentsociety/simulation/infrastructuremanager.py:388` — `GlobalDispatcherCacheActor.remote(metrics_actor=self._metrics_actor)` — correctly wired already.
- `agentsociety/llm/llm.py:260–287` — `LLM._probe_semantic_cache()` measures `probe_latency` at line 274 but only logs it to debug; it calls `metrics_actor.record_cache_stats.remote(hit=True)` on a hit (line 282) but **never emits latency to Prometheus**.
- `agentsociety/llm/llm.py:393–414` — `LLM._record_cache_miss()` calls `metrics_actor.record_cache_stats.remote(hit=False)` on a miss but **never emits latency**.
- `agentsociety/agent/dispatcher_cache_actor.py:73–86` — `GlobalDispatcherCacheActor.check_cache()` records hits/misses but has no `time` import and no latency measurement.
- `agentsociety/performance/MetricsTracker.py:1–117` — defines all existing counters; no Histogram for cache latency exists.
- `agentsociety/performance/prometheusActor.py:82–92` — exposes `record_cache_stats`, `record_cache_hit_validation`, `record_dispatcher_cache_stats`; does not expose a latency method.

### Call chain for Qdrant cache metrics (current, broken)

```
dispatcher.py:202 → GlobalDispatcherCacheActor.check_cache.remote()
    → dispatcher_cache_actor.py:82 → metrics_actor.record_dispatcher_cache_stats.remote(True/False)
    → prometheusActor.py:90 → metricsTracker.record_dispatcher_cache_stats(hit)
    → MetricsTracker.py:112 → dispatcher_cache_hits/misses.labels(...).inc()   [WORKS]

LLM.atext_request (llm.py:501) → LLM._probe_semantic_cache (llm.py:255)
    → QdrantCacheActor.query_and_maybe_serve.remote()
    ← returns result
    → if hit: metrics_actor.record_cache_stats.remote(hit=True)   [WORKS for hits]
    → probe_latency measured but NOT emitted to Prometheus          [GAP 1]

LLM._record_cache_miss (llm.py:393)
    → metrics_actor.record_cache_stats.remote(hit=False)           [WORKS for misses]
    → probe latency NOT available here (measured upstream)          [GAP 2 — latency must be emitted earlier]
```

### After this feature

```
LLM._probe_semantic_cache (llm.py:255)
    → QdrantCacheActor.query_and_maybe_serve.remote()
    ← returns result
    → metrics_actor.record_cache_stats.remote(hit=True/False)      [existing, no change]
    → metrics_actor.record_cache_latency.remote(                   [NEW]
          cache_type="qdrant",
          prompt_name=prompt_identity[0],
          duration=probe_latency,
      )

GlobalDispatcherCacheActor.check_cache (dispatcher_cache_actor.py:73)
    → t0 = time.perf_counter()
    → ... existing logic ...
    → metrics_actor.record_dispatcher_cache_stats.remote(hit)      [existing]
    → metrics_actor.record_cache_latency.remote(                   [NEW]
          cache_type="dispatcher",
          prompt_name="dispatcher",
          duration=time.perf_counter() - t0,
      )

PrometheusActor.record_cache_latency (prometheusActor.py)          [NEW method]
    → MetricsTracker.record_cache_latency(...)                     [NEW method]
    → cache_lookup_duration_seconds.labels(...).observe(duration)  [NEW Histogram]
```

## Similar Patterns & Reuse

- **Latency histogram pattern**: `agentsociety/performance/BlockPerformance.py:18–22` — `block_duration = Histogram("performance_block_execution_duration_seconds", ..., ["exp_id", "block_name", "func_name", "agent_id", "actor"])`. The new `cache_lookup_duration_seconds` histogram follows identical construction.
- **Hit/miss counter pattern**: `agentsociety/performance/MetricsTracker.py:50–59` — `dispatcher_cache_hits` / `dispatcher_cache_misses` counters with `["exp_id"]` label set. The new histogram adds `cache_type` and `prompt_name` labels by analogy with `cache_hits_total` at line 20–29.
- **Fire-and-forget metrics emission from Ray actor**: `agentsociety/agent/dispatcher_cache_actor.py:81–85` — `self._metrics_actor.record_dispatcher_cache_stats.remote(True/False)`. Identical pattern applies in `QdrantCacheActor` if it holds a `_metrics_actor` reference.
- **`time.perf_counter()` latency measurement**: `agentsociety/llm/llm.py:260,274` — already measures Qdrant probe latency but discards it after a debug log. The new code re-uses `probe_latency` (already computed) and emits it.

## Implementation Strategy

### Step 1 — Add `record_cache_latency` to `MetricsTracker`

**Before**: `agentsociety/performance/MetricsTracker.py:117` — file ends after `record_dispatcher_cache_stats`.

**After**: Add one new `Histogram` field in `__init__` and a new `record_cache_latency` method.

```
cache_lookup_duration_seconds = Histogram(
    "cache_lookup_duration_seconds",
    "Latency of cache lookup operations (query only, not write)",
    ["exp_id", "cache_type", "prompt_name"],
)
```

Method signature:
```python
def record_cache_latency(self, cache_type: str, prompt_name: str, duration: float) -> None:
    self.cache_lookup_duration_seconds.labels(
        exp_id=self.exp_id,
        cache_type=cache_type,
        prompt_name=prompt_name,
    ).observe(duration)
```

Labels:
- `cache_type`: `"qdrant"` or `"dispatcher"` — distinguishes the two systems.
- `prompt_name`: `prompt_identity[0]` for Qdrant calls; `"dispatcher"` (a fixed string) for dispatcher calls, since the dispatcher cache is not keyed by prompt.

### Step 2 — Expose `record_cache_latency` on `PrometheusActor`

**Before**: `agentsociety/performance/prometheusActor.py:90–92` — last method is `record_dispatcher_cache_stats`.

**After**: Add:
```python
def record_cache_latency(self, cache_type: str, prompt_name: str, duration: float) -> None:
    """Record cache lookup latency for either cache system."""
    self.metricsTracker.record_cache_latency(cache_type, prompt_name, duration)
```

### Step 3 — Emit Qdrant probe latency from `LLM._probe_semantic_cache`

**Before**: `agentsociety/llm/llm.py:274–287` — `probe_latency` is computed but only emitted to a debug log; `record_cache_stats` is called only on a hit.

**After**: After the `record_cache_stats` call block (which already handles hit=True), also emit for misses and emit latency unconditionally:

```python
# Always record hit/miss (move miss reporting here from _record_cache_miss)
if self._metrics_actor is not None:
    hit = probe_result is not None
    self._metrics_actor.record_cache_stats.remote(
        prompt_name=str(context["prompt_identity"][0]),
        hit=hit,
    )
    self._metrics_actor.record_cache_latency.remote(
        cache_type="qdrant",
        prompt_name=str(context["prompt_identity"][0]),
        duration=probe_latency,
    )
```

Important: once hit/miss reporting is moved into `_probe_semantic_cache`, the corresponding call in `LLM._record_cache_miss` at line 411 must be **removed** to avoid double-counting misses. The miss is now recorded in `_probe_semantic_cache` unconditionally. The hit was already recorded there; the miss was previously recorded elsewhere. Moving both into one place is cleaner.

### Step 4 — Emit dispatcher cache latency from `GlobalDispatcherCacheActor.check_cache`

**Before**: `agentsociety/agent/dispatcher_cache_actor.py:1` — no `time` import; `check_cache` at line 73 has no timing.

**After**:
1. Add `import time` at the top.
2. Wrap the body of `check_cache` with `t0 = time.perf_counter()` before the cache lookup and `duration = time.perf_counter() - t0` after it.
3. After the existing `record_dispatcher_cache_stats.remote(hit)` call, add:
```python
if self._metrics_actor is not None:
    self._metrics_actor.record_cache_latency.remote(
        cache_type="dispatcher",
        prompt_name="dispatcher",
        duration=duration,
    )
```

The dispatcher cache lookup is pure Python dict access — expected sub-millisecond. The histogram will confirm this empirically.

### Step 5 — Wire `metrics_actor` into `QdrantCacheActor`

This step is required if we ever want the `QdrantCacheActor` to emit metrics itself (e.g., in a future step where it self-reports rebuild counts). For the current feature scope, latency and hit/miss are reported by the `LLM` layer, not by `QdrantCacheActor` directly — so this step is optional but recommended for completeness.

**Before**: `agentsociety/llm/cache/ray_actor.py:44–55` — `QdrantCacheActor.__init__` has no `metrics_actor` parameter.

**After**:
1. Add `metrics_actor=None` parameter to `__init__`.
2. Store as `self._metrics_actor = metrics_actor`.
3. In `agentsociety/simulation/infrastructuremanager.py:418`, pass `metrics_actor=self._metrics_actor`.

No calls to `metrics_actor` are needed inside `QdrantCacheActor` yet — the existing `_hit_counts` / `_miss_counts` dicts serve as internal state, and the `LLM` layer reports to Prometheus. The wiring establishes the capability for future use without incurring any current behavior change.

### Step 6 — Update Grafana dashboard

There is no pre-built Grafana JSON file in the repo (the `grafana/provisioning/dashboards/` directory contains only the `dashboard.yml` provisioning config file; no `.json` dashboard exists). Dashboard panels must be created manually in the Grafana UI and then exported. For this feature, add the following panels to the existing dashboard (or create a new "Cache Performance" row):

1. **Qdrant cache hit rate** — `rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))` grouped by `prompt_name`. Type: time series.
2. **Dispatcher cache hit rate** — `rate(dispatcher_cache_hits_total[5m]) / (rate(dispatcher_cache_hits_total[5m]) + rate(dispatcher_cache_misses_total[5m]))`. Type: stat/gauge.
3. **Qdrant cache lookup latency (p50/p95/p99)** — `histogram_quantile(0.95, rate(cache_lookup_duration_seconds_bucket{cache_type="qdrant"}[5m]))`. Type: time series.
4. **Dispatcher cache lookup latency (p99)** — `histogram_quantile(0.99, rate(cache_lookup_duration_seconds_bucket{cache_type="dispatcher"}[5m]))`. Expected to be near zero; useful as a sanity check.

## Trade-Offs

- **Latency measurement location**: Qdrant probe latency is measured in `LLM._probe_semantic_cache` (the caller), not inside `QdrantCacheActor`. This means it includes Ray RPC serialization overhead, not just query time inside Qdrant. This is actually more useful — it's the latency as experienced by the LLM, which is what matters for performance tuning. The downside is it can't be measured if the cache is called from somewhere other than `LLM`.
- **Dispatcher latency measurement location**: Measured inside `GlobalDispatcherCacheActor.check_cache`. This is pure Python dict access time, unaffected by Ray RPC, and is therefore more accurate as a pure cache measurement. Asymmetry with the Qdrant measurement is intentional and explicitly called out above.
- **Moving miss reporting into `_probe_semantic_cache`**: Simplifies the flow (one call site for both hits and misses), but requires removing the call from `_record_cache_miss`. This is a behavioral change and must be verified: `_record_cache_miss` is only reached when `_should_probe_cache` returned `True` (same condition as `_probe_semantic_cache`), so the same population of calls is covered. The removal is safe.
- **`prompt_name="dispatcher"` as a fixed label**: Loses per-intention granularity for dispatcher cache latency. This is intentional — the dispatcher cache lookup is O(1) dict access with no variable cost per intention, so the granularity would be noise.

## Rejected Approaches

- **Add `prometheus_client` counters directly inside `QdrantCacheActor`**: Rejected because `prometheus_client` is not safe across Ray processes. Each actor process would have its own in-process registry, which would not be scraped by the Prometheus HTTP server started in `PrometheusActor`. All metric emission must go through `PrometheusActor`.
- **Record Qdrant latency inside `QdrantCacheActor.query_and_maybe_serve`**: Rejected because (a) it would require wiring `metrics_actor` into the actor and making a fire-and-forget remote call on every query (adding a remote call to every cache probe), and (b) it measures Qdrant internal time rather than the wall-clock latency experienced by the LLM caller. The current location in `LLM._probe_semantic_cache` is more accurate for capacity planning.
- **Add a separate `QdrantLatencyTracker` class**: Rejected as over-engineering. The existing `MetricsTracker` is the right place; adding one `Histogram` and one method there follows the established pattern.
- **Use OpenTelemetry spans instead of Prometheus histograms**: Rejected. The stack already uses Prometheus histograms for block performance (`performance_block_execution_duration_seconds`). Consistency with the existing pattern outweighs any benefit of richer OTLP tracing for this use case.
- **Add `agent_id` label to cache latency histogram**: Rejected due to cardinality. With 1000+ agents, `agent_id` as a Prometheus label would create thousands of time series per metric, causing Prometheus memory exhaustion. `BlockPerformance` makes this same trade-off.

## Assumptions & Open Questions

- **Assumption**: The `probe_latency` variable at `llm.py:274` is not used anywhere else in `_probe_semantic_cache` after the debug log. Verified: the return statement at line 287 does not reference it. The change is safe.
- **Assumption**: `_record_cache_miss` is only reached when `_should_probe_cache` was True (i.e., only when a cache probe was attempted). Verified: `_record_cache_miss` is called at `llm.py:574` only inside the `if context is not None:` branch following a successful live LLM call, and only when `_should_probe_cache` / `_is_context_cache_eligible` conditions hold (checked inside `_record_cache_miss` at line 396). Moving miss reporting to `_probe_semantic_cache` covers the same condition.
- **Open question**: Should the `cache_lookup_duration_seconds` histogram bucket boundaries be tuned? The default `prometheus_client` Histogram buckets span 0.005s to 10s. Qdrant probes typically take 10–200ms based on the debug log format at `llm.py:276`. Explicit bucket boundaries like `[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]` would give better p50/p95 resolution. This is a minor config detail left to the implementer.
- **Open question**: The existing `cache_hits_total` / `cache_misses_total` metrics are keyed by `prompt_name`, which is `prompt_identity[0]`. If the same prompt is routed to a fine-tuned model via `RoutingLLM`, will hits and misses be correctly attributed? Yes: `RoutingLLM` delegates to inner `LLM` instances which share the same `_metrics_actor`. No change needed.

## Code That Could Be Refactored *(informational)*

- `agentsociety/llm/llm.py:280–286` — hit reporting currently lives inside the `if cache_hit_probe` branch in `_probe_semantic_cache`, while miss reporting lives in `_record_cache_miss`. These are logically the same event (a cache query completed). Step 3 of this plan consolidates them, which would be a side-effect improvement.
- `agentsociety/llm/cache/ray_actor.py:77–80` — `_hit_counts` and `_miss_counts` are maintained as Python dicts internally and written to JSON on `close()`. They are never forwarded to Prometheus. After this feature, the internal dicts are redundant with Prometheus counters for Qdrant. They are still useful for the end-of-run JSON stats file, so they should be kept — but a comment should note the duplication.
- `agentsociety/performance/BlockPerformance.py:49` — `print("Recording block performance:", data_to_add)` is commented out but still present. Not related to this feature but should be cleaned up.

## Proposed Next Steps

1. **Step 1**: Add `cache_lookup_duration_seconds` Histogram and `record_cache_latency()` to `agentsociety/performance/MetricsTracker.py`.
2. **Step 2**: Add `record_cache_latency()` method to `agentsociety/performance/prometheusActor.py`.
3. **Step 3**: In `agentsociety/llm/llm.py`, consolidate hit/miss reporting into `_probe_semantic_cache` and emit latency there; remove the duplicate `record_cache_stats(hit=False)` call from `_record_cache_miss`.
4. **Step 4**: Add `import time` and latency measurement to `agentsociety/agent/dispatcher_cache_actor.py:check_cache`.
5. **Step 5** *(recommended)*: Add `metrics_actor=None` parameter to `QdrantCacheActor.__init__` and pass it from `agentsociety/simulation/infrastructuremanager.py:_init_llm_cache_actor`.
6. **Step 6**: Add Grafana panels for cache hit rate and latency quantiles (manual UI work, then export JSON to `agentsociety/performance/grafana/provisioning/dashboards/`).
7. **Verify**: Run an e2e test (e.g., `tests/e2e/006_qdrant_cache.py` via `sh tests/run_e2e_tests.sh`) with monitoring enabled and confirm new metrics appear in Prometheus at `localhost:9091`.
