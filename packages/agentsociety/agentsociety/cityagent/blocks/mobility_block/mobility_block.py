import random
from enum import Enum
from typing import Optional

from pydantic import Field # type: ignore

from ....agent import (
    AgentToolbox,
    Block,
    BlockContext,
    BlockParams,
    DotDict,
)
from ....agent.dispatcher import BlockDispatcher
from ....memory import Memory
from ...sharing_params import SocietyAgentBlockOutput
from .move_block import MoveBlock
from .place_selection_block import PlaceSelectionBlock
from .transport_mode_selection_block import TransportModeSelectionBlock


class TransportModeEnum(Enum):
    WALK = "walk"
    BIKE = "bike"
    CAR = "car"
    BUS = "bus"
    SUBWAY = "subway"

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
