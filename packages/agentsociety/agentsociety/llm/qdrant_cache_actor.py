import json
import os
import re
import time
import uuid
from collections import defaultdict
from typing import Any, Optional

import numpy as np
import ray
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models

from ..logger import get_logger


def _sanitize_collection_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name)


class MultiFeatureQdrantChampionCache:
    """Feature-champion semantic cache backed by one Qdrant collection."""

    def __init__(
        self,
        *,
        client: QdrantClient,
        collection_name: str,
        feature_names: list[str],
        probability_threshold: float,
        batch_size: int,
        n_neighbors: int,
        distance_quantile: float,
        validation_size: float = 0.2,
        random_state: int = 42,
    ):
        if not feature_names:
            raise ValueError("feature_names must not be empty")

        self.client = client
        self.collection_name = collection_name
        self.feature_names = feature_names
        self.probability_threshold = probability_threshold
        self.batch_size = batch_size
        self.n_neighbors = n_neighbors
        self.distance_quantile = distance_quantile
        self.validation_size = validation_size
        self.random_state = random_state

        self.buffer_rows: list[dict[str, Any]] = []
        self.master_rows: list[dict[str, Any]] = []

        self.active_feature: Optional[str] = None
        self.max_neighbor_distance: Optional[float] = None
        self.last_feature_scores: dict[str, dict[str, Any]] = {}
        self.rebuild_count = 0

        self.collection_initialized = False

    def _collection_exists(self) -> bool:
        return self.client.collection_exists(self.collection_name)

    def _ensure_collection(self, feature_row: dict[str, np.ndarray]) -> None:
        if self.collection_initialized:
            return

        if self._collection_exists():
            self.collection_initialized = True
            self._load_existing_rows()
            return

        vectors_config: dict[str, models.VectorParams] = {}
        for feature in self.feature_names:
            vec = np.asarray(feature_row[feature], dtype=float).reshape(-1)
            vectors_config[feature] = models.VectorParams(
                size=int(vec.shape[0]),
                distance=models.Distance.COSINE,
            )

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=vectors_config,
        )
        self.collection_initialized = True

    def _load_existing_rows(self) -> None:
        if self.master_rows:
            return

        points, offset = self.client.scroll(
            collection_name=self.collection_name,
            with_payload=True,
            with_vectors=True,
            limit=1024,
        )
        while True:
            for p in points:
                payload = p.payload or {}
                label = payload.get("label")
                vectors = p.vector or {}
                if label is None or not isinstance(vectors, dict):
                    continue

                features: dict[str, np.ndarray] = {}
                for feature in self.feature_names:
                    vec = vectors.get(feature)
                    if vec is None:
                        break
                    features[feature] = np.asarray(vec, dtype=float)
                else:
                    self.master_rows.append({"features": features, "label": str(label)})

            if offset is None:
                break
            points, offset = self.client.scroll(
                collection_name=self.collection_name,
                with_payload=True,
                with_vectors=True,
                limit=1024,
                offset=offset,
            )

        if len(self.master_rows) >= self.n_neighbors:
            self._rebuild_model()

    def model_ready(self) -> bool:
        return (
            self.collection_initialized
            and self.active_feature is not None
            and self.max_neighbor_distance is not None
            and len(self.master_rows) >= self.n_neighbors
        )

    def _labels(self) -> np.ndarray:
        return np.asarray([str(r["label"]) for r in self.master_rows], dtype=str)

    def _feature_matrix(self, feature_name: str) -> np.ndarray:
        return np.vstack(
            [np.asarray(r["features"][feature_name], dtype=float) for r in self.master_rows]
        )

    def _query_neighbors(self, feature_name: str, query_vec: np.ndarray, limit: int):
        res = self.client.query_points(
            collection_name=self.collection_name,
            using=feature_name,
            query=query_vec.reshape(-1).tolist(),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        return getattr(res, "points", [])

    def _compute_threshold_for_feature(self, feature_name: str) -> Optional[float]:
        if len(self.master_rows) < self.n_neighbors:
            return None

        furthest_distances = []
        for r in self.master_rows:
            q = np.asarray(r["features"][feature_name], dtype=float)
            pts = self._query_neighbors(feature_name, q, self.n_neighbors)
            if len(pts) < self.n_neighbors:
                continue
            furthest = float(1.0 - float(pts[-1].score))
            furthest_distances.append(furthest)

        if not furthest_distances:
            return None
        return float(np.quantile(np.asarray(furthest_distances, dtype=float), self.distance_quantile))

    def _score_feature(self, feature_name: str, X_all: np.ndarray, y_all: np.ndarray) -> dict[str, Any]:
        if len(y_all) < self.n_neighbors:
            return {
                "feature": feature_name,
                "macro_f1": 0.0,
                "accuracy": 0.0,
                "status": "insufficient_samples",
            }

        unique_labels = np.unique(y_all)
        if len(unique_labels) < 2:
            return {
                "feature": feature_name,
                "macro_f1": 1.0,
                "accuracy": 1.0,
                "status": "single_class",
            }

        rng = np.random.default_rng(self.random_state)
        idx = np.arange(len(y_all))
        rng.shuffle(idx)

        val_count = max(1, int(len(idx) * self.validation_size))
        if val_count >= len(idx):
            val_count = max(1, len(idx) // 5)

        val_idx = idx[:val_count]
        train_idx = idx[val_count:]
        if len(train_idx) == 0:
            return {
                "feature": feature_name,
                "macro_f1": 0.0,
                "accuracy": 0.0,
                "status": "insufficient_train_split",
            }

        X_train = X_all[train_idx]
        y_train = y_all[train_idx]
        X_val = X_all[val_idx]
        y_val = y_all[val_idx]

        y_pred = []
        k = max(1, min(self.n_neighbors, len(X_train)))
        X_train_norm = X_train / np.maximum(
            np.linalg.norm(X_train, axis=1, keepdims=True),
            1e-12,
        )

        for q in X_val:
            q_norm = q / max(float(np.linalg.norm(q)), 1e-12)
            sims = X_train_norm @ q_norm
            top_idx = np.argpartition(-sims, kth=k - 1)[:k]
            vote_sum: dict[str, float] = defaultdict(float)
            for i in top_idx:
                label = str(y_train[i])
                vote_sum[label] += float(max(sims[i], 1e-12))
            pred_label = max(vote_sum.items(), key=lambda kv: kv[1])[0]
            y_pred.append(pred_label)

        y_pred_arr = np.asarray(y_pred, dtype=str)

        # Macro-F1 and accuracy implemented locally to avoid extra dependencies.
        labels = np.unique(np.concatenate([y_val.astype(str), y_pred_arr]))
        f1_scores = []
        for label in labels:
            tp = np.sum((y_val == label) & (y_pred_arr == label))
            fp = np.sum((y_val != label) & (y_pred_arr == label))
            fn = np.sum((y_val == label) & (y_pred_arr != label))
            precision = tp / max(tp + fp, 1)
            recall = tp / max(tp + fn, 1)
            if precision + recall == 0:
                f1_scores.append(0.0)
            else:
                f1_scores.append(float(2 * precision * recall / (precision + recall)))

        macro_f1 = float(np.mean(f1_scores)) if f1_scores else 0.0
        accuracy = float(np.mean(y_val == y_pred_arr)) if len(y_val) else 0.0

        return {
            "feature": feature_name,
            "macro_f1": macro_f1,
            "accuracy": accuracy,
            "status": "ok",
        }

    def _flush_buffer(self) -> None:
        if not self.buffer_rows:
            return

        points = []
        for r in self.buffer_rows:
            vectors = {
                f: np.asarray(r["features"][f], dtype=float).reshape(-1).tolist()
                for f in self.feature_names
            }
            points.append(
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vectors,
                    payload={"label": str(r["label"])}
                )
            )

        self.client.upsert(collection_name=self.collection_name, points=points)
        self.master_rows.extend(self.buffer_rows)
        self.buffer_rows = []

    def _rebuild_model(self) -> None:
        if len(self.master_rows) < self.n_neighbors:
            return

        y_all = self._labels()
        feature_scores = []
        for feature in self.feature_names:
            X_all = self._feature_matrix(feature)
            feature_scores.append(self._score_feature(feature, X_all, y_all))

        best = sorted(
            feature_scores,
            key=lambda row: (row["macro_f1"], row["accuracy"]),
            reverse=True,
        )[0]

        best_feature = str(best["feature"])
        self.active_feature = best_feature
        self.max_neighbor_distance = self._compute_threshold_for_feature(best_feature)
        self.rebuild_count += 1
        self.last_feature_scores = {
            str(row["feature"]): {
                "macro_f1": float(row["macro_f1"]),
                "accuracy": float(row["accuracy"]),
                "status": str(row["status"]),
            }
            for row in feature_scores
        }

        get_logger().debug(
            f"Cache rebuild #{self.rebuild_count} for {self.collection_name}: "
            f"feature={self.active_feature}, max_neighbor_distance={self.max_neighbor_distance}"
        )

    def evaluate(self, feature_row: dict[str, np.ndarray]) -> dict[str, Any]:
        self._ensure_collection(feature_row)

        if not self.model_ready():
            return {"cache_hit": False, "reason": "model_not_ready"}
        if self.active_feature not in feature_row:
            return {"cache_hit": False, "reason": "missing_active_feature"}

        q = np.asarray(feature_row[self.active_feature], dtype=float)
        pts = self._query_neighbors(self.active_feature, q, self.n_neighbors)
        if len(pts) < self.n_neighbors:
            return {"cache_hit": False, "reason": "insufficient_neighbors"}

        vote_sum: dict[str, float] = defaultdict(float)
        total_vote = 0.0
        for p in pts:
            payload = p.payload or {}
            label = str(payload.get("label", ""))
            sim = float(max(float(p.score), 1e-12))
            vote_sum[label] += sim
            total_vote += sim

        if total_vote <= 1e-12:
            return {"cache_hit": False, "reason": "zero_total_vote"}

        pred_label, top_vote = max(vote_sum.items(), key=lambda kv: kv[1])
        top_proba = float(top_vote / total_vote)
        furthest_neighbor_distance = float(1.0 - float(pts[-1].score))

        cache_hit = (
            self.max_neighbor_distance is not None
            and top_proba >= self.probability_threshold
            and furthest_neighbor_distance <= self.max_neighbor_distance
        )

        return {
            "cache_hit": bool(cache_hit),
            "label": pred_label,
            "top_proba": top_proba,
            "furthest_neighbor_distance": furthest_neighbor_distance,
            "selected_feature": self.active_feature,
        }

    def record(self, feature_row: dict[str, np.ndarray], label: str) -> None:
        self._ensure_collection(feature_row)
        self.buffer_rows.append({"features": feature_row, "label": label})
        if len(self.buffer_rows) >= self.batch_size:
            self._flush_buffer()
            self._rebuild_model()


@ray.remote
class QdrantCacheActor:
    """Ray actor that serves and updates the semantic cache for LLM prompts."""

    def __init__(
        self,
        qdrant_path: str,
        embedding_model: str,
        embedding_cache_dir: str,
        probability_threshold: float,
        batch_size: int,
        n_neighbors: int,
        distance_quantile: float,
    ):
        self._qdrant_path = qdrant_path
        os.makedirs(self._qdrant_path, exist_ok=True)
        self._stats_path = os.path.join(self._qdrant_path, "stats.json")

        self._embedding = TextEmbedding(
            model_name=embedding_model,
            cache_dir=embedding_cache_dir,
            threads=max(1, os.cpu_count() or 1),
        )
        self._client = QdrantClient(path=self._qdrant_path)

        self._probability_threshold = probability_threshold
        self._batch_size = batch_size
        self._n_neighbors = n_neighbors
        self._distance_quantile = distance_quantile

        self._caches: dict[str, MultiFeatureQdrantChampionCache] = {}
        self._feature_names: dict[str, list[str]] = {}
        self._schemas: dict[str, dict[str, dict[str, Any]]] = {}
        self._hit_counts: dict[str, int] = defaultdict(int)
        self._miss_counts: dict[str, int] = defaultdict(int)

    def _collection_name(self, prompt_identity: tuple[str, str, str]) -> str:
        name, origin, version = prompt_identity
        raw = f"{name}__{origin}__{version}"
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

    def _embed_typed_fields(
        self,
        prompt_inputs: dict[str, Any],
        input_schema: dict[str, dict[str, Any]],
    ) -> dict[str, np.ndarray]:
        feature_row: dict[str, np.ndarray] = {}
        for key in sorted(prompt_inputs.keys()):
            value = prompt_inputs[key]
            field_schema = input_schema.get(key, {}) if isinstance(input_schema, dict) else {}
            declared_type = str(field_schema.get("type", "text"))
            if declared_type.lower() in {"float", "integer"}:
                feature_row[key] = self._encode_numeric_field(value, declared_type)
            else:
                text = self._normalize_by_type(value, declared_type)
                emb = next(self._embedding.embed([text]))
                feature_row[key] = np.asarray(emb, dtype=float)
        return feature_row

    def _is_cache_eligible(self, output_schema: dict[str, dict[str, Any]]) -> bool:
        if not output_schema:
            return False
        allowed = {"categorical", "float", "integer"}
        return all(str(field.get("type", "")).lower() in allowed for field in output_schema.values())

    def _extract_label(self, llm_response: Any, output_schema: dict[str, dict[str, Any]]) -> Optional[str]:
        if not output_schema:
            return None

        parsed: Any = llm_response
        output_names = list(output_schema.keys())
        if isinstance(parsed, str):
            # Plain-text prompts (no JSON response_format) should still be recorded as dataset labels.
            if len(output_names) == 1:
                only_key = output_names[0]
                only_type = str(output_schema[only_key].get("type", "")).lower()
                if only_type == "text":
                    return parsed
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
        )
        self._caches[collection_name] = cache
        self._feature_names[collection_name] = feature_names
        return cache

    def query_and_maybe_serve(
        self,
        prompt_identity: tuple[str, str, str],
        prompt_inputs: dict[str, Any],
        input_schema: dict[str, dict[str, Any]],
        output_schema: dict[str, dict[str, Any]],
    ) -> Optional[Any]:
        collection_name = self._collection_name(prompt_identity)
        self._schemas[collection_name] = output_schema or {}

        if not prompt_inputs:
            self._miss_counts[collection_name] += 1
            return None

        feature_row = self._embed_typed_fields(prompt_inputs, input_schema)
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
        return decoded

    def record(
        self,
        prompt_identity: tuple[str, str, str],
        prompt_inputs: dict[str, Any],
        input_schema: dict[str, dict[str, Any]],
        llm_response: Any,
        output_schema: Optional[dict[str, dict[str, Any]]] = None,
    ) -> None:
        collection_name = self._collection_name(prompt_identity)
        schema = output_schema or self._schemas.get(collection_name, {})
        if not prompt_inputs or not schema:
            return

        label = self._extract_label(llm_response, schema)
        if label is None:
            return

        feature_row = self._embed_typed_fields(prompt_inputs, input_schema)
        cache = self._get_or_create_cache(collection_name, list(feature_row.keys()))
        cache.record(feature_row, label)

    def get_stats(self) -> dict[str, dict[str, Any]]:
        output: dict[str, dict[str, Any]] = {}
        names = set(self._hit_counts.keys()) | set(self._miss_counts.keys()) | set(self._caches.keys())
        for name in names:
            cache = self._caches.get(name)
            output[name] = {
                "hits": int(self._hit_counts.get(name, 0)),
                "misses": int(self._miss_counts.get(name, 0)),
                "total": int(self._hit_counts.get(name, 0) + self._miss_counts.get(name, 0)),
                "rebuild_count": int(cache.rebuild_count) if cache is not None else 0,
                "active_feature": cache.active_feature if cache is not None else None,
                "max_neighbor_distance": cache.max_neighbor_distance if cache is not None else None,
            }
        return output

    def close(self) -> None:
        # Flush pending buffers and persist stats.
        for cache in self._caches.values():
            cache._flush_buffer()
            cache._rebuild_model()

        stats = {
            "timestamp": time.time(),
            "collections": self.get_stats(),
        }
        with open(self._stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=True, indent=2)

        self._client.close()
        get_logger().info(f"Qdrant cache stats written to {self._stats_path}")
