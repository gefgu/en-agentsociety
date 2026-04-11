import random
import time

from typing import Any, Optional

import json_repair

from ..agent import (
    AgentToolbox,
    Block,
    CitizenAgentBase,
    MemoryAttribute,
)
from ..logger import get_logger
from ..memory import Memory
from .blocks import CognitionBlock, NeedsBlock, PlanBlock, DailyScheduleBlock
from .sharing_params import (
    SocietyAgentConfig,
    SocietyAgentBlockOutput,
    SocietyAgentContext,
)
from ..message import Message


class SocietyAgent(CitizenAgentBase):
    ParamsType = SocietyAgentConfig
    BlockOutputType = SocietyAgentBlockOutput
    Context = SocietyAgentContext
    StatusAttributes = [
        MemoryAttribute(
            name="hunger_satisfaction",
            type=float,
            default_or_value=0.9,
            description="agent's hunger satisfaction, 0-1",
        ),
        MemoryAttribute(
            name="energy_satisfaction",
            type=float,
            default_or_value=0.9,
            description="agent's energy satisfaction, 0-1",
        ),
        MemoryAttribute(
            name="safety_satisfaction",
            type=float,
            default_or_value=0.4,
            description="agent's safety satisfaction, 0-1",
        ),
        MemoryAttribute(
            name="social_satisfaction",
            type=float,
            default_or_value=0.6,
            description="agent's social satisfaction, 0-1",
        ),
        MemoryAttribute(
            name="current_need",
            type=str,
            default_or_value="none",
            description="agent's current need",
        ),
        # cognition
        MemoryAttribute(
            name="emotion",
            type=dict,
            default_or_value={
                "sadness": 5,
                "joy": 5,
                "fear": 5,
                "disgust": 5,
                "anger": 5,
                "surprise": 5,
            },
            description="agent's emotion, 0-10",
        ),
        MemoryAttribute(
            name="thought",
            type=str,
            default_or_value="Currently nothing good or bad is happening",
            description="agent's thought",
            whether_embedding=True,
        ),
        MemoryAttribute(
            name="emotion_types",
            type=str,
            default_or_value="Relief",
            description="agent's emotion types",
            whether_embedding=True,
        ),
        MemoryAttribute(
            name="firm_id", type=int, default_or_value=0, description="agent's firm id"
        ),
        MemoryAttribute(
            name="government_id",
            type=int,
            default_or_value=0,
            description="agent's government id",
        ),
        MemoryAttribute(
            name="bank_id", type=int, default_or_value=0, description="agent's bank id"
        ),
        MemoryAttribute(
            name="nbs_id", type=int, default_or_value=0, description="agent's nbs id"
        ),
        MemoryAttribute(
            name="depression",
            type=float,
            default_or_value=0.0,
            description="agent's depression, 0-1",
        ),
        MemoryAttribute(
            name="working_experience",
            type=list,
            default_or_value=[],
            description="agent's working experience",
        ),
        MemoryAttribute(
            name="work_hour_month",
            type=float,
            default_or_value=160,
            description="agent's work hour per month",
        ),
        MemoryAttribute(
            name="work_hour_finish",
            type=float,
            default_or_value=0,
            description="agent's work hour finished",
        ),
        # social
        MemoryAttribute(
            name="social_network",
            type=list,
            default_or_value=[],
            description="all social network",
        ),
        MemoryAttribute(
            name="chat_histories",
            type=dict,
            default_or_value={},
            description="all chat histories",
        ),
        MemoryAttribute(
            name="interactions",
            type=dict,
            default_or_value={},
            description="all interaction records",
        ),
        # mobility
        MemoryAttribute(
            name="number_poi_visited",
            type=int,
            default_or_value=1,
            description="agent's number of poi visited",
        ),
    ]
    description: str = """
A social agent that can interact with other agents and the environment.
The main workflow includes:
1. Agent needs determination (based on Maxlow's Hierarchy Needs) —— including hunger needs, safety needs, social needs and emergency needs)
2. Plan generation (The citizen generate a detailed plan based on the needs)
3. Step execution (The citizen execute the action based on the generated plan)

Notice: The capability of citizen is controled by the BLOCKS (defaultly, it contains 4 blocks:
1). MobilityBlock: endow the citizen with the ability to move around the city
2). EconomyBlock: endow the citizen with the ability to shoping and working
3). SocialBlock: endow the citizen with the ability to socializing with other citizens
4). OtherBlocks: handle other intentions (e.g., cooking, sleeping, etc.)

You can add more blocks to the citizen as you wish to adapt to the different scenarios. We strongly recommend you keep the default blocks as they are.
"""

    """Agent implementation with configurable cognitive/behavioral modules and social interaction capabilities."""

    def __init__(
        self,
        id: int,
        name: str,
        toolbox: AgentToolbox,
        memory: Memory,
        agent_params: Optional[SocietyAgentConfig] = None,
        blocks: Optional[list[Block]] = None,
    ) -> None:
        """Initialize agent with core components and configuration."""
        super().__init__(
            id=id,
            name=name,
            toolbox=toolbox,
            memory=memory,
            agent_params=agent_params,
            blocks=blocks,
        )

        self.needs_block = NeedsBlock(
            id=self.id,
            toolbox=self._toolbox,
            agent_memory=self.memory,
            agent_context=self.context,
        )

        self.plan_block = PlanBlock(
            agent=self,
            toolbox=self._toolbox,
            agent_memory=self.memory,
            agent_context=self.context,
            max_plan_steps=self.params.max_plan_steps,
        )

        self.cognition_block = CognitionBlock(
            agent=self,
            toolbox=self._toolbox,
            agent_memory=self.memory,
        )

        self.daily_schedule_block = DailyScheduleBlock(
            agent=self,
            toolbox=self._toolbox,
            agent_memory=self.memory,
        )

        self.prompt_manager = Block._get_or_create_prompt_manager(None)
        self.environment_reflection_prompt_name = "societyagent_environment_reflection"
        self.status_summary_prompt_name = "societyagent_status_summary"
        self.chat_belief_update_prompt_name = "societyagent_chat_belief_update"
        self.chat_response_decision_prompt_name = "societyagent_chat_response_decision"

        # register blocks
        self.dispatcher.register_dispatcher_prompt(self.params.block_dispatch_prompt)

        self.step_count = -1
        self.cognition_update = -1

    def _build_prompt_context(
        self,
        *,
        prompt_name: str,
        state_dict: dict[str, Any],
        func_name: str,
    ) -> dict[str, Any]:
        return {
            "block_name": "SocietyAgent",
            "func_name": func_name,
            "agent_id": str(self.id),
            "prompt_identity": self.prompt_manager.get_prompt_identity(prompt_name),
            "prompt_inputs": {
                key: state_dict[key]
                for key in self.prompt_manager.get_typed_input_fields(prompt_name)
                if key in state_dict
            },
            "prompt_input_schema": self.prompt_manager.get_input_schema(prompt_name),
            "prompt_output_schema": self.prompt_manager.get_output_schema(prompt_name),
        }

    async def status_summary(self):
        """
        Status summary
        """
        required_fields = self.prompt_manager.get_required_fields(
            self.status_summary_prompt_name
        )
        current_location = getattr(
            self.context,
            "current_location",
            getattr(self.context, "current_position", "Outside"),
        )
        state_dict = await self.prompt_manager.build_agent_state(
            required_fields=required_fields,
            context={
                "current_time": self.context.current_time,
                "weather": self.context.weather,
                "temperature": self.context.temperature,
                "current_location": current_location,
                "other_information": self.context.other_information,
                "current_need": self.context.current_need,
                "current_plan_target": self.context.plan_target,
                "current_intention": self.context.current_intention,
                "current_emotion": self.context.current_emotion,
                "current_thought": self.context.current_thought,
            },
            memory=self.memory,
        )
        dialog = self.prompt_manager.format_prompt_to_dialog(
            self.status_summary_prompt_name, state_dict
        )
        summary_text = await self.llm.atext_request(
            dialog,
            context=self._build_prompt_context(
                prompt_name=self.status_summary_prompt_name,
                state_dict=state_dict,
                func_name="status_summary",
            ),
        )
        await self.memory.status.update("status_summary", summary_text)

    async def before_forward(self):
        """Before forward"""
        await super().before_forward()
        assert self.environment is not None
        # preparing context values
        # Current Time
        now_time = self.environment.get_datetime(format_time=True)
        self.context.current_time = now_time[1]

        # Current Emotion
        emotion_types = await self.memory.status.get("emotion_types")
        self.context.current_emotion = emotion_types

        # Current Thought
        thought = await self.memory.status.get("thought")
        self.context.current_thought = thought

        # Current Location
        position_now = await self.memory.status.get("position")
        home_location = await self.memory.status.get("home")
        work_location = await self.memory.status.get("work")
        current_location = "Outside"
        if (
            "aoi_position" in position_now
            and position_now["aoi_position"] == home_location["aoi_position"]
        ):
            current_location = "At home"
        elif (
            "aoi_position" in position_now
            and position_now["aoi_position"] == work_location["aoi_position"]
        ):
            current_location = "At workplace"
        self.context.current_position = current_location

        # Area Information
        aoi_info = await self.get_aoi_info()
        if not aoi_info:
            self.context.area_information = "Don't know"
        else:
            self.context.area_information = aoi_info

        # Weather
        weather_info = self.environment.sense("weather")
        self.context.weather = weather_info

        # Temperature
        temperature_info = self.environment.sense("temperature")
        self.context.temperature = temperature_info

        # Other Information
        other_info = self.environment.sense("other_information")
        self.context.other_information = other_info

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
        await self.needs_block.reset()

    async def plan_generation(self):
        """Generate a new plan if no current plan exists in memory."""
        cognition = None
        current_plan = await self.memory.status.get("current_plan", False)
        if current_plan is None or not current_plan:
            cognition = (
                await self.plan_block.forward()
            )  # Delegate to PlanBlock for plan creation
        return cognition

    async def reflect_to_environment(self):
        """Reflect to the environment"""
        aoi_info = await self.get_aoi_info()
        if aoi_info:
            required_fields = self.prompt_manager.get_required_fields(
                self.environment_reflection_prompt_name
            )
            state_dict = await self.prompt_manager.build_agent_state(
                required_fields=required_fields,
                context={"area_information": aoi_info},
                memory=self.memory,
            )
            dialog = self.prompt_manager.format_prompt_to_dialog(
                self.environment_reflection_prompt_name, state_dict
            )
            reflection = await self.llm.atext_request(
                dialog,
                context=self._build_prompt_context(
                    prompt_name=self.environment_reflection_prompt_name,
                    state_dict=state_dict,
                    func_name="reflect_to_environment",
                ),
            )
            await self.save_agent_thought(reflection)

    # Main workflow
    async def forward(self):
        """Main agent loop coordinating status updates, plan execution, and cognition."""
        start_time = time.time()
        self.step_count += 1

        if self.step_count == 0:
            # initalize big5 
            await self.cognition_block.initialize_big5()
            await self.cognition_block.initialize_hobbies()
            await self.cognition_block.initialize_preferences()

        # reflect to environment
        await self.reflect_to_environment()

        # check last step
        ifpass = await self.check_and_update_step()
        if not ifpass:
            return
        get_logger().debug(
            f"Agent {self.id}: Finished main workflow - check and update step"
        )

        # Maxlow's Needs
        cognition = await self.needs_block.forward()
        if self.params.enable_cognition and cognition:
            await self.save_agent_thought(cognition)

        # Planned-Behavior
        cognition = await self.plan_generation()
        if cognition:
            await self.save_agent_thought(cognition)
        get_logger().debug(f"Agent {self.id}: Finished main workflow - plan")

        # step execution - dispatch to different blocks
        await self.step_execution()
        get_logger().debug(f"Agent {self.id}: Finished main workflow - step execution")

        # cognition
        if self.params.enable_cognition:
            await self.cognition_block.forward()
        get_logger().debug(f"Agent {self.id}: Finished main workflow - cognition")

        return time.time() - start_time

    async def check_and_update_step(self):
        """Check if the previous step has been completed"""
        assert self.environment is not None
        status = await self.memory.status.get("status")
        if status == 2:
            # Agent is moving
            return False

        # Get the previous step information
        current_plan = await self.memory.status.get("current_plan", False)
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
                    if self.params.enable_cognition:
                        try:
                            # Update emotion for the plan
                            related_memories = await self.memory.stream.get_by_ids(
                                current_plan["stream_nodes"]
                            )
                            incident = f"You have successfully completed the plan: {related_memories}"
                            conclusion = await self.cognition_block.emotion_update(
                                incident
                            )
                            await self.save_agent_thought(conclusion)
                            await self.memory.stream.add_cognition_to_memory(
                                current_plan["stream_nodes"], conclusion
                            )
                        except Exception as e:
                            get_logger().warning(
                                f"Check_and_update_step (emotion_update): {str(e)}"
                            )
                    await self.memory.status.update("current_plan", current_plan)
                return True
            else:
                # last step is failed
                current_plan["failed"] = True
                _, current_plan["end_time"] = self.environment.get_datetime(
                    format_time=True
                )
                if self.params.enable_cognition:
                    related_memories = None
                    try:
                        # Update emotion for the plan
                        related_memories = await self.memory.stream.get_by_ids(
                            current_plan["stream_nodes"]
                        )
                        incident = (
                            f"You have failed to complete the plan: {related_memories}"
                        )
                        conclusion = await self.cognition_block.emotion_update(incident)
                        await self.save_agent_thought(conclusion)
                        await self.memory.stream.add_cognition_to_memory(
                            current_plan["stream_nodes"], conclusion
                        )
                    except Exception as e:
                        get_logger().warning(
                            f"Check_and_update_step (emotion_update): {str(e)}"
                        )
                await self.memory.status.update("current_plan", current_plan)
                return True
        # The previous step has not been completed
        return False

    async def do_chat(self, message: Message) -> str:
        """Process incoming social/economic messages and generate responses."""
        payload = message.payload
        if payload.get("type", "social") == "social":
            try:
                # Extract basic info
                sender_id = message.from_id
                if not sender_id:
                    return ""

                content = payload.get("content", "Hello, how are you?")
                if isinstance(content, dict):
                    content = content.get("content", "Hello, how are you?")

                # add social memory
                description = f"You received a social message: {content}"
                await self.memory.stream.add(topic="social", description=description)
                if self.params.enable_cognition:
                    # update emotion
                    await self.cognition_block.emotion_update(description)

                # Get chat histories and ensure proper format
                chat_histories = await self.memory.status.get("chat_histories") or {}
                if not isinstance(chat_histories, dict):
                    chat_histories = {}

                # Update chat history with received message
                if sender_id not in chat_histories:
                    chat_histories[sender_id] = ""
                if chat_histories[sender_id]:
                    chat_histories[sender_id] += "，"
                chat_histories[sender_id] += f"he/she: {content}"

                # Get relationship strength and type
                my_social_network = await self.memory.status.get("social_network", [])
                relationship_strength = "unknown"
                relationship_type = "I don't know him/her"
                matched_relation = None
                for relation in my_social_network:
                    if relation.target_id == sender_id:
                        relationship_strength = f"Affinity: {relation.affinity}, Trust: {relation.trust}, Familiarity: {relation.familiarity} (0-1 Scale)"
                        relationship_type = relation.kind
                        matched_relation = relation
                        break

                recent_chat_history = chat_histories.get(sender_id, "No chat history")
                get_logger().debug(f"Recent chat history: {recent_chat_history}")
                try:
                    recent_chat_history = recent_chat_history[-200:]
                except Exception as e:
                    get_logger().warning(
                        f"Error in do_chat (recent_chat_history): {str(e)}"
                    )
                    recent_chat_history = "No chat history"

                required_fields = self.prompt_manager.get_required_fields(
                    self.chat_belief_update_prompt_name
                )
                state_dict = await self.prompt_manager.build_agent_state(
                    required_fields=required_fields,
                    context={
                        "content": content,
                        "sender_id": sender_id,
                        "relationship_type": relationship_type,
                        "relationship_strength": relationship_strength,
                    },
                    memory=self.memory,
                )
                dialog = self.prompt_manager.format_prompt_to_dialog(
                    self.chat_belief_update_prompt_name, state_dict
                )

                belief_update_response = await self.llm.atext_request(
                    dialog=dialog,
                    response_format={"type": "json_object"},
                    context=self._build_prompt_context(
                        prompt_name=self.chat_belief_update_prompt_name,
                        state_dict=state_dict,
                        func_name="do_chat",
                    ),
                )
                belief_update = json_repair.loads(belief_update_response)  # type: ignore
                if matched_relation is not None:
                    matched_relation.affinity = belief_update.get("affinity", matched_relation.affinity)
                    matched_relation.trust = belief_update.get("trust", matched_relation.trust)
                    matched_relation.familiarity = belief_update.get("familiarity", matched_relation.familiarity)

                get_logger().debug(
                    f"Agent {self.id}: Updated relationship with {sender_id}: {relationship_type}, Affinity: {belief_update.get('affinity', 'n/a')}, Trust: {belief_update.get('trust', 'n/a')}, Familiarity: {belief_update.get('familiarity', 'n/a')}"
                )



                required_fields = self.prompt_manager.get_required_fields(
                    self.chat_response_decision_prompt_name
                )
                state_dict = await self.prompt_manager.build_agent_state(
                    required_fields=required_fields,
                    context={
                        "content": content,
                        "relationship_strength": relationship_strength,
                        "relationship_type": relationship_type,
                        "recent_chat_history": recent_chat_history,
                    },
                    memory=self.memory,
                )
                dialog = self.prompt_manager.format_prompt_to_dialog(
                    self.chat_response_decision_prompt_name, state_dict
                )

                respond = await self.llm.atext_request(
                    dialog=dialog,
                    response_format={"type": "json_object"},
                    context=self._build_prompt_context(
                        prompt_name=self.chat_response_decision_prompt_name,
                        state_dict=state_dict,
                        func_name="do_chat",
                    ),
                )
                should_respond = json_repair.loads(respond)["should_respond"]  # type: ignore
                if should_respond == "NO":
                    return ""
                response_content = json_repair.loads(respond)["response_content"]  # type: ignore
                if response_content:
                    # Update chat history with response
                    chat_histories[sender_id] += f"，me: {response_content}"
                    await self.memory.status.update("chat_histories", chat_histories)

                    # Send response
                    await self.send_message_to_agent(sender_id, response_content)
                    return response_content
                else:
                    return ""
            except Exception as e:
                get_logger().warning(f"SocietyAgent Error in do_chat: {str(e)}")
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
            await self.memory.stream.add(topic="economy", description=description)
            if self.params.enable_cognition:
                await self.cognition_block.emotion_update(description)
            return ""

    async def react_to_intervention(self, intervention_message: str):
        """React to an intervention"""
        # cognition
        conclusion = await self.cognition_block.emotion_update(intervention_message)
        await self.save_agent_thought(conclusion)
        await self.memory.stream.add(topic="cognition", description=conclusion)
        # needs
        await self.needs_block.reflect_to_intervention(intervention_message)

    async def reset_position(self):
        """Reset the position of the agent."""
        assert self.environment is not None
        home = await self.status.get("home")
        home = home["aoi_position"]["aoi_id"]
        await self.environment.reset_person_position(person_id=self.id, aoi_id=home)

    async def step_execution(self):
        """Execute the current step in the active plan based on step type."""
        assert self.environment is not None
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
            self.context.current_step = current_step
            self.context.current_intention = current_step["intention"]
            self.context.plan_context = execution_context
            position = await self.memory.status.get("position")
            if "aoi_position" in position:
                current_step["position"] = position["aoi_position"]["aoi_id"]
            current_step["start_time"] = self.environment.get_tick()
            result = None
            if self.blocks and len(self.blocks) > 0:
                selected_block = await self.dispatcher.dispatch(self.context)
                if selected_block:
                    result = await selected_block.forward(self.context)
                    get_logger().debug(
                        f"Agent {self.id}: Executed block {selected_block.__class__.__name__} for intention '{self.context.current_intention}' with result: {result}"
                    )
                    result = result.model_dump()
                else:
                    get_logger().warning(
                        f"There is no appropriate block found for {self.context['current_intention']}"
                    )
                    node_id = await self.memory.stream.add(
                        topic="activity",
                        description=f"I finished: {self.context['current_intention']}",
                    )
                    result = {
                        "success": True,
                        "evaluation": f"I finished: {self.context['current_intention']}",
                        "consumed_time": random.randint(1, 100),
                        "node_id": node_id,
                    }
            else:
                get_logger().warning(
                    f"There is no block found for {self.context['current_intention']}"
                )
                node_id = await self.memory.stream.add(
                    topic="activity",
                    description=f"I finished: {self.context['current_intention']}",
                )
                result = {
                    "success": True,
                    "evaluation": f"I finished: {self.context['current_intention']}",
                    "consumed_time": random.randint(1, 100),
                    "node_id": node_id,
                }
            if result is not None:
                current_step["evaluation"] = result
                get_logger().debug(
                    f"Agent {self.id}: Step execution result: {result}"
                )
                
                # Extract key fields from result and add them to step for easy access by other blocks
                # This allows the needs block to access poi_id and other mobility data
                mobility_fields = ["poi_id", "next_place", "next_place_type", "to_place", "poi_type", "is_poi" ]
                for field in mobility_fields:
                    if field in result:
                        current_step[field] = result[field]
                        get_logger().debug(
                            f"Agent {self.id}: Extracted mobility field from step execution: {field} = {result[field]}"
                        )

            # Update current_step, plan, and execution_context information
            current_plan["steps"][step_index] = current_step
            await self.memory.status.update("current_plan", current_plan)
            await self.memory.status.update("execution_context", execution_context)
