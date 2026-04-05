import asyncio
import json
from typing import Any, Optional

from fastembed import SparseTextEmbedding

from ..agent.memory_config_generator import MemoryConfig
from ..environment import Environment
from .kv_memory import KVMemory
from .spatial_memory import SpatialMemory
from .stream_memory import StreamMemory

__all__ = ["Memory"]


class Memory:
    """
    A class to manage different types of memory (status and stream).

    - **Attributes**:
        - `_status` (`KVMemory`): Stores status-related data.
        - `_stream` (`StreamMemory`): Stores stream-related data.
    """

    def __init__(
        self,
        environment: Optional[Environment],
        embedding: SparseTextEmbedding,
        memory_config: MemoryConfig,
    ) -> None:
        """
        Initializes the Memory with a unified memory configuration.

        - **Args**:
            - `environment` (Environment): The environment object.
            - `embedding` (SparseTextEmbedding): The embedding object.
            - `memory_config` (MemoryConfig): The unified memory configuration.
        """
        self._lock = asyncio.Lock()
        self._environment = environment
        self._embedding = embedding

        # Initialize status memory with unified config
        self._status = KVMemory(
            memory_config=memory_config,
            embedding=self._embedding,
        )

        # Add StreamMemory
        self._stream = StreamMemory(
            environment=self._environment,
            embedding=self._embedding,
            status_memory=self._status,
        )

        self._spatial = SpatialMemory(embedding=self._embedding)

    @property
    def status(self) -> KVMemory:
        return self._status

    @property
    def stream(self) -> StreamMemory:
        return self._stream

    @property
    def spatial(self) -> SpatialMemory:
        return self._spatial

    async def initialize_embeddings(self):
        """
        Initialize embeddings within the status memory.

        - **Description**:
            - Asynchronously initializes embeddings for the status memory component, which prepares the system for performing searches.
        """
        await self._status.initialize_embeddings()

    async def export(self) -> dict[str, Any]:
        """
        Export all memory stores as a single payload.
        """
        return {
            "status": await self._status.export_all(),
            "stream": await self._stream.export(),
            "spatial": await self._spatial.export(),
        }

    async def create_snapshot_records(
        self,
        exp_id: str,
        simulation_step: int,
        agent_id: int,
        day: int,
        t: int,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Create checkpoint-ready KV/stream/spatial records for one agent.
        """
        memory_exports = await self.export()
        kv_data = memory_exports.get("status", {})
        stream_nodes = memory_exports.get("stream", [])
        spatial_nodes = memory_exports.get("spatial", [])

        kv_records: list[dict[str, Any]] = []
        for key, value in kv_data.items():
            try:
                value_json = json.dumps(value, ensure_ascii=False)
            except (TypeError, ValueError):
                value_json = json.dumps(str(value))
            kv_records.append(
                {
                    "exp_id": exp_id,
                    "simulation_step": simulation_step,
                    "agent_id": agent_id,
                    "key": key,
                    "value_json": value_json,
                }
            )

        stream_records: list[dict[str, Any]] = []
        for node in stream_nodes:
            stream_records.append(
                {
                    "exp_id": exp_id,
                    "simulation_step": simulation_step,
                    "agent_id": agent_id,
                    "memory_id": node["id"] or 0,
                    "cognition_id": node.get("cognition_id"),
                    "topic": node.get("topic", ""),
                    "location": str(node.get("location", "")),
                    "description": node.get("description", ""),
                    "day": node.get("day", day),
                    "t": node.get("t", t),
                }
            )

        spatial_records: list[dict[str, Any]] = []
        for node in spatial_nodes:
            spatial_records.append(
                {
                    "exp_id": exp_id,
                    "simulation_step": simulation_step,
                    "agent_id": agent_id,
                    "location_id": str(node.get("location_id", "")),
                    "description": node.get("description", ""),
                    "price": node.get("price", 0.5),
                    "atmosphere": node.get("atmosphere", 0.5),
                    "satisfaction": node.get("satisfaction", 0.5),
                    "convenience": node.get("convenience", 0.5),
                    "uncertainty": node.get("uncertainty", 0.25),
                }
            )

        return {
            "kv": kv_records,
            "stream": stream_records,
            "spatial": spatial_records,
            "status": kv_data,
        }

    async def resume_from_snapshots(
        self,
        static_updates: dict[str, Any],
        kv_entries: list[dict[str, Any]],
        stream_entries: list[dict[str, Any]],
        spatial_entries: list[dict[str, Any]],
    ) -> None:
        """
        Restore all memory stores from resume snapshots.
        """
        static_keys = set(static_updates.keys())
        for key, value in static_updates.items():
            if value is not None:
                await self._status.update(key, value, mode="replace")

        await self._status.resume(kv_entries, skip_keys=static_keys)
        await self._stream.resume(stream_entries)
        await self._spatial.resume(spatial_entries)
