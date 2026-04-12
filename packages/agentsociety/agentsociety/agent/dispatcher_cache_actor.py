from typing import Optional

import ray


@ray.remote
class GlobalDispatcherCacheActor:
    """Global cache shared across agents for dispatcher block selection."""

    def __init__(self, min_sample_size: int = 1000, agreement_threshold: float = 0.999):
        self.cache: dict[tuple[tuple[str, ...], str], dict] = {}
        self.min_sample_size = min_sample_size
        self.agreement_threshold = agreement_threshold

    def _build_key(self, possible_blocks: list[str], ctx_intention: str) -> tuple[tuple[str, ...], str]:
        return (tuple(sorted(possible_blocks)), ctx_intention)

    def check_cache(self, possible_blocks: list[str], ctx_intention: str) -> Optional[str]:
        key = self._build_key(possible_blocks, ctx_intention)
        if key in self.cache:
            value = self.cache[key]
            if (value["count"] >= self.min_sample_size) and (
                value["agreement_rate"] >= self.agreement_threshold
            ):
                value["cache_hit_count"] += 1
                return value["most_common_block"]
        return None

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
        self.cache.clear()
