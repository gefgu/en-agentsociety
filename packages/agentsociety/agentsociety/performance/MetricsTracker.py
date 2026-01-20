from typing import Literal
from ..logger import get_logger
import ray
import time
from collections import defaultdict
from prometheus_client import Counter, Histogram, Gauge, start_http_server


class MetricsTracker:
    def __init__(self, exp_id: str):
        self.exp_id = exp_id

        self.simulation_step_duration = Histogram(
            "metrics_simulation_step_duration_seconds",
            "Duration of simulation steps in seconds",
            ["exp_id"],
        )

    def record_simulation_step_duration(
        self,
        duration: float,
    ) -> None:
        self.simulation_step_duration.labels(
            exp_id=self.exp_id,
        ).observe(duration)

