[metadata]
name = "mobility_place_analysis"
version = "1.0.0"
origin = "agentsociety"
description = "Decide whether to go home, workplace, known place, or other based on personality and life context."

[inputs]
required = [
    "plan",
    "intention",
    "place_list",
    "other_info",
    "household",
    "life_stage",
    "hobbies",
    "goals",
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
    "leisure_preference",
    "risk_tolerance"
]

[inputs.plan]
type = "text"
description = "The agent's daily plan."

[inputs.intention]
type = "text"
description = "The agent's stated mobility requirement."

[inputs.place_list]
type = "text"
description = "Allowed place types for this decision step."

[inputs.other_info]
type = "text"
description = "Additional context that can affect place choice."

[inputs.household]
type = "text"
description = "Description of the agent's household composition."

[inputs.life_stage]
type = "text"
description = "The agent's current stage of life (e.g., Young adulthood, Mid-life)."

[inputs.hobbies]
type = "text"
description = "Interests and activities the agent enjoys."

[inputs.goals]
type = "text"
description = "The agent's short-term or long-term objectives."

[inputs.openness]
type = "integer"
description = "Big Five trait: Openness (1=Low, 2=Medium, 3=High)."

[inputs.conscientiousness]
type = "integer"
description = "Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High)."

[inputs.extraversion]
type = "integer"
description = "Big Five trait: Extraversion (1=Low, 2=Medium, 3=High)."

[inputs.agreeableness]
type = "integer"
description = "Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High)."

[inputs.neuroticism]
type = "integer"
description = "Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High)."

[inputs.leisure_preference]
type = "text"
description = "Preference for free time (e.g., outdoor, indoor, social, solitary)."

[inputs.risk_tolerance]
type = "float"
description = "Tolerance for new or unfamiliar places (0.0=Risk-averse, 1.0=Risk-seeking)."

[prompt]
input = """As an intelligent analysis system, please determine the type of place the user needs to visit based on their input requirement.
User Plan: {plan}
User requirement: {intention}
Household type: {household}
Life stage: {life_stage}
Hobbies: {hobbies}
Goals: {goals}
Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
openness: {openness}, conscientiousness: {conscientiousness}, extraversion: {extraversion}, agreeableness: {agreeableness}, neuroticism: {neuroticism}.
Your behavioral preferences are:
- Leisure Preference: {leisure_preference}
- Risk Tolerance: {risk_tolerance}
Other information:
-------------------------
{other_info}
-------------------------
"""
output_guidance = """
Your output must be a single selection from {place_list} without any additional text or explanation.

Please response in json format (Do not return any other text), example:
{{
    "place_type": "home"
}}
"""

[outputs.place_type]
type = "categorical"
categories = ["home", "work", "other"]
description = "The selected primary location type."


[metadata]
name = "needs_evaluation"
version = "1.0.0"
origin = "citysim"
description = "Evaluate completed plan results and adjust need satisfaction"

[inputs]
required = [
    "current_need",
    "plan_target",
    "evaluation_results",
    "hunger_satisfaction",
    "energy_satisfaction",
    "safety_satisfaction",
    "social_satisfaction",
    "household",
    "life_stage",
    "hobbies",
    "goals",
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
    "social_frequency"
]

[inputs.current_need]
type = "text"
description = "The current need to evaluate (e.g., hunger, energy, safety, social, whatever)."

[inputs.plan_target]
type = "text"
description = "The goal the agent attempted to complete for the current need."

[inputs.evaluation_results]
type = "text"
description = "Execution outcome and observed results for the completed actions."

[inputs.hunger_satisfaction]
type = "float"
description = "Current hunger satisfaction level (0.0 to 1.0)."

[inputs.energy_satisfaction]
type = "float"
description = "Current energy satisfaction level (0.0 to 1.0)."

[inputs.safety_satisfaction]
type = "float"
description = "Current safety satisfaction level (0.0 to 1.0)."

[inputs.social_satisfaction]
type = "float"
description = "Current social satisfaction level (0.0 to 1.0)."

[inputs.household]
type = "text"
description = "Description of the agent's household composition."

[inputs.life_stage]
type = "text"
description = "The agent's current stage of life (e.g., Young adulthood, Mid-life)."

[inputs.hobbies]
type = "text"
description = "Interests and activities the agent enjoys."

[inputs.goals]
type = "text"
description = "The agent's short-term or long-term objectives."

[inputs.openness]
type = "integer"
description = "Big Five trait: Openness (1=Low, 2=Medium, 3=High)."

[inputs.conscientiousness]
type = "integer"
description = "Big Five trait: Conscientiousness (1=Low, 2=Medium, 3=High)."

[inputs.extraversion]
type = "integer"
description = "Big Five trait: Extraversion (1=Low, 2=Medium, 3=High)."

[inputs.agreeableness]
type = "integer"
description = "Big Five trait: Agreeableness (1=Low, 2=Medium, 3=High)."

[inputs.neuroticism]
type = "integer"
description = "Big Five trait: Neuroticism (1=Low, 2=Medium, 3=High)."

[inputs.social_frequency]
type = "float"
description = "Frequency of seeking social interaction (0.0=Rarely initiates social contact, 1.0=Frequently seeks social interaction)."

[prompt]
input = """You are an evaluation system for an intelligent agent. The agent has performed the following actions to satisfy the {current_need} need:

Goal: {plan_target}
Execution situation:
{evaluation_results}

Current satisfaction:
- hunger_satisfaction: {hunger_satisfaction}
- energy_satisfaction: {energy_satisfaction}
- safety_satisfaction: {safety_satisfaction}
- social_satisfaction: {social_satisfaction}

Household type: {household}
Life stage: {life_stage}
Hobbies: {hobbies}
Goals: {goals}

Big Five Personality Traits (1=Low, 2=Medium, 3=High):
- Openness: {openness}
- Conscientiousness: {conscientiousness}
- Extraversion: {extraversion}
- Agreeableness: {agreeableness}
- Neuroticism: {neuroticism}

Behavioral Preferences:
- Social Frequency: {social_frequency} (0.0=Rarely initiates social contact, 1.0=Frequently seeks social interaction)

Please evaluate and adjust the value of {current_need} satisfaction based on the execution results above.

Notes:
1. Satisfaction values range from 0-1, where:
   - 1 means the need is fully satisfied
   - 0 means the need is completely unsatisfied
   - Higher values indicate greater need satisfaction
2. Consider social_frequency when evaluating social satisfaction: higher social_frequency means social activities have greater impact.
"""
output_guidance = """
Return JSON only, without any extra text.

If current_need is not "whatever", return only the updated value for that need, for example:
{{
    "hunger_satisfaction": new_hunger_satisfaction_value
}}

If current_need is "whatever", return both safety and social satisfaction values, for example:
{{
    "safety_satisfaction": new_safety_satisfaction_value,
    "social_satisfaction": new_social_satisfaction_value
}}
"""

[outputs.hunger_satisfaction]
type = "float"
description = "Updated hunger satisfaction level (0.0 to 1.0)."

[outputs.energy_satisfaction]
type = "float"
description = "Updated energy satisfaction level (0.0 to 1.0)."

[outputs.safety_satisfaction]
type = "float"
description = "Updated safety satisfaction level (0.0 to 1.0)."

[outputs.social_satisfaction]
type = "float"
description = "Updated social satisfaction level (0.0 to 1.0)."


import time
import uuid
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from qdrant_client import QdrantClient
from qdrant_client.http import models


class MultiFeatureQdrantChampionCache:
    """
    Qdrant port of MultiFeatureEvolvingSimulationCache with hard feature championship.

    Key behavior:
    - Multiple feature spaces are tracked.
    - At each rebuild, all features are scored (macro-F1/accuracy) on history.
    - Exactly one best feature is selected as active_feature.
    - Cache inference uses only active_feature (no PCA).
    """

    def __init__(
        self,
        feature_names: list[str],
        probability_threshold: float = 0.95,
        batch_size: int = 1000,
        n_neighbors: int = 50,
        distance_quantile: float = 0.95,
        validation_size: float = 0.2,
        random_state: int = 42,
        collection_name: str = "move_analysis_feature_champion_cache",
    ):
        if not feature_names:
            raise ValueError("feature_names must not be empty.")

        self.feature_names = feature_names
        self.probability_threshold = probability_threshold
        self.batch_size = batch_size
        self.n_neighbors = n_neighbors
        self.distance_quantile = distance_quantile
        self.validation_size = validation_size
        self.random_state = random_state
        self.collection_name = collection_name

        # Pending/new rows before rebuild
        self.buffer_rows = []

        # Master history rows used for feature championship scoring
        self.master_rows = []

        # Active model state
        self.active_feature = None
        self.max_neighbor_distance = None
        self.last_feature_scores = {}
        self.rebuild_count = 0

        # Qdrant client/collection
        self.client = QdrantClient(":memory:")
        self.collection_initialized = False

        # Metrics
        self._cache_calls = 0
        self._cache_hits = 0
        self._cache_miss = 0
        self._cache_mistake = 0

        # Benchmarking
        self.benchmark_totals = {
            "feature_eval_seconds": 0.0,
            "rebuild_total_seconds": 0.0,
        }
        self.benchmark_feature_eval_seconds = {feature: 0.0 for feature in self.feature_names}
        self.benchmark_rebuild_log = []

    def _init_collection_from_row(self, feature_row: dict[str, np.ndarray]):
        if self.collection_initialized:
            return

        vectors_config = {}
        for feature in self.feature_names:
            v = np.asarray(feature_row[feature], dtype=float).reshape(-1)
            vectors_config[feature] = models.VectorParams(
                size=int(v.shape[0]),
                distance=models.Distance.COSINE,
            )

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=vectors_config,
        )
        self.collection_initialized = True

    def model_ready(self) -> bool:
        return (
            self.collection_initialized
            and self.active_feature is not None
            and self.max_neighbor_distance is not None
            and len(self.master_rows) >= self.n_neighbors
        )

    def _feature_matrix(self, feature_name: str) -> np.ndarray:
        return np.vstack([np.asarray(r["features"][feature_name], dtype=float) for r in self.master_rows])

    def _labels(self) -> np.ndarray:
        return np.asarray([str(r["label"]) for r in self.master_rows], dtype=str)

    def _score_feature_model(self, feature_name: str, X_all: np.ndarray, y_all: np.ndarray) -> dict:
        t0 = time.perf_counter()

        if len(y_all) < self.n_neighbors:
            elapsed = time.perf_counter() - t0
            return {
                "feature": feature_name,
                "macro_f1": -1.0,
                "accuracy": -1.0,
                "status": "insufficient_rows",
                "eval_seconds": elapsed,
            }

        unique_labels = np.unique(y_all)
        if len(unique_labels) < 2:
            elapsed = time.perf_counter() - t0
            return {
                "feature": feature_name,
                "macro_f1": 1.0,
                "accuracy": 1.0,
                "status": "single_class",
                "eval_seconds": elapsed,
            }

        try:
            X_train, X_val, y_train, y_val = train_test_split(
                X_all,
                y_all,
                test_size=self.validation_size,
                random_state=self.random_state,
                stratify=y_all,
            )
        except ValueError:
            X_train, X_val, y_train, y_val = train_test_split(
                X_all,
                y_all,
                test_size=self.validation_size,
                random_state=self.random_state,
                stratify=None,
            )

        k = max(1, min(self.n_neighbors, len(X_train)))
        knn = KNeighborsClassifier(n_neighbors=k, weights="distance", n_jobs=-1)
        knn.fit(X_train, y_train)
        y_pred = knn.predict(X_val)

        elapsed = time.perf_counter() - t0
        return {
            "feature": feature_name,
            "macro_f1": float(f1_score(y_val, y_pred, average="macro")),
            "accuracy": float(accuracy_score(y_val, y_pred)),
            "status": "ok",
            "eval_seconds": elapsed,
        }

    def _query_neighbors(self, feature_name: str, query_vec: np.ndarray, limit: int):
        res = self.client.query_points(
            collection_name=self.collection_name,
            using=feature_name,
            query=np.asarray(query_vec, dtype=float).reshape(-1).tolist(),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        return getattr(res, "points", [])

    def _compute_threshold_for_feature(self, feature_name: str) -> float | None:
        if len(self.master_rows) < self.n_neighbors:
            return None

        furthest_distances = []
        for r in self.master_rows:
            q = np.asarray(r["features"][feature_name], dtype=float)
            pts = self._query_neighbors(feature_name, q, self.n_neighbors)
            if len(pts) < self.n_neighbors:
                continue
            # With cosine metric in Qdrant, score is similarity; convert to distance-like value.
            furthest_d = 1.0 - float(pts[-1].score)
            furthest_distances.append(furthest_d)

        if len(furthest_distances) == 0:
            return None
        return float(np.quantile(np.asarray(furthest_distances, dtype=float), self.distance_quantile))

    def _flush_buffer(self):
        if len(self.buffer_rows) == 0:
            return

        points = []
        for r in self.buffer_rows:
            vecs = {f: np.asarray(r["features"][f], dtype=float).reshape(-1).tolist() for f in self.feature_names}
            points.append(
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vecs,
                    payload={"place_type": str(r["label"])},
                )
            )

        self.client.upsert(collection_name=self.collection_name, points=points)
        self.master_rows.extend(self.buffer_rows)
        self.buffer_rows = []

    def _rebuild_model(self):
        if len(self.master_rows) < self.n_neighbors:
            return

        rebuild_t0 = time.perf_counter()
        y_all = self._labels()
        feature_scores = []

        for feature in self.feature_names:
            X_all = self._feature_matrix(feature)
            feature_scores.append(self._score_feature_model(feature, X_all, y_all))

        score_df = pd.DataFrame(feature_scores)
        feature_eval_seconds = float(score_df["eval_seconds"].sum())
        best = score_df.sort_values(["macro_f1", "accuracy"], ascending=False).iloc[0]
        best_feature = str(best["feature"])

        best_threshold = self._compute_threshold_for_feature(best_feature)
        self.active_feature = best_feature
        self.max_neighbor_distance = best_threshold
        self.rebuild_count += 1

        self.last_feature_scores = {
            row["feature"]: {
                "macro_f1": row["macro_f1"],
                "accuracy": row["accuracy"],
                "status": row["status"],
                "eval_seconds": row["eval_seconds"],
            }
            for _, row in score_df.iterrows()
        }

        rebuild_total_seconds = float(time.perf_counter() - rebuild_t0)
        self.benchmark_totals["feature_eval_seconds"] += feature_eval_seconds
        self.benchmark_totals["rebuild_total_seconds"] += rebuild_total_seconds
        for _, row in score_df.iterrows():
            self.benchmark_feature_eval_seconds[str(row["feature"])] += float(row["eval_seconds"])

        self.benchmark_rebuild_log.append(
            {
                "rebuild_index": self.rebuild_count,
                "records": len(self.master_rows),
                "selected_feature": self.active_feature,
                "selected_macro_f1": float(best["macro_f1"]),
                "selected_accuracy": float(best["accuracy"]),
                "feature_eval_seconds": feature_eval_seconds,
                "rebuild_total_seconds": rebuild_total_seconds,
                "max_neighbor_distance": self.max_neighbor_distance,
            }
        )

        print(
            f"Rebuild #{self.rebuild_count}: "
            f"records={len(self.master_rows)} | "
            f"selected_feature={self.active_feature} | "
            f"macro_f1={float(best['macro_f1']):.4f} | "
            f"acc={float(best['accuracy']):.4f} | "
            f"total_s={rebuild_total_seconds:.3f} | "
            f"max_neighbor_distance={self.max_neighbor_distance}"
        )

    def _evaluate_cache(self, feature_row: dict[str, np.ndarray]) -> dict:
        if not self.model_ready():
            return {
                "cache_hit": False,
                "pred_label": None,
                "top_proba": None,
                "furthest_neighbor_distance": None,
                "reason": "model_not_ready",
                "selected_feature": self.active_feature,
            }

        if self.active_feature not in feature_row:
            return {
                "cache_hit": False,
                "pred_label": None,
                "top_proba": None,
                "furthest_neighbor_distance": None,
                "reason": "active_feature_missing",
                "selected_feature": self.active_feature,
            }

        q = np.asarray(feature_row[self.active_feature], dtype=float)
        pts = self._query_neighbors(self.active_feature, q, self.n_neighbors)
        if len(pts) < self.n_neighbors:
            return {
                "cache_hit": False,
                "pred_label": None,
                "top_proba": None,
                "furthest_neighbor_distance": None,
                "reason": "not_enough_neighbors",
                "selected_feature": self.active_feature,
            }

        # Distance-weighted vote from similarity scores
        vote_sum = {}
        total_vote = 0.0
        for p in pts:
            lbl = str((p.payload or {}).get("place_type", ""))
            sim = max(0.0, float(p.score))
            vote_sum[lbl] = vote_sum.get(lbl, 0.0) + sim
            total_vote += sim

        if total_vote <= 1e-12:
            return {
                "cache_hit": False,
                "pred_label": None,
                "top_proba": None,
                "furthest_neighbor_distance": None,
                "reason": "zero_similarity",
                "selected_feature": self.active_feature,
            }

        pred_label, top_vote = max(vote_sum.items(), key=lambda kv: kv[1])
        top_proba = float(top_vote / total_vote)
        furthest_neighbor_distance = float(1.0 - float(pts[-1].score))

        cache_hit = (
            top_proba >= self.probability_threshold
            and furthest_neighbor_distance <= self.max_neighbor_distance
        )

        return {
            "cache_hit": bool(cache_hit),
            "pred_label": str(pred_label),
            "top_proba": top_proba,
            "furthest_neighbor_distance": furthest_neighbor_distance,
            "reason": "passed" if cache_hit else "low_conf_or_far",
            "selected_feature": self.active_feature,
        }

    def evaluate_and_update(self, feature_row: dict[str, np.ndarray], llm_fallback_function):
        self._cache_calls += 1

        # Create collection lazily using first seen row dimensions.
        self._init_collection_from_row(feature_row)

        cache_eval = self._evaluate_cache(feature_row)
        if cache_eval["cache_hit"]:
            pred = str(cache_eval["pred_label"])
            self._cache_hits += 1
            return {**cache_eval, "output_label": pred, "source": "cache", "model_ready": True}

        # Cache miss -> fallback label
        llm_label = str(llm_fallback_function(feature_row))
        self._cache_miss += 1
        self.buffer_rows.append({"features": feature_row, "label": llm_label})

        if len(self.buffer_rows) >= self.batch_size:
            self._flush_buffer()
            self._rebuild_model()

        return {**cache_eval, "output_label": llm_label, "source": "llm", "model_ready": self.model_ready()}


def run_qdrant_feature_champion_simulation(
    df: pd.DataFrame,
    feature_names: list[str],
    label_col: str = "place_type",
    step_col: str = "simulation_step",
    probability_threshold: float = 0.95,
    batch_size: int = 1000,
    n_neighbors: int = 50,
    distance_quantile: float = 0.95,
    validation_size: float = 0.2,
    random_state: int = 42,
) -> tuple[pd.DataFrame, dict, pd.DataFrame, MultiFeatureQdrantChampionCache]:
    required_cols = [step_col, label_col] + feature_names
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    seq_df = (
        df[required_cols]
        .dropna(subset=feature_names + [label_col])
        .sort_values(step_col)
        .reset_index(drop=True)
    )

    cache = MultiFeatureQdrantChampionCache(
        feature_names=feature_names,
        probability_threshold=probability_threshold,
        batch_size=batch_size,
        n_neighbors=n_neighbors,
        distance_quantile=distance_quantile,
        validation_size=validation_size,
        random_state=random_state,
    )

    rows = []
    first_model_step = None

    sim_t0 = time.perf_counter()
    for r in tqdm(seq_df.itertuples(index=False), total=len(seq_df), desc="Running Qdrant feature-champion simulation"):
        feature_row = {f: np.asarray(getattr(r, f), dtype=float) for f in feature_names}
        y_true = str(getattr(r, label_col))
        sim_step = int(getattr(r, step_col))

        out = cache.evaluate_and_update(feature_row, llm_fallback_function=lambda _x, y=y_true: y)

        if first_model_step is None and out["model_ready"]:
            first_model_step = sim_step

        if out["source"] == "cache" and out["output_label"] != y_true:
            cache._cache_mistake += 1

        rows.append(
            {
                "simulation_step": sim_step,
                "true_label": y_true,
                "output_label": out["output_label"],
                "source": out["source"],
                "cache_hit": bool(out["source"] == "cache"),
                "cache_miss": bool(out["source"] == "llm"),
                "wrong_evaluation": bool((out["source"] == "cache") and (out["output_label"] != y_true)),
                "top_proba": out["top_proba"],
                "furthest_neighbor_distance": out["furthest_neighbor_distance"],
                "max_neighbor_distance": cache.max_neighbor_distance,
                "reason": out["reason"],
                "selected_feature": out["selected_feature"],
            }
        )

    sim_total_seconds = float(time.perf_counter() - sim_t0)
    evolving_cache_df = pd.DataFrame(rows)

    total = len(evolving_cache_df)
    cache_hits = int(evolving_cache_df["cache_hit"].sum())
    cache_misses = int(evolving_cache_df["cache_miss"].sum())
    wrong_evaluations = int(evolving_cache_df["wrong_evaluation"].sum())

    rebuild_log_df = pd.DataFrame(cache.benchmark_rebuild_log)

    summary = {
        "total_rows": total,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "wrong_evaluations": wrong_evaluations,
        "hit_rate": cache_hits / total if total else 0.0,
        "miss_rate": cache_misses / total if total else 0.0,
        "wrong_rate_overall": wrong_evaluations / total if total else 0.0,
        "wrong_rate_on_hits": wrong_evaluations / cache_hits if cache_hits else 0.0,
        "model_rebuilds": cache.rebuild_count,
        "first_model_available_step": first_model_step,
        "final_master_records": len(cache.master_rows),
        "pending_buffer_records": len(cache.buffer_rows),
        "probability_threshold": cache.probability_threshold,
        "distance_quantile": cache.distance_quantile,
        "latest_max_neighbor_distance": cache.max_neighbor_distance,
        "active_feature_at_end": cache.active_feature,
        "last_feature_scores": cache.last_feature_scores,
        "benchmark": {
            "simulation_total_seconds": sim_total_seconds,
            "feature_eval_seconds_total": cache.benchmark_totals["feature_eval_seconds"],
            "rebuild_total_seconds": cache.benchmark_totals["rebuild_total_seconds"],
            "feature_eval_seconds_by_feature": dict(cache.benchmark_feature_eval_seconds),
        },
    }

    return evolving_cache_df, summary, rebuild_log_df, cache


# --- Run the Qdrant championship port (no PCA, hard winner feature) ---
feature_names = ["intention_embedding", "plan_embedding"]

qdrant_champion_df, qdrant_champion_summary, qdrant_champion_rebuilds, qdrant_champion_cache = run_qdrant_feature_champion_simulation(
    df=parsed_df,
    feature_names=feature_names,
    label_col="place_type",
    step_col="simulation_step",
    probability_threshold=0.95,
    batch_size=1000,
    n_neighbors=50,
    distance_quantile=0.95,
    validation_size=0.2,
    random_state=42,
)

print(pd.Series(qdrant_champion_summary).drop(labels=["benchmark", "last_feature_scores"]).to_string())
print("\nBenchmark summary:")
print(pd.Series(qdrant_champion_summary["benchmark"]).to_string())

print("\nPer-rebuild timing table:")
print(qdrant_champion_rebuilds.to_string(index=False) if len(qdrant_champion_rebuilds) else "No rebuilds yet")

print("\nWrong cache-hit examples:")
wrong_examples = qdrant_champion_df[qdrant_champion_df["wrong_evaluation"]][
    ["simulation_step", "true_label", "output_label", "selected_feature", "top_proba", "furthest_neighbor_distance", "max_neighbor_distance"]
].head(10)
print(wrong_examples.to_string(index=False) if len(wrong_examples) else "None")

print("\nCache-miss examples:")
miss_examples = qdrant_champion_df[qdrant_champion_df["cache_miss"]][
    ["simulation_step", "true_label", "output_label", "reason", "selected_feature"]
].head(10)
print(miss_examples.to_string(index=False) if len(miss_examples) else "None")

print("\nFeature usage over time:")
print(qdrant_champion_df["selected_feature"].value_counts(dropna=False).to_string())

qdrant_champion_df.head()

total_rows                                    15095
cache_hits                                     8440
cache_misses                                   6655
wrong_evaluations                               184
hit_rate                                   0.559126
miss_rate                                  0.440874
wrong_rate_overall                         0.012189
wrong_rate_on_hits                         0.021801
model_rebuilds                                    6
first_model_available_step                       54
final_master_records                           6000
pending_buffer_records                          655
probability_threshold                          0.95
distance_quantile                              0.95
latest_max_neighbor_distance               0.162763
active_feature_at_end           intention_embedding

Benchmark summary:
simulation_total_seconds                                                  229.294118
feature_eval_seconds_total                                                  0.371975
rebuild_total_seconds                                                     140.663859
feature_eval_seconds_by_feature    {'intention_embedding': 0.1857003364712, 'plan...

Per-rebuild timing table:
 rebuild_index  records    selected_feature  selected_macro_f1  selected_accuracy  feature_eval_seconds  rebuild_total_seconds  max_neighbor_distance
             1     1000 intention_embedding           0.918515           0.960000              0.022923               4.022356               0.245239
             2     2000 intention_embedding           0.901579           0.932500              0.036700               8.701460               0.193252
             3     3000 intention_embedding           0.864763           0.878333              0.055286              15.449507               0.175519
             4     4000 intention_embedding           0.872740           0.875000              0.071916              25.340709               0.165248
             5     5000 intention_embedding           0.862636           0.862000              0.082570              36.756615               0.164944
             6     6000 intention_embedding           0.867791           0.865000              0.102580              50.393214               0.162763

Wrong cache-hit examples:
 simulation_step true_label output_label    selected_feature  top_proba  furthest_neighbor_distance  max_neighbor_distance
              58      other    workplace intention_embedding   0.960395                    0.109396               0.245239
              62      other    workplace intention_embedding   0.957911                    0.135764               0.245239
              64      other    workplace intention_embedding   0.977777                    0.243743               0.245239
              74      other    workplace intention_embedding   0.974612                    0.244955               0.245239
              75      other    workplace intention_embedding   0.977777                    0.243743               0.245239
              78      other    workplace intention_embedding   0.974612                    0.244955               0.245239
              78      other    workplace intention_embedding   0.957579                    0.128747               0.245239
              81       home    workplace intention_embedding   0.959787                    0.150032               0.245239
              85      other    workplace intention_embedding   0.977777                    0.243743               0.245239
              86       home    workplace intention_embedding   0.959787                    0.150032               0.245239

Cache-miss examples:
 simulation_step true_label output_label          reason selected_feature
               0       home         home model_not_ready             None
               0       home         home model_not_ready             None
               0       home         home model_not_ready             None
               0       home         home model_not_ready             None
               0       home         home model_not_ready             None
               0       home         home model_not_ready             None
               0       home         home model_not_ready             None
               0       home         home model_not_ready             None
               0       home         home model_not_ready             None
               0       home         home model_not_ready             None

Feature usage over time:
selected_feature
intention_embedding    14095
None                    1000


import time
import uuid
import numpy as np
import pandas as pd
import tomllib
from pathlib import Path
from tqdm import tqdm
from fastembed import TextEmbedding
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from qdrant_client import QdrantClient
from qdrant_client.http import models


class QdrantFeatureChampionRegressorCache:
    """
    Qdrant championship cache for single-output regression.

    - Tracks multiple feature spaces in one Qdrant collection.
    - Rebuilds every batch_size misses.
    - Selects one best feature by validation MAE at each rebuild.
    - Uses uncertainty (neighbor std) + distance gate for cache hits.
    """

    def __init__(
        self,
        feature_names: list[str],
        uncertainty_threshold: float = 10.0,
        error_threshold: float = 20.0,
        batch_size: int = 1000,
        n_neighbors: int = 50,
        distance_quantile: float = 0.95,
        validation_size: float = 0.2,
        random_state: int = 42,
        collection_name: str = "qdrant_feature_champion_regression",
    ):
        if not feature_names:
            raise ValueError("feature_names must not be empty.")

        self.feature_names = feature_names
        self.uncertainty_threshold = uncertainty_threshold
        self.error_threshold = error_threshold
        self.batch_size = batch_size
        self.n_neighbors = n_neighbors
        self.distance_quantile = distance_quantile
        self.validation_size = validation_size
        self.random_state = random_state
        self.collection_name = collection_name

        self.client = QdrantClient(":memory:")
        self.collection_initialized = False

        self.buffer_rows = []
        self.master_rows = []

        self.active_feature = None
        self.max_neighbor_distance = None
        self.last_feature_scores = {}
        self.rebuild_count = 0

    def _init_collection_from_row(self, feature_row: dict[str, np.ndarray]):
        if self.collection_initialized:
            return

        vectors_config = {}
        for feature in self.feature_names:
            v = np.asarray(feature_row[feature], dtype=float).reshape(-1)
            vectors_config[feature] = models.VectorParams(
                size=int(v.shape[0]),
                distance=models.Distance.COSINE,
            )

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=vectors_config,
        )
        self.collection_initialized = True

    def model_ready(self) -> bool:
        return (
            self.collection_initialized
            and self.active_feature is not None
            and self.max_neighbor_distance is not None
            and len(self.master_rows) >= self.n_neighbors
        )

    def _labels(self) -> np.ndarray:
        return np.asarray([float(r["label"]) for r in self.master_rows], dtype=float)

    def _feature_matrix(self, feature_name: str) -> np.ndarray:
        return np.vstack([np.asarray(r["features"][feature_name], dtype=float) for r in self.master_rows])

    def _query_neighbors(self, feature_name: str, query_vec: np.ndarray, limit: int):
        res = self.client.query_points(
            collection_name=self.collection_name,
            using=feature_name,
            query=np.asarray(query_vec, dtype=float).reshape(-1).tolist(),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        return getattr(res, "points", [])

    def _score_feature(self, feature_name: str, X_all: np.ndarray, y_all: np.ndarray) -> dict:
        if len(y_all) < max(self.n_neighbors, 20):
            return {"feature": feature_name, "mae": float("inf"), "status": "insufficient_rows"}

        X_train, X_val, y_train, y_val = train_test_split(
            X_all,
            y_all,
            test_size=self.validation_size,
            random_state=self.random_state,
        )

        k = max(1, min(self.n_neighbors, len(X_train)))
        knn = KNeighborsRegressor(n_neighbors=k, weights="distance", n_jobs=-1)
        knn.fit(X_train, y_train)
        y_pred = knn.predict(X_val)
        mae = float(mean_absolute_error(y_val, y_pred))

        return {"feature": feature_name, "mae": mae, "status": "ok"}

    def _compute_threshold_for_feature(self, feature_name: str) -> float | None:
        if len(self.master_rows) < self.n_neighbors:
            return None

        furthest_distances = []
        for r in self.master_rows:
            q = np.asarray(r["features"][feature_name], dtype=float)
            pts = self._query_neighbors(feature_name, q, self.n_neighbors)
            if len(pts) < self.n_neighbors:
                continue
            furthest_d = 1.0 - float(pts[-1].score)
            furthest_distances.append(furthest_d)

        if len(furthest_distances) == 0:
            return None
        return float(np.quantile(np.asarray(furthest_distances, dtype=float), self.distance_quantile))

    def _flush_buffer(self):
        if len(self.buffer_rows) == 0:
            return

        points = []
        for r in self.buffer_rows:
            vecs = {f: np.asarray(r["features"][f], dtype=float).reshape(-1).tolist() for f in self.feature_names}
            points.append(
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vecs,
                    payload={"target": float(r["label"])},
                )
            )

        self.client.upsert(collection_name=self.collection_name, points=points)
        self.master_rows.extend(self.buffer_rows)
        self.buffer_rows = []

    def _rebuild_model(self):
        if len(self.master_rows) < max(self.n_neighbors, 20):
            return

        y_all = self._labels()
        feature_scores = []
        for feature in self.feature_names:
            X_all = self._feature_matrix(feature)
            feature_scores.append(self._score_feature(feature, X_all, y_all))

        score_df = pd.DataFrame(feature_scores).sort_values("mae", ascending=True)
        best = score_df.iloc[0]
        best_feature = str(best["feature"])
        best_threshold = self._compute_threshold_for_feature(best_feature)

        self.active_feature = best_feature
        self.max_neighbor_distance = best_threshold
        self.rebuild_count += 1
        self.last_feature_scores = {
            row["feature"]: {"mae": float(row["mae"]), "status": row["status"]}
            for _, row in score_df.iterrows()
        }

        print(
            f"Rebuild #{self.rebuild_count}: records={len(self.master_rows)} | "
            f"selected_feature={self.active_feature} | mae={float(best['mae']):.4f} | "
            f"max_neighbor_distance={self.max_neighbor_distance}"
        )

    def _evaluate_cache(self, feature_row: dict[str, np.ndarray]) -> dict:
        if not self.model_ready():
            return {
                "cache_hit": False,
                "pred_value": None,
                "neighbor_std": None,
                "furthest_neighbor_distance": None,
                "reason": "model_not_ready",
                "selected_feature": self.active_feature,
            }

        if self.active_feature not in feature_row:
            return {
                "cache_hit": False,
                "pred_value": None,
                "neighbor_std": None,
                "furthest_neighbor_distance": None,
                "reason": "active_feature_missing",
                "selected_feature": self.active_feature,
            }

        q = np.asarray(feature_row[self.active_feature], dtype=float)
        pts = self._query_neighbors(self.active_feature, q, self.n_neighbors)
        if len(pts) < self.n_neighbors:
            return {
                "cache_hit": False,
                "pred_value": None,
                "neighbor_std": None,
                "furthest_neighbor_distance": None,
                "reason": "not_enough_neighbors",
                "selected_feature": self.active_feature,
            }

        sims = np.asarray([max(0.0, float(p.score)) for p in pts], dtype=float)
        targets = np.asarray([float((p.payload or {}).get("target", np.nan)) for p in pts], dtype=float)
        valid = np.isfinite(targets)
        sims = sims[valid]
        targets = targets[valid]

        if len(targets) == 0:
            return {
                "cache_hit": False,
                "pred_value": None,
                "neighbor_std": None,
                "furthest_neighbor_distance": None,
                "reason": "invalid_neighbors",
                "selected_feature": self.active_feature,
            }

        if float(sims.sum()) <= 1e-12:
            pred_value = float(np.mean(targets))
        else:
            pred_value = float(np.average(targets, weights=sims))

        neighbor_std = float(np.std(targets))
        furthest_neighbor_distance = float(1.0 - float(pts[-1].score))

        cache_hit = (
            neighbor_std <= self.uncertainty_threshold
            and furthest_neighbor_distance <= self.max_neighbor_distance
        )

        return {
            "cache_hit": bool(cache_hit),
            "pred_value": pred_value,
            "neighbor_std": neighbor_std,
            "furthest_neighbor_distance": furthest_neighbor_distance,
            "reason": "passed" if cache_hit else "uncertain_or_far",
            "selected_feature": self.active_feature,
        }

    def evaluate_and_update(self, feature_row: dict[str, np.ndarray], llm_fallback_function):
        self._init_collection_from_row(feature_row)

        cache_eval = self._evaluate_cache(feature_row)
        if cache_eval["cache_hit"]:
            return {
                **cache_eval,
                "output_value": cache_eval["pred_value"],
                "source": "cache",
                "model_ready": True,
            }

        llm_value = float(llm_fallback_function(feature_row))
        self.buffer_rows.append({"features": feature_row, "label": llm_value})

        if len(self.buffer_rows) >= self.batch_size:
            self._flush_buffer()
            self._rebuild_model()

        return {
            **cache_eval,
            "output_value": llm_value,
            "source": "llm",
            "model_ready": self.model_ready(),
        }


def run_qdrant_sleep_champion_cache(
    df: pd.DataFrame,
    toml_path: str | Path,
    step_col: str = "simulation_step",
    label_col: str = "time",
    uncertainty_threshold: float = 10.0,
    error_threshold: float = 20.0,
    batch_size: int = 1000,
    n_neighbors: int = 50,
    distance_quantile: float = 0.95,
    validation_size: float = 0.2,
    random_state: int = 42,
):
    with Path(toml_path).open("rb") as f:
        cfg = tomllib.load(f)
    required_inputs = cfg.get("inputs", {}).get("required", [])
    if not required_inputs:
        raise ValueError("No [inputs.required] fields found in TOML.")

    eval_df = df.copy()
    eval_df[label_col] = pd.to_numeric(eval_df[label_col], errors="coerce")
    eval_df = eval_df[eval_df[label_col].notna()].copy()

    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    feature_names = []
    for field in required_inputs:
        if field not in eval_df.columns:
            continue
        feature_name = f"{field}_embedding"
        texts = eval_df[field].fillna("").astype(str).tolist()
        eval_df[feature_name] = list(model.embed(texts, parallel=0))
        feature_names.append(feature_name)

    if not feature_names:
        raise ValueError("No feature embeddings were built from TOML inputs.")

    seq_cols = [step_col, label_col] + feature_names
    seq_df = (
        eval_df[seq_cols]
        .dropna(subset=[label_col] + feature_names)
        .sort_values(step_col)
        .reset_index(drop=True)
    )

    cache = QdrantFeatureChampionRegressorCache(
        feature_names=feature_names,
        uncertainty_threshold=uncertainty_threshold,
        error_threshold=error_threshold,
        batch_size=batch_size,
        n_neighbors=n_neighbors,
        distance_quantile=distance_quantile,
        validation_size=validation_size,
        random_state=random_state,
        collection_name="qdrant_sleep_champion",
    )

    rows = []
    first_model_step = None

    for r in tqdm(seq_df.itertuples(index=False), total=len(seq_df), desc="Running Qdrant sleep cache"):
        sim_step = int(getattr(r, step_col))
        y_true = float(getattr(r, label_col))
        feature_row = {f: np.asarray(getattr(r, f)) for f in feature_names}

        out = cache.evaluate_and_update(feature_row, llm_fallback_function=lambda _x, y=y_true: y)
        if first_model_step is None and out["model_ready"]:
            first_model_step = sim_step

        abs_error = abs(float(out["output_value"]) - y_true)
        wrong_eval = bool((out["source"] == "cache") and (abs_error > error_threshold))

        rows.append(
            {
                "simulation_step": sim_step,
                "true_time": y_true,
                "pred_time": float(out["output_value"]),
                "abs_error": abs_error,
                "source": out["source"],
                "cache_hit": bool(out["source"] == "cache"),
                "cache_miss": bool(out["source"] == "llm"),
                "wrong_evaluation": wrong_eval,
                "neighbor_std": out["neighbor_std"],
                "furthest_neighbor_distance": out["furthest_neighbor_distance"],
                "max_neighbor_distance": cache.max_neighbor_distance,
                "reason": out["reason"],
                "selected_feature": out["selected_feature"],
            }
        )

    eval_out_df = pd.DataFrame(rows)
    total = len(eval_out_df)
    hits = int(eval_out_df["cache_hit"].sum())
    misses = int(eval_out_df["cache_miss"].sum())
    wrong = int(eval_out_df["wrong_evaluation"].sum())

    summary = {
        "total_rows": total,
        "features": feature_names,
        "cache_hits": hits,
        "cache_misses": misses,
        "wrong_evaluations": wrong,
        "hit_rate": hits / total if total else 0.0,
        "miss_rate": misses / total if total else 0.0,
        "wrong_rate_overall": wrong / total if total else 0.0,
        "wrong_rate_on_hits": wrong / hits if hits else 0.0,
        "mae_all_outputs": float(eval_out_df["abs_error"].mean()) if total else float("nan"),
        "mae_cache_hits": float(eval_out_df.loc[eval_out_df["cache_hit"], "abs_error"].mean()) if hits else float("nan"),
        "model_rebuilds": cache.rebuild_count,
        "first_model_available_step": first_model_step,
        "final_master_records": len(cache.master_rows),
        "pending_buffer_records": len(cache.buffer_rows),
        "uncertainty_threshold": uncertainty_threshold,
        "error_threshold": error_threshold,
        "distance_quantile": distance_quantile,
        "latest_max_neighbor_distance": cache.max_neighbor_distance,
        "active_feature_at_end": cache.active_feature,
        "last_feature_scores": cache.last_feature_scores,
    }

    return eval_out_df, summary, cache


def run_qdrant_needs_champion_cache(
    df: pd.DataFrame,
    required_inputs: list[str],
    output_cols: list[str],
    step_col: str = "simulation_step",
    uncertainty_threshold: float = 0.08,
    error_threshold: float = 0.20,
    batch_size: int = 1000,
    n_neighbors: int = 50,
    distance_quantile: float = 0.95,
    validation_size: float = 0.2,
    random_state: int = 42,
):
    eval_df = df.copy()
    for c in output_cols:
        if c in eval_df.columns:
            eval_df[c] = pd.to_numeric(eval_df[c], errors="coerce")

    existing_outputs = [c for c in output_cols if c in eval_df.columns]
    if not existing_outputs:
        raise ValueError("None of the output fields are present in parsed needs dataframe.")

    eval_df = eval_df[eval_df[existing_outputs].notna().any(axis=1)].copy()
    if eval_df.empty:
        raise ValueError("No rows with valid needs outputs after parsing.")

    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    feature_specs = []
    for field in required_inputs:
        col = field if field in eval_df.columns else f"input_{field}"
        if col not in eval_df.columns:
            continue
        emb_col = f"{field}_embedding"
        texts = eval_df[col].fillna("").astype(str).tolist()
        eval_df[emb_col] = list(model.embed(texts, parallel=0))
        feature_specs.append((field, col, emb_col))

    feature_names = [x[2] for x in feature_specs]
    if not feature_names:
        raise ValueError("No feature embeddings were built from needs inputs.")

    seq_cols = [step_col] + existing_outputs + feature_names
    seq_df = (
        eval_df[seq_cols]
        .dropna(subset=feature_names)
        .sort_values(step_col)
        .reset_index(drop=True)
    )

    caches = {
        out_col: QdrantFeatureChampionRegressorCache(
            feature_names=feature_names,
            uncertainty_threshold=uncertainty_threshold,
            error_threshold=error_threshold,
            batch_size=batch_size,
            n_neighbors=n_neighbors,
            distance_quantile=distance_quantile,
            validation_size=validation_size,
            random_state=random_state,
            collection_name=f"qdrant_needs_champion_{out_col}",
        )
        for out_col in existing_outputs
    }

    first_model_step = {k: None for k in existing_outputs}
    rows = []

    for r in tqdm(seq_df.itertuples(index=False), total=len(seq_df), desc="Running Qdrant needs cache"):
        sim_step = int(getattr(r, step_col))
        feature_row = {f: np.asarray(getattr(r, f)) for f in feature_names}

        true_vals = {k: getattr(r, k) for k in existing_outputs}
        valid_targets = [k for k, v in true_vals.items() if pd.notna(v)]
        if not valid_targets:
            continue

        probe = {k: caches[k]._evaluate_cache(feature_row) for k in valid_targets}
        all_targets_cache_hit = all(probe[k]["cache_hit"] for k in valid_targets)

        row = {
            "simulation_step": sim_step,
            "targets_present": len(valid_targets),
            "all_targets_cache_hit": bool(all_targets_cache_hit),
            "any_target_cache_miss": not bool(all_targets_cache_hit),
        }

        for k in existing_outputs:
            y_true = float(true_vals[k]) if pd.notna(true_vals[k]) else np.nan
            row[f"true_{k}"] = y_true

            if pd.isna(y_true):
                row[f"pred_{k}"] = np.nan
                row[f"abs_error_{k}"] = np.nan
                row[f"source_{k}"] = "missing_gt"
                row[f"cache_hit_{k}"] = False
                row[f"wrong_evaluation_{k}"] = False
                row[f"neighbor_std_{k}"] = np.nan
                row[f"furthest_neighbor_distance_{k}"] = np.nan
                row[f"selected_feature_{k}"] = None
                continue

            if all_targets_cache_hit:
                out = probe[k]
                pred_val = float(out["pred_value"])
                source = "cache"
                model_ready = True
            else:
                out = caches[k].evaluate_and_update(feature_row, llm_fallback_function=lambda _x, y=y_true: y)
                pred_val = float(out["output_value"])
                source = out["source"]
                model_ready = out["model_ready"]

            if first_model_step[k] is None and model_ready:
                first_model_step[k] = sim_step

            abs_err = abs(pred_val - y_true)
            wrong_eval = bool((source == "cache") and (abs_err > error_threshold))

            row[f"pred_{k}"] = pred_val
            row[f"abs_error_{k}"] = abs_err
            row[f"source_{k}"] = source
            row[f"cache_hit_{k}"] = bool(source == "cache")
            row[f"wrong_evaluation_{k}"] = wrong_eval
            row[f"neighbor_std_{k}"] = out.get("neighbor_std")
            row[f"furthest_neighbor_distance_{k}"] = out.get("furthest_neighbor_distance")
            row[f"selected_feature_{k}"] = out.get("selected_feature")

        rows.append(row)

    eval_out_df = pd.DataFrame(rows)
    total = len(eval_out_df)

    target_stats = {}
    for k in existing_outputs:
        source_col = f"source_{k}"
        err_col = f"abs_error_{k}"
        wrong_col = f"wrong_evaluation_{k}"

        valid_mask = eval_out_df[source_col].isin(["cache", "llm"])
        target_total = int(valid_mask.sum())
        target_hits = int((eval_out_df[source_col] == "cache").sum())
        target_misses = int((eval_out_df[source_col] == "llm").sum())
        target_wrong = int(eval_out_df[wrong_col].sum())

        target_stats[k] = {
            "rows": target_total,
            "cache_hits": target_hits,
            "cache_misses": target_misses,
            "wrong_evaluations": target_wrong,
            "hit_rate": target_hits / target_total if target_total else 0.0,
            "wrong_rate_overall": target_wrong / target_total if target_total else 0.0,
            "wrong_rate_on_hits": target_wrong / target_hits if target_hits else 0.0,
            "mae_all": float(eval_out_df.loc[valid_mask, err_col].mean()) if target_total else float("nan"),
            "mae_cache_hits": float(eval_out_df.loc[eval_out_df[source_col] == "cache", err_col].mean()) if target_hits else float("nan"),
            "model_rebuilds": caches[k].rebuild_count,
            "first_model_available_step": first_model_step[k],
            "active_feature_at_end": caches[k].active_feature,
            "latest_max_neighbor_distance": caches[k].max_neighbor_distance,
            "last_feature_scores": caches[k].last_feature_scores,
        }

    summary = {
        "total_rows": total,
        "features": feature_names,
        "feature_input_columns": {logical: actual for logical, actual, _ in feature_specs},
        "outputs": existing_outputs,
        "all_targets_cache_hit_rows": int(eval_out_df["all_targets_cache_hit"].sum()) if total else 0,
        "all_targets_cache_hit_rate": float(eval_out_df["all_targets_cache_hit"].mean()) if total else 0.0,
        "any_target_cache_miss_rows": int(eval_out_df["any_target_cache_miss"].sum()) if total else 0,
        "uncertainty_threshold": uncertainty_threshold,
        "error_threshold": error_threshold,
        "distance_quantile": distance_quantile,
        "target_stats": target_stats,
    }

    return eval_out_df, summary, caches


    # Qdrant championship evaluation for both blocks: sleep (single output) + needs (multi-output).

if "parsed_sleep_df" not in globals():
    raise ValueError("parsed_sleep_df is missing. Run the sleep parsing cell first.")

sleep_input_df = parsed_sleep_df.copy()

# Fallback: recover numeric sleep `time` directly from raw response text when parser misses it.
if ("time" not in sleep_input_df.columns) or (pd.to_numeric(sleep_input_df["time"], errors="coerce").notna().sum() == 0):
    if "df" in globals() and "response" in df.columns and len(df) == len(sleep_input_df):
        resp_num = pd.to_numeric(df["response"], errors="coerce")
        if resp_num.notna().sum() == 0:
            ext = df["response"].astype(str).str.extract(r"([-+]?[0-9]*\.?[0-9]+)", expand=False)
            resp_num = pd.to_numeric(ext, errors="coerce")
        sleep_input_df["time"] = resp_num.to_numpy()
        print(f"Recovered sleep time labels from response: {int(resp_num.notna().sum())}")
    else:
        print("Could not apply sleep fallback label extraction (missing aligned raw df.response).")

sleep_eval_qdrant_df, sleep_qdrant_summary, sleep_qdrant_cache = run_qdrant_sleep_champion_cache(
    df=sleep_input_df,
    toml_path=Path("toml_helpers/other_sleep_time_estimate_agentsociety_v1_0.toml"),
    step_col="simulation_step",
    label_col="time",
    uncertainty_threshold=10.0,
    error_threshold=20.0,
    batch_size=1000,
    n_neighbors=50,
    distance_quantile=0.95,
    validation_size=0.2,
    random_state=42,
)

print("SleepBlock Qdrant Championship Summary")
print(pd.Series({k: v for k, v in sleep_qdrant_summary.items() if k != "last_feature_scores"}).to_string())
print("\nSleepBlock last feature scores (MAE, lower is better):")
print(pd.DataFrame.from_dict(sleep_qdrant_summary["last_feature_scores"], orient="index").to_string())

if "parsed_needs_df" not in globals():
    raise ValueError("parsed_needs_df is missing. Run the needs parsing cell first.")

if "needs_required_inputs" not in globals() or "needs_output_cols" not in globals():
    needs_toml_path = Path("toml_helpers/needs_evaluation_citysim_v1_0.toml")
    with needs_toml_path.open("rb") as f:
        _cfg = tomllib.load(f)
    needs_required_inputs = _cfg.get("inputs", {}).get("required", [])
    needs_output_cols = list(_cfg.get("outputs", {}).keys())

needs_eval_qdrant_df, needs_qdrant_summary, needs_qdrant_caches = run_qdrant_needs_champion_cache(
    df=parsed_needs_df,
    required_inputs=needs_required_inputs,
    output_cols=needs_output_cols,
    step_col="simulation_step",
    uncertainty_threshold=0.08,
    error_threshold=0.20,
    batch_size=1000,
    n_neighbors=50,
    distance_quantile=0.95,
    validation_size=0.2,
    random_state=42,
)

print("\nNeeds Qdrant Championship Summary")
print(pd.Series({k: v for k, v in needs_qdrant_summary.items() if k != "target_stats"}).to_string())
print("\nNeeds per-target stats:")
print(pd.DataFrame(needs_qdrant_summary["target_stats"]).T.to_string())

display(sleep_eval_qdrant_df.head())
display(needs_eval_qdrant_df.head())

SleepBlock Qdrant Championship Summary
total_rows                                                                   5500
features                        [plan_embedding, intention_embedding, emotion_...
cache_hits                                                                   4500
cache_misses                                                                 1000
wrong_evaluations                                                               0
hit_rate                                                                 0.818182
miss_rate                                                                0.181818
wrong_rate_overall                                                            0.0
wrong_rate_on_hits                                                            0.0
mae_all_outputs                                                          0.267047
mae_cache_hits                                                            0.32639
model_rebuilds                                                                  1
first_model_available_step                                                     25
final_master_records                                                         1000
pending_buffer_records                                                          0
uncertainty_threshold                                                        10.0
error_threshold                                                              20.0
distance_quantile                                                            0.95
latest_max_neighbor_distance                                                 -0.0
active_feature_at_end                                              plan_embedding

SleepBlock last feature scores (MAE, lower is better):
                          mae status
plan_embedding       0.249414     ok
intention_embedding  0.249414     ok
emotion_embedding    0.249414     ok