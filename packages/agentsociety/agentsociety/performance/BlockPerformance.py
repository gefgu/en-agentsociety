from typing import Literal
from ..logger import get_logger
import ray
import time
from collections import defaultdict
from prometheus_client import Counter, Histogram, Gauge, start_http_server

class BlockPerformance:
    def __init__(self, exp_id: str):
        self.exp_id = exp_id
        self.blocks_data = []  # Register blocks here if necessary

        self.calls = Counter(
            "performance_block_calls_total",
            "Number of calls to blocks",
            ["exp_id", "block_name", "func_name", "agent_id", "actor", "model_role"],
        )
        self.block_duration = Histogram(
            "performance_block_execution_duration_seconds",
            "Time spent in block execution",
            ["exp_id", "block_name", "func_name", "agent_id", "actor"],
        )
        self.token_counter = Counter(
            "performance_tokens_total",
            "Number of tokens processed by LLMs",
            ["exp_id", "direction", "actor", "block_name", "func_name", "agent_id", "model_role"],
        )

    def record_performance(
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
        timestamp = time.time()
        data_to_add = {
            "block_name": block_name,
            "func_name": func_name,
            "duration": duration,
            "token_input": token_input,
            "token_output": token_output,
            "timestamp": timestamp,
        }
        # print("Recording block performance:", data_to_add)
        self.blocks_data.append(data_to_add)

        self.calls.labels(
            exp_id=self.exp_id,
            block_name=block_name,
            func_name=func_name,
            actor=actor,
            agent_id=agent_id,
            model_role=model_role,
        ).inc(1)

        self.block_duration.labels(
            exp_id=self.exp_id,
            block_name=block_name,
            func_name=func_name,
            actor=actor,
            agent_id=agent_id,
        ).observe(duration)

        self.token_counter.labels(
            exp_id=self.exp_id,
            direction="input",
            actor=actor,
            block_name=block_name,
            func_name=func_name,
            agent_id=agent_id,
            model_role=model_role,
        ).inc(token_input)
        self.token_counter.labels(
            exp_id=self.exp_id,
            direction="output",
            actor=actor,
            block_name=block_name,
            func_name=func_name,
            agent_id=agent_id,
            model_role=model_role,
        ).inc(token_output)

    def get_stats(self):
        stats = defaultdict(
            lambda: {
                "calls": 0,
                "total_duration": 0.0,
                "total_token_input": 0,
                "total_token_output": 0,
            }
        )
        for record in self.blocks_data:
            key = (record["block_name"], record["func_name"])
            stats[key]["calls"] += 1
            stats[key]["total_duration"] += record["duration"]
            stats[key]["total_token_input"] += record["token_input"]
            stats[key]["total_token_output"] += record["token_output"]

        # Convert to a more readable format
        formatted_stats = {}
        for (block_name, func_name), data in stats.items():
            formatted_stats[f"{block_name}.{func_name}"] = {
                "calls": data["calls"],
                "total_duration": data["total_duration"],
                "average_duration": data["total_duration"] / data["calls"],
                "total_token_input": data["total_token_input"],
                "total_token_output": data["total_token_output"],
            }
        return formatted_stats
