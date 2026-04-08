from typing import Optional

from pydantic import BaseModel, Field


class QdrantCacheConfig(BaseModel):
    """Configuration for the Qdrant-backed LLM semantic cache."""

    enabled: bool = Field(default=False)
    path: Optional[str] = Field(default=None)
    probability_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    batch_size: int = Field(default=1000, ge=1)
    n_neighbors: int = Field(default=50, ge=1)
    distance_quantile: float = Field(default=0.95, ge=0.0, le=1.0)
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5")
    embedding_cache_dir: Optional[str] = Field(default=None)
