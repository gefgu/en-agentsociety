# Cache Metrics: Hits, Misses, and Latency — Run Tracking

Based on plan: `docs/features/cache-metrics.md`

## Steps

- [x] Step 1 — Add `cache_lookup_duration_seconds` Histogram and `record_cache_latency()` to `MetricsTracker`
- [ ] Step 2 — Expose `record_cache_latency()` on `PrometheusActor`
- [ ] Step 3 — Emit Qdrant probe latency from `LLM._probe_semantic_cache` and consolidate hit/miss reporting
- [ ] Step 4 — Add `import time` and latency measurement to `GlobalDispatcherCacheActor.check_cache`
- [ ] Step 5 — Wire `metrics_actor=None` parameter into `QdrantCacheActor.__init__` and pass from `InfrastructureManager`
