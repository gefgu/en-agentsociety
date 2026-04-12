from collections import deque
from dataclasses import dataclass
from typing import Any, Optional, Union

from fastembed import SparseTextEmbedding

from ..environment import Environment
from ..vectorstore import VectorStore
from .kv_memory import KVMemory


@dataclass
class MemoryNode:
    """
    A data class representing a memory node.

    - **Attributes**:
        - `topic`: The topic associated with the memory node.
        - `day`: Day of the event or memory.
        - `t`: Time stamp or order.
        - `location`: Location where the event occurred.
        - `description`: Description of the memory.
        - `cognition_id`: ID related to cognitive memory (optional).
        - `id`: Unique ID for this memory node (optional).
    """

    topic: str
    day: int
    t: int
    location: str
    description: str
    cognition_id: Optional[int] = None  # ID related to cognitive memory
    id: Optional[int] = None  # Unique ID for the memory node


class StreamMemory:
    """
    A class used to store and manage time-ordered stream information.

    - **Attributes**:
        - `_memories`: A deque to store memory nodes with a maximum length limit.
        - `_memory_id_counter`: An internal counter to generate unique IDs for each new memory node.
        - `_vectorstore`: The Faiss query object for search functionality.
        - `_status_memory`: The status memory object.
        - `_environment`: The environment object.
    """

    def __init__(
        self,
        environment: Optional[Environment],
        status_memory: KVMemory,
        embedding: SparseTextEmbedding,
        max_len: int = 1000,
    ):
        """
        Initialize an instance of StreamMemory.

        - **Args**:
            - `environment` (Environment): The environment object.
            - `status_memory` (KVMemory): The status memory object.
            - `embedding` (SparseTextEmbedding): The embedding object.
            - `max_len` (int): Maximum length of the deque. Default is 1000.
        """
        self._memories: deque = deque(maxlen=max_len)  # Limit the maximum storage
        self._memory_id_counter: int = 0  # Used for generating unique IDs
        self._status_memory = status_memory
        self._environment = environment
        self._vectorstore = VectorStore(embedding)

    async def add(self, topic: str, description: str) -> int:
        """
        A generic method for adding a memory node and returning the memory node ID.

        - **Args**:
            - `topic` (str): The topic associated with the memory node.
            - `description` (str): Description of the memory.

        - **Returns**:
            - `int`: The unique ID of the newly added memory node.
        """
        if self._environment is None:
            raise ValueError("Environment is not initialized")
        day, t = self._environment.get_datetime()
        position = await self._status_memory.get("position")
        if "aoi_position" in position:
            location = position["aoi_position"]["aoi_id"]
        elif "lane_position" in position:
            location = position["lane_position"]["lane_id"]
        else:
            location = "unknown"

        current_id = self._memory_id_counter
        self._memory_id_counter += 1
        memory_node = MemoryNode(
            topic=topic,
            day=day,
            t=t,
            location=location,
            description=description,
            id=current_id,
        )
        self._memories.append(memory_node)

        # create embedding for new memories
        await self._vectorstore.add_documents(
            documents=[description],
            extra_tags={
                "topic": topic,
                "day": day,
                "time": t,
            },
        )

        return current_id

    async def get_related_cognition(self, memory_id: int) -> Union[MemoryNode, None]:
        """
        Retrieve the related cognition memory node by its ID.

        - **Args**:
            - `memory_id` (int): The ID of the memory to find related cognition for.

        - **Returns**:
            - `Optional[MemoryNode]`: The related cognition memory node, if found; otherwise, None.
        """
        for m in self._memories:
            if m.topic == "cognition" and m.id == memory_id:
                return m
        return None

    async def format_memory(self, memories: list[MemoryNode]) -> str:
        """
        Format a list of memory nodes into a readable string representation.

        - **Args**:
            - `memories` (list[MemoryNode]): List of MemoryNode objects to format.

        - **Returns**:
            - `str`: A formatted string containing the details of each memory node.
        """
        formatted_results = []
        for memory in memories:
            memory_topic = memory.topic
            memory_day = memory.day
            memory_time_seconds = memory.t
            cognition_id = memory.cognition_id

            # Format time
            if memory_time_seconds != "unknown":
                hours = memory_time_seconds // 3600
                minutes = (memory_time_seconds % 3600) // 60
                seconds = memory_time_seconds % 60
                memory_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                memory_time = "unknown"

            memory_location = memory.location

            # Add cognition information (if exists)
            cognition_info = ""
            if cognition_id is not None:
                cognition_memory = await self.get_related_cognition(cognition_id)
                if cognition_memory:
                    cognition_info = (
                        f"\n  Related cognition: {cognition_memory.description}"
                    )

            formatted_results.append(
                f"- [{memory_topic}]: {memory.description} [day: {memory_day}, time: {memory_time}, "
                f"location: {memory_location}]{cognition_info}"
            )
        return "\n".join(formatted_results)

    async def get_by_ids(self, memory_ids: list[int]) -> str:
        """Retrieve memories by specified IDs"""
        memories = [memory for memory in self._memories if memory.id in memory_ids]
        sorted_results = sorted(memories, key=lambda x: (x.day, x.t), reverse=True)
        return await self.format_memory(sorted_results)

    async def search(
        self,
        query: str,
        topic: Optional[str] = None,
        top_k: int = 3,
        day_range: Optional[tuple[int, int]] = None,
        time_range: Optional[tuple[int, int]] = None,
    ) -> str:
        """
        Search stream memory with optional filters and return formatted results.

        - **Args**:
            - `query` (str): The text to use for searching.
            - `topic` (Optional[str], optional): Filter memories by this topic. Defaults to None.
            - `top_k` (int, optional): Number of top relevant memories to return. Defaults to 3.
            - `day_range` (Optional[tuple[int, int]], optional): Tuple of start and end days for filtering. Defaults to None.
            - `time_range` (Optional[tuple[int, int]], optional): Tuple of start and end times for filtering. Defaults to None.

        - **Returns**:
            - `str`: Formatted string of the search results.
        """
        filter_dict: dict[str, Any] = {"type": "stream"}

        if topic:
            filter_dict["topic"] = topic

        # Add time range filter
        if day_range:
            start_day, end_day = day_range
            filter_dict["day"] = {"gte": start_day, "lte": end_day}

        if time_range:
            start_time, end_time = time_range
            filter_dict["time"] = {"gte": start_time, "lte": end_time}

        top_results = await self._vectorstore.similarity_search(
            query=query,
            k=top_k,
            filter=filter_dict,
        )

        # Sort results by time (first by day, then by time)
        sorted_results = sorted(
            top_results,
            key=lambda x: (x[2].get("day", 0), x[2].get("time", 0)),
            reverse=True,
        )

        formatted_results = []
        for content, _, metadata in sorted_results:
            memory_topic = metadata.get("topic", "unknown")
            memory_day = metadata.get("day", "unknown")
            memory_time_seconds = metadata.get("time", "unknown")
            cognition_id = metadata.get("cognition_id", None)

            # Format time
            if memory_time_seconds != "unknown":
                hours = memory_time_seconds // 3600
                minutes = (memory_time_seconds % 3600) // 60
                seconds = memory_time_seconds % 60
                memory_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                memory_time = "unknown"

            memory_location = metadata.get("location", "unknown")

            # Add cognition information (if exists)
            cognition_info = ""
            if cognition_id is not None:
                cognition_memory = await self.get_related_cognition(cognition_id)
                if cognition_memory:
                    cognition_info = (
                        f"\n  Related cognition: {cognition_memory.description}"
                    )

            formatted_results.append(
                f"- [{memory_topic}]: {content} [day: {memory_day}, time: {memory_time}, "
                f"location: {memory_location}]{cognition_info}"
            )
        return "Nothing" if len(formatted_results) == 0 else "\n".join(formatted_results)

    async def search_today(
        self,
        query: str = "",  # Optional query text
        topic: Optional[str] = None,
        top_k: int = 100,  # Default to a larger number to ensure all memories of the day are retrieved
    ) -> str:
        """Search all memory events from today

        - **Args**:
            - `query` (`str`): Optional query text, returns all memories of the day if empty. Defaults to "".
            - `topic` (`Optional[str]`): Optional memory topic for filtering specific types of memories. Defaults to None.
            - `top_k` (`int`): Number of most relevant memories to return. Defaults to 100.

        - **Returns**:
            - `str`: Formatted text of today's memories.
        """
        if self._environment is None:
            raise ValueError("Environment is not initialized")
        current_day, _ = self._environment.get_datetime()
        # Use the search method, setting day_range to today
        return await self.search(
            query=query, topic=topic, top_k=top_k, day_range=(current_day, current_day)
        )

    async def add_cognition_to_memory(
        self, memory_ids: list[int], cognition: str
    ) -> None:
        """
        Add cognition to existing memory nodes.

        - **Args**:
            - `memory_ids` (list[int]): List of IDs of the memories to which cognition will be added.
            - `cognition` (str): Description of the cognition to add.
        """
        # Find all corresponding memories
        target_memories = []
        for memory in self._memories:
            if memory.id in memory_ids:
                target_memories.append(memory)

        # Add cognitive memory
        cognition_id = await self.add(topic="cognition", description=cognition)

        # Update the cognition_id of all original memories
        for target_memory in target_memories:
            target_memory.cognition_id = cognition_id

    async def get_all(self) -> list[dict]:
        """
        Retrieve all stream memory nodes as dictionaries.

        - **Returns**:
            - `list[dict]`: List of all memory nodes as dictionaries.
        """
        return [
            {
                "id": memory.id,
                "cognition_id": memory.cognition_id,
                "topic": memory.topic,
                "location": memory.location,
                "description": memory.description,
                "day": memory.day,
                "t": memory.t,
            }
            for memory in self._memories
        ]

    async def export(self) -> list[dict]:
        """
        Export stream memory in checkpoint-compatible format.
        """
        return await self.get_all()

    async def resume(self, stream_entries: list[dict[str, Any]]) -> None:
        """
        Restore stream memory from checkpoint entries.
        """
        for entry in stream_entries:
            node = MemoryNode(
                id=int(entry.get("memory_id") or 0),
                topic=str(entry.get("topic", "")),
                location=str(entry.get("location", "")),
                description=str(entry.get("description", "")),
                day=int(entry.get("day", 0)),
                t=int(entry.get("t", 0)),
                cognition_id=entry.get("cognition_id"),
            )
            self._memories.append(node)
            if node.id is not None and self._memory_id_counter <= node.id:
                self._memory_id_counter = node.id + 1
