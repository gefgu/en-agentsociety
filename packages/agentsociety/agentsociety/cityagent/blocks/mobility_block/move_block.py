import time
from typing import TYPE_CHECKING

from pycityproto.city.trip.v2.trip_pb2 import TripMode # type: ignore

from ....agent import AgentToolbox, Block, DotDict
from ....logger import get_logger
from ....memory import Memory

if TYPE_CHECKING:
    from .place_selection_block import PlaceSelectionBlock
    from .transport_mode_selection_block import TransportModeSelectionBlock


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
        if self.agent.params.simulation_mode == "citysim":
            transport_result = await self.transport_mode_block.forward(context)
            selected_mode = transport_result.get("transport_mode", "car")
        else:
            selected_mode = "car"

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
        poi_id = None
        place_selection_result = None  # Store PlaceSelectionBlock result for later merging

        place_knowledge = await self.memory.status.get("location_knowledge")
        known_places = list(place_knowledge.keys())
        places = ["home", "workplace"] + known_places + ["other"]

        # 1. LLM Decision
        analysis_result = await self.execute_prompt(
            self.place_analysis_prompt_name,
            {
                "plan": context["plan_context"]["plan"],
                "intention": context["current_step"]["intention"],
                "place_list": places,
                "other_info": self.environment.environment.get("other_information", "None"),
            },
            func_name="forward",
        )
        if analysis_result.success:
            response_type = analysis_result.parsed.get("place_type", "home")
        else:
            get_logger().warning(
                f"MobilityBlock: Place Analysis failed: {analysis_result.error}",
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
                else:
                    get_logger().warning(
                        f"MobilityBlock (Agent {self.agent.id}): PlaceSelectionBlock failed for intention '{context['current_step']['intention']}'. Evaluation: {place_selection_result.get('evaluation', 'No evaluation')}",
                        extra={"agent_id": self.agent.id},
                    )

            # 2b. Enforce place selection: fail if destination is still unavailable
            if next_place is None:
                failure_reason = (
                    "PlaceSelectionBlock did not provide next_place"
                    if place_selection_result is None
                    else place_selection_result.get(
                        "evaluation", "PlaceSelectionBlock did not provide next_place"
                    )
                )
                get_logger().error(
                    f"MobilityBlock (Agent {self.agent.id}): Move to other place failed because next_place is missing after PlaceSelectionBlock. Reason: {failure_reason}",
                    extra={"agent_id": self.agent.id},
                )
                node_id = await self.memory.stream.add(
                    topic="mobility",
                    description=(
                        f"Failed to find destination for {context['current_step']['intention']}: {failure_reason}"
                    ),
                )
                return {
                    "success": False,
                    "evaluation": f"Failed to select destination: {failure_reason}",
                    "consumed_time": 5,
                    "node_id": node_id,
                    "poi_id": None,
                    "is_poi": False,
                }

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