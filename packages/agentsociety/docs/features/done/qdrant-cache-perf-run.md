# Run tracking: qdrant-cache-perf

Plan: `/mnt/raid5/gustavo/citysim/packages/agentsociety/docs/features/qdrant-cache-perf.md`
Test command: none (no automated test suite; correctness validated by code review)

## Steps

- [x] Step 1 — Extend `QdrantCacheConfig` with `embed_batch_timeout_ms` and `embed_max_batch_size`
- [x] Step 2 — Create `EmbedActor` in `agentsociety/llm/cache/embed_actor.py`
- [x] Step 3 — Refactor `QdrantCacheActor` to accept `embed_actor`, make methods async, delegate embedding
- [x] Step 4 — Wire `EmbedActor` construction and teardown in `InfrastructureManager`
- [x] Step 5 — Audit Fix B: wrap `_drain_one_rebuild` and close-path flush/rebuild in `asyncio.to_thread`; add `asyncio.Lock`
- [x] Step 6 — Audit Fix C: cap tournament data fetch and add random offset to `_get_tournament_data`
- [x] Step 7 — Audit Fix D: add `min_rebuild_threshold` to `QdrantCacheConfig` and `MultiFeatureQdrantChampionCache`
- [x] Step 8 — Add `embed_batch_size` histogram to `MetricsTracker` and expose via `PrometheusActor`
- [x] Step 9 — Update `__init__.py` re-exports for `EmbedActor`
