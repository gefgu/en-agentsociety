import math
import random
import time
from enum import Enum
from typing import Optional

# from ...environment.environment import TransportModeEnum
import json_repair # type: ignore
import numpy as np # type: ignore
from pycityproto.city.trip.v2.trip_pb2 import TripMode # type: ignore
from pydantic import Field # type: ignore

from ...agent import (
    AgentToolbox,
    Block,
    BlockContext,
    BlockParams,
    DotDict,
)
from ...agent.dispatcher import BlockDispatcher
from ...logger import get_logger
from ...memory import Memory
from ..sharing_params import SocietyAgentBlockOutput
from .utils import clean_json_response


class TransportModeEnum(Enum):
    WALK = "walk"
    BIKE = "bike"
    CAR = "car"
    BUS = "bus"
    SUBWAY = "subway"


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
            time_window = days * 24 * 60 * 60  # Convert days to seconds
            
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
            if self.prompt_manager is None:
                raise RuntimeError("PromptManager is not initialized")

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
            
            # Get agent state
            emotion = await self.memory.status.get("emotion", "neutral")
            thought = await self.memory.status.get("thought", "")
            household = await self.memory.status.get("household", "unknown")
            life_stage = await self.memory.status.get("life_stage", "unknown")
            big5 = await self.memory.status.get("big5", {})

            required_fields = self.prompt_manager.get_required_fields(
                self.area_selection_prompt_name
            )
            state_dict = await self.prompt_manager.build_agent_state(
                required_fields=required_fields,
                context={
                    "plan": context.get("plan_context", {}).get("plan", "No plan"),
                    "intention": context.get("current_step", {}).get("intention", "Unknown"),
                    "emotion": emotion,
                    "thought": thought,
                    "household": household,
                    "life_stage": life_stage,
                    "big5": big5,
                    "visit_history": visit_history,
                    "ranked_areas": ranked_areas_str,
                },
                memory=self.memory,
            )
            dialog = self.prompt_manager.format_prompt_to_dialog(
                self.area_selection_prompt_name, state_dict
            )

            # LLM selection
            response = await self.llm.atext_request(
                dialog,
                response_format={"type": "json_object"},
                context={
                    "block_name": self.name,
                    "func_name": "AOI Area Selection",
                    "agent_id": self.agent.id,
                },
            )
            
            result = json_repair.loads(clean_json_response(response))
            selected_ids = result.get("selected_area_ids", [])
            reasoning = result.get("reasoning", "No reasoning provided")
            
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
            if self.prompt_manager is None:
                raise RuntimeError("PromptManager is not initialized")

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
            emotion = await self.memory.status.get("emotion", "neutral")
            thought = await self.memory.status.get("thought", "")
            household = await self.memory.status.get("household", "unknown")
            life_stage = await self.memory.status.get("life_stage", "unknown")
            big5 = await self.memory.status.get("big5", {})

            required_fields = self.prompt_manager.get_required_fields(
                self.neighborhood_selection_prompt_name
            )
            state_dict = await self.prompt_manager.build_agent_state(
                required_fields=required_fields,
                context={
                    "plan": context.get("plan_context", {}).get("plan", "No plan"),
                    "intention": context.get("current_step", {}).get("intention", "Unknown"),
                    "emotion": emotion,
                    "thought": thought,
                    "household": household,
                    "life_stage": life_stage,
                    "big5": big5,
                    "visit_history": visit_history,
                    "candidate_neighborhoods": candidate_neighborhoods,
                },
                memory=self.memory,
            )
            dialog = self.prompt_manager.format_prompt_to_dialog(
                self.neighborhood_selection_prompt_name, state_dict
            )

            response = await self.llm.atext_request(
                dialog,
                response_format={"type": "json_object"},
                context={
                    "block_name": self.name,
                    "func_name": "Neighborhood Selection",
                    "agent_id": self.agent.id,
                },
            )

            result = json_repair.loads(clean_json_response(response))
            selected_ids = result.get("selected_neighborhood_ids", [])
            reasoning = result.get("reasoning", "No reasoning provided")

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
        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        # Get Big Five personality traits
        big5 = await self.memory.status.get("big5", {})

        # Get household and life stage
        household = await self.memory.status.get("household", "unknown")
        life_stage = await self.memory.status.get("life_stage", "unknown")
        hobbies = await self.memory.status.get("hobbies", [])
        hobbies_str = ", ".join(hobbies) if isinstance(hobbies, list) else str(hobbies)
        goals = await self.memory.status.get("goals", [])
        goals_str = ", ".join(goals) if isinstance(goals, list) else str(goals)

        # Get preferences
        preferences = await self.memory.status.get("preferences", {})
        leisure_preference = preferences.get("leisure_preference", "indoor")
        risk_tolerance = preferences.get("risk_tolerance", 0.5)

        # Stage 1: Select primary POI category
        poi_cate = self.environment.get_poi_cate()
        type_required_fields = self.prompt_manager.get_required_fields(
            self.type_selection_prompt_name
        )
        type_state = await self.prompt_manager.build_agent_state(
            required_fields=type_required_fields,
            context={
                "plan": context["plan_context"]["plan"],
                "intention": context["current_step"]["intention"],
                "poi_category": list(poi_cate.keys()),
                "other_info": self.environment.environment.get("other_information", "None"),
                "household": household,
                "life_stage": life_stage,
                "hobbies": hobbies_str,
                "goals": goals_str,
                "big5": big5,
                "leisure_preference": leisure_preference,
                "risk_tolerance": risk_tolerance,
            },
            memory=self.memory,
        )
        type_dialog = self.prompt_manager.format_prompt_to_dialog(
            self.type_selection_prompt_name, type_state
        )
        try:
            # LLM-based category selection
            levelOneType = await self.llm.atext_request(
                type_dialog,
                response_format={"type": "json_object"},
                context={
                    "block_name": self.name,
                    "func_name": "Level 1 Type Selection",
                    "agent_id": self.agent.id,
                },
            )
            levelOneType = json_repair.loads(clean_json_response(levelOneType))["place_type"]  # type: ignore
            sub_category = poi_cate[levelOneType]
        except Exception as e:
            get_logger().warning(f"MobilityBlock: Level 1 selection failed: {e}")
            levelOneType = random.choice(list(poi_cate.keys()))
            sub_category = poi_cate[levelOneType]

        # Stage 2: Select sub-category
        try:
            second_type_required_fields = self.prompt_manager.get_required_fields(
                self.second_type_selection_prompt_name
            )
            second_type_state = await self.prompt_manager.build_agent_state(
                required_fields=second_type_required_fields,
                context={
                    "plan": context["plan_context"]["plan"],
                    "intention": context["current_step"]["intention"],
                    "poi_category": sub_category,
                    "other_info": self.environment.environment.get("other_information", "None"),
                    "household": household,
                    "life_stage": life_stage,
                    "hobbies": hobbies_str,
                    "goals": goals_str,
                    "big5": big5,
                    "leisure_preference": leisure_preference,
                    "risk_tolerance": risk_tolerance,
                },
                memory=self.memory,
            )
            second_type_dialog = self.prompt_manager.format_prompt_to_dialog(
                self.second_type_selection_prompt_name, second_type_state
            )
            levelTwoType = await self.llm.atext_request(
                second_type_dialog,
                response_format={"type": "json_object"},
                context={
                    "block_name": self.name,
                    "func_name": "Level 2 Type Selection",
                    "agent_id": self.agent.id,
                },
            )
            levelTwoType = json_repair.loads(clean_json_response(levelTwoType))["place_type"]  # type: ignore
        except Exception as e:
            get_logger().warning(f"MobilityBlock: Level 2 selection failed: {e}")
            levelTwoType = random.choice(sub_category)

        # Get travel radius from LLM
        try:
            radius_required_fields = self.prompt_manager.get_required_fields(
                self.radius_prompt_name
            )
            radius_state = await self.prompt_manager.build_agent_state(
                required_fields=radius_required_fields,
                context={
                    "weather": self.environment.environment.get("weather", "unknown"),
                    "temperature": self.environment.environment.get("temperature", "unknown"),
                    "current_emotion": context.get("current_emotion", "unknown"),
                    "current_thought": context.get("current_thought", ""),
                    "other_information": self.environment.environment.get("other_information", "None"),
                    "household": household,
                    "life_stage": life_stage,
                    "hobbies": hobbies_str,
                    "big5": big5,
                    "risk_tolerance": risk_tolerance,
                },
                memory=self.memory,
            )
            radius_dialog = self.prompt_manager.format_prompt_to_dialog(
                self.radius_prompt_name, radius_state
            )
            radius = await self.llm.atext_request(
                radius_dialog,
                response_format={"type": "json_object"},
                context={
                    "block_name": self.name,
                    "func_name": "Radius Selection",
                    "agent_id": self.agent.id,
                },
            )
            radius = int(json_repair.loads(clean_json_response(radius))["radius"])  # type: ignore

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


class MoveBlock(Block):
    """Block for executing mobility operations (home/work/other)"""

    name = "MoveBlock"
    description = "Executes mobility operations between locations"

    def __init__(
        self,
        toolbox: AgentToolbox,
        agent_memory: Memory,
        place_selection_block: "PlaceSelectionBlock",
        transport_mode_block: "TransportModeSelectionBlock",
    ):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )
        self.place_analysis_prompt_name = "mobility_place_analysis"
        self.place_selection_block = place_selection_block
        self.transport_mode_block = transport_mode_block

    async def _execute_movement(
        self, context: DotDict, target_place_id: any, description: str, destination_type: str = None, is_poi: bool = False # type: ignore
    ):
        db_tool = self.toolbox.get_tool("db_actor")
        
        context["to_place"] = target_place_id
        context["destination_type"] = destination_type
        context["is_poi"] = is_poi
        transport_result = await self.transport_mode_block.forward(context)
        selected_mode = transport_result.get("transport_mode", "car")

        node_id = await self.memory.stream.add(
            topic="mobility",
            description=description,
        )
        trip_mode = TripMode.TRIP_MODE_DRIVE_ONLY
        # UNCOMMENT TO ALLOW OTHER MODES WHEN THEY ARE FIXED.
        # if selected_mode == "walk": 
        #     trip_mode = TripMode.TRIP_MODE_WALK_ONLY
        # elif selected_mode == "bike":
        #     trip_mode = TripMode.TRIP_MODE_BIKE_WALK

        try:
            await self.environment.set_aoi_schedules(
                person_id=self.agent.id,
                target_positions=target_place_id,
                modes=[trip_mode],
            )
        except Exception as e:
            try:
                get_logger().warning(
                    f"MoveBlock: Failed to set aoi schedules with transport mode {selected_mode}: {e}. Trying with car",
                    extra={"agent_id": self.agent.id},
                )
                await self.environment.set_aoi_schedules(
                    person_id=self.agent.id,
                    target_positions=target_place_id,
                    modes=[TripMode.TRIP_MODE_DRIVE_ONLY],
                )
                selected_mode = "car"
            except Exception as e:
                get_logger().error(
                    f"MoveBlock: Failed to set aoi schedules with car mode as fallback: {e}",
                    extra={"agent_id": self.agent.id},
                )
                return {
                    "success": False,
                    "evaluation": f"Failed to move to {target_place_id} using any transport mode",
                    "to_place": target_place_id,
                    "description": description,
                    "destination_type": destination_type,
                    "transport_mode": None,
                    "consumed_time": 0,
                    "node_id": node_id,
                    "is_poi": is_poi,
                }

        if db_tool:
            db_tool.get_tool().insert_user_transport_type_record.remote(
                timestamp=time.time(),
                agent_id=self.agent.id,
                transport_type=selected_mode,
            )

        # Build result with core movement data
        result = {
            "success": True,
            "evaluation": f"Successfully moved to {target_place_id} using {selected_mode}",
            "to_place": target_place_id,
            "description": description,
            "destination_type": destination_type,
            "transport_mode": selected_mode,
            "consumed_time": 45,
            "node_id": node_id,
            "is_poi": is_poi,
        }
        
        # Preserve mobility context fields (from PlaceSelectionBlock) for needs block
        mobility_fields = ["poi_id", "next_place", "next_place_type", "poi_type", "is_poi"]
        for field in mobility_fields:
            if field in context:
                result[field] = context[field]


        get_logger().debug(
            f"MoveBlock: Movement execution result: {result}",
            extra={"agent_id": self.agent.id},
        )
        
        return result

    async def forward(self, context: DotDict):
        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        # Get Big Five personality traits
        big5 = await self.memory.status.get("big5", {})
        poi_id = None
        place_selection_result = None  # Store PlaceSelectionBlock result for later merging

        # Get household and life stage
        household = await self.memory.status.get("household", "unknown")
        life_stage = await self.memory.status.get("life_stage", "unknown")
        hobbies = await self.memory.status.get("hobbies", [])
        hobbies_str = ", ".join(hobbies) if isinstance(hobbies, list) else str(hobbies)
        goals = await self.memory.status.get("goals", [])
        goals_str = ", ".join(goals) if isinstance(goals, list) else str(goals)

        # Get preferences
        preferences = await self.memory.status.get("preferences", {})
        leisure_preference = preferences.get("leisure_preference", "indoor")
        risk_tolerance = preferences.get("risk_tolerance", 0.5)

        place_knowledge = await self.memory.status.get("location_knowledge")
        known_places = list(place_knowledge.keys())
        places = ["home", "workplace"] + known_places + ["other"]

        # 1. LLM Decision
        required_fields = self.prompt_manager.get_required_fields(
            self.place_analysis_prompt_name
        )
        state_dict = await self.prompt_manager.build_agent_state(
            required_fields=required_fields,
            context={
                "plan": context["plan_context"]["plan"],
                "intention": context["current_step"]["intention"],
                "place_list": places,
                "other_info": self.environment.environment.get("other_information", "None"),
                "household": household,
                "life_stage": life_stage,
                "hobbies": hobbies_str,
                "goals": goals_str,
                "big5": big5,
                "leisure_preference": leisure_preference,
                "risk_tolerance": risk_tolerance,
            },
            memory=self.memory,
        )
        dialog = self.prompt_manager.format_prompt_to_dialog(
            self.place_analysis_prompt_name, state_dict
        )

        response = await self.llm.atext_request(
            dialog,
            response_format={"type": "json_object"},
            context={
                "block_name": self.name,
                "func_name": "Place Analysis",
                "agent_id": self.agent.id,
            },
        )

        try:
            response = clean_json_response(response)
            response_type = json_repair.loads(response)["place_type"]  # type: ignore
        except Exception:
            get_logger().warning(
                f"MobilityBlock: Place Analysis: wrong type of place, raw response: {response}",
                extra={"agent_id": self.agent.id},
            )
            response_type = "home"

        # 2. Resolve Destination Variables
        target_aoi_id = None
        destination_type = None
        description_str = None

        if response_type == "home":
            home_data = await self.memory.status.get("home")
            target_aoi_id = home_data["aoi_position"]["aoi_id"]
            destination_type = "home"
            description_str = "I returned home"

        elif response_type == "workplace":
            work_data = await self.memory.status.get("work")
            target_aoi_id = work_data["aoi_position"]["aoi_id"]
            destination_type = "workplace"
            description_str = "I went to my workplace"

        elif response_type in known_places:
            place_info = place_knowledge[response_type]
            target_aoi_id = place_info["id"]
            # Try to get type from knowledge, fallback to known_places key or unknown
            destination_type = place_info.get("type", "unknown")
            description_str = f"I went to {response_type}"

        else:
            # Handle "other" places
            next_place = context.get("next_place", None)
            # 2a. If not provided, try Place Selection Block
            if next_place is None:
                get_logger().info(
                    f"MobilityBlock (Agent {self.agent.id}): No next_place provided, calling PlaceSelectionBlock",
                    extra={"agent_id": self.agent.id},
                )
                place_selection_result = await self.place_selection_block.forward(
                    context
                )
                if place_selection_result["success"]:
                    next_place = context.get("next_place", None)
                    # Store poi_id from place selection result
                    poi_id = place_selection_result.get("poi_id")

            # 2b. If still None, pick Random
            if next_place is None:
                aois = self.environment.map.get_all_aois()
                while True:
                    r_aoi = random.choice(aois)
                    if len(r_aoi["poi_ids"]) > 0:
                        r_poi = random.choice(r_aoi["poi_ids"])
                        break
                poi = self.environment.map.get_poi(r_poi)
                poi_cat = poi.get("category", "unknown")
                # Structure: (Name, AOI_ID, Type)
                next_place = (poi["name"], poi["aoi_id"], poi_cat)
                poi_id = r_poi
                get_logger().warning(
                    f"MobilityBlock (Agent {self.agent.id}): Move to other place: no next_place provided, randomly selected {next_place}. POI ID: {poi_id}, AOI ID: {r_aoi['id']}",
                    extra={"agent_id": self.agent.id},
                )

            # 2c. Unpack tuple
            # Assumes next_place is (Name, AOI_ID, Type) based on your original random logic
            place_name = next_place[0]
            target_aoi_id = next_place[1]
            # Determine type: check tuple index 2, context, or fallback
            if len(next_place) > 2:
                destination_type = next_place[2]
            else:
                destination_type = context.get("next_place_type", "unknown")

            description_str = f"I went to {place_name}"

        # 3. Update State & Check Position
        await self.memory.status.update("pending_destination_type", destination_type)
        now_place = await self.memory.status.get("position")
        # Add memory stream item
        node_id = await self.memory.stream.add(
            topic="mobility",
            description=description_str,
        )

        # Check if we are already there
        if (
            "aoi_position" in now_place
            and now_place["aoi_position"]["aoi_id"] == target_aoi_id
        ):
            result = {
                "success": True,
                "evaluation": f"Successfully reached destination (already at {target_aoi_id})",
                "to_place": target_aoi_id,
                "consumed_time": 0,
                "node_id": node_id,
                "poi_id": poi_id,
            }
            # Preserve mobility context fields
            mobility_fields = ["poi_id", "next_place", "next_place_type", "poi_type"]
            for field in mobility_fields:
                if field in context:
                    result[field] = context[field]
                    get_logger().debug(
                        f"MoveBlock: Preserved context field {field} with value {context[field]} in movement result",
                        extra={"agent_id": self.agent.id},
                    )
            
            # Merge place_selection_result if it exists
            if place_selection_result and place_selection_result.get("success"):
                for key in ["poi_id", "poi_type", "next_place_type"]:
                    if key in place_selection_result and place_selection_result[key] is not None:
                        result[key] = place_selection_result[key]
                        get_logger().debug(
                            f"MoveBlock: Merged PlaceSelectionBlock field {key} with value {place_selection_result[key]}",
                            extra={"agent_id": self.agent.id},
                        )

            get_logger().debug(
                f"MoveBlock: Final result after merging PlaceSelectionBlock result: {result}",
                extra={"agent_id": self.agent.id},
            )
            return result

        # 4. Execute Movement
        number_poi_visited = await self.memory.status.get("number_poi_visited")
        number_poi_visited += 1
        await self.memory.status.update("number_poi_visited", number_poi_visited)

        # Execute movement and merge place_selection_result if it exists
        is_poi = poi_id is not None
        movement_result = await self._execute_movement(context, target_aoi_id, description_str, destination_type, is_poi)
        if is_poi:
            movement_result["poi_id"] = poi_id
            movement_result["is_poi"] = True
        
        # Merge place_selection_result into movement_result
        if place_selection_result and place_selection_result.get("success"):
            for key in ["poi_id", "poi_type", "next_place_type", "is_poi"]:
                if key in place_selection_result and place_selection_result[key] is not None:
                    movement_result[key] = place_selection_result[key]
                    get_logger().debug(
                        f"MoveBlock: Merged {key} from PlaceSelectionBlock into movement result: {movement_result[key]}",
                        extra={"agent_id": self.agent.id},
                    )


        get_logger().debug(
            f"MoveBlock: Final movement result after merging PlaceSelectionBlock result: {movement_result}",
            extra={"agent_id": self.agent.id},
        )
        
        return movement_result


class TransportModeSelectionBlock(Block):
    """
    Block for selecting transport mode based on utility approximation.

    Formula: v* = arg max_v U(d, t, m, w, T, p, theta, V)
    Where:
      d: distance
      t: time
      m: month
      w: weather
      T: temperature
      p: persona
      V: available vehicles
    """

    name = "TransportModeSelectionBlock"
    description = "Selects the transport mode for a trip"
    NeedAgent = True

    def __init__(self, toolbox: AgentToolbox, agent_memory: Memory):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )
        self.mode_selection_prompt_name = "mobility_transport_mode_selection"
        self.transportation_modes = [m.value for m in TransportModeEnum]

    def _calculate_distance(self, start_xy, end_xy):
        """Calculates Euclidean distance in meters."""
        return math.sqrt(
            (start_xy["x"] - end_xy["x"]) ** 2 + (start_xy["y"] - end_xy["y"]) ** 2
        )

    async def forward(self, context: DotDict):
        """Select transport mode based on context"""
        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        current_pos = await self.memory.status.get("position")
        start_xy = current_pos["xy_position"]
        target_id = (
            context.get("to_place") or context.get("next_place", [None, None])[1]
        )

        if target_id:
            try:
                target_obj = self.environment.map.get_poi(target_id)
            except KeyError:
                target_obj = self.environment.map.get_aoi(target_id)
            if target_obj:
                target_xy = target_obj.get("position", {"x": 0, "y": 0})
                distance = int(self._calculate_distance(start_xy, target_xy))
            else:
                get_logger().warning(
                    f"TransportModeSelectionBlock (Agent {self.agent.id}): Target ID {target_id} not found in map."
                )
                distance = 0
        else:
            get_logger().warning(
                f"TransportModeSelectionBlock (Agent {self.agent.id}): No target position provided. Context {context}"
            )
            distance = 0

        sim_time = self.environment.get_datetime(True)
        month = "Current Month"  # TODO.
        weather = self.environment.environment.get("weather", "Don't know")
        temperature = self.environment.environment.get("temperature", "Don't know")

        name = await self.memory.status.get("name")
        age = await self.memory.status.get("age")
        gender = await self.memory.status.get("gender")
        occupation = await self.memory.status.get("occupation")
        personality = await self.memory.status.get("personality")

        # Construct the persona string manually
        persona = f"Name: {name}, Age: {age}, Gender: {gender}, Occupation: {occupation}, Personality: {personality}"
        # ------------------------
        emotion = await self.memory.status.get("emotion")

        # Get Big Five personality traits
        big5 = await self.memory.status.get("big5", {})

        # Get household and life stage
        household = await self.memory.status.get("household", "unknown")
        life_stage = await self.memory.status.get("life_stage", "unknown")
        hobbies = await self.memory.status.get("hobbies", [])
        hobbies_str = ", ".join(hobbies) if isinstance(hobbies, list) else str(hobbies)

        # Get preferences
        preferences = await self.memory.status.get("preferences", {})
        risk_tolerance = preferences.get("risk_tolerance", 0.5)

        available_modes_list = self.transportation_modes

        required_fields = self.prompt_manager.get_required_fields(
            self.mode_selection_prompt_name
        )
        state_dict = await self.prompt_manager.build_agent_state(
            required_fields=required_fields,
            context={
                "distance": distance,
                "time": sim_time,
                "month": month,
                "weather": weather,
                "temperature": temperature,
                "persona": persona,
                "emotion": emotion,
                "available_modes": ", ".join(available_modes_list),
                "household": household,
                "life_stage": life_stage,
                "hobbies": hobbies_str,
                "big5": big5,
                "risk_tolerance": risk_tolerance,
            },
            memory=self.memory,
        )
        dialog = self.prompt_manager.format_prompt_to_dialog(
            self.mode_selection_prompt_name, state_dict
        )

        try:
            response = await self.llm.atext_request(
                dialog,
                response_format={"type": "json_object"},
                context={
                    "block_name": self.name,
                    "func_name": "forward",
                    "agent_id": self.agent.id,
                },
            )
            response = clean_json_response(response)
            response = json_repair.loads(response)
            selected_mode_str = response.get("mode", "car")
            reason = response.get("reason", "No reason provided.")

        except Exception as e:
            get_logger().warning(
                f"TransportModeSelectionBlock (Agent {self.agent.id}): Mode selection failed: {e}",
                extra={"agent_id": self.agent.id},
            )
            selected_mode_str = TransportModeEnum.CAR.value
            reason = "CAR selected due to LLM failure."

        node_id = await self.memory.stream.add(
            topic="transport_mode_selection",
            description=f"Selected transport mode: {selected_mode_str}. Reason: {reason}",
        )

        get_logger().info(
            f"TransportModeSelectionBlock (Agent {self.agent.id}): Selected transport mode: {selected_mode_str}. Reason: {reason}",
            extra={"agent_id": self.agent.id},
        )

        # await self.environment.set_person_vehicle_attribute(
        #     person_id=self.agent.id,
        #     transport_mode=TransportModeEnum(selected_mode_str),
        # ) # TODO

        return {
            "success": True,
            "evaluation": f"Selected transport mode: {selected_mode_str}",
            "transport_mode": selected_mode_str,
            "consumed_time": 2,
            "node_id": node_id,
        }


class MobilityNoneBlock(Block):
    """
    MobilityNoneBlock
    """

    name = "MobilityNoneBlock"
    description = "Handles other mobility operations"

    def __init__(self, toolbox: AgentToolbox, agent_memory: Memory):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )

    async def forward(self, context: DotDict):
        """Log completion without action"""
        node_id = await self.memory.stream.add(
            topic="mobility",
            description=f"I finished {context['current_step']['intention']}",
        )
        return {
            "success": True,
            "evaluation": f"Finished executing {context['current_step']['intention']}",
            "consumed_time": 0,
            "node_id": node_id,
        }


class MobilityBlockParams(BlockParams):
    # PlaceSelection
    radius_prompt: str = Field(
        default="mobility_radius_selection",
        description="Legacy config field kept for compatibility; PromptManager now controls radius prompt resolution",
    )
    search_limit: int = Field(
        default=50, description="Number of POIs to retrieve from map service"
    )
    max_areas_to_consider: int = Field(
        default=20,
        description="Number of AOI areas to rank for macro-level selection",
    )
    max_area_distance: int = Field(
        default=50000,
        description="Maximum distance (meters) for AOI area consideration",
    )


class MobilityBlockContext(BlockContext):
    next_place: Optional[tuple[str, int]] = Field(
        default=None, description="The next place to go"
    )


class MobilityBlock(Block):
    """
    Main mobility coordination block.
    """

    ParamsType = MobilityBlockParams
    OutputType = SocietyAgentBlockOutput
    ContextType = MobilityBlockContext
    name = "MobilityBlock"
    description = (
        "Used for moving like go to work, go to home, go to other places, etc."
    )
    actions = {
        "place_selection": "Support the place selection action",
        "move": "Support the move action",
        "transport_mode_selection": "Support the transport mode selection action",
        "mobility_none": "Support other mobility operations",
    }
    NeedAgent = True

    def __init__(
        self,
        toolbox: AgentToolbox,
        agent_memory: Memory,
        block_params: Optional[MobilityBlockParams] = None,
    ):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
            block_params=block_params,
        )
        # initialize all blocks
        self.place_selection_block = PlaceSelectionBlock(
            toolbox,
            agent_memory,
            search_limit=self.params.search_limit,
            max_areas_to_consider=self.params.max_areas_to_consider,
            max_area_distance=self.params.max_area_distance,
        )
        self.transport_mode_block = TransportModeSelectionBlock(toolbox, agent_memory)

        self.move_block = MoveBlock(
            toolbox,
            agent_memory,
            place_selection_block=self.place_selection_block,
            transport_mode_block=self.transport_mode_block,
        )
        self.mobility_none_block = MobilityNoneBlock(toolbox, agent_memory)
        self.trigger_time = 0  # Block invocation counter
        self.token_consumption = 0  # LLM token tracker

        # Initialize block routing system
        self.dispatcher = BlockDispatcher(self._toolbox, agent_memory)
        # register all blocks

        blocks = [
            self.place_selection_block,
            self.move_block,
            self.mobility_none_block,
        ]
        # blocks.append(self.transport_mode_block) - Don't need to dispatch to transport mode block directly, it's called internally by move block

        self.dispatcher.register_blocks(blocks)

    def set_agent(self, agent: any) -> None:
        """Associate the block and its sub-blocks with a specific agent.

        Args:
            agent: The agent instance to associate with.
        """
        super().set_agent(agent)
        self.place_selection_block.set_agent(agent)
        self.move_block.set_agent(agent)
        self.mobility_none_block.set_agent(agent)
        self.transport_mode_block.set_agent(agent)

    async def forward(self, agent_context: DotDict) -> SocietyAgentBlockOutput:
        """Main entry point - delegates to sub-blocks"""
        self.trigger_time += 1
        context = agent_context | self.context
        # Select the appropriate sub-block using dispatcher
        selected_block = await self.dispatcher.dispatch(context)
        if selected_block is None:
            return self.OutputType(
                success=False,
                evaluation=f"Failed to {agent_context['current_step']['intention']}",
                consumed_time=random.randint(1, 30),
                node_id=None,
            )
        # Execute the selected sub-block and get the result
        result = await selected_block.forward(context)  #

        return self.OutputType(**result)
