from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from fastembed import SparseTextEmbedding

from ..logger import get_logger
from ..vectorstore import VectorStore


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
                beliefs = {
                    "price": 0.5,
                    "atmosphere": 0.5,
                    "satisfaction": 0.5,
                    "convenience": 0.5,
                }
            else:
                # Accumulate scores from neighbors
                beliefs = {
                    "price": 0.0,
                    "atmosphere": 0.0,
                    "satisfaction": 0.0,
                    "convenience": 0.0,
                }
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

            semantic_text = (
                f"Location {node.location_id} description: {node.description}. "
                f"Price: {node.price}, Atmosphere: {node.atmosphere}, "
                f"Satisfaction: {node.satisfaction}, Convenience: {node.convenience}, "
                f"Uncertainty: {node.uncertainty}."
            )

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

    async def update_belief_location(
        self,
        new_price: float,
        new_atmosphere: float,
        new_satisfaction: float,
        new_convenience: float,
        location_id: str,
    ) -> None:
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

    async def retrieve_location(
        self,
        location_id: str,
        location_description: Optional[str],
    ) -> Optional[SpatialMemoryNode]:
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

    async def export(self) -> list[dict]:
        """
        Export spatial memory in checkpoint-compatible format.
        """
        return [
            {
                "location_id": node.location_id,
                "description": node.description,
                "price": node.price,
                "atmosphere": node.atmosphere,
                "satisfaction": node.satisfaction,
                "convenience": node.convenience,
                "uncertainty": node.uncertainty,
            }
            for node in self._locations.values()
        ]

    async def resume(self, spatial_entries: list[dict[str, Any]]) -> None:
        """
        Restore spatial memory from checkpoint entries.
        """
        for entry in spatial_entries:
            loc_id = str(entry.get("location_id", ""))
            if not loc_id:
                continue
            self._locations[loc_id] = SpatialMemoryNode(
                location_id=loc_id,
                description=str(entry.get("description", "")),
                price=float(entry.get("price", 0.5)),
                atmosphere=float(entry.get("atmosphere", 0.5)),
                satisfaction=float(entry.get("satisfaction", 0.5)),
                convenience=float(entry.get("convenience", 0.5)),
                uncertainty=float(entry.get("uncertainty", 0.25)),
            )
