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
    skip_mode: bool = Field(default=False)
    embed_batch_timeout_ms: int = Field(
        default=25,
        ge=1,
        le=500,
        description=(
            "Maximum milliseconds EmbedActor waits before firing an incomplete "
            "batch. At high concurrency the batch fills before this timeout fires, "
            "so the practical penalty is < 1 ms. In low-concurrency scenarios the "
            "worst-case added latency equals this value."
        ),
    )
    embed_max_batch_size: int = Field(
        default=256,
        ge=1,
        description=(
            "Maximum number of texts coalesced into a single fastembed ONNX "
            "inference call inside EmbedActor. Larger values improve GPU/CPU "
            "utilisation at the cost of memory."
        ),
    )
    min_rebuild_threshold: int = Field(
        default=1000,
        ge=1,
        description=(
            "Minimum number of buffered miss records that triggers a KNN model "
            "rebuild even when `batch_size` has not been reached. Useful for small "
            "simulations where the buffer rarely fills to `batch_size`. "
            "Note: the Qdrant upsert flush is still controlled by `batch_size`; "
            "this knob only affects when the championship model is rebuilt."
        ),
    )
    tournament_sample_size: int = Field(
        default=5000,
        ge=1,
        description=(
            "Maximum number of Qdrant points fetched per rebuild for the KNN "
            "tournament. Lowered from the previous hard-coded 5000 to reduce "
            "bandwidth. Repeated rebuilds use a random scroll offset so different "
            "slices of the collection are sampled over time."
        ),
    )
