import asyncio
import json
import os
import time
from collections import defaultdict
from typing import Any, Optional
import re

import numpy as np
import ray
from qdrant_client import QdrantClient

from ...logger import get_logger
from .qdrant_cache import MultiFeatureQdrantChampionCache

def _sanitize_collection_name(name: str) -> str:
    """Replace characters outside [a-zA-Z0-9_-] with underscores for Qdrant collection names."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name)


@ray.remote
class QdrantCacheActor:
    """Ray actor that serves and updates the semantic cache for LLM prompts.

    Wraps MultiFeatureQdrantChampionCache instances (one per prompt collection)
    behind a Ray remote interface so that all Ray agent actors share a single
    cache. Stores statistics to a JSON file on close().

    :param qdrant_path: Directory where Qdrant persists collection data.
    :param embed_actor: EmbedActor Ray actor handle used for all text
        embedding. QdrantCacheActor no longer holds a fastembed model.
    :param probability_threshold: Minimum top-class probability for a cache hit.
    :param batch_size: Number of records to buffer before flushing to Qdrant.
    :param n_neighbors: Neighbour count used for KNN voting and threshold calc.
    :param distance_quantile: Quantile of furthest-neighbour distances as the
        acceptance distance threshold.
    :param llm_model_name: Name of the LLM model (e.g. "gpt-4o"). Appended to
        Qdrant collection names so caches from different models never mix.
    :param min_rebuild_threshold: Minimum buffer size that triggers a model
        rebuild even when batch_size has not been reached.
    :param tournament_sample_size: Maximum Qdrant points fetched per rebuild.

    Called from: InfrastructureManager._init_llm_cache_actor
        (simulation/infrastructuremanager.py).
    """

    def __init__(
        self,
        qdrant_path: str,
        embed_actor: Any,
        probability_threshold: float,
        batch_size: int,
        n_neighbors: int,
        distance_quantile: float,
        llm_model_name: str,
        exp_id: str,
        metrics_actor=None,
        min_rebuild_threshold: int = 50,
        tournament_sample_size: int = 2000,
    ):
        self._qdrant_path = qdrant_path
        os.makedirs(self._qdrant_path, exist_ok=True)
        self._exp_id = _sanitize_collection_name(exp_id)
        self._metrics_actor = metrics_actor
        self._stats_path = os.path.join(self._qdrant_path, f"stats_{self._exp_id}.json")

        # Embedding is now delegated to EmbedActor; this actor owns only the
        # Qdrant client.
        self._embed_actor = embed_actor
        self._client = QdrantClient(path=self._qdrant_path)

        self._probability_threshold = probability_threshold
        self._batch_size = batch_size
        self._n_neighbors = n_neighbors
        self._distance_quantile = distance_quantile
        self._llm_model_name = llm_model_name
        self._min_rebuild_threshold = min_rebuild_threshold
        self._tournament_sample_size = tournament_sample_size

        self._caches: dict[str, MultiFeatureQdrantChampionCache] = {}
        self._feature_names: dict[str, list[str]] = {}
        self._schemas: dict[str, dict[str, dict[str, Any]]] = {}
        # _hit_counts and _miss_counts are maintained in parallel with Prometheus
        # counters (since the cache-metrics feature). They are used for the
        # end-of-run JSON stats file; the Prometheus counters handle real-time
        # observability. Both are intentionally kept in sync.
        self._hit_counts: dict[str, int] = defaultdict(int)
        self._miss_counts: dict[str, int] = defaultdict(int)
        self._shadow_hit_validation_counts: dict[str, int] = defaultdict(int)
        self._shadow_hit_right_counts: dict[str, int] = defaultdict(int)
        self._pending_rebuilds: set[str] = set()
        # Lock prevents concurrent _rebuild_model calls (each potentially running
        # in asyncio.to_thread) from racing on championship.active_feature.
        self._rebuild_lock: asyncio.Lock = asyncio.Lock()

    def _collection_name(self, prompt_identity: tuple[str, str, str]) -> str:
        """Build a model-scoped Qdrant collection name from prompt identity.

        Appends the LLM model name so that caches built with different models
        never share a collection. Characters outside [a-zA-Z0-9_-] are
        replaced with underscores.

        :param prompt_identity: (name, origin, version) triple from PromptManager.
        :returns: Sanitised collection name string.
        """
        name, origin, version = prompt_identity
        raw = f"{name}__{origin}__{version}__{self._llm_model_name}"
        return _sanitize_collection_name(raw)

    def _normalize_by_type(self, value: Any, declared_type: str) -> str:
        t = declared_type.lower()
        if value is None:
            return ""

        if t == "integer":
            try:
                return str(int(float(value)))
            except Exception:
                return str(value)

        if t == "float":
            try:
                return f"{float(value):.6f}"
            except Exception:
                return str(value)

        if t == "categorical":
            return str(value).strip().lower()

        return str(value)

    def _encode_numeric_field(self, value: Any, declared_type: str) -> np.ndarray:
        t = declared_type.lower()
        try:
            numeric = float(value)
        except Exception:
            numeric = 0.0

        if t == "integer":
            numeric = float(int(numeric))

        # Keep numeric fields as direct numeric features (no text embedding).
        return np.asarray([numeric], dtype=float)

    async def _embed_typed_fields_via_actor(
        self,
        prompt_inputs: dict[str, Any],
        input_schema: dict[str, dict[str, Any]],
    ) -> dict[str, np.ndarray]:
        """Build a feature row by embedding all text fields via EmbedActor.

        Numeric fields (float/integer) are encoded locally without embedding.
        All text fields for a single probe are gathered into one list and sent
        to EmbedActor in a single remote call, allowing EmbedActor to coalesce
        them with requests from other concurrent callers.

        :param prompt_inputs: Dict of field name to raw value.
        :param input_schema: Dict of field name to {type: ...} metadata.
        :returns: Dict of field name to numpy embedding/scalar vector.

        Called from: QdrantCacheActor.query_and_maybe_serve and
            QdrantCacheActor.record (llm/cache/ray_actor.py).
        """
        feature_row: dict[str, np.ndarray] = {}
        text_keys: list[str] = []
        text_values: list[str] = []

        for key in sorted(prompt_inputs.keys()):
            value = prompt_inputs[key]
            field_schema = input_schema.get(key, {}) if isinstance(input_schema, dict) else {}
            declared_type = str(field_schema.get("type", "text"))
            if declared_type.lower() in {"float", "integer"}:
                feature_row[key] = self._encode_numeric_field(value, declared_type)
            else:
                text_keys.append(key)
                text_values.append(self._normalize_by_type(value, declared_type))

        if text_keys:
            # One remote call to EmbedActor batches all text fields for this
            # probe, and EmbedActor coalesces across concurrent callers.
            raw_vecs: list[list[float]] = await self._embed_actor.embed_batch.remote(
                text_values
            )
            for key, vec in zip(text_keys, raw_vecs):
                feature_row[key] = np.asarray(vec, dtype=float)

        return feature_row

    def _is_cache_eligible(self, output_schema: dict[str, dict[str, Any]]) -> bool:
        if not output_schema:
            return False
        allowed = {"categorical", "float", "integer"}
        return all(str(field.get("type", "")).lower() in allowed for field in output_schema.values())

    def _extract_label(self, llm_response: Any, output_schema: dict[str, dict[str, Any]]) -> Optional[str]:
        if not self._is_cache_eligible(output_schema):
            return None

        parsed: Any = llm_response
        output_names = list(output_schema.keys())
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except Exception:
                return None

        if not isinstance(parsed, dict):
            return None

        if len(output_names) == 1:
            key = output_names[0]
            if key not in parsed:
                return None
            return str(parsed[key])

        merged = {}
        for key in output_names:
            if key in parsed:
                merged[key] = parsed[key]
        if not merged:
            return None
        return json.dumps(merged, sort_keys=True)

    def _decode_label_to_output(self, label: str, output_schema: dict[str, dict[str, Any]]) -> Any:
        output_names = list(output_schema.keys())
        if len(output_names) == 1:
            key = output_names[0]
            field_type = str(output_schema[key].get("type", "")).lower()
            if field_type == "integer":
                try:
                    return {key: int(float(label))}
                except Exception:
                    return {key: label}
            if field_type == "float":
                try:
                    return {key: float(label)}
                except Exception:
                    return {key: label}
            return {key: label}

        try:
            parsed = json.loads(label)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        return None

    def _get_or_create_cache(
        self,
        collection_name: str,
        feature_names: list[str],
    ) -> MultiFeatureQdrantChampionCache:
        if collection_name in self._caches:
            return self._caches[collection_name]

        cache = MultiFeatureQdrantChampionCache(
            client=self._client,
            collection_name=collection_name,
            feature_names=feature_names,
            probability_threshold=self._probability_threshold,
            batch_size=self._batch_size,
            n_neighbors=self._n_neighbors,
            distance_quantile=self._distance_quantile,
            min_rebuild_threshold=self._min_rebuild_threshold,
            tournament_sample_size=self._tournament_sample_size,
        )
        self._caches[collection_name] = cache
        self._feature_names[collection_name] = feature_names
        if cache.consume_bootstrap_rebuild_flag():
            self._pending_rebuilds.add(collection_name)
        return cache

    async def _drain_one_rebuild(self) -> None:
        """Drain at most one pending rebuild from the queue.

        Runs the KNN rebuild off the event loop via asyncio.to_thread so that
        the actor remains responsive to new probe requests while the ONNX
        tournament runs. An asyncio.Lock prevents overlapping rebuilds that
        could race on championship.active_feature.

        Called twice in query_and_maybe_serve (once at entry, once at exit on
        a hit) to eagerly process the rebuild queue. The dual-drain is correct
        because this method is idempotent when the pending set is empty.
        """
        if not self._pending_rebuilds:
            return

        collection_name = next(iter(self._pending_rebuilds))
        self._pending_rebuilds.discard(collection_name)
        cache = self._caches.get(collection_name)
        if cache is None:
            return

        async with self._rebuild_lock:
            try:
                await asyncio.to_thread(cache._rebuild_model)
            except Exception:
                get_logger().exception(
                    f"Actor-side cache rebuild failed for {collection_name}"
                )

    async def query_and_maybe_serve(
        self,
        prompt_identity: tuple[str, str, str],
        prompt_inputs: dict[str, Any],
        input_schema: dict[str, dict[str, Any]],
        output_schema: dict[str, dict[str, Any]],
    ) -> Optional[Any]:
        """Query the cache and return a cached label if confidence is high.

        :param prompt_identity: (name, origin, version) triple identifying the prompt.
        :param prompt_inputs: Dict of field name to value for input features.
        :param input_schema: Dict of field name to {type: ...} for each input.
        :param output_schema: Dict of field name to {type: ...} for each output.
        :returns: Decoded output dict on a cache hit, or None on a miss.

        Called from: LLM._probe_semantic_cache (llm/llm.py).
        """
        await self._drain_one_rebuild()
        collection_name = self._collection_name(prompt_identity)
        self._schemas[collection_name] = output_schema or {}

        if not prompt_inputs:
            self._miss_counts[collection_name] += 1
            return None

        feature_row = await self._embed_typed_fields_via_actor(prompt_inputs, input_schema)
        cache = self._get_or_create_cache(collection_name, list(feature_row.keys()))

        if not self._is_cache_eligible(output_schema):
            self._miss_counts[collection_name] += 1
            return None

        evaluation = cache.evaluate(feature_row)
        if not evaluation.get("cache_hit", False):
            self._miss_counts[collection_name] += 1
            return None

        label = str(evaluation.get("label", ""))
        decoded = self._decode_label_to_output(label, output_schema)
        if decoded is None:
            self._miss_counts[collection_name] += 1
            return None

        self._hit_counts[collection_name] += 1
        await self._drain_one_rebuild()
        return decoded

    async def record(
        self,
        prompt_identity: tuple[str, str, str],
        prompt_inputs: dict[str, Any],
        input_schema: dict[str, dict[str, Any]],
        llm_response: Any,
        output_schema: Optional[dict[str, dict[str, Any]]] = None,
    ) -> None:
        """Record a prompt+response pair for training and cache warming.

        :param prompt_identity: (name, origin, version) triple.
        :param prompt_inputs: Input feature values.
        :param input_schema: Input field type metadata.
        :param llm_response: Raw LLM response string or dict.
        :param output_schema: Output field type metadata (falls back to stored schema).

        Called from: LLM._record_cache_miss (llm/llm.py).
        Side effect: Writes to Qdrant collection once the buffer fills to batch_size.
        """
        await self._drain_one_rebuild()
        collection_name = self._collection_name(prompt_identity)
        schema = output_schema or self._schemas.get(collection_name, {})
        if not prompt_inputs or not schema or not self._is_cache_eligible(schema):
            return

        label = self._extract_label(llm_response, schema)
        if label is None:
            return

        feature_row = await self._embed_typed_fields_via_actor(prompt_inputs, input_schema)
        cache = self._get_or_create_cache(collection_name, list(feature_row.keys()))
        rebuild_needed = cache.record(feature_row, label)
        if rebuild_needed:
            self._pending_rebuilds.add(collection_name)
        await self._drain_one_rebuild()

    def record_shadow_hit_validation(
        self,
        prompt_identity: tuple[str, str, str],
        right: bool,
    ) -> None:
        """Record whether a probed cache hit matched the live LLM output.

        This is used only in shadow mode (cache is evaluated but not used to
        skip live LLM calls).

        :param prompt_identity: (name, origin, version) triple.
        :param right: True if cached output equals normalized live output.
        """
        collection_name = self._collection_name(prompt_identity)
        self._shadow_hit_validation_counts[collection_name] += 1
        if right:
            self._shadow_hit_right_counts[collection_name] += 1

    def get_stats(self) -> dict[str, dict[str, Any]]:
        """Return per-collection hit/miss counters and model state.

        :returns: Dict keyed by collection name with hits, misses, total,
            rebuild_count, active_feature, max_neighbor_distance,
            shadow_hit_right, shadow_hit_validations, shadow_hit_right_rate.

        Called from: e2e tests and monitoring code.
        """
        output: dict[str, dict[str, Any]] = {}
        names = (
            set(self._hit_counts.keys())
            | set(self._miss_counts.keys())
            | set(self._caches.keys())
            | set(self._shadow_hit_validation_counts.keys())
        )
        for name in names:
            cache = self._caches.get(name)
            shadow_hit_validations = int(self._shadow_hit_validation_counts.get(name, 0))
            shadow_hit_right = int(self._shadow_hit_right_counts.get(name, 0))
            output[name] = {
                "hits": int(self._hit_counts.get(name, 0)),
                "misses": int(self._miss_counts.get(name, 0)),
                "total": int(self._hit_counts.get(name, 0) + self._miss_counts.get(name, 0)),
                "rebuild_count": int(cache.rebuild_count) if cache is not None else 0,
                "active_feature": cache.active_feature if cache is not None else None,
                "max_neighbor_distance": cache.max_neighbor_distance if cache is not None else None,
                "shadow_hit_right": shadow_hit_right,
                "shadow_hit_validations": shadow_hit_validations,
                "shadow_hit_right_rate": (
                    float(shadow_hit_right / shadow_hit_validations)
                    if shadow_hit_validations > 0
                    else None
                ),
            }
        return output

    async def close(self) -> None:
        """Flush pending records, rebuild models, and write exp-scoped stats JSON.

        Flush and rebuild are moved to asyncio.to_thread so that the actor
        event loop is not blocked during potentially expensive Qdrant upserts
        and KNN tournament computations at shutdown.

        Side effect: Writes <qdrant_path>/stats_<exp_id>.json; closes the QdrantClient.
        Called from: InfrastructureManager.close (simulation/infrastructuremanager.py).
        """
        for cache in self._caches.values():
            await asyncio.to_thread(cache._flush_buffer)
            await asyncio.to_thread(cache._rebuild_model)

        stats = {
            "timestamp": time.time(),
            "exp_id": self._exp_id,
            "collections": self.get_stats(),
        }
        with open(self._stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=True, indent=2)

        self._client.close()
        get_logger().info(f"Qdrant cache stats written to {self._stats_path}")
