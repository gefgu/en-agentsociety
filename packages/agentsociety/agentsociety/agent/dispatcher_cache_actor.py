import json
import logging
import os
import time
from typing import Optional

import ray

logger = logging.getLogger(__name__)


def load_dispatcher_cache(path: str) -> dict[tuple[tuple[str, ...], str], dict]:
    """Load dispatcher cache from a JSON file. Returns empty dict if file is missing."""
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        records = json.load(f)
    return {
        (tuple(r["blocks"]), r["intention"]): r["value"]
        for r in records
    }


def store_dispatcher_cache(
    cache: dict[tuple[tuple[str, ...], str], dict], path: str
) -> None:
    """Persist dispatcher cache to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    records = [
        {"blocks": list(key[0]), "intention": key[1], "value": value}
        for key, value in cache.items()
    ]
    with open(path, "w") as f:
        json.dump(records, f)


@ray.remote
class GlobalDispatcherCacheActor:
    """Global cache shared across agents for dispatcher block selection."""

    def __init__(
        self,
        min_sample_size: int = 1000,
        agreement_threshold: float = 0.999,
        data_dir: Optional[str] = None,
        llm_model_name: Optional[str] = None,
        metrics_actor=None,
    ):
        self.cache: dict[tuple[tuple[str, ...], str], dict] = {}
        self.min_sample_size = min_sample_size
        self.agreement_threshold = agreement_threshold
        self._metrics_actor = metrics_actor
        if data_dir:
            safe_name = (llm_model_name or "unknown").replace("/", "_").replace(":", "_")
            self._json_path = os.path.join(data_dir, f"dispatcher_cache_{safe_name}.json")
        else:
            self._json_path = None
        if self._json_path:
            try:
                self.cache = load_dispatcher_cache(self._json_path)
                if self.cache:
                    logger.info(
                        "Dispatcher cache reloaded from %s (%d entries)",
                        self._json_path,
                        len(self.cache),
                    )
            except Exception as e:
                logger.warning("Failed to reload dispatcher cache from %s: %s", self._json_path, e)
                self.cache = {}

    def _build_key(self, possible_blocks: list[str], ctx_intention: str) -> tuple[tuple[str, ...], str]:
        return (tuple(sorted(possible_blocks)), ctx_intention)

    def check_cache(self, possible_blocks: list[str], ctx_intention: str) -> Optional[str]:
        t_start = time.perf_counter()
        key = self._build_key(possible_blocks, ctx_intention)
        result = None
        hit = False
        if key in self.cache:
            value = self.cache[key]
            if (value["count"] >= self.min_sample_size) and (
                value["agreement_rate"] >= self.agreement_threshold
            ):
                value["cache_hit_count"] += 1
                hit = True
                result = value["most_common_block"]
        duration = time.perf_counter() - t_start
        if self._metrics_actor is not None:
            self._metrics_actor.record_dispatcher_cache_stats.remote(hit)
            self._metrics_actor.record_cache_latency.remote(
                cache_type="dispatcher",
                prompt_name="dispatcher",
                duration=duration,
            )
        return result

    def update_cache(
        self, possible_blocks: list[str], ctx_intention: str, target_block: str
    ) -> None:
        key = self._build_key(possible_blocks, ctx_intention)

        if key not in self.cache:
            self.cache[key] = {
                "block_counts": {},
                "most_common_block": None,
                "agreement_rate": 0.0,
                "count": 0,
                "cache_hit_count": 0,
            }

        value = self.cache[key]
        value["count"] += 1
        value["block_counts"][target_block] = (
            value["block_counts"].get(target_block, 0) + 1
        )

        most_common_block, most_common_count = max(
            value["block_counts"].items(), key=lambda x: x[1]
        )
        value["most_common_block"] = most_common_block
        value["agreement_rate"] = most_common_count / value["count"]

    def close(self) -> None:
        if self._json_path:
            try:
                store_dispatcher_cache(self.cache, self._json_path)
                logger.info(
                    "Dispatcher cache saved to %s (%d entries)",
                    self._json_path,
                    len(self.cache),
                )
            except Exception as e:
                logger.warning("Failed to save dispatcher cache to %s: %s", self._json_path, e)
        self.cache.clear()
