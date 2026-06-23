from prometheus_client import Counter, Histogram


class MetricsTracker:
    def __init__(self, exp_id: str):
        self.exp_id = exp_id

        self.simulation_step_duration = Histogram(
            "metrics_simulation_step_duration_seconds",
            "Duration of simulation steps in seconds",
            ["exp_id"],
        )

        self.table_records = Counter(
            "metrics_table_records_total",
            "Total number of records inserted into ClickHouse tables",
            ["exp_id", "table_name"],
        )

        self.cache_hits = Counter(
            "cache_hits_total",
            "Total number of LLM semantic cache hits",
            ["exp_id", "prompt_name"],
        )

        self.cache_misses = Counter(
            "cache_misses_total",
            "Total number of LLM semantic cache misses",
            ["exp_id", "prompt_name"],
        )

        self.cache_hit_right = Counter(
            "cache_hit_right_total",
            "Total number of cache hits validated as correct",
            ["exp_id", "prompt_name"],
        )

        self.cache_hit_wrong = Counter(
            "cache_hit_wrong_total",
            "Total number of cache hits validated as wrong",
            ["exp_id", "prompt_name"],
        )

        self.llm_tokens_by_prompt = Counter(
            "llm_tokens_by_prompt_total",
            "Token usage broken down by prompt identity and model role",
            ["exp_id", "prompt_name", "direction", "model_role"],
        )

        self.dispatcher_cache_hits = Counter(
            "dispatcher_cache_hits_total",
            "Total number of GlobalDispatcherCacheActor cache hits",
            ["exp_id"],
        )

        self.dispatcher_cache_misses = Counter(
            "dispatcher_cache_misses_total",
            "Total number of GlobalDispatcherCacheActor cache misses",
            ["exp_id"],
        )

        self.cache_lookup_duration_seconds = Histogram(
            "cache_lookup_duration_seconds",
            "Latency of cache lookup operations (query only, not write)",
            ["exp_id", "cache_type", "prompt_name"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
        )

        self.embed_batch_size = Histogram(
            "embed_batch_size",
            "Number of texts coalesced into a single EmbedActor ONNX inference call",
            ["exp_id"],
            buckets=[1, 2, 4, 8, 16, 32, 64, 128, 256],
        )

    def record_llm_tokens_by_prompt(
        self,
        prompt_name: str,
        token_input: int,
        token_output: int,
        model_role: str = "base",
    ) -> None:
        self.llm_tokens_by_prompt.labels(
            exp_id=self.exp_id,
            prompt_name=prompt_name,
            direction="input",
            model_role=model_role,
        ).inc(token_input)
        self.llm_tokens_by_prompt.labels(
            exp_id=self.exp_id,
            prompt_name=prompt_name,
            direction="output",
            model_role=model_role,
        ).inc(token_output)

    def record_simulation_step_duration(
        self,
        duration: float,
    ) -> None:
        self.simulation_step_duration.labels(
            exp_id=self.exp_id,
        ).observe(duration)

    def record_table_records(
        self,
        table_name: str,
        record_count: int,
    ) -> None:
        self.table_records.labels(
            exp_id=self.exp_id,
            table_name=table_name,
        ).inc(record_count)

    def record_cache_stats(self, prompt_name: str, hit: bool) -> None:
        if hit:
            self.cache_hits.labels(exp_id=self.exp_id, prompt_name=prompt_name).inc()
        else:
            self.cache_misses.labels(exp_id=self.exp_id, prompt_name=prompt_name).inc()

    def record_cache_hit_validation(self, prompt_name: str, right: bool) -> None:
        if right:
            self.cache_hit_right.labels(exp_id=self.exp_id, prompt_name=prompt_name).inc()
        else:
            self.cache_hit_wrong.labels(exp_id=self.exp_id, prompt_name=prompt_name).inc()

    def record_dispatcher_cache_stats(self, hit: bool) -> None:
        if hit:
            self.dispatcher_cache_hits.labels(exp_id=self.exp_id).inc()
        else:
            self.dispatcher_cache_misses.labels(exp_id=self.exp_id).inc()

    def record_embed_batch_size(self, size: int) -> None:
        """Record the number of texts in a single EmbedActor inference batch.

        Args:
            size: Number of texts that were coalesced into one ONNX call.

        @usedBy: PrometheusActor.record_embed_batch_size
        """
        self.embed_batch_size.labels(exp_id=self.exp_id).observe(size)

    def record_cache_latency(
        self, cache_type: str, prompt_name: str, duration: float
    ) -> None:
        """Record the wall-clock latency of a single cache lookup.

        Args:
            cache_type: ``"qdrant"`` or ``"dispatcher"`` — identifies which cache system.
            prompt_name: The first element of ``prompt_identity`` for Qdrant calls;
                ``"dispatcher"`` (fixed) for dispatcher cache calls.
            duration: Elapsed time in seconds measured by the caller.

        @usedBy: PrometheusActor.record_cache_latency
        """
        self.cache_lookup_duration_seconds.labels(
            exp_id=self.exp_id,
            cache_type=cache_type,
            prompt_name=prompt_name,
        ).observe(duration)
