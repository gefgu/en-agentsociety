from typing import Literal
from ..logger import get_logger
import ray
import time
from collections import defaultdict
from prometheus_client import Counter, Histogram, Gauge, start_http_server


class RoutingTrackerActor:
    def __init__(self, exp_id: str):
        self.exp_id = exp_id
        self.blocks_data = []  # Register blocks here if necessary

        self.calls = Counter(
            "llm_routing_calls_total",
            "Number of routing calls to LLMs",
            ["exp_id", "block_name", "func_name", "routed", "agent_id"],
        )

    def record_performance(
        self,
        block_name: str,
        func_name: str,
        agent_id: str,
        routed: bool,
    ) -> None:
        timestamp = time.time()
        data_to_add = {
            "block_name": block_name,
            "func_name": func_name,
            "timestamp": timestamp,
            "routed": routed,
        }
        # print("Recording block performance:", data_to_add)
        self.blocks_data.append(data_to_add)

        self.calls.labels(
            exp_id=self.exp_id,
            block_name=block_name,
            func_name=func_name,
            agent_id=agent_id,
            routed=str(routed),
        ).inc(1)

    def get_stats(self):
        stats = defaultdict(
            lambda: {
                "calls": 0,
                "routed": 0,
            }
        )
        for record in self.blocks_data:
            key = (record["block_name"], record["func_name"])
            stats[key]["calls"] += 1
            stats[key]["routed"] += record["routed"]

        # Convert to a more readable format
        formatted_stats = {}
        for (block_name, func_name), data in stats.items():
            formatted_stats[f"{block_name}.{func_name}"] = {
                "calls": data["calls"],
                "routing_ratio": data["routed"] / data["calls"],
            }
        return formatted_stats
