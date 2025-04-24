import random
import time

import jsonc

from ..agent import Agent, AgentToolbox, Block, CitizenAgentBase
from ..environment import Environment
from ..llm import LLM
from ..logger import get_logger
from ..memory import Memory
from .blocks import (CognitionBlock, EconomyBlock, MobilityBlock, NeedsBlock,
                     OtherBlock, PlanBlock, SocialBlock)
from .blocks.economy_block import MonthPlanBlock


class PlanAndActionBlock(Block):
    """Active workflow coordinating needs assessment, planning, and action execution.

    Combines multiple sub-modules to manage agent's monthly planning, needs updates,
    step-by-step plan generation, and execution of mobility/social/economic actions.
    """

    # Sub-modules for different behavioral aspects
    month_plan_block: MonthPlanBlock
    needs_block: NeedsBlock
    plan_block: PlanBlock
    mobility_block: MobilityBlock
    social_block: SocialBlock
    economy_block: EconomyBlock
    other_block: OtherBlock

    def __init__(
        self,
        agent: Agent,
        llm: LLM,
        environment: Environment,
        memory: Memory,
        enable_mobility: bool = True,
        enable_social: bool = True,
        enable_economy: bool = True,
        enable_cognition: bool = True,
    ):
        """Initialize PlanAndActionBlock with configurable behavior switches and sub-modules."""
        super().__init__(
            name="plan_and_action_block",
            llm=llm,
            environment=environment,
            memory=memory,
        )
        self._agent = agent
        # Configuration flags for enabling/disabling behaviors
        self.enable_mobility = enable_mobility
        self.enable_social = enable_social
        self.enable_economy = enable_economy
        self.enable_cognition = enable_cognition
        self.month_plan_block = MonthPlanBlock(
            llm=llm, environment=environment, memory=memory
        )
        self.needs_block = NeedsBlock(llm=llm, environment=environment, memory=memory)
        self.plan_block = PlanBlock(llm=llm, environment=environment, memory=memory)
        self.mobility_block = MobilityBlock(
            llm=llm, environment=environment, memory=memory
        )
        self.social_block = SocialBlock(
            agent=agent, llm=llm, environment=environment, memory=memory
        )
        self.economy_block = EconomyBlock(
            llm=llm, environment=environment, memory=memory
        )
        self.other_block = OtherBlock(llm=llm, memory=memory)

    async def reset(self):
        """Reset the plan and action block."""
        await self.needs_block.reset()

    async def plan_generation(self):
        """Generate a new plan if no current plan exists in memory."""
        cognition = None
        current_plan = await self.memory.status.get("current_plan")
        if current_plan is None or not current_plan:
            cognition = (
                await self.plan_block.forward()
            )  # Delegate to PlanBlock for plan creation
        return cognition

    async def step_execution(self):
        """Execute the current step in the active plan based on step type."""
        current_plan = await self.memory.status.get("current_plan")
        if (
            current_plan is None
            or not current_plan
            or len(current_plan.get("steps", [])) == 0
        ):
            return  # No plan, no execution
        step_index = current_plan.get("index", 0)
        execution_context = await self.memory.status.get("execution_context")
        current_step = current_plan.get("steps", [])[step_index]
        # check current_step is valid (not empty)
        if current_step:
            step_type = current_step.get("type")
            position = await self.memory.status.get("position")
            if "aoi_position" in position:
                current_step["position"] = position["aoi_position"]["aoi_id"]
            current_step["start_time"] = self.environment.get_tick()
            result = None
            if step_type == "mobility":
                if self.enable_mobility:
                    result = await self.mobility_block.forward(
                        current_step, execution_context
                    )
                else:
                    result = {
                        "success": False,
                        "evaluation": f"Mobility Behavior is disabled",
                        "consumed_time": 0,
                        "node_id": None,
                    }
            elif step_type == "social":
                if self.enable_social:
                    result = await self.social_block.forward(
                        current_step, execution_context
                    )
                else:
                    result = {
                        "success": False,
                        "evaluation": f"Social Behavior is disabled",
                        "consumed_time": 0,
                        "node_id": None,
                    }
            elif step_type == "economy":
                if self.enable_economy:
                    result = await self.economy_block.forward(
                        current_step, execution_context
                    )
                else:
                    result = {
                        "success": False,
                        "evaluation": f"Economy Behavior is disabled",
                        "consumed_time": 0,
                        "node_id": None,
                    }
            elif step_type == "other":
                result = await self.other_block.forward(current_step, execution_context)
            else:
                result = {
                    "success": True,
                    "evaluation": f"Finished {current_step['intention']}",
                    "consumed_time": random.randint(1, 10),
                    "node_id": None,
                }
            if result != None:
                current_step["evaluation"] = result

            # Update current_step, plan, and execution_context information
            current_plan["steps"][step_index] = current_step
            await self.memory.status.update("current_plan", current_plan)
            await self.memory.status.update("execution_context", execution_context)

    async def forward(self, step=None, context=None):
        # Long-term decision
        await self.month_plan_block.forward()

        # update needs
        cognition = await self.needs_block.forward()
        if cognition:
            await self._agent.save_agent_thought(cognition)

        # plan generation
        cognition = await self.plan_generation()
        if cognition:
            await self._agent.save_agent_thought(cognition)

        # step execution
        await self.step_execution()


class MindBlock(Block):
    """Cognitive workflow handling emotion updates and reasoning processes."""

    cognition_block: CognitionBlock

    def __init__(self, llm: LLM, environment: Environment, memory: Memory):
        super().__init__(
            name="mind_block",
            llm=llm,
            environment=environment,
            memory=memory,
        )
        self.cognition_block = CognitionBlock(
            llm=self.llm, memory=self.memory, environment=self.environment
        )

    async def forward(self, step=None, context=None):
        """Execute cognitive processing for emotion updates."""
        await self.cognition_block.forward()


class SocietyAgent(CitizenAgentBase):
    """Agent implementation with configurable cognitive/behavioral modules and social interaction capabilities."""

    mind_block: MindBlock
    plan_and_action_block: PlanAndActionBlock

    configurable_fields = [
        "enable_cognition",
        "enable_mobility",
        "enable_social",
        "enable_economy",
    ]
    default_values = {
        "enable_cognition": True,
        "enable_mobility": True,
        "enable_social": True,
        "enable_economy": True,
    }
    fields_description = {
        "enable_cognition": "Enable cognition workflow",
        "enable_mobility": "Enable mobility workflow",
        "enable_social": "Enable social workflow",
        "enable_economy": "Enable economy workflow",
    }

    def __init__(
        self,
        id: int,
        name: str,
        toolbox: AgentToolbox,
        memory: Memory,
    ) -> None:
        """Initialize agent with core components and configuration."""
        super().__init__(
            id=id,
            name=name,
            toolbox=toolbox,
            memory=memory,
        )

        # config
        self.enable_cognition = True
        self.enable_mobility = True
        self.enable_social = True
        self.enable_economy = True

        self.mind_block = MindBlock(
            llm=self.llm, environment=self.environment, memory=self.memory
        )
        self.plan_and_action_block = PlanAndActionBlock(
            agent=self,
            llm=self.llm,
            environment=self.environment,
            memory=self.memory,
            enable_mobility=self.enable_mobility,
            enable_social=self.enable_social,
            enable_economy=self.enable_economy,
            enable_cognition=self.enable_cognition,
        )
        self.step_count = -1
        self.cognition_update = -1

    async def reset(self):
        """Reset the agent."""
        # reset position to home
        await self.reset_position()

        # reset needs
        await self.memory.status.update("current_need", "none")

        # reset plans and actions
        await self.memory.status.update("current_plan", {})
        await self.memory.status.update("execution_context", {})

        # reset initial flag
        await self.plan_and_action_block.reset()

    # Main workflow
    async def forward(self):
        """Main agent loop coordinating status updates, plan execution, and cognition."""
        start_time = time.time()
        self.step_count += 1
        # sync agent status with simulator
        await self.update_motion()
        get_logger().debug(f"Agent {self.id}: Finished main workflow - update motion")

        # check last step
        ifpass = await self.check_and_update_step()
        if not ifpass:
            return
        get_logger().debug(
            f"Agent {self.id}: Finished main workflow - check and update step"
        )

        # plan and action
        await self.plan_and_action_block.forward()
        get_logger().debug(f"Agent {self.id}: Finished main workflow - plan and action")

        # cognition
        if self.enable_cognition:
            await self.mind_block.forward()
        get_logger().debug(f"Agent {self.id}: Finished main workflow - cognition")

        return time.time() - start_time

    async def check_and_update_step(self):
        """Check if the previous step has been completed"""
        status = await self.memory.status.get("status")
        if status == 2:
            # Agent is moving
            return False

        # Get the previous step information
        current_plan = await self.memory.status.get("current_plan")
        # If there is no current plan, return True
        if current_plan is None or not current_plan:
            return True
        step_index = current_plan.get("index", 0)
        current_step = current_plan.get("steps", [])[step_index]
        time_now = self.environment.get_tick()
        step_start_time = current_step["start_time"]
        step_consumed_time = current_step["evaluation"]["consumed_time"]
        try:
            time_end_plan = step_start_time + int(step_consumed_time) * 60
        except Exception as e:
            get_logger().warning(f"Error in check_and_update_step: {str(e)}")
            time_end_plan = time_now
        if time_now >= time_end_plan:
            # The previous step has been completed
            current_step["evaluation"]["consumed_time"] = (
                time_now - step_start_time
            ) / 60
            current_plan["stream_nodes"].append(current_step["evaluation"]["node_id"])
            if current_step["evaluation"]["success"]:
                # last step is completed
                current_plan["steps"][step_index] = current_step
                if step_index + 1 < len(current_plan["steps"]):
                    # Last step is completed
                    current_plan["index"] = step_index + 1
                    await self.memory.status.update("current_plan", current_plan)
                else:
                    # Whole plan is completed
                    current_plan["completed"] = True
                    _, current_plan["end_time"] = self.environment.get_datetime(
                        format_time=True
                    )
                    related_memories = None
                    if self.enable_cognition:
                        try:
                            # Update emotion for the plan
                            related_memories = await self.memory.stream.get_by_ids(
                                current_plan["stream_nodes"]
                            )
                            incident = f"You have successfully completed the plan: {related_memories}"
                            conclusion = (
                                await self.mind_block.cognition_block.emotion_update(
                                    incident
                                )
                            )
                            await self.save_agent_thought(conclusion)
                            await self.memory.stream.add_cognition_to_memory(
                                current_plan["stream_nodes"], conclusion
                            )
                        except Exception as e:
                            get_logger().warning(
                                f"Error in check_and_update_step (emotion_update): {str(e)}\nrelated_memories: {related_memories}"
                            )
                    await self.memory.status.update("current_plan", current_plan)
                return True
            else:
                # last step is failed
                current_plan["failed"] = True
                _, current_plan["end_time"] = self.environment.get_datetime(
                    format_time=True
                )
                if self.enable_cognition:
                    related_memories = None
                    try:
                        # Update emotion for the plan
                        related_memories = await self.memory.stream.get_by_ids(
                            current_plan["stream_nodes"]
                        )
                        incident = (
                            f"You have failed to complete the plan: {related_memories}"
                        )
                        conclusion = (
                            await self.mind_block.cognition_block.emotion_update(
                                incident
                            )
                        )
                        await self.save_agent_thought(conclusion)
                        await self.memory.stream.add_cognition_to_memory(
                            current_plan["stream_nodes"], conclusion
                        )
                    except Exception as e:
                        get_logger().warning(
                            f"Error in check_and_update_step (emotion_update): {str(e)}\nrelated_memories: {related_memories}"
                        )
                await self.memory.status.update("current_plan", current_plan)
                return True
        # The previous step has not been completed
        return False

    async def process_agent_chat_response(self, payload: dict) -> str:
        """Process incoming social/economic messages and generate responses."""
        if payload["type"] == "social":
            resp = f"Agent {self.id} received agent chat response: {payload}"
            try:
                # Extract basic info
                sender_id = payload.get("from")
                if not sender_id:
                    return ""

                raw_content = payload.get("content", "")

                # Parse message content
                try:
                    message_data = jsonc.loads(raw_content)
                    content = message_data["content"]
                    propagation_count = message_data.get("propagation_count", 1)
                except (jsonc.JSONDecodeError, TypeError, KeyError):
                    content = raw_content
                    propagation_count = 1

                if not content:
                    return ""

                # add social memory
                description = f"You received a social message: {content}"
                await self.memory.stream.add_social(description=description)
                if self.enable_cognition:
                    # update emotion
                    await self.mind_block.cognition_block.emotion_update(description)

                # Get chat histories and ensure proper format
                chat_histories = await self.memory.status.get("chat_histories") or {}
                if not isinstance(chat_histories, dict):
                    chat_histories = {}

                # Update chat history with received message
                if sender_id not in chat_histories:
                    chat_histories[sender_id] = ""
                if chat_histories[sender_id]:
                    chat_histories[sender_id] += "，"
                chat_histories[sender_id] += f"them: {content}"

                # Check propagation limit
                if propagation_count > 5:
                    await self.memory.status.update("chat_histories", chat_histories)
                    return ""

                # Get relationship score
                relationships = await self.memory.status.get("relationships") or {}
                relationship_score = relationships.get(sender_id, 50)

                # Decision prompt
                should_respond_prompt = f"""Based on:
        - Received message: "{content}"
        - Our relationship score: {relationship_score}/100
        - My profile: {{
            "gender": "{await self.memory.status.get("gender") or ""}",
            "education": "{await self.memory.status.get("education") or ""}",
            "personality": "{await self.memory.status.get("personality") or ""}",
            "occupation": "{await self.memory.status.get("occupation") or ""}"
        }}
        - My current emotion: {await self.memory.status.get("emotion_types")}
        - Recent chat history: {chat_histories.get(sender_id, "")}

        Should I respond to this message? Consider:
        1. Is this a message that needs/deserves a response?
        2. Would it be natural for someone with my personality to respond?
        3. Is our relationship close enough to warrant a response?

        Answer only YES or NO, in JSON format, e.g. {{"should_respond": "YES"}}"""

                should_respond = await self.llm.atext_request(
                    dialog=[
                        {
                            "role": "system",
                            "content": "You are helping decide whether to respond to a message.",
                        },
                        {"role": "user", "content": should_respond_prompt},
                    ],
                    response_format={"type": "json_object"},
                )
                should_respond = jsonc.loads(should_respond)["should_respond"]
                if should_respond == "NO":
                    return ""

                response_prompt = f"""Based on:
        - Received message: "{content}"
        - Our relationship score: {relationship_score}/100
        - My profile: {{
            "gender": "{await self.memory.status.get("gender") or ""}",
            "education": "{await self.memory.status.get("education") or ""}",
            "personality": "{await self.memory.status.get("personality") or ""}",
            "occupation": "{await self.memory.status.get("occupation") or ""}"
        }}
        - My current emotion: {await self.memory.status.get("emotion_types")}
        - Recent chat history: {chat_histories.get(sender_id, "")}

        Generate an appropriate response that:
        1. Matches my personality and background
        2. Maintains natural conversation flow
        3. Is concise (under 100 characters)
        4. Reflects our relationship level

        Response should be ONLY the message text, no explanations."""

                response = await self.llm.atext_request(
                    [
                        {
                            "role": "system",
                            "content": "You are helping generate a chat response.",
                        },
                        {"role": "user", "content": response_prompt},
                    ]
                )

                if response:
                    # Update chat history with response
                    chat_histories[sender_id] += f"，me: {response}"
                    await self.memory.status.update("chat_histories", chat_histories)

                    # Send response
                    serialized_response = jsonc.dumps(
                        {
                            "content": response,
                            "propagation_count": propagation_count + 1,
                        },
                        ensure_ascii=False,
                    )
                    await self.send_message_to_agent(sender_id, serialized_response)
                return response

            except Exception as e:
                get_logger().warning(f"Error in process_agent_chat_response: {str(e)}")
                return ""
        else:
            content = payload["content"]
            key, value = content.split("@")
            if "." in value:
                value = float(value)
            else:
                value = int(value)
            description = f"You received a economic message: Your {key} has changed from {await self.memory.status.get(key)} to {value}"
            await self.memory.status.update(key, value)
            await self.memory.stream.add_economy(description=description)
            if self.enable_cognition:
                await self.mind_block.cognition_block.emotion_update(description)
            return ""

    async def react_to_intervention(self, intervention_message: str):
        """React to an intervention"""
        # cognition
        conclusion = await self.mind_block.cognition_block.emotion_update(
            intervention_message
        )
        await self.save_agent_thought(conclusion)
        await self.memory.stream.add_cognition(description=conclusion)
        # needs
        await self.plan_and_action_block.needs_block.reflect_to_intervention(
            intervention_message
        )

    async def reset_position(self):
        """Reset the position of the agent."""
        home = await self.status.get("home")
        home = home["aoi_position"]["aoi_id"]
        await self.environment.reset_person_position(person_id=self.id, aoi_id=home)
