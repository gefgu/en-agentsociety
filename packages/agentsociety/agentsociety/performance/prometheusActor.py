from typing import Literal

from .BlockPerformance import BlockPerformance
from .RoutingTracker import RoutingTrackerActor
from ..logger import get_logger
import ray
import time
from collections import defaultdict
from prometheus_client import Counter, Histogram, Gauge, start_http_server


@ray.remote
class PrometheusActor:
    def __init__(self, exp_id: str):
        self.exp_id = exp_id

        try:
            start_http_server(9091)
        except Exception as e:
            get_logger().warning(f"Failed to start Prometheus HTTP server: {e}")

        self.blockPerformance = BlockPerformance(exp_id)
        self.routingTracker = RoutingTrackerActor(exp_id)

    def record_block_performance(
        self,
        block_name: str,
        func_name: str,
        duration: float,
        actor: Literal["llm", "modernbert", "catboost"],
        agent_id: str,
        token_input: int,
        token_output: int,
    ) -> None:
        self.blockPerformance.record_performance(
            block_name,
            func_name,
            duration,
            actor,
            agent_id,
            token_input,
            token_output,
        )

    def record_routing(
        self,
        block_name: str,
        func_name: str,
        agent_id: str,
        routed: bool,
    ) -> None:
        self.routingTracker.record_performance(
            block_name,
            func_name,
            agent_id,
            routed,
        )

    def get_block_performance_stats(self):
        return self.blockPerformance.get_stats()

    def get_routing_stats(self):
        return self.routingTracker.get_stats()