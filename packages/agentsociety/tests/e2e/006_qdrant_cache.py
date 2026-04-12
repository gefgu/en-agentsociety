"""End-to-end test for the Qdrant-backed LLM semantic cache.

Tests that:
- QdrantCacheActor starts and accepts records via Ray remote.
- After 51+ near-identical records, at least one query_and_maybe_serve call
  returns a non-None result (functional cache hit).
- stats.json written by close() contains a collections entry with hits > 0.
- All collection names in stats.json contain the llm_model_name suffix,
  verifying model-scoped collection naming (Step 14).

Does NOT exercise the live LLM or skip_mode; those require a full simulation
run and are verified by the success-criteria checklist in the plan.
"""

import json
import os
import sys
import tempfile

# Must be set before importing ray.
os.environ["RAY_ENABLE_UV_RUN_RUNTIME_ENV"] = "0"
os.environ["RAY_RUNTIME_ENV_IGNORE_GITIGNORE"] = "1"

import ray


def _run_test(tmpdir: str) -> None:
    """Execute all three phases of the cache e2e test.

    :param tmpdir: Writable temporary directory for Qdrant on-disk storage.
    :raises AssertionError: If any assertion fails.
    """
    from agentsociety.llm.cache import QdrantCacheActor

    MODEL_NAME = "gpt-4o"
    PROMPT_IDENTITY = ("needs_evaluation", "citysim", "1.0")
    INPUT_SCHEMA = {"activity": {"type": "text"}}
    OUTPUT_SCHEMA = {"hunger_satisfaction": {"type": "float"}}

    # Use low thresholds so 51 records are enough to trigger a rebuild and hit.
    N_NEIGHBORS = 50
    BATCH_SIZE = 50

    actor = QdrantCacheActor.remote(
        qdrant_path=tmpdir,
        embedding_model="BAAI/bge-small-en-v1.5",
        embedding_cache_dir=os.path.join(tmpdir, "fastembed_cache"),
        probability_threshold=0.7,
        batch_size=BATCH_SIZE,
        n_neighbors=N_NEIGHBORS,
        distance_quantile=0.95,
        llm_model_name=MODEL_NAME,
    )

    # Phase 1: Warm the cache with 51 near-identical records.
    activity_variants = [
        "eating lunch at home",
        "having lunch at home",
        "lunch at home again",
        "eating at home for lunch",
        "home lunch",
        "having a meal at home",
        "eating a meal at home",
        "lunch meal at home",
        "midday meal at home",
        "home midday lunch",
    ]
    # Cycle through variants to produce 51 slightly-varied records.
    for i in range(51):
        activity = activity_variants[i % len(activity_variants)]
        ray.get(
            actor.record.remote(
                PROMPT_IDENTITY,
                {"activity": activity},
                INPUT_SCHEMA,
                "0.8",
                OUTPUT_SCHEMA,
            )
        )

    stats_after_warm = ray.get(actor.get_stats.remote())
    # Determine expected collection name: name__origin__version__model
    expected_collection = f"needs_evaluation__citysim__1_0__{MODEL_NAME}"
    assert expected_collection in stats_after_warm, (
        f"Expected collection '{expected_collection}' not found in stats. "
        f"Got: {list(stats_after_warm.keys())}"
    )
    total_records = stats_after_warm[expected_collection]["total"]
    # total counts misses from query calls; here we only recorded — check via
    # the cache object indirectly: if rebuild happened, rebuild_count > 0.
    rebuild_count = stats_after_warm[expected_collection]["rebuild_count"]
    assert rebuild_count >= 1, (
        f"Expected at least one model rebuild after {51} records "
        f"with batch_size={BATCH_SIZE}, got rebuild_count={rebuild_count}. "
        f"Full stats entry: {stats_after_warm[expected_collection]}"
    )
    print(f"Phase 1 OK: rebuild_count={rebuild_count}, collection={expected_collection}")

    # Phase 2: Assert functional cache hit.
    result = ray.get(
        actor.query_and_maybe_serve.remote(
            PROMPT_IDENTITY,
            {"activity": "eating lunch"},
            INPUT_SCHEMA,
            OUTPUT_SCHEMA,
        )
    )
    assert result is not None, (
        "Expected a cache hit (non-None result) after warming with 51 records, "
        "but got None. The cache may not have rebuilt its KNN model. "
        f"Stats: {stats_after_warm}"
    )
    # Result should be a dict with a float value in [0.0, 1.0].
    assert isinstance(result, dict), f"Expected dict result, got {type(result)}: {result}"
    value = result.get("hunger_satisfaction")
    assert value is not None, f"'hunger_satisfaction' key missing from result: {result}"
    float_value = float(value)
    assert 0.0 <= float_value <= 1.0, (
        f"hunger_satisfaction={float_value} is outside [0.0, 1.0]. Result: {result}"
    )
    print(f"Phase 2 OK: cache hit returned {result}")

    # Phase 3: Stats integrity — close and check stats.json.
    ray.get(actor.close.remote())
    stats_path = os.path.join(tmpdir, "stats.json")
    assert os.path.exists(stats_path), f"stats.json not written to {stats_path}"

    with open(stats_path, encoding="utf-8") as f:
        stats_json = json.load(f)

    assert "collections" in stats_json, f"'collections' key missing from stats.json: {stats_json}"
    collections = stats_json["collections"]
    assert len(collections) >= 1, f"stats.json contains no collections: {stats_json}"

    # Verify all collection names contain the model name (Step 14 contract).
    for col_name in collections:
        assert MODEL_NAME in col_name, (
            f"Collection name '{col_name}' does not contain model name '{MODEL_NAME}'. "
            "Model-scoped naming (Step 14) is not working correctly."
        )

    # Verify at least one hit was recorded.
    total_hits = sum(entry.get("hits", 0) for entry in collections.values())
    assert total_hits > 0, (
        f"Expected hits > 0 in stats.json after a successful Phase 2 hit. "
        f"stats.json collections: {collections}"
    )
    print(f"Phase 3 OK: stats.json has {total_hits} hit(s) across {len(collections)} collection(s)")


def main() -> None:
    """Entry point: init Ray, run the test, shut down Ray."""
    ray.init()
    try:
        with tempfile.TemporaryDirectory(prefix="agentsociety_qdrant_test_") as tmpdir:
            print(f"Using Qdrant temp dir: {tmpdir}")
            _run_test(tmpdir)
            print("All assertions passed.")
    finally:
        ray.shutdown()


if __name__ == "__main__":
    main()
    sys.exit(0)
