from agentsociety.agent import IndividualAgentBase
from typing import Any

class BehaviorModelingAgent(IndividualAgentBase):
    """
    A template agent for the Behavior Modeling benchmark.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def forward(self, task_context: dict[str, Any]):
        target = task_context["target"]
        if target == "review_writing":
            return {"stars": 3, "review": "This is a review"}
        elif target == "recommendation":
            return {"item_list": task_context["candidate_list"]}