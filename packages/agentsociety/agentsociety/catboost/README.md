# `catboost/` — CatBoost Need-Adjustment Backend

This package provides an ML-based alternative to LLM-powered need-satisfaction adjustment for citizen agents.

---

## Background

After each action, a `SocietyAgent`'s need-satisfaction scores (`hunger_satisfaction`, `energy_satisfaction`, `safety_satisfaction`, `social_satisfaction`) must be updated. The naive approach uses an LLM to evaluate the action description and output new scores — which is slow and expensive.

This module replaces that LLM call with **CatBoost regression models** that run ~100× faster.

---

## Files

| File | Purpose |
|---|---|
| `catboost_adjust_needs.py` | `CatBoostAdjustNeedsActor` — Ray actor performing inference |
| `dispatcher.py` | `CatBoostDispatcherActor` — routes requests to the correct actor |

---

## Architecture

```
Agent action text
       │
       ▼
CatBoostDispatcherActor (Ray)
       │
       ├─► CatBoostAdjustNeedsActor (hungry model)
       ├─► CatBoostAdjustNeedsActor (tired model)
       ├─► CatBoostAdjustNeedsActor (safe model)
       └─► CatBoostAdjustNeedsActor (social model)
              │
              ▼
       predicted satisfaction delta
```

---

## `CatBoostAdjustNeedsActor`

A Ray remote actor (`num_cpus=4`) that:

1. Loads 4 pre-trained `CatBoostRegressor` models (`_hungry.cbm`, `_tired.cbm`, `_safe.cbm`, `_social.cbm`).
2. Loads a pre-fitted PCA transform for dimensionality reduction.
3. At inference time, embeds the action text with `fastembed.TextEmbedding`, applies PCA, runs the model, and returns a predicted satisfaction score.

```python
actor = CatBoostAdjustNeedsActor.remote(
    model_path_prefix="/models/catboost/needs",
    pca_path="/models/catboost/pca.pkl",
)
result = await actor.predict.remote(prompt_text="had a meal at a restaurant", need="hungry")
# result: {"hunger_satisfaction": 0.85}
```

### Key Parameters

- `model_path_prefix`: Path prefix; models are expected at `{prefix}_hungry.cbm`, etc.
- `pca_path`: Path to the joblib-serialized PCA object.

---

## `CatBoostDispatcherActor`

Routes inference requests to the appropriate `CatBoostAdjustNeedsActor` based on the need type. Multiple actors can be registered to enable parallel processing.

---

## Training the Models

The CatBoost models are trained externally (see the `citysim` training scripts). Training data consists of `(action_text, satisfaction_delta)` pairs collected from LLM-evaluated simulation runs. The models learn to predict satisfaction adjustments from text embeddings.

---

## Enabling in Simulation

Pass the actor configuration in `Config`:

```python
# The SimulationEngine automatically starts CatBoostAdjustNeedsActor
# if catboost_model_config is provided in the environment config.
```

When disabled, the original LLM-based need adjustment is used as fallback.
