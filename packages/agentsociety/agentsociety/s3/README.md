# `s3/` — S3 Object Storage Client

This package provides a thin wrapper around S3-compatible object storage for saving and loading simulation artifacts.

---

## Files

| File | Purpose |
|---|---|
| `client.py` | `S3Client` and `S3Config` |

---

## `S3Config`

```python
class S3Config(BaseModel):
    endpoint: str          # e.g. "https://s3.amazonaws.com" or MinIO endpoint
    bucket: str
    access_key: str
    secret_key: str
    region: str = "us-east-1"
    prefix: str = ""       # optional key prefix for all objects
```

---

## `S3Client` API

```python
client = S3Client(config=S3Config(...))
await client.init()

# Upload a file
await client.upload_file(local_path="results.json", key="experiments/exp_001/results.json")

# Download a file
await client.download_file(key="models/catboost_needs.cbm", local_path="./catboost_needs.cbm")

# Upload bytes directly
await client.put_object(key="snapshots/tick_3600.pkl", data=pickle.dumps(state))

# List objects
keys = await client.list_objects(prefix="experiments/exp_001/")

await client.close()
```

---

## Usage in Simulation

S3 is used for:

1. **Model artifacts**: CatBoost model files and PCA transforms can be loaded from S3 at startup.
2. **Result export**: Agent status snapshots and dialog logs can be exported to S3 after the simulation.
3. **Config distribution**: Experiment configs can be read from S3 in multi-node deployments.

Configured via `EnvConfig.s3`:

```python
class EnvConfig(BaseModel):
    s3: Optional[S3Config] = None
```

All S3 operations are **optional** — the simulation runs without S3 and uses local filesystem only.
