from typing import Literal

from .MetricsTracker import MetricsTracker

from .BlockPerformance import BlockPerformance
from .RoutingTracker import RoutingTrackerActor
from ..logger import get_logger
import ray
from prometheus_client import start_http_server


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
        model_role: str = "base",
    ) -> None:
        self.blockPerformance.record_performance(
            block_name,
            func_name,
            duration,
            actor,
            agent_id,
            token_input,
            token_output,
            model_role=model_role,
        )

    def record_llm_tokens_by_prompt(
        self,
        prompt_name: str,
        token_input: int,
        token_output: int,
        model_role: str = "base",
    ) -> None:
        self.metricsTracker.record_llm_tokens_by_prompt(
            prompt_name, token_input, token_output, model_role
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

    def record_cache_stats(self, prompt_name: str, hit: bool) -> None:
        """Record cache hit/miss metrics for a given prompt."""
        self.metricsTracker.record_cache_stats(prompt_name, hit)

    def record_cache_hit_validation(self, prompt_name: str, right: bool) -> None:
        """Record whether a cache hit matched the live model output."""
        self.metricsTracker.record_cache_hit_validation(prompt_name, right)

    def record_dispatcher_cache_stats(self, hit: bool) -> None:
        """Record a dispatcher cache hit or miss."""
        self.metricsTracker.record_dispatcher_cache_stats(hit)

    def record_cache_latency(
        self, cache_type: str, prompt_name: str, duration: float
    ) -> None:
        """Record the wall-clock latency of a single cache lookup.

        Args:
            cache_type: ``"qdrant"`` or ``"dispatcher"``.
            prompt_name: First element of ``prompt_identity`` for Qdrant; ``"dispatcher"`` for the dispatcher cache.
            duration: Elapsed time in seconds.

        @usedBy: LLM._probe_semantic_cache, GlobalDispatcherCacheActor.check_cache
        """
        self.metricsTracker.record_cache_latency(cache_type, prompt_name, duration)

    def record_embed_batch_size(self, size: int) -> None:
        """Record the number of texts coalesced into one EmbedActor ONNX inference call.

        Args:
            size: Number of texts in the batch.

        @usedBy: EmbedActor._batch_processor (llm/cache/embed_actor.py)
        """
        self.metricsTracker.record_embed_batch_size(size)

    def get_block_performance_stats(self):
        return self.blockPerformance.get_stats()

    def get_routing_stats(self):
        return self.routingTracker.get_stats()