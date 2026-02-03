import math
import random
import time
from enum import Enum
from typing import Optional

# from ...environment.environment import TransportModeEnum
import json_repair
import numpy as np
from pycityproto.city.trip.v2.trip_pb2 import TripMode
from pydantic import Field

from ...agent import (
    AgentToolbox,
    Block,
    BlockContext,
    BlockParams,
    DotDict,
    FormatPrompt,
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


# Prompt templates for LLM interactions
PLACE_TYPE_SELECTION_PROMPT = """
As an intelligent decision system, please determine the type of place the user needs to visit based on their input requirement.
User Plan: {plan}
User requirement: {intention}
Other information: 
-------------------------
{other_info}
-------------------------
Your output must be a single selection from {poi_category} without any additional text or explanation.

Please response in json format (Do not return any other text), example:
{{
    "place_type": "shopping"
}}
"""

PLACE_SECOND_TYPE_SELECTION_PROMPT = """
As an intelligent decision system, please determine the type of place the user needs to visit based on their input requirement.
User Plan: {plan}
User requirement: {intention}
Other information: 
-------------------------
{other_info}
-------------------------

Your output must be a single selection from {poi_category} without any additional text or explanation.

Please response in json format (Do not return any other text), example:
{{
    "place_type": "shopping"
}}
"""

PLACE_ANALYSIS_PROMPT = """
As an intelligent analysis system, please determine the type of place the user needs to visit based on their input requirement.
User Plan: {plan}
User requirement: {intention}
Other information: 
-------------------------
{other_info}
-------------------------

Your output must be a single selection from {place_list} without any additional text or explanation.

Please response in json format (Do not return any other text), example:
{{
    "place_type": "home"
}}
"""

RADIUS_PROMPT = """As an intelligent decision system, please determine the maximum travel radius (in meters) based on the current emotional state.

Current weather: ${context.weather}
Current temperature: ${context.temperature}
Your current emotion: ${context.current_emotion}
Your current thought: ${context.current_thought}
Other information: 
-------------------------
${context.other_information}
-------------------------

Please analyze how these emotions would affect travel willingness and return only a single integer number between 3000-200000 representing the maximum travel radius in meters. A more positive emotional state generally leads to greater willingness to travel further.

Please response in json format (Do not return any other text), example:
{{
    "radius": 10000
}}
"""

TRANSPORT_MODE_SELECTION_PROMPT = """
As an intelligent transport decision system, please select the most appropriate transport mode for the user based on the current context and their persona.
You are approximating a utility function where you maximize the user's comfort, efficiency, and preference.

Context:
- Trip Distance: {distance} meters
- Current Time: {time}
- Month: {month}
- Weather: {weather}
- Temperature: {temperature}
- User Persona: {persona}
- User Current Emotion/Thought: {emotion}

Available Transport Modes:
{available_modes}

Please analyze the utility of each mode given the weather (e.g., avoid walking in heavy rain), distance (e.g., avoid walking for >2km), and persona.
Select one mode and provide a brief reason.

Please response in json format (Do not return any other text), example:
{{
    "mode": "TRIP_MODE_DRIVE_ONLY",
    "reason": "Given the heavy rain and the 5km distance, driving is the most comfortable option despite the traffic."
}}
"""


def gravity_model(pois):
    """
    Calculate selection probabilities for POIs using a gravity model.

    The model considers both distance decay (prefer closer locations)
    and spatial density (avoid overcrowded areas). Distances are grouped
    into 1km bins up to 10km, with POIs beyond 10km in a 'more' category.

    Args:
        pois: List of POI tuples containing (poi_data, distance)

    Returns:
        List of tuples: (name, id, normalized_weight, distance)
        with selection probabilities based on gravity model
    """
    # Handle empty input
    if not pois:
        return []
    # Initialize distance bins
    pois_Dis = {f"{d}k": [] for d in range(1, 11)}
    pois_Dis["more"] = []

    # Categorize POIs into distance bins
    for poi in pois:
        classified = False
        for d in range(1, 11):
            if (d - 1) * 1000 <= poi[1] < d * 1000:
                pois_Dis[f"{d}k"].append(poi)
                classified = True
                break
        if not classified:
            pois_Dis["more"].append(poi)

    res = []
    distanceProb = []
    # Calculate weights for each POI
    for poi in pois:
        classified = False
        for d in range(1, 11):
            if (d - 1) * 1000 <= poi[1] < d * 1000:
                n = len(pois_Dis[f"{d}k"])
                # Calculate ring area between (d-1)km and d km
                S = math.pi * ((d * 1000) ** 2 - ((d - 1) * 1000) ** 2)
                density = n / S  # POIs per square meter
                distance = max(poi[1], 1)  # Avoid division by zero

                # Inverse square distance decay combined with density
                weight = density / (distance**2)
                res.append((poi[0]["name"], poi[0]["id"], weight, distance))
                distanceProb.append(1 / math.sqrt(distance))
                classified = True
                break
        # Handle POIs beyond 10km that weren't classified
        if not classified:
            n = len(pois_Dis["more"])
            # Use a large ring area for POIs beyond 10km
            S = math.pi * (20000**2 - 10000**2)  # Assume 10-20km ring
            density = n / S
            distance = max(poi[1], 1)
            weight = density / (distance**2)
            res.append((poi[0]["name"], poi[0]["id"], weight, distance))
            distanceProb.append(1 / math.sqrt(distance))

    # Handle case with no results
    if len(res) == 0:
        return []

    # Normalize probabilities and sample
    distanceProb = np.array(distanceProb)
    distanceProb /= distanceProb.sum()

    # Adjust sample size to not exceed available POIs
    sample_size = min(50, len(res))
    # Randomly sample candidates weighted by distance probabilities
    sample_indices = np.random.choice(
        len(res), size=sample_size, p=distanceProb, replace=False
    )
    sampled_pois = [res[i] for i in sample_indices]

    # Normalize weights for final selection
    total_weight = sum(item[2] for item in sampled_pois)
    # Handle case where total_weight is zero
    if total_weight == 0:
        # Assign equal weights if all weights are zero
        return [
            (item[0], item[1], 1.0 / len(sampled_pois), item[3])
            for item in sampled_pois
        ]
    return [
        (item[0], item[1], item[2] / total_weight, item[3]) for item in sampled_pois
    ]


class PlaceSelectionBlock(Block):
    """
    Block for selecting destinations based on user intention.

    Implements a two-stage selection process:
    1. Select primary POI category (e.g., 'shopping')
    2. Select sub-category (e.g., 'bookstore')
    Uses LLM for decision making with fallback to random selection.

    Configurable Fields:
        search_limit: Max number of POIs to retrieve from map service
    """

    name = "PlaceSelectionBlock"
    description = "Selects destinations for unknown locations (excluding home/work)"

    def __init__(
        self,
        toolbox: AgentToolbox,
        agent_memory: Memory,
        search_limit: int = 50,
    ):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )
        self.typeSelectionPrompt = FormatPrompt(PLACE_TYPE_SELECTION_PROMPT)
        self.secondTypeSelectionPrompt = FormatPrompt(
            PLACE_SECOND_TYPE_SELECTION_PROMPT
        )
        self.radiusPrompt = FormatPrompt(
            RADIUS_PROMPT,
            memory=agent_memory,
        )
        self.search_limit = search_limit  # Default config value

    async def forward(self, context: DotDict):
        """Execute the destination selection workflow"""
        # Stage 1: Select primary POI category
        poi_cate = self.environment.get_poi_cate()
        await self.typeSelectionPrompt.format(
            plan=context["plan_context"]["plan"],
            intention=context["current_step"]["intention"],
            poi_category=list(poi_cate.keys()),
            other_info=self.environment.environment.get("other_information", "None"),
        )
        try:
            # LLM-based category selection
            levelOneType = await self.llm.atext_request(
                self.typeSelectionPrompt.to_dialog(),
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
            await self.secondTypeSelectionPrompt.format(
                plan=context["plan_context"]["plan"],
                intention=context["current_step"]["intention"],
                poi_category=sub_category,
                other_info=self.environment.environment.get(
                    "other_information", "None"
                ),
            )
            levelTwoType = await self.llm.atext_request(
                self.secondTypeSelectionPrompt.to_dialog(),
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
            await self.radiusPrompt.format(context=context)
            radius = await self.llm.atext_request(
                self.radiusPrompt.to_dialog(),
                response_format={"type": "json_object"},
                context={
                    "block_name": self.name,
                    "func_name": "Radius Selection",
                    "agent_id": self.agent.id,
                },
            )
            radius = int(json_repair.loads(radius)["radius"])  # type: ignore

        except Exception as e:
            get_logger().warning(f"MobilityBlock: Radius selection failed: {e}")
            radius = 10000  # Default 10km

        # Query and select POI
        xy = (await self.memory.status.get("position"))["xy_position"]
        center = (xy["x"], xy["y"])
        pois = self.environment.map.query_pois(
            center=center,
            category_prefix=levelTwoType,
            radius=radius,
            limit=self.search_limit,
        )

        poi_type = "unknown"
        if pois and len(pois) > 0:
            pois = gravity_model(pois)
            probabilities = [item[2] for item in pois]
            selected = np.random.choice(len(pois), p=probabilities)
            next_place = (pois[selected][0], pois[selected][1])
            poi_type = levelTwoType
        else:  # Fallback random selection
            all_pois = self.environment.map.get_all_pois()
            next_place = random.choice(all_pois)
            poi_type = next_place.get("category", "unknown")
            next_place = (next_place["name"], next_place["id"], poi_type)
            get_logger().warning(
                f"MobilityBlock: No POIs found for type {levelTwoType} within {radius}m. Randomly selected {next_place}",
                extra={"agent_id": self.agent.id},
            )

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
        enforce_place_selection=False,
        enforce_transport_mode_selection=False,
        place_selection_block: "PlaceSelectionBlock" = None,
        transport_mode_block: "TransportModeSelectionBlock" = None,
    ):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )
        self.placeAnalysisPrompt = FormatPrompt(PLACE_ANALYSIS_PROMPT)
        self.place_selection_block = place_selection_block
        self.transport_mode_block = transport_mode_block
        self.enforce_place_selection = enforce_place_selection
        self.enforce_transport_mode_selection = enforce_transport_mode_selection

    async def _execute_movement(
        self, context: DotDict, target_place_id: any, description: str
    ):
        db_tool = self.toolbox.get_tool("db_actor")
        if self.enforce_transport_mode_selection:
            context["to_place"] = target_place_id

            transport_result = await self.transport_mode_block.forward(context)
            selected_mode = transport_result.get("transport_mode", "car")

            node_id = await self.memory.stream.add(
                topic="mobility",
                description=description,
            )
            trip_mode = TripMode.TRIP_MODE_DRIVE_ONLY
            if selected_mode == "walk":
                trip_mode = TripMode.TRIP_MODE_WALK_ONLY
            elif selected_mode == "bike":
                trip_mode = TripMode.TRIP_MODE_BIKE_WALK

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
                        "transport_mode": None,
                        "consumed_time": 0,
                        "node_id": node_id,
                    }

            if db_tool:
                db_tool.get_tool().insert_user_transport_type_record.remote(
                    timestamp=time.time(),
                    agent_id=self.agent.id,
                    transport_type=selected_mode,
                )

            return {
                "success": True,
                "evaluation": f"Successfully moved to {target_place_id} using {selected_mode}",
                "to_place": target_place_id,
                "transport_mode": selected_mode,
                "consumed_time": 45,
                "node_id": node_id,
            }
        else:
            try:
                await self.environment.set_aoi_schedules(
                    person_id=self.agent.id,
                    target_positions=target_place_id,
                    # modes=[get_random_transport_mode()],
                )
            except Exception as e:
                get_logger().error(
                    f"MoveBlock: Failed to set aoi schedules: {e}",
                    extra={"agent_id": self.agent.id},
                )
                return {
                    "success": False,
                    "evaluation": f"Failed to move to {target_place_id}",
                    "to_place": target_place_id,
                    "transport_mode": None,
                    "consumed_time": 0,
                    "node_id": None,
                }
            node_id = await self.memory.stream.add(
                topic="mobility",
                description=description,
            )
            return {
                "success": True,
                "evaluation": f"Successfully moved to {target_place_id}",
                "to_place": target_place_id,
                "transport_mode": None,
                "consumed_time": 45,
                "node_id": node_id,
            }

    async def forward(self, context: DotDict):
        agent_id = await self.memory.status.get("id")
        place_knowledge = await self.memory.status.get("location_knowledge")
        known_places = list(place_knowledge.keys())
        places = ["home", "workplace"] + known_places + ["other"]
        poi_type = None
        await self.placeAnalysisPrompt.format(
            plan=context["plan_context"]["plan"],
            intention=context["current_step"]["intention"],
            place_list=places,
            other_info=self.environment.environment.get("other_information", "None"),
        )
        response = await self.llm.atext_request(
            self.placeAnalysisPrompt.to_dialog(),
            response_format={"type": "json_object"},
            context={
                "block_name": self.name,
                "func_name": "Place Analysis",
                "agent_id": self.agent.id,
            },
        )
        try:
            response = clean_json_response(response)
            response = json_repair.loads(response)["place_type"]  # type: ignore
        except Exception:
            get_logger().warning(
                f"MobilityBlock: Place Analysis: wrong type of place, raw response: {response}",
                extra={"agent_id": self.agent.id},
            )
            response = "home"
        if response == "home":
            await self.memory.status.update("pending_destination_type", "home")
            # go back home
            home = await self.memory.status.get("home")
            home = home["aoi_position"]["aoi_id"]
            nowPlace = await self.memory.status.get("position")
            node_id = await self.memory.stream.add(
                topic="mobility",
                description="I returned home",
            )
            if (
                "aoi_position" in nowPlace
                and nowPlace["aoi_position"]["aoi_id"] == home
            ):
                return {
                    "success": True,
                    "evaluation": "Successfully returned home (already at home)",
                    "to_place": home,
                    "consumed_time": 0,
                    "node_id": node_id,
                }

            number_poi_visited = await self.memory.status.get("number_poi_visited")
            number_poi_visited += 1
            await self.memory.status.update("number_poi_visited", number_poi_visited)
            return await self._execute_movement(context, home, "I returned home")
        elif response == "workplace":
            await self.memory.status.update("pending_destination_type", "workplace")
            # back to workplace
            work = await self.memory.status.get("work")
            work = work["aoi_position"]["aoi_id"]
            nowPlace = await self.memory.status.get("position")
            node_id = await self.memory.stream.add(
                topic="mobility",
                description="I went to my workplace",
            )
            if (
                "aoi_position" in nowPlace
                and nowPlace["aoi_position"]["aoi_id"] == work
            ):
                return {
                    "success": True,
                    "evaluation": "Successfully reached the workplace (already at the workplace)",
                    "to_place": work,
                    "consumed_time": 0,
                    "node_id": node_id,
                }
            # await self.environment.set_aoi_schedules(
            #     person_id=agent_id,
            #     target_positions=work,
            #     # modes=[get_random_transport_mode()],
            # )
            number_poi_visited = await self.memory.status.get("number_poi_visited")
            number_poi_visited += 1
            await self.memory.status.update("number_poi_visited", number_poi_visited)

            return await self._execute_movement(context, work, "I went to my workplace")

        elif response in known_places:
            the_place = place_knowledge[response]["id"]
            nowPlace = await self.memory.status.get("position")
            node_id = await self.memory.stream.add(
                topic="mobility",
                description=f"I went to {response}",
            )
            if (
                "aoi_position" in nowPlace
                and nowPlace["aoi_position"]["aoi_id"] == the_place
            ):
                return {
                    "success": True,
                    "evaluation": f"Successfully reached {response} (already at {response})",
                    "to_place": the_place,
                    "consumed_time": 0,
                    "node_id": node_id,
                }
            # await self.environment.set_aoi_schedules(
            #     person_id=agent_id,
            #     target_positions=the_place,
            #     # modes=[get_random_transport_mode()],
            # )
            number_poi_visited = await self.memory.status.get("number_poi_visited")
            number_poi_visited += 1
            await self.memory.status.update("number_poi_visited", number_poi_visited)
            return await self._execute_movement(
                context, the_place, f"I went to {response}"
            )

        else:
            # move to other places
            poi_type = None
            next_place = context.get("next_place", None)
            nowPlace = await self.memory.status.get("position")

            if next_place is None and self.enforce_place_selection:
                get_logger().info(
                    f"MobilityBlock (Agent {self.agent.id}): No next_place provided, calling PlaceSelectionBlock",
                    extra={"agent_id": self.agent.id},
                )
                # Enforce place selection if not provided
                place_selection_result = await self.place_selection_block.forward(
                    context
                )
                if place_selection_result["success"]:
                    next_place = context.get("next_place", None)

            node_id = await self.memory.stream.add(
                topic="mobility",
                description=f"I went to {next_place}",
            )
            if next_place is not None:
                poi_type = context.get("next_place_type", "unknown")

                # await self.environment.set_aoi_schedules(
                #     person_id=agent_id,
                #     target_positions=next_place[1],
                #     # modes=[get_random_transport_mode()],
                # )
            else:
                aois = self.environment.map.get_all_aois()
                while True:
                    r_aoi = random.choice(aois)
                    if len(r_aoi["poi_ids"]) > 0:
                        r_poi = random.choice(r_aoi["poi_ids"])
                        break
                poi = self.environment.map.get_poi(r_poi)
                poi_type = poi.get("category", "unknown")
                next_place = (poi["name"], poi["aoi_id"], poi_type)
                get_logger().warning(
                    f"MobilityBlock (Agent {self.agent.id}): Move to other place: no next_place provided, randomly selected {next_place}",
                    extra={"agent_id": self.agent.id},
                )

                # await self.environment.set_aoi_schedules(
                #     person_id=agent_id,
                #     target_positions=next_place[1],
                #     # modes=[get_random_transport_mode()],
                # )
            number_poi_visited = await self.memory.status.get("number_poi_visited")
            number_poi_visited += 1

            await self.memory.status.update("pending_destination_type", poi_type)
            await self.memory.status.update("number_poi_visited", number_poi_visited)

            return await self._execute_movement(
                context, next_place[1], f"I went to {next_place}"
            )


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
        self.modeSelectionPrompt = FormatPrompt(TRANSPORT_MODE_SELECTION_PROMPT)
        self.transportation_modes = [m.value for m in TransportModeEnum]

    def _calculate_distance(self, start_xy, end_xy):
        """Calculates Euclidean distance in meters."""
        return math.sqrt(
            (start_xy["x"] - end_xy["x"]) ** 2 + (start_xy["y"] - end_xy["y"]) ** 2
        )

    async def forward(self, context: DotDict):
        """Select transport mode based on context"""
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

        available_modes_list = self.transportation_modes

        # 2. Format Prompt
        await self.modeSelectionPrompt.format(
            distance=distance,
            time=sim_time,
            month=month,
            weather=weather,
            temperature=temperature,
            persona=persona,
            emotion=emotion,
            available_modes=", ".join(available_modes_list),
        )

        try:
            response = await self.llm.atext_request(
                self.modeSelectionPrompt.to_dialog(),
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
        default=RADIUS_PROMPT, description="Used to determine the maximum travel radius"
    )
    search_limit: int = Field(
        default=50, description="Number of POIs to retrieve from map service"
    )
    enforce_place_selection: bool = Field(
        default=False,
        description="Whether to enforce place selection when next_place is not provided",
    )
    enforce_transport_mode_selection: bool = Field(
        default=False,
        description="Whether to enforce transport mode selection for movements",
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
            toolbox, agent_memory, self.params.search_limit
        )
        enforce_trasnport_mode_selection = self.params.enforce_transport_mode_selection
        if enforce_trasnport_mode_selection:
            self.transport_mode_block = TransportModeSelectionBlock(
                toolbox, agent_memory
            )
        else:
            self.transport_mode_block = None

        self.move_block = MoveBlock(
            toolbox,
            agent_memory,
            place_selection_block=self.place_selection_block,
            transport_mode_block=self.transport_mode_block,
            enforce_place_selection=self.params.enforce_place_selection,
            enforce_transport_mode_selection=self.params.enforce_trasnport_mode_selection,
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

        if enforce_trasnport_mode_selection:
            blocks.append(self.transport_mode_block)

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
