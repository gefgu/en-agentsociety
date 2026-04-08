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


