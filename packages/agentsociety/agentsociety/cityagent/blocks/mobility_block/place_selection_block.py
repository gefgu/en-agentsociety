import math
import random

import numpy as np # type: ignore

from ....agent import AgentToolbox, Block, DotDict
from ....logger import get_logger
from ....memory import Memory


class PlaceSelectionBlock(Block):
    """
    Block for selecting destinations based on user intention.

    Implements a three-stage selection process:
    0. Select candidate neighborhoods (fallback to AOI areas)
    1. Select primary POI category (e.g., 'shopping')
    2. Select sub-category (e.g., 'bookstore')
    3. Apply gravity model to filtered POIs
    Uses LLM for decision making with fallback to random selection.

    Configurable Fields:
        search_limit: Max number of POIs to retrieve from map service
        max_areas_to_consider: Number of areas to rank for selection
        max_area_distance: Maximum distance for area consideration (meters)
    """

    name = "PlaceSelectionBlock"
    description = "Selects destinations for unknown locations (excluding home/work)"

    def __init__(
        self,
        toolbox: AgentToolbox,
        agent_memory: Memory,
        search_limit: int = 50,
        max_areas_to_consider: int = 20,
        max_area_distance: int = 50000,
    ):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )
        self.type_selection_prompt_name = "mobility_place_type_selection"
        self.second_type_selection_prompt_name = "mobility_place_second_type_selection"
        self.radius_prompt_name = "mobility_radius_selection"
        self.neighborhood_selection_prompt_name = "mobility_neighborhood_selection"
        self.area_selection_prompt_name = "mobility_aoi_area_selection"
        self.search_limit = search_limit
        self.max_areas_to_consider = max_areas_to_consider
        self.max_area_distance = max_area_distance

    async def get_recent_visit_history(self, days: int = 7):
        """Retrieve agent's recent mobility history from stream memory."""
        try:
            # Get mobility events from the last N days
            day, _= self.environment.get_datetime()
            
            mobility_events = await self.memory.stream.search(
                "location",
                topic="mobility",
                day_range=(max(day - 7, 0), day)
            )

            
            if not mobility_events:
                return "No recent visit history available."

            return mobility_events
        except Exception as e:
            get_logger().warning(
                f"PlaceSelectionBlock: Failed to retrieve visit history: {e}",
                extra={"agent_id": self.agent.id},
            )
            return "Unable to retrieve visit history."

    def _calculate_aoi_popularity(self, aoi_data):
        """Calculate area popularity based on number of POIs (more POIs = more popular)."""
        poi_count = len(aoi_data.get("poi_ids", []))
        # Use logarithmic scale to prevent extreme values
        # Normalize to 0-1 range
        if poi_count == 0:
            return 0
        popularity = min(1, math.log(poi_count + 1, 10) * 0.2)
        return popularity

    async def select_candidate_areas(self, context: DotDict, center, radius):
        """
        Stage 0: Select candidate AOI areas before POI selection.

        Returns:
            List of selected AOI IDs to filter POIs, or None if selection fails
        """
        aoi_candidates = []  # Initialize at the start
        try:
            # Get all AOIs within radius
            all_aois = self.environment.map.get_all_aois()

            # Filter by distance and calculate scores
            for aoi in all_aois:
                aoi_pos = aoi.get("position", {})
                aoi_center = (aoi_pos.get("x", 0), aoi_pos.get("y", 0))

                # Calculate distance
                distance = math.sqrt(
                    (center[0] - aoi_center[0]) ** 2 + (center[1] - aoi_center[1]) ** 2
                )

                if distance > self.max_area_distance:
                    continue

                # Calculate popularity
                popularity = self._calculate_aoi_popularity(aoi)

                # Combined score: 40% distance (inverted), 60% popularity
                # Normalize distance to 0-100 (closer = higher score)
                distance_score = max(0, 100 - (distance / self.max_area_distance * 100))
                combined_score = (0.4 * distance_score) + (0.6 * popularity * 100)

                aoi_candidates.append({
                    "id": aoi.get("id"),
                    "distance": distance,
                    "popularity": popularity,
                    "score": combined_score,
                    "poi_count": len(aoi.get("poi_ids", [])),
                })

            if not aoi_candidates:
                get_logger().warning(
                    f"PlaceSelectionBlock: No AOIs found within {self.max_area_distance}m",
                    extra={"agent_id": self.agent.id},
                )
                return None

            # Sort by combined score and take top N
            aoi_candidates.sort(key=lambda x: x["score"], reverse=True)
            top_candidates = aoi_candidates[:self.max_areas_to_consider]

            # Format for LLM
            ranked_areas_str = "\n".join([
                f"- AOI {aoi['id']}: {aoi['distance']:.0f}m away, {aoi['poi_count']} POIs, popularity={aoi['popularity']:.1f}, score={aoi['score']:.1f}"
                for aoi in top_candidates
            ])

            # Get visit history
            visit_history = await self.get_recent_visit_history()

            result = await self.execute_prompt(
                self.area_selection_prompt_name,
                {
                    "plan": context.get("plan_context", {}).get("plan", "No plan"),
                    "intention": context.get("current_step", {}).get("intention", "Unknown"),
                    "visit_history": visit_history,
                    "ranked_areas": ranked_areas_str,
                },
                func_name="select_candidate_areas",
            )

            if not result.success:
                raise RuntimeError(f"Area selection LLM failed: {result.error}")

            selected_ids = result.parsed.get("selected_area_ids", [])
            reasoning = result.parsed.get("reasoning", "No reasoning provided")

            get_logger().info(
                f"PlaceSelectionBlock: Selected {len(selected_ids)} areas: {selected_ids}. Reasoning: {reasoning}",
                extra={"agent_id": self.agent.id},
            )

            return selected_ids

        except Exception as e:
            get_logger().warning(
                f"PlaceSelectionBlock: Area selection failed: {e}, using top scored areas",
                extra={"agent_id": self.agent.id},
            )
            # Fallback: return top 5 areas by score
            if aoi_candidates:
                return [aoi["id"] for aoi in aoi_candidates[:5]]
            return None

    async def select_candidate_neighborhoods(self, context: DotDict, pois):
        """
        Stage 0: Select candidate neighborhoods before AOI fallback.

        Returns:
            Tuple[List[int], Dict[int, int]] where values are selected neighborhood IDs
            and POI->Neighborhood mapping; or None if selection fails.
        """
        try:
            all_neighborhoods = self.environment.map.get_all_neighborhoods()
            if not all_neighborhoods:
                return None

            neighborhood_candidates = {}
            poi_to_neighborhood = {}
            for poi_tuple in pois:
                poi_data = poi_tuple[0]
                poi_id = poi_data.get("id")
                poi_pos = poi_data.get("position", {})
                point = (poi_pos.get("x", 0), poi_pos.get("y", 0))
                neighborhood = self.environment.map.query_neighborhood_by_point(point)
                if neighborhood is None:
                    continue
                hood_id = neighborhood.get("id")
                if hood_id is None:
                    continue

                poi_to_neighborhood[poi_id] = hood_id
                if hood_id not in neighborhood_candidates:
                    neighborhood_candidates[hood_id] = {
                        "id": hood_id,
                        "name": neighborhood.get("name", f"Neighborhood {hood_id}"),
                        "description": neighborhood.get(
                            "description", "No description available"
                        ),
                        "poi_count": 0,
                    }
                neighborhood_candidates[hood_id]["poi_count"] += 1

            if not neighborhood_candidates:
                return None

            candidates = sorted(
                neighborhood_candidates.values(),
                key=lambda x: x["poi_count"],
                reverse=True,
            )[: self.max_areas_to_consider]

            candidate_neighborhoods = "\n".join(
                [
                    f"- Neighborhood {hood['id']} '{hood['name']}': {hood['description']} ({hood['poi_count']} matching POIs)"
                    for hood in candidates
                ]
            )

            visit_history = await self.get_recent_visit_history()
            result = await self.execute_prompt(
                self.neighborhood_selection_prompt_name,
                {
                    "plan": context.get("plan_context", {}).get("plan", "No plan"),
                    "intention": context.get("current_step", {}).get("intention", "Unknown"),
                    "visit_history": visit_history,
                    "candidate_neighborhoods": candidate_neighborhoods,
                },
                func_name="select_candidate_neighborhoods",
            )

            if not result.success:
                raise RuntimeError(f"Neighborhood selection LLM failed: {result.error}")

            selected_ids = result.parsed.get("selected_neighborhood_ids", [])
            reasoning = result.parsed.get("reasoning", "No reasoning provided")

            get_logger().info(
                f"PlaceSelectionBlock: Selected {len(selected_ids)} neighborhoods: {selected_ids}. Reasoning: {reasoning}",
                extra={"agent_id": self.agent.id},
            )
            return selected_ids, poi_to_neighborhood

        except Exception as e:
            get_logger().warning(
                f"PlaceSelectionBlock: Neighborhood selection failed: {e}",
                extra={"agent_id": self.agent.id},
            )
            return None

    async def gravity_model(self, pois):
        """
        Calculate selection probabilities for POIs using a gravity model.

        The model considers both distance decay (prefer closer locations)
        and spatial density (avoid overcrowded areas).

        Args:
            pois: List of POI tuples containing (poi_data, distance)

        Returns:
            List of tuples: (name, id, normalized_weight, distance)
            with selection probabilities based on gravity model
        """

        get_logger().info(
            f"Gravity Model: Starting with {len(pois)} POIs.",
            extra={"agent_id": self.agent.id},
        )

        # Handle empty input
        if not pois:
            return []

        epsilon = 1e-5  # Small constant to prevent division by zero
        distance_decay = 2
        pois_with_weights = []
        for poi_tuple in pois:
            try:
                # Unpack the tuple correctly
                poi_data = poi_tuple[0]  # First element is the POI dict
                distance = poi_tuple[1]  # Second element is the distance

                get_logger().debug(f"Processing type {type(poi_data)} POI: {poi_data} at distance {distance:.2f}m")

                # Get POI attributes safely
                poi_id = poi_data.get("id")
                poi_description = poi_data.get(
                    "description", poi_data.get("category", "unknown")
                )
                poi_name = poi_data.get("name", "Unknown")

                # Retrieve location beliefs from spatial memory
                node = await self.memory.spatial.retrieve_location(
                    poi_id, poi_description
                )

                if node:
                    beliefs = {
                        "price": node.price,
                        "atmosphere": node.atmosphere,
                        "convenience": node.convenience,
                        "satisfaction": node.satisfaction,
                    }
                else:
                    beliefs = {
                        "price": 0.5,
                        "atmosphere": 0.5,
                        "convenience": 0.5,
                        "satisfaction": 0.5,
                    }

                bj = (
                    beliefs["price"]
                    + beliefs["atmosphere"]
                    + beliefs["convenience"]
                    + beliefs["satisfaction"]
                ) / 4

                # Apply distance decay with belief adjustment
                adjusted_distance = distance ** (1 + (distance_decay) * (bj - 0.5))
                weight = (bj + epsilon) / (adjusted_distance + epsilon)

                pois_with_weights.append((poi_name, poi_id, weight, distance))

            except Exception as e:
                get_logger().warning(
                    f"Gravity Model: Failed to process POI: {e}",
                    extra={"agent_id": self.agent.id},
                )
                # Fallback: use default values
                try:
                    poi_data = poi_tuple[0]
                    distance = poi_tuple[1]
                    poi_id = poi_data.get("id", "unknown")
                    poi_name = poi_data.get("name", "Unknown")
                    weight = (0.5 + epsilon) / (distance + epsilon)
                    pois_with_weights.append((poi_name, poi_id, weight, distance))
                except Exception as inner_e:
                    get_logger().error(
                        f"Gravity Model: Failed to add POI to weights list: {inner_e}",
                        extra={"agent_id": self.agent.id},
                    )
                    continue

        # Normalize weights
        total_weight = sum(item[2] for item in pois_with_weights)
        if total_weight == 0:
            # Assign equal weights if all weights are zero
            pois_with_weights = [
                (item[0], item[1], 1.0 / len(pois_with_weights), item[3])
                for item in pois_with_weights
            ]
        else:
            pois_with_weights = [
                (item[0], item[1], item[2] / total_weight, item[3])
                for item in pois_with_weights
            ]

        return pois_with_weights

    async def forward(self, context: DotDict):
        """Execute the destination selection workflow"""

        # Stage 1: Select primary POI category
        poi_cate = self.environment.get_poi_cate()
        try:
            type_result = await self.execute_prompt(
                self.type_selection_prompt_name,
                {
                    "plan": context["plan_context"]["plan"],
                    "intention": context["current_step"]["intention"],
                    "poi_category": list(poi_cate.keys()),
                    "other_info": self.environment.environment.get("other_information", "None"),
                },
                func_name="forward",
            )
            if not type_result.success:
                raise RuntimeError(f"Level 1 type selection failed: {type_result.error}")
            _parsed = type_result.parsed
            # Accept "place_type", "type", or "category" as the key
            levelOneType = (_parsed.get("place_type") or _parsed.get("type") or _parsed.get("category") or "")
            if levelOneType not in poi_cate:
                # Case-insensitive / normalised match against valid keys
                _norm = levelOneType.lower().replace(" ", "_").replace("-", "_")
                levelOneType = next(
                    (k for k in poi_cate if k.lower().replace(" ", "_").replace("-", "_") == _norm),
                    None,
                ) or next(
                    (k for k in poi_cate if _norm in k.lower() or k.lower() in _norm),
                    random.choice(list(poi_cate.keys())),
                )
            sub_category = poi_cate[levelOneType]
        except Exception as e:
            get_logger().debug(f"MobilityBlock: Level 1 selection failed: {e}")
            levelOneType = random.choice(list(poi_cate.keys()))
            sub_category = poi_cate[levelOneType]

        # Stage 2: Select sub-category
        try:
            second_type_result = await self.execute_prompt(
                self.second_type_selection_prompt_name,
                {
                    "plan": context["plan_context"]["plan"],
                    "intention": context["current_step"]["intention"],
                    "poi_category": sub_category,
                    "other_info": self.environment.environment.get("other_information", "None"),
                },
                func_name="forward",
            )
            if not second_type_result.success:
                raise RuntimeError(f"Level 2 type selection failed: {second_type_result.error}")
            _parsed2 = second_type_result.parsed
            levelTwoType = (_parsed2.get("place_type") or _parsed2.get("type") or _parsed2.get("category") or "")
            if levelTwoType not in sub_category:
                _norm2 = levelTwoType.lower().replace(" ", "_").replace("-", "_")
                levelTwoType = next(
                    (v for v in sub_category if v.lower().replace(" ", "_").replace("-", "_") == _norm2),
                    None,
                ) or next(
                    (v for v in sub_category if _norm2 in v.lower() or v.lower() in _norm2),
                    random.choice(sub_category),
                )
        except Exception as e:
            get_logger().debug(f"MobilityBlock: Level 2 selection failed: {e}")
            levelTwoType = random.choice(sub_category)

        # Get travel radius from LLM
        try:
            radius_result = await self.execute_prompt(
                self.radius_prompt_name,
                {
                    "weather": self.environment.environment.get("weather", "unknown"),
                    "temperature": self.environment.environment.get("temperature", "unknown"),
                    "current_emotion": context.get("current_emotion", "unknown"),
                    "current_thought": context.get("current_thought", ""),
                    "other_information": self.environment.environment.get("other_information", "None"),
                },
                func_name="forward",
            )
            if not radius_result.success:
                raise RuntimeError(f"Radius selection failed: {radius_result.error}")
            radius = int(radius_result.parsed.get("radius", 10000))
        except Exception as e:
            get_logger().warning(f"MobilityBlock: Radius selection failed: {e}")
            radius = 10000  # Default 10km

        xy = (await self.memory.status.get("position"))["xy_position"]
        center = (xy["x"], xy["y"])

        # Query POIs with category filter
        pois = self.environment.map.query_pois(
            center=center,
            category_prefix=levelTwoType,
            radius=radius,
            limit=self.search_limit,
        )

        selected_area_ids = None
        used_neighborhood_filter = False

        if self.agent.params.simulation_mode == "citysim":
            neighborhood_selection_result = await self.select_candidate_neighborhoods(
                context, pois
            )
            if neighborhood_selection_result:
                selected_neighborhood_ids, poi_to_neighborhood = (
                    neighborhood_selection_result
                )
                filtered_pois = []
                for poi_tuple in pois:
                    poi_data = poi_tuple[0]
                    poi_id = poi_data.get("id")
                    if (
                        poi_id in poi_to_neighborhood
                        and poi_to_neighborhood[poi_id] in selected_neighborhood_ids
                    ):
                        filtered_pois.append(poi_tuple)

                if filtered_pois:
                    get_logger().info(
                        f"PlaceSelectionBlock: Filtered {len(pois)} POIs to {len(filtered_pois)} POIs in selected neighborhoods",
                        extra={"agent_id": self.agent.id},
                    )
                    pois = filtered_pois
                    used_neighborhood_filter = True
                else:
                    get_logger().warning(
                        "PlaceSelectionBlock: Neighborhood filter returned no POIs, falling back to AOI filtering",
                        extra={"agent_id": self.agent.id},
                    )

            # Fallback to AOI filtering if neighborhood selection is unavailable/empty
            if not used_neighborhood_filter:
                selected_area_ids = await self.select_candidate_areas(context, center, radius)

                # Filter POIs by selected areas (if area selection succeeded)
                if selected_area_ids:
                    filtered_pois = []
                    for poi_tuple in pois:
                        poi_data = poi_tuple[0]
                        poi_aoi_id = poi_data.get("aoi_id")
                        if poi_aoi_id in selected_area_ids:
                            filtered_pois.append(poi_tuple)

                    get_logger().info(
                        f"PlaceSelectionBlock: Filtered {len(pois)} POIs to {len(filtered_pois)} POIs in selected areas",
                        extra={"agent_id": self.agent.id},
                    )
                    pois = filtered_pois

        poi_type = "unknown"
        if pois and len(pois) > 0:
            pois = await self.gravity_model(pois)
            probabilities = [item[2] for item in pois]
            selected = np.random.choice(len(pois), p=probabilities)
            next_place = (pois[selected][0], pois[selected][1])
            poi_type = levelTwoType

            context["next_place"] = next_place
            context["next_place_type"] = poi_type
            await self.memory.status.update("pending_destination_type", poi_type)

            node_id = await self.memory.stream.add(
                topic="mobility",
                description=f"For {context['current_step']['intention']}, selected: {next_place} (type: {poi_type})",
            )
            return {
                "success": True,
                "evaluation": f"Selected destination: {next_place}",
                "poi_type": poi_type,
                "poi_id": pois[selected][1],
                "consumed_time": 5,
                "node_id": node_id,
            }
        else:
            # No POIs found - return failure instead of random selection
            get_logger().error(
                f"PlaceSelectionBlock: No POIs found for type {levelTwoType} within {radius}m. Cannot select destination. "
                f"Intention: {context['current_step']['intention']}, Radius: {radius}, "
                f"Level1: {levelOneType}, Level2: {levelTwoType}, Selected Areas: {selected_area_ids}",
                extra={"agent_id": self.agent.id},
            )
            node_id = await self.memory.stream.add(
                topic="mobility",
                description=f"Failed to find suitable destination for {context['current_step']['intention']}",
            )
            return {
                "success": False,
                "evaluation": f"No POIs found for type {levelTwoType} within {radius}m",
                "poi_type": None,
                "poi_id": None,  # Explicitly include poi_id as None for failed selections
                "consumed_time": 5,
                "node_id": node_id,
            }