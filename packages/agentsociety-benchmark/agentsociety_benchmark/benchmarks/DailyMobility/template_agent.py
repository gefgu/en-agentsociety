from agentsociety.agent import CitizenAgentBase, MemoryAttribute
from pycityproto.city.person.v2.motion_pb2 import Status
import random

class DailyMobilityAgent(CitizenAgentBase):
    """
    A template agent for the Daily Mobility Generation benchmark.
    A simple agent that moves to a random destination every hour.
    """
    StatusAttributes = [
        MemoryAttribute(
            name="current_plan",
            type=dict,
            default_or_value={},
            description="agent's current plan",
        ),
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.movement_gap = 60 * 60
        self.last_movement_time = -1
        self.movement_status = [Status.STATUS_WALKING, Status.STATUS_DRIVING]
        self.intention_list = [
            "sleep",
            "home activity",
            "other",
            "work",
            "shopping",
            "eating out",
            "leisure and entertainment",
        ]

    async def go_to_aoi(self, aoi_id: int):
        assert self.environment is not None
        await self.environment.set_aoi_schedules(
            self.id,
            target_positions = aoi_id,
        )

    async def log_intention(self, intention: str):
        await self.memory.status.update("current_plan", {
            "target": intention,
            "index": 0,
            "steps": [{"intention": intention}]
        })

    async def forward(self):
        # check my status
        citizen_status = await self.memory.status.get("status")
        if citizen_status in self.movement_status:
            # agent is moving
            return

        # get the current time
        assert self.environment is not None
        _, time = self.environment.get_datetime()
        if self.last_movement_time == -1 or time - self.last_movement_time > self.movement_gap:
            self.last_movement_time = time
            # randomly select a destination
            aoi_ids = self.environment.get_aoi_ids()
            destination_aoi_id = random.choice(aoi_ids)
            # move to the destination
            await self.go_to_aoi(destination_aoi_id)
            intention = random.choice(self.intention_list)
            await self.log_intention(intention)