from pydantic import BaseModel
from datetime import datetime

__all__ = [
    "StorageBenchmark",
]


class StorageBenchmark(BaseModel):
    tenant_id: str
    id: str
    benchmark_name: str
    llm: str
    agent: str
    status: int
    result_info: str
    final_score: float
    config: str
    error: str
    official_validated: bool
    created_at: datetime
    updated_at: datetime