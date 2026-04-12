# Qdrant LLM Cache — Run Tracking

Plan file: `docs/features/qdrant-llm-cache.md`

## Steps

- [x] Step 13: Reorganise into `llm/cache/` subpackage — split `qdrant_cache_actor.py` into `cache/qdrant_cache.py` (pure Python, `MultiFeatureQdrantChampionCache`) and `cache/ray_actor.py` (`QdrantCacheActor`), move config to `cache/config.py`, create `cache/__init__.py` with re-exports, update all import sites.
- [x] Step 14: Add LLM model name to collection name — new `llm_model_name: str` param on `QdrantCacheActor`, append to `_collection_name()`, pass from `InfrastructureManager._init_llm_cache_actor()`.
- [x] Step 11: Add `skip_mode: bool = False` to `QdrantCacheConfig`, wire into `LLM.__init__` and `_maybe_serve_probe_result()` so a cache hit skips the LLM call when `skip_mode=True`.
- [x] Test (Step 12): Create `tests/e2e/006_qdrant_cache.py` and wire into `tests/run_e2e_tests.sh`.
