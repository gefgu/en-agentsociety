from __future__ import annotations

from collections.abc import Callable
from typing import Any, Optional

import numpy as np


def accuracy_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Compute exact-match accuracy score."""
        y_true_str = y_true.astype(str)
        y_pred_str = y_pred.astype(str)
        return float(np.mean(y_true_str == y_pred_str)) if len(y_true_str) else 0.0

def macro_f1_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Compute macro-averaged F1 score across all present labels."""
        y_true_str = y_true.astype(str)
        y_pred_str = y_pred.astype(str)
        labels = np.unique(np.concatenate([y_true_str, y_pred_str]))

        f1_scores: list[float] = []
        for label in labels:
            tp = np.sum((y_true_str == label) & (y_pred_str == label))
            fp = np.sum((y_true_str != label) & (y_pred_str == label))
            fn = np.sum((y_true_str == label) & (y_pred_str != label))
            precision = tp / max(tp + fp, 1)
            recall = tp / max(tp + fn, 1)
            if precision + recall == 0:
                f1_scores.append(0.0)
            else:
                f1_scores.append(float(2 * precision * recall / (precision + recall)))

        return float(np.mean(f1_scores)) if f1_scores else 0.0



class QdrantCacheChampionship:
    """Feature championship model used by the Qdrant cache.

    This class is responsible for selecting the best-performing feature and
    tracking rebuild metadata. It does not perform storage or nearest-neighbor
    querying directly.
    """

    def __init__(
        self,
        *,
        feature_names: list[str],
        n_neighbors: int,
        validation_size: float,
        random_state: int,
    ) -> None:
        self.feature_names = feature_names
        self.n_neighbors = n_neighbors
        self.validation_size = validation_size
        self.random_state = random_state

        self.active_feature: Optional[str] = None
        self.max_neighbor_distance: Optional[float] = None
        self.last_feature_scores: dict[str, dict[str, Any]] = {}
        self.rebuild_count = 0

    def _predict_labels(
        self,
        X_train_norm: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        k: int,
    ) -> np.ndarray:
        if len(X_val) == 0:
            return np.asarray([], dtype=str)

        k_eff = max(1, min(k, X_train_norm.shape[0]))

        X_val_norm = X_val / np.maximum(
            np.linalg.norm(X_val, axis=1, keepdims=True),
            1e-12,
        )
        # Cosine-KNN in batch: S = X_val_norm @ X_train_norm^T, then weighted vote
        # p(c|x_i) ∝ sum_{j in TopK(i), y_j=c} max(S_ij, eps) and argmax_c picks label.
        sim_matrix = X_val_norm @ X_train_norm.T

        top_idx = np.argpartition(-sim_matrix, kth=k_eff - 1, axis=1)[:, :k_eff]
        top_sims = np.maximum(np.take_along_axis(sim_matrix, top_idx, axis=1), 1e-12)

        y_train_str = y_train.astype(str)
        labels, label_codes = np.unique(y_train_str, return_inverse=True)
        top_label_codes = label_codes[top_idx]

        n_val = top_idx.shape[0]
        vote_totals = np.zeros((n_val, len(labels)), dtype=float)
        row_idx = np.repeat(np.arange(n_val), k_eff)
        col_idx = top_label_codes.reshape(-1)
        weights = top_sims.reshape(-1)
        np.add.at(vote_totals, (row_idx, col_idx), weights)

        pred_codes = np.argmax(vote_totals, axis=1)
        return labels[pred_codes].astype(str)

    def score_feature(
        self,
        *,
        feature_name: str,
        X_all: np.ndarray,
        y_all: np.ndarray,
    ) -> dict[str, Any]:
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

        k = max(1, min(self.n_neighbors, len(X_train)))
        X_train_norm = X_train / np.maximum(
            np.linalg.norm(X_train, axis=1, keepdims=True),
            1e-12,
        )
        y_pred_arr = self._predict_labels(X_train_norm, y_train, X_val, k)

        macro_f1 = macro_f1_score(y_val, y_pred_arr)
        accuracy = accuracy_score(y_val, y_pred_arr)

        return {
            "feature": feature_name,
            "macro_f1": macro_f1,
            "accuracy": accuracy,
            "status": "ok",
        }

    def rebuild(
        self,
        *,
        labels: np.ndarray,
        feature_matrix_provider: Callable[[str], np.ndarray],
        threshold_provider: Callable[[str], Optional[float]],
    ) -> None:
        feature_scores = []
        for feature in self.feature_names:
            X_all = feature_matrix_provider(feature)
            feature_scores.append(
                self.score_feature(
                    feature_name=feature,
                    X_all=X_all,
                    y_all=labels,
                )
            )

        best = sorted(
            feature_scores,
            key=lambda row: (row["macro_f1"], row["accuracy"]),
            reverse=True,
        )[0]

        best_feature = str(best["feature"])
        self.active_feature = best_feature
        self.max_neighbor_distance = threshold_provider(best_feature)
        self.rebuild_count += 1
        self.last_feature_scores = {
            str(row["feature"]): {
                "macro_f1": float(row["macro_f1"]),
                "accuracy": float(row["accuracy"]),
                "status": str(row["status"]),
            }
            for row in feature_scores
        }
