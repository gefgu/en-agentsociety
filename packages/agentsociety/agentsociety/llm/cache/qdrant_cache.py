import random
import uuid
from collections import defaultdict
from typing import Any, Optional

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models

from ...logger import get_logger
from .championship import QdrantCacheChampionship


class MultiFeatureQdrantChampionCache:
    """Feature-champion semantic cache backed by one Qdrant collection.

    Stores prompt input embeddings alongside their LLM output labels in a
    Qdrant collection. Periodically rebuilds a KNN championship model that
    selects the best-performing input feature for nearest-neighbour lookup.

    :param client: Open QdrantClient instance targeting the storage directory.
    :param collection_name: Name of the Qdrant collection to use or create.
    :param feature_names: Ordered list of named input feature vectors.
    :param probability_threshold: Minimum top-class probability to emit a hit.
    :param batch_size: Number of miss records to buffer before calling
        ``client.upsert`` and flushing to Qdrant. Controls I/O frequency.
    :param n_neighbors: Neighbour count for KNN voting and threshold estimation.
    :param distance_quantile: Quantile of furthest-neighbour distances used as
        the acceptance threshold during evaluation.
    :param min_rebuild_threshold: Minimum buffer size that triggers a KNN model
        rebuild. When the buffer reaches this size a rebuild is scheduled even
        if ``batch_size`` has not been reached. Useful for small simulations
        where the buffer rarely fills to ``batch_size``.
        Note: the flush to Qdrant still happens at ``batch_size``; this knob
        only controls when the championship model is rebuilt.
    :param tournament_sample_size: Maximum number of Qdrant points fetched per
        rebuild. Repeated rebuilds use a random scroll offset so different
        slices are sampled over time.
    :param validation_size: Fraction of data held out when scoring features.
    :param random_state: Seed for reproducible train/val splits.

    Called from: QdrantCacheActor._get_or_create_cache (llm/cache/ray_actor.py).
    """

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
        min_rebuild_threshold: int = 50,
        tournament_sample_size: int = 2000,
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
        self.min_rebuild_threshold = min_rebuild_threshold
        self.tournament_sample_size = tournament_sample_size
        self.validation_size = validation_size
        self.random_state = random_state

        self.buffer_rows: list[dict[str, Any]] = []
        self._bootstrap_rebuild_needed = False

        self.championship = QdrantCacheChampionship(
            feature_names=self.feature_names,
            n_neighbors=self.n_neighbors,
            validation_size=self.validation_size,
            random_state=self.random_state,
        )

        self.collection_initialized = False

    @property
    def active_feature(self) -> Optional[str]:
        return self.championship.active_feature

    @property
    def max_neighbor_distance(self) -> Optional[float]:
        return self.championship.max_neighbor_distance

    @property
    def last_feature_scores(self) -> dict[str, dict[str, Any]]:
        return self.championship.last_feature_scores

    @property
    def rebuild_count(self) -> int:
        return self.championship.rebuild_count

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
        # Startup bootstrap should avoid loading all vectors into RAM.
        if self._has_enough_points_for_model():
            self._bootstrap_rebuild_needed = True

    def consume_bootstrap_rebuild_flag(self) -> bool:
        needed = self._bootstrap_rebuild_needed
        self._bootstrap_rebuild_needed = False
        return needed

    def _has_enough_points_for_model(self) -> bool:
        points, _ = self.client.scroll(
            collection_name=self.collection_name,
            limit=self.n_neighbors,
            with_vectors=False,
            with_payload=False,
        )
        return len(points) >= self.n_neighbors

    def model_ready(self) -> bool:
        return (
            self.collection_initialized
            and self.championship.active_feature is not None
            and self.championship.max_neighbor_distance is not None
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

    def _compute_threshold_for_feature(
        self, feature_name: str, tournament_matrix: np.ndarray
    ) -> float:
        # Use the tournament_matrix we already fetched to find distances
        # Normalize
        X = tournament_matrix
        X_norm = X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-12)

        # Cosine Similarity matrix (Self-similarity)
        sims = X_norm @ X_norm.T

        # Get the n-th neighbor (index n_neighbors since index 0 is always 'self')
        k = min(self.n_neighbors + 1, sims.shape[0])
        # Partition to find top-k, take the k-th distance
        dist = 1.0 - np.partition(sims, -k, axis=1)[:, -k]

        return float(np.quantile(dist, self.distance_quantile))

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
                    payload={"label": str(r["label"])},
                )
            )

        self.client.upsert(collection_name=self.collection_name, points=points)
        self.buffer_rows = []

    def _rebuild_model(self) -> None:
        # 1. Fetch the tournament data (The 'Tournament Set')
        y_tournament, X_tournament_map = self._get_tournament_data(
            sample_size=self.tournament_sample_size
        )

        if len(y_tournament) < self.n_neighbors:
            return

        # 2. Pass a lambda to provide the matrix from our tournament set
        self.championship.rebuild(
            labels=y_tournament,
            feature_matrix_provider=lambda feat: X_tournament_map[feat],
            # We still need a threshold based on the global distribution
            threshold_provider=lambda feat: self._compute_threshold_for_feature(
                feat, tournament_matrix=X_tournament_map[feat]
            ),
        )

        get_logger().debug(
            f"Cache rebuild #{self.championship.rebuild_count} for {self.collection_name}: "
            f"feature={self.championship.active_feature}, "
            f"max_neighbor_distance={self.championship.max_neighbor_distance}"
        )

    def evaluate(self, feature_row: dict[str, np.ndarray]) -> dict[str, Any]:
        self._ensure_collection(feature_row)

        if not self.model_ready():
            return {"cache_hit": False, "reason": "model_not_ready"}
        if self.championship.active_feature not in feature_row:
            return {"cache_hit": False, "reason": "missing_active_feature"}

        active_feature = self.championship.active_feature
        assert active_feature is not None  # Guarded by model_ready above.

        q = np.asarray(feature_row[active_feature], dtype=float)
        pts = self._query_neighbors(active_feature, q, self.n_neighbors)
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
            self.championship.max_neighbor_distance is not None
            and top_proba >= self.probability_threshold
            and furthest_neighbor_distance <= self.championship.max_neighbor_distance
        )

        return {
            "cache_hit": bool(cache_hit),
            "label": pred_label,
            "top_proba": top_proba,
            "furthest_neighbor_distance": furthest_neighbor_distance,
            "selected_feature": active_feature,
        }

    def _get_tournament_data(self, sample_size: int = 2000):
        """Fetch a capped, shuffled sample of points from Qdrant for KNN scoring.

        Fetches up to ``sample_size`` points and shuffles the result so
        repeated rebuild calls see different random subsets of the fetched
        data. This avoids always scoring the same deterministic slice of the
        collection while keeping the Qdrant fetch simple and predictable.

        :param sample_size: Maximum number of points to retrieve.
        :returns: Tuple of (labels array, feature_matrix_map) where
            feature_matrix_map maps feature name to a (N, D) float array.

        Called from: MultiFeatureQdrantChampionCache._rebuild_model.
        """
        points, _ = self.client.scroll(
            collection_name=self.collection_name,
            limit=sample_size,
            with_vectors=True,
            with_payload=["label"],
        )

        # Shuffle so repeated rebuilds (which may fetch the same leading points
        # when the collection is larger than sample_size) use different random
        # subsets for the train/validation split inside the championship.
        points = list(points)
        random.shuffle(points)

        labels = []
        feature_matrices = {feat: [] for feat in self.feature_names}

        for p in points:
            labels.append(str(p.payload["label"]))
            for feat in self.feature_names:
                feature_matrices[feat].append(p.vector[feat])

        return (np.array(labels), {f: np.array(v) for f, v in feature_matrices.items()})

    def record(self, feature_row: dict[str, np.ndarray], label: str) -> bool:
        """Buffer a feature row and label; signal when a rebuild should fire.

        The Qdrant upsert flush happens at ``batch_size`` records.
        A rebuild signal is emitted at ``min_rebuild_threshold`` records even
        when ``batch_size`` has not been reached, so the championship model
        activates sooner in small simulations.

        :param feature_row: Dict of feature name to embedding/scalar vector.
        :param label: String output label for this training sample.
        :returns: True when a rebuild should be triggered, False otherwise.

        Called from: QdrantCacheActor.record (llm/cache/ray_actor.py).
        Side effect: May call client.upsert and clear buffer_rows.
        """
        self._ensure_collection(feature_row)
        self.buffer_rows.append({"features": feature_row, "label": label})
        buffer_len = len(self.buffer_rows)
        if buffer_len >= self.batch_size:
            self._flush_buffer()
            return True
        # Trigger an early rebuild once the buffer crosses min_rebuild_threshold
        # even if we haven't reached batch_size yet.
        if buffer_len >= self.min_rebuild_threshold:
            return True
        return False
