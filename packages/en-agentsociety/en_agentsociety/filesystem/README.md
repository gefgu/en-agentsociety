# `filesystem/` — Abstract Filesystem Client

This package provides a unified filesystem abstraction that transparently handles both local disk and S3-backed storage.

---

## Files

| File | Purpose |
|---|---|
| `client.py` | `FilesystemClient` — unified read/write/list API |

---

## Purpose

Internal code (model loading, config reading, artifact writing) uses `FilesystemClient` instead of direct `open()` / `boto3` calls. This allows the same code path to work with local files during development and S3-backed files in production without any changes.

---

## API

```python
from en_agentsociety.filesystem import FilesystemClient

# Local filesystem
client = FilesystemClient(base_path="./data")

# S3-backed (pass S3Config)
client = FilesystemClient(s3_config=S3Config(...), base_path="experiments/")

# Read
data = await client.read("models/catboost.cbm")      # bytes

# Write
await client.write("results/output.json", json.dumps(results).encode())

# Check existence
exists = await client.exists("models/catboost.cbm")

# List files
files = await client.list("models/")
```

---

## Notes

- When `s3_config` is provided, all paths are resolved relative to the S3 bucket + base prefix.
- When only `base_path` is provided, paths are resolved relative to the local base directory.
- All methods are `async` for non-blocking I/O.
