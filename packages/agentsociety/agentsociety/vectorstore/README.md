# `vectorstore/` — Sparse Vector Store

This package provides a lightweight vector store backed by `fastembed` BM25 sparse embeddings. It is used internally by `KVMemory` and `StreamMemory` for semantic search over agent memory.

---

## Files

| File | Purpose |
|---|---|
| `vectorstore.py` | `VectorStore` — add, update, and search document collections |

---

## Features

- **Sparse BM25 embeddings** via `fastembed.SparseTextEmbedding`
- **In-memory storage** — no external vector database required
- **Batch document ingestion** with auto-generated document IDs
- **Top-k cosine similarity search** over stored documents
- **Tag-based filtering** — attach arbitrary metadata to documents and filter search results

---

## API

```python
from agentsociety.vectorstore import VectorStore
from fastembed import SparseTextEmbedding

embedding = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")
store = VectorStore(embedding=embedding)

# Add documents
doc_ids = await store.add_documents(
    documents=["The agent ate lunch at a restaurant", "The agent went jogging"],
    extra_tags={"agent_id": [1, 1], "type": ["action", "action"]},
)

# Update a document
await store.update_document(doc_id=doc_ids[0], new_text="The agent had dinner at home")

# Semantic search
results = await store.search(
    query="food and eating",
    top_k=3,
    filter_tags={"agent_id": 1},
)
# results: [{"doc_id": ..., "text": ..., "score": ..., "tags": ...}, ...]
```

---

## Integration

`KVMemory` uses one `VectorStore` instance per memory store (status, profile). When a field has an `embedding_template`, its value is embedded and stored here, enabling:

```python
results = await agent.memory.status.search("hungry and tired", top_k=3)
```

---

## Embedding Model

The default sparse embedding model is `prithivida/Splade_PP_en_v1` (SPLADE++). It is downloaded automatically from Hugging Face on first use (or from `hf-mirror.com` if configured).

Dense embedding models are not used by default; `SparseTextEmbedding` provides a good balance of search quality and CPU-only inference speed.
