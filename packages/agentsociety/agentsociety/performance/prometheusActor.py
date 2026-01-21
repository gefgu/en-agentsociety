from typing import Literal

from .MetricsTracker import MetricsTracker

from .BlockPerformance import BlockPerformance
from .RoutingTracker import RoutingTrackerActor
from ..logger import get_logger
import ray
import time
from collections import defaultdict
from prometheus_client import Counter, Histogram, Gauge, start_http_server


@ray.remote
class PrometheusActor:
    def __init__(self, exp_id: str, port: int = 8001):
        self.exp_id = exp_id

        try:
            start_http_server(port)
        except Exception as e:
            get_logger().warning(f"Failed to start Prometheus HTTP server: {e}")

        self.blockPerformance = BlockPerformance(exp_id)
        self.routingTracker = RoutingTrackerActor(exp_id)
        self.metricsTracker = MetricsTracker(exp_id)

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


    def record_simulation_step_duration(self, duration: float) -> None:
        """Log the duration of a simulation step."""
        self.metricsTracker.record_simulation_step_duration(duration)

    def record_table_records(self, table_name: str, record_count: int) -> None:
        """Log the number of records inserted into a ClickHouse table."""
        self.metricsTracker.record_table_records(table_name, record_count)

    def get_block_performance_stats(self):
        return self.blockPerformance.get_stats()

    def get_routing_stats(self):
        return self.routingTracker.get_stats()