import ray
import time
from collections import defaultdict


@ray.remote
class BlockPerformanceActor:
    def __init__(self):
        self.blocks_data = []  # Register blocks here if necessary

    def record_performance(
        self,
        block_name: str,
        func_name: str,
        duration: float,
        token_input: int,
        token_output: int,
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
