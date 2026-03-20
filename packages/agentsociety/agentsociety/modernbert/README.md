# `modernbert/` — ModernBERT Regression Actor (Experimental)

This package contains an **experimental**, currently disabled Ray actor that uses a fine-tuned ModernBERT model for need-satisfaction regression.

> **Status**: All code in this module is commented out. It is preserved for future reactivation once the integration is tested.

---

## Files

| File | Purpose |
|---|---|
| `modernbert_regression_actor.py` | (Commented out) `ModernBERTRegressionActor` Ray actor |

---

## Intended Design

`ModernBERTRegressionActor` is a GPU-enabled Ray actor that runs a fine-tuned `ModernBERT` transformer model to predict agent need-satisfaction scores directly from action text.

### Architecture

```
Action description text
        │
        ▼
ModernBERTRegressionActor (Ray, num_gpus=0.1)
  └── ModernBERT tokenizer + seq classification head
        │
        ▼
[hunger, energy, social, fun] satisfaction scores (0–1 each)
```

### Comparison with CatBoost

| | CatBoost (`catboost/`) | ModernBERT (`modernbert/`) |
|---|---|---|
| **Model type** | Gradient boosted trees | Transformer neural network |
| **Input encoding** | BM25 sparse → PCA → trees | Direct tokenization |
| **Hardware** | CPU only | GPU (CUDA) preferred |
| **Speed** | Very fast | Slower, but more expressive |
| **Status** | Active | Experimental / commented out |

---

## Reactivating

To re-enable:

1. Uncomment all code in `modernbert_regression_actor.py`.
2. Install `torch` and `transformers`.
3. Place a fine-tuned `ModernBERT` checkpoint at the configured model path.
4. Configure the actor in `SimulationEngine` (replace `CatBoostAdjustNeedsActor`).

The Ray actor is designed with `num_gpus=0.1` to allow fractional GPU sharing across multiple actor instances.

---

## Training

The ModernBERT model is fine-tuned on:
- Input: action description text (same format as the need-adjustment LLM prompts)
- Target: 4-dimensional regression labels → `[hunger, energy, social, fun]` satisfaction deltas

Datasets and training scripts are maintained separately in the `citysim` training repository.
