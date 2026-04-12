import asyncio
import json
from collections import deque
from copy import deepcopy
from typing import Any, Literal, Optional, Union

from fastembed import SparseTextEmbedding

from ..agent.memory_config_generator import MemoryConfig
from ..logger import get_logger
from ..utils.decorators import lock_decorator
from ..vectorstore import VectorStore


_MISSING = object()


class KVMemory:
    def __init__(
        self,
        memory_config: MemoryConfig,
        embedding: SparseTextEmbedding,
    ):
        """
        Initialize the KVMemory with a unified memory configuration.

        - **Args**:
            - `memory_config` (MemoryConfig): The unified memory configuration.
            - `embedding` (SparseTextEmbedding): The embedding object.
        """
        self._memory_config = memory_config
        self._data = {}
        self._vectorstore = VectorStore(embedding)
        self._key_to_doc_id = {}
        self._lock = asyncio.Lock()

        # Initialize from memory config
        for attr in memory_config.attributes.values():
            # Add to init_data
            self._data[attr.name] = deepcopy(attr.default_or_value)

    async def initialize_embeddings(self) -> None:
        """Initialize embeddings for all fields that require them."""
        # Create embeddings for each field that requires it
        documents = []
        keys = []

        # Collect documents and keys from all memory types
        for key, value in self._data.items():
            if self.should_embed(key):
                semantic_text = self._generate_semantic_text(key, value)
                documents.append(semantic_text)
                keys.append(key)

        # Add all documents in one batch
        doc_ids = await self._vectorstore.add_documents(
            documents=documents,
            extra_tags={
                "key": keys,
            },
        )

        # Map document IDs back to their keys
        for key, doc_id in zip(keys, doc_ids, strict=False):
            self._key_to_doc_id[key] = doc_id

    def _generate_semantic_text(self, key: str, value: Any) -> str:
        """
        Generate semantic text for a given key and value.
        """
        if key in self._memory_config.attributes:
            config = self._memory_config.attributes[key]
            if config.embedding_template:
                return config.embedding_template.format(value)
        return f"My {key} is {value}"

    @lock_decorator
    async def search(
        self, query: str, top_k: int = 3, filter: Optional[dict] = None
    ) -> str:
        """
        Search for relevant memories based on the provided query.

        - **Args**:
            - `query` (str): The text query to search for.
            - `top_k` (int, optional): Number of top relevant memories to return. Defaults to 3.
            - `filter` (Optional[dict], optional): Additional filters for the search. Defaults to None.

        - **Returns**:
            - `str`: Formatted string of the search results.
        """
        filter_dict = {}
        if filter is not None:
            filter_dict.update(filter)
        top_results: list[tuple[str, float, dict]] = (
            await self._vectorstore.similarity_search(
                query=query,
                k=top_k,
                filter=filter_dict,
            )
        )
        # formatted results
        formatted_results = []
        for content, _, _ in top_results:
            formatted_results.append(f"- {content} ")

        return "Nothing" if len(formatted_results) == 0 else "\n".join(formatted_results)

    def should_embed(self, key: str) -> bool:
        return (
            key in self._memory_config.attributes
            and self._memory_config.attributes[key].whether_embedding
        )

    @lock_decorator
    async def get(
        self,
        key: Any,
        default_value: Any = _MISSING,
    ) -> Any:
        """
        Retrieve a value from the memory.

        - **Args**:
            - `key` (Any): The key to retrieve.
            - `default_value` (Optional[Any], optional): Default value if the key is not found. Defaults to None.

        - **Returns**:
            - `Any`: The retrieved value or the default value if the key is not found.

        - **Raises**:
            - `KeyError`: If the key is not found in any of the memory sections and no default value is provided.
        """
        if key in self._data:
            return deepcopy(self._data[key])
        if default_value is _MISSING:
            raise KeyError(f"No attribute `{key}` in memories!")
        return default_value

    @lock_decorator
    async def update(
        self,
        key: Any,
        value: Any,
        mode: Union[Literal["replace"], Literal["merge"]] = "replace",
    ) -> None:
        """
        Update a value in the memory and refresh embeddings if necessary.

        - **Args**:
            - `key` (Any): The key to update.
            - `value` (Any): The new value to set.
            - `mode` (Union[Literal["replace"], Literal["merge"]], optional): Update mode. Defaults to "replace".

        - **Raises**:
            - `ValueError`: If an invalid update mode is provided.
            - `KeyError`: If the key is not found in any of the memory sections.
        """
        # If key doesn't exist, add it directly
        if key not in self._data:
            self._data[key] = value
            # Check if we should embed this field
            if self.should_embed(key):
                semantic_text = self._generate_semantic_text(key, value)
                # Add embedding for new key
                doc_ids = await self._vectorstore.add_documents(
                    documents=[semantic_text],
                    extra_tags={
                        "key": key,
                    },
                )
                self._key_to_doc_id[key] = doc_ids[0]
            return

        # Update existing key
        if mode == "replace":
            # Replace the value directly
            self._data[key] = value

            # Update embeddings if needed
            if self.should_embed(key):
                semantic_text = self._generate_semantic_text(key, value)

                # Delete old embedding if it exists
                if key in self._key_to_doc_id and self._key_to_doc_id[key]:
                    await self._vectorstore.delete_documents(
                        to_delete_ids=[self._key_to_doc_id[key]],
                    )

                # Add new embedding
                doc_ids = await self._vectorstore.add_documents(
                    documents=[semantic_text],
                    extra_tags={
                        "key": key,
                    },
                )
                self._key_to_doc_id[key] = doc_ids[0]

        elif mode == "merge":
            # Get current value
            original_value = self._data[key]

            # Merge based on the type of original value
            if isinstance(original_value, set):
                original_value.update(set(value))
            elif isinstance(original_value, dict):
                original_value.update(dict(value))
            elif isinstance(original_value, list):
                original_value.extend(list(value))
            elif isinstance(original_value, deque):
                original_value.extend(deque(value))
            else:
                # Fall back to replace if merge is not supported
                get_logger().debug(
                    f"Type of {type(original_value)} does not support mode `merge`, using `replace` instead!"
                )
                self._data[key] = value

            # Update embeddings if needed
            if self.should_embed(key):
                semantic_text = self._generate_semantic_text(key, self._data[key])

                # Delete old embedding if it exists
                if key in self._key_to_doc_id and self._key_to_doc_id[key]:
                    await self._vectorstore.delete_documents(
                        to_delete_ids=[self._key_to_doc_id[key]],
                    )

                # Add new embedding
                doc_ids = await self._vectorstore.add_documents(
                    documents=[semantic_text],
                    extra_tags={
                        "key": key,
                    },
                )
                self._key_to_doc_id[key] = doc_ids[0]
        else:
            # Invalid mode
            raise ValueError(f"Invalid update mode `{mode}`!")

    @lock_decorator
    async def export(self, keys: list[str]) -> dict[str, Any]:
        """
        Export the memory of a given keys.
        """
        result = {}
        for k in keys:
            if k in self._data:
                result[k] = deepcopy(self._data[k])
        return result

    @lock_decorator
    async def export_all(self) -> dict[str, Any]:
        """
        Export all key-value memory entries.
        """
        return deepcopy(self._data)

    async def resume(
        self,
        kv_entries: list[dict[str, Any]],
        skip_keys: Optional[set[str]] = None,
    ) -> None:
        """
        Restore KV memory from checkpoint entries.
        """
        skipped = skip_keys or set()
        for entry in kv_entries:
            key = str(entry.get("key", ""))
            if not key or key in skipped:
                continue

            if "value_json" in entry:
                try:
                    value = json.loads(entry["value_json"])
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
            elif "value" in entry:
                value = entry.get("value")
            else:
                continue

            await self.update(key, value, mode="replace")
