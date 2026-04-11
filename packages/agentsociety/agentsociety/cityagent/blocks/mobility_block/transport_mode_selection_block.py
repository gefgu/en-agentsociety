import math
from enum import Enum

import json_repair # type: ignore

from ....agent import AgentToolbox, Block, DotDict
from ....logger import get_logger
from ....memory import Memory
from ..utils import clean_json_response


class TransportModeEnum(Enum):
    WALK = "walk"
    BIKE = "bike"
    CAR = "car"
    BUS = "bus"
    SUBWAY = "subway"


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
                "available_modes": ", ".join(available_modes_list),
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
                context=self.build_llm_prompt_context(
                    prompt_name=self.mode_selection_prompt_name,
                    state_dict=state_dict,
                    func_name="forward",
                ),
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