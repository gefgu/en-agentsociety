# Due to the current limitations of the simulator's support, only NoneBlock, MessageBlock, and FindPersonBlock are available in the Dispatcher.

from typing import Any, Optional
import json_repair

from ...agent import (
    AgentToolbox,
    Block,
    BlockParams,
    DotDict,
    BlockContext,
)
from ...logger import get_logger
from ...memory import Memory
from ...agent.dispatcher import BlockDispatcher
from .utils import clean_json_response
from ..sharing_params import SocietyAgentBlockOutput
from pydantic import Field
import numpy as np


class SocialNoneBlock(Block):
    """
    NoneBlock
    """

    name = "SocialNoneBlock"
    description = "Handle all other cases if you are not trying to determine the social target or send a message to someone"

    def __init__(self, toolbox: AgentToolbox, agent_memory: Memory):
        super().__init__(toolbox=toolbox, agent_memory=agent_memory)
        self.time_estimate_prompt_name = "social_time_estimate"

    async def forward(self, context):
        """Executes default behavior when no specific block matches the intention.

        Args:
            step: Current workflow step with 'intention' and other metadata.
            context: Additional execution context (e.g., agent's plan).

        Returns:
            A result dictionary indicating success/failure, time consumed, and execution details.
        """
        intention = str(context["current_step"].get("intention", "socialize"))

        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        required_fields = self.prompt_manager.get_required_fields(
            self.time_estimate_prompt_name
        )
        state_dict = await self.prompt_manager.build_agent_state(
            required_fields=required_fields,
            context={
                "intention": intention,
                "plan_context": context.get("plan_context", {}),
                "current_step": context.get("current_step", {}),
            },
            memory=self.memory,
        )
        dialog = self.prompt_manager.format_prompt_to_dialog(
            self.time_estimate_prompt_name, state_dict
        )

        result = await self.llm.atext_request(
            dialog,
            response_format={"type": "json_object"},
            context=self.build_llm_prompt_context(
                prompt_name=self.time_estimate_prompt_name,
                state_dict=state_dict,
                func_name="forward",
            ),
        )
        result = clean_json_response(result)

        try:
            result: Any = json_repair.loads(result)
            node_id = await self.memory.stream.add(
                topic="social", description=f"I want to: {intention}"
            )
            return {
                "success": True,
                "evaluation": f"Finished {intention}",
                "consumed_time": result["time"],
                "node_id": node_id,
            }
        except Exception as e:
            get_logger().warning(
                f"Error occurred while parsing the evaluation response: {e}, original result: {result}"
            )
            node_id = await self.memory.stream.add(
                topic="social", description=f"I failed to execute {intention}"
            )
            return {
                "success": False,
                "evaluation": f"Failed to execute {intention}",
                "consumed_time": 5,
                "node_id": node_id,
            }


class FindPersonBlock(Block):
    """
    Block for selecting an appropriate agent to socialize with based on relationship strength and context.
    """

    name = "FindPersonBlock"
    description = "Find a suitable person to socialize with"

    def __init__(self, toolbox: AgentToolbox, agent_memory: Memory):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )

    async def forward(self, context: DotDict):
        """Identifies a target agent and interaction mode (online/offline).

        Args:
            context: Additional execution context (may store selected target).

        Returns:
            Result dict with target agent, interaction mode, and execution status.
        """
        try:
            # Get friends list and relationship strength
            my_social_network = await self.memory.status.get("social_network", [])
            if len(my_social_network) == 0:
                node_id = await self.memory.stream.add(
                    topic="social",
                    description="I can't find any target to contact with in my social network.",
                )
                return {
                    "success": False,
                    "evaluation": "No target found in social network.",
                    "consumed_time": 5,
                    "node_id": node_id,
                }

            person_weights = []
            for relation in my_social_network:
                weight = (relation.affinity + relation.trust + relation.familiarity) / 3
                person_weights.append((relation.target_id, relation.kind, weight))
            
            total_weight = sum(weight for _, _, weight in person_weights)
            if total_weight == 0:
                # If all weights are zero, assign equal probability
                person_weights = [(target_id, kind, 1 / len(person_weights)) for target_id, kind, weight in person_weights]
            else:
                person_weights = [(target_id, kind, weight / total_weight) for target_id, kind, weight in person_weights]

            # Create separate arrays for selection
            probabilities = np.array([weight for _, _, weight in person_weights])
            indices = np.arange(len(person_weights))

            # Select an index based on probabilities
            selected_idx = np.random.choice(indices, p=probabilities)

            # Get the selected person data
            target_id, relationship_type, _ = person_weights[selected_idx]
            mode = "online"

            node_id = await self.memory.stream.add(
                topic="social",
                description=f"I selected the friend {target_id} for {mode} interaction",
            )
            return {
                "success": True,
                "evaluation": f"Selected friend {target_id} for {mode} interaction",
                "consumed_time": 15,
                "mode": mode,
                "target": target_id,
                "node_id": node_id,
            }

        except Exception as e:
            get_logger().warning(f"Error in finding person: {e}")
            node_id = await self.memory.stream.add(
                topic="social",
                description="I can't find any friends to socialize with.",
            )
            return {
                "success": False,
                "evaluation": f"Error in finding person: {str(e)}",
                "consumed_time": 5,
                "node_id": node_id,
            }


class MessageBlock(Block):
    """Generate and send messages"""

    name = "MessageBlock"
    description = "Send social message to someone (including online and offline, phone call, social post, etc.)"

    def __init__(self, toolbox: AgentToolbox, agent_memory: Memory):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
        )
        self.find_person_block = FindPersonBlock(toolbox, agent_memory)
        self.message_prompt_name = "social_message_generation"

    async def _build_message_context(self, context: DotDict, target: int, environment_info: str) -> dict[str, Any]:
        social_network = await self.memory.status.get("social_network") or []
        relationship = next(
            (relation for relation in social_network if relation.target_id == target),
            None,
        )
        if relationship is None:
            raise ValueError(f"No relation found for target {target}")

        relationship_strength = (
            "Relationship Strength (0-1 Scale): "
            f"Affinity {relationship.affinity}, Familiarity {relationship.familiarity}, Trust {relationship.trust}"
        )

        chat_histories = await self.memory.status.get("chat_histories") or {}
        chat_history = (
            chat_histories.get(target, "") if isinstance(chat_histories, dict) else ""
        )

        discussion_constraint = ""
        topics = await self.memory.status.get("attitude") or {}
        topic_names = topics.keys() if hasattr(topics, "keys") else []
        if topic_names:
            topics_str = ", ".join(f'"{topic}"' for topic in topic_names)
            discussion_constraint = (
                f"Limit your discussion to the following topics: {topics_str}."
            )

        return {
            "relationship_type": relationship.kind,
            "relationship_strength": relationship_strength,
            "chat_history": chat_history,
            "intention": context.get("current_step", {}).get("intention", ""),
            "discussion_constraint": discussion_constraint,
            "environment_info": environment_info,
        }

    async def forward(self, context: DotDict):
        """Generates a message, sends it to the target, and updates chat history.

        Args:
            context: Execution context (may contain pre-selected target).

        Returns:
            Result dict with message content, target, and execution status.
        """
        target = None
        try:
            # Get target from context or find one
            target = context.get("target") if context else None
            if not target:
                result = await self.find_person_block.forward(context)
                if not result["success"]:
                    return {
                        "success": False,
                        "evaluation": "Could not find target for message",
                        "consumed_time": 5,
                        "node_id": result["node_id"],
                    }
                target = result["target"]

            environment_info = """"""
            weather = self.environment.sense("weather")
            if weather:
                environment_info += f"\nCurrent weather: {weather}"
            other_info = self.environment.sense("other_information")
            if other_info:
                environment_info += f"\nOther information: {other_info}"
            if not environment_info:
                environment_info = "No environment information"

            if self.prompt_manager is None:
                raise RuntimeError("PromptManager is not initialized")

            message_context = await self._build_message_context(
                context=context,
                target=target,
                environment_info=environment_info,
            )
            required_fields = self.prompt_manager.get_required_fields(
                self.message_prompt_name
            )
            state_dict = await self.prompt_manager.build_agent_state(
                required_fields=required_fields,
                context=message_context,
                memory=self.memory,
            )
            dialog = self.prompt_manager.format_prompt_to_dialog(
                self.message_prompt_name, state_dict
            )

            # Generate message
            message = await self.llm.atext_request(
                dialog,
                timeout=300,
                context=self.build_llm_prompt_context(
                    prompt_name=self.message_prompt_name,
                    state_dict=state_dict,
                    func_name="forward",
                ),
            )

            # Update chat history with proper format
            chat_histories = await self.memory.status.get("chat_histories") or {}
            if not isinstance(chat_histories, dict):
                chat_histories = {}
            if target not in chat_histories:
                chat_histories[target] = ""
            elif len(chat_histories[target]) > 0:
                chat_histories[target] += ", "
            chat_histories[target] += f"me: {message}"

            await self.memory.status.update("chat_histories", chat_histories)

            # Send message
            await self.agent.send_message_to_agent(target, message, type="social")
            node_id = await self.memory.stream.add(
                topic="social", description=f"I sent a message to {target}: {message}"
            )
            return {
                "success": True,
                "evaluation": f"Sent message to {target}: {message}",
                "consumed_time": 10,
                "node_id": node_id,
            }

        except Exception as e:
            get_logger().warning(f"Error in sending message: {e}")
            node_id = await self.memory.stream.add(
                topic="social", description=f"I can't send a message to {target}"
            )
            return {
                "success": False,
                "evaluation": f"Error in sending message: {str(e)}",
                "consumed_time": 5,
                "node_id": node_id,
            }


class SocialBlockParams(BlockParams): ...


class SocialBlockContext(BlockContext):
    target: Optional[int] = Field(
        default=None,
        description="The target agent id that the agent is going to socialize with",
    )


class SocialBlock(Block):
    """
    Orchestrates social interactions by dispatching to appropriate sub-blocks.
    """

    ParamsType = SocialBlockParams
    OutputType = SocietyAgentBlockOutput
    ContextType = SocialBlockContext
    NeedAgent = True
    name = "SocialBlock"
    description = "Do social interactions, for example, find a friend, send a message, and other social activities."
    actions = {
        "find_person": "Support the find person action, determine the social target.",
        "message": "Support the message action, send a message to the social target.",
        "social_none": "Support other social operations",
    }

    def __init__(
        self,
        toolbox: AgentToolbox,
        agent_memory: Memory,
        block_params: Optional[SocialBlockParams] = None,
    ):
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
            block_params=block_params,
        )
        self.find_person_block = FindPersonBlock(toolbox, agent_memory)
        self.message_block = MessageBlock(toolbox, agent_memory)
        self.noneblock = SocialNoneBlock(toolbox, agent_memory)
        self.dispatcher = BlockDispatcher(toolbox, agent_memory)

        self.trigger_time = 0
        self.token_consumption = 0

        self.dispatcher.register_blocks(
            [self.find_person_block, self.message_block, self.noneblock]
        )

    async def forward(self, agent_context: DotDict) -> SocietyAgentBlockOutput:
        """Main entry point for social interactions. Dispatches to sub-blocks based on context.

        Args:
            step: Workflow step containing intention and metadata.
            context: Additional execution context.

        Returns:
            Result dict from the executed sub-block.
        """
        try:
            self.trigger_time += 1

            context = agent_context | self.context
            self.message_block.set_agent(self.agent)
            # Select the appropriate sub-block using dispatcher
            selected_block = await self.dispatcher.dispatch(context)
            if not selected_block:
                return self.OutputType(
                    success=False,
                    evaluation=f"Failed to complete social interaction with default behavior: {context['current_intention']}",
                    consumed_time=15,
                    node_id=None,
                )
            # Execute the selected sub-block and get the result
            result = await selected_block.forward(context)
            return self.OutputType(**result)

        except Exception as e:
            get_logger().warning(f"Error in social block: {e}")
            return self.OutputType(
                success=False,
                evaluation=f"Failed to complete social interaction with default behavior: {str(e)}",
                consumed_time=15,
                node_id=None,
            )

    def set_agent(self, agent: Any) -> None:
        """Associate the block and its sub-blocks with a specific agent.

        Args:
            agent: The agent instance to associate with.
        """
        super().set_agent(agent)
        self.find_person_block.set_agent(agent)
        self.message_block.set_agent(agent)
        self.noneblock.set_agent(agent)


    async def get_number_of_contacts_in_last_7_days(self) -> int:
        """Calculate the number of unique contacts the agent has interacted with in the last 7 days.

        Returns:
            The count of unique contacts in the last 7 days.
        """
        # Search for unique target ids in the stream memory with topic "social" and description containing "I sent a message to"

        day, t = self.environment.get_datetime()
        unique_contacts = set()

        memory_nodes = await self.memory.stream.search(
            query ="I sent a message to",
            topic="social",
            day_range=(max(day - 7, 0), day),
            top_k=25
        )

        memory_nodes = memory_nodes.split("\n") if isinstance(memory_nodes, str) else memory_nodes

        for node in memory_nodes:
            description = node
            if description and "I sent a message to" in description:
                # Extract target id from the description
                parts = description.split("I sent a message to")
                if len(parts) > 1:
                    target_part = parts[1].strip()
                    target_id = target_part.split(":")[0].strip()
                    get_logger().info(f"Found contact in memory: {target_id}. Move to DEBUG later.")
                    unique_contacts.add(target_id)

        return len(unique_contacts)