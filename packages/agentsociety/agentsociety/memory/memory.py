import asyncio
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal, Optional, Union

from fastembed import SparseTextEmbedding

from ..environment import Environment
from ..logger import get_logger
from ..utils.decorators import lock_decorator
from ..vectorstore import VectorStore
from ..agent.memory_config_generator import MemoryConfig

__all__ = [
    "KVMemory",
    "StreamMemory",
    "Memory",
    "SpatialMemory"
]


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
        for key, doc_id in zip(keys, doc_ids):
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
        for content, score, metadata in top_results:
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
        default_value: Optional[Any] = None,
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
        else:
            if default_value is None:
                raise KeyError(f"No attribute `{key}` in memories!")
            else:
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
        for content, score, metadata in sorted_results:
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


@dataclass
class SpatialMemoryNode:
    """
    A data class representing a spatial memory node.

    - **Attributes**:
        - `location_id`: The ID of the location.
        - `description`: Description of the location.

    """

    location_id: str
    description: str
    price: float
    atmosphere: float
    satisfaction: float
    convenience: float
    uncertainty: float

class SpatialMemory:
    """
    A class used to store and manage spatial information.

    - **Attributes**:
        - `_locations`: A dictionary to store location information with location IDs as keys.
    """

    def __init__(self, embedding: SparseTextEmbedding):
        """
        Initialize an instance of SpatialMemory.
        """
        self._locations: dict[str, SpatialMemoryNode] = {}
        self._vectorstore = VectorStore(embedding)
        self._loc_to_doc_id: dict[str, str] = {}
        self._default_uncertainty = 0.25
        self.SIGMA_OBS = 0.2
        self.ALPHA_DECAY = 0.03


    async def add_location(self, location_id: str, location_description: Optional[str]) -> None:
        """
        Add a spatial memory node.

        - **Args**:
            - `node` (SpatialMemoryNode): The spatial memory node to add.
        """

        if location_id not in self._locations:
            top_most_similar = await self.search_for_new_poi(
                location_id=location_id,
                location_description=location_description or "",
                top_k=10,
            )
            beliefs = {}

            if not top_most_similar:
                beliefs = {"price": 0.5, "atmosphere": 0.5, "satisfaction": 0.5, "convenience": 0.5}
            else:
              # Accumulate scores from neighbors
              beliefs = {"price": 0.0, "atmosphere": 0.0, "satisfaction": 0.0, "convenience": 0.0}
              counts = 0

              for node in top_most_similar:
                  if node.price is not None:
                      beliefs["price"] += node.price
                  if node.atmosphere is not None:
                      beliefs["atmosphere"] += node.atmosphere
                  if node.satisfaction is not None:
                      beliefs["satisfaction"] += node.satisfaction
                  if node.convenience is not None:
                      beliefs["convenience"] += node.convenience
                  counts += 1

              # Calculate Average
              beliefs = {k: v / counts for k, v in beliefs.items()}
            node = SpatialMemoryNode(
                location_id=location_id,
                description=location_description or "",
                price=beliefs["price"],
                atmosphere=beliefs["atmosphere"],
                satisfaction=beliefs["satisfaction"],
                convenience=beliefs["convenience"],
                uncertainty=self._default_uncertainty,
            )
            self._locations[location_id] = node


    async def add_or_update_location(self, location_id: str, location_description: Optional[str]) -> None:
        """
        Add a spatial memory node.

        - **Args**:
            - `node` (SpatialMemoryNode): The spatial memory node to add.
        """

        if location_id not in self._locations:
            try:
              await self.add_location(location_id, location_description)
            except Exception as e:
              get_logger().error(f"Error adding location {location_id}: {e}")
              return

        if location_id in self._loc_to_doc_id:
            # Delete old embedding if it exists
            await self._vectorstore.delete_documents(
                to_delete_ids=[self._loc_to_doc_id[location_id]],
            )

        try:
          node = self._locations[location_id]

          semantic_text = f"Location {node.location_id} description: {node.description}. Price: {node.price}, Atmosphere: {node.atmosphere}, Satisfaction: {node.satisfaction}, Convenience: {node.convenience}, Uncertainty: {node.uncertainty}."

          doc_ids = await self._vectorstore.add_documents(
              documents=[semantic_text],
              extra_tags={
                  "location_id": location_id,
                  "type": "spatial",
              },
          )

          self._loc_to_doc_id[location_id] = doc_ids[0]
        except Exception as e:
          get_logger().error(f"Error adding/updating location {location_id}: {e}")


    async def update_belief_location(self, new_price: float, new_atmosphere: float, new_satisfaction: float, new_convenience: float, location_id: str) -> None:
        """
        Update the belief of a spatial memory node.

        - **Args**:
            - `location_id` (str): The ID of the location to update.
            - `new_price` (float): New price value.
            - `new_atmosphere` (float): New atmosphere value.
            - `new_satisfaction` (float): New satisfaction value.
            - `new_convenience` (float): New convenience value.
        """
        if location_id in self._locations:
            node = self._locations[location_id]

            k_gain = node.uncertainty / (node.uncertainty + self.SIGMA_OBS)

            new_price = (k_gain * new_price) + ((1 - k_gain) * node.price)
            new_atmosphere = (k_gain * new_atmosphere) + ((1 - k_gain) * node.atmosphere)
            new_satisfaction = (k_gain * new_satisfaction) + ((1 - k_gain) * node.satisfaction)
            new_convenience = (k_gain * new_convenience) + ((1 - k_gain) * node.convenience)

            # Simple averaging update
            node.price = new_price
            node.atmosphere = new_atmosphere
            node.satisfaction = new_satisfaction
            node.convenience = new_convenience

            # Decrease uncertainty
            node.uncertainty = (1 - k_gain) * node.uncertainty

            # Update the location in the dictionary
            self._locations[location_id] = node

            # Update embedding
            await self.add_or_update_location(location_id, node.description)


    async def decay_beliefs(self):
      """
      Decay the beliefs (increase uncertainty) of all spatial memory nodes. Do it at the end of each day to simulate the effect of time on memory accuracy.
      """

      for location_id, node in self._locations.items():

          if node.price != 0.5:  # Only decay if it's not already at the default value
            node.price = node.price + (self.ALPHA_DECAY * (-1 if node.price > 0.5 else 1))
          if node.atmosphere != 0.5:
            node.atmosphere = node.atmosphere + (self.ALPHA_DECAY * (-1 if node.atmosphere > 0.5 else 1))
          if node.satisfaction != 0.5:
            node.satisfaction = node.satisfaction + (self.ALPHA_DECAY * (-1 if node.satisfaction > 0.5 else 1))
          if node.convenience != 0.5:
            node.convenience = node.convenience + (self.ALPHA_DECAY * (-1 if node.convenience > 0.5 else 1))

          # Update the location in the dictionary
          self._locations[location_id] = node

          # Update embedding
          await self.add_or_update_location(location_id, node.description)


    async def retrieve_location(self, location_id: str, location_description: Optional[str]) -> Optional[SpatialMemoryNode]:
        """
        Retrieve a spatial memory node by its location ID.

        - **Args**:
            - `location_id` (str): The ID of the location to retrieve.

        - **Returns**:
            - `SpatialMemoryNode`: The spatial memory node associated with the given location ID.
        """

        try:
            return self._locations.get(
                location_id,
                await self.add_or_update_location(location_id, location_description),
            )
        except Exception as e:
            get_logger().error(f"Error retrieving location {location_id}: {e}")

    async def get_interest(self):
        """Get ratio of POIs where satisfaction > 0.5"""
        total_pois = len(self._locations)
        if total_pois == 0:
            return 0.0
        interested_pois = sum(1 for node in self._locations.values() if node.satisfaction > 0.5)
        return interested_pois / total_pois

    async def search_for_new_poi(
        self,
        location_id: str,
        location_description: str,
        top_k: int = 10,
    ) -> list[SpatialMemoryNode]:
        """
        Search spatial memory with the provided query and return formatted results.

        - **Args**:
            - `location_id` (str): The ID of the location to search for.
            - `location_description` (str): The description of the location to search for.
            - `top_k` (int, optional): Number of top relevant locations to return. Defaults to 10.

        - **Returns**:
            - `list[SpatialMemoryNode]`: List of top relevant spatial memory nodes.
        """
        query = f"Location {location_id} description: {location_description}."

        # Perform the search in the vector store
        search_results = await self._vectorstore.similarity_search(
            query=query,
            k=top_k,
            filter={"type": "spatial"},
        )

        search_results = [
            result[2]
            for result in search_results
            if result[2].get("location_id") != location_id
        ]

        # Retrieve the corresponding SpatialMemoryNode objects
        nodes = [
            self._locations[result["location_id"]]
            for result in search_results
            if result["location_id"] in self._locations
        ]

        return nodes


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
