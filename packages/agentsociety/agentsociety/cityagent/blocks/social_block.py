# Due to the current limitations of the simulator's support, only NoneBlock, MessageBlock, and FindPersonBlock are available in the Dispatcher.

import time
from typing import Any, Optional
import json_repair

from ...agent import (
    AgentToolbox,
    Block,
    FormatPrompt,
    BlockParams,
    DotDict,
    BlockContext,
)
from ...logger import get_logger
from ...memory import Memory
from ...agent.dispatcher import BlockDispatcher
from .utils import TIME_ESTIMATE_PROMPT, clean_json_response
from ..sharing_params import SocietyAgentBlockOutput
from pydantic import Field
import numpy as np


class MessagePromptManager:
    """
    Manages the creation of message prompts by dynamically formatting templates with agent-specific data.
    """

    def __init__(self):
        pass

    async def get_prompt(
        self,
        memory,
        step: dict[str, Any],
        environment_info: str,
        target: int,
        template: str,
    ):
        """Generates a formatted prompt for message creation.

        Args:
            memory: Agent's memory to retrieve status data.
            step: Current workflow step containing intention and context.
            target: ID of the target agent for communication.
            template: Raw template string to be formatted.

        Returns:
            Formatted prompt string with placeholders replaced by agent-specific data.
        """

        # Retrieve data
        social_network = await memory.status.get("social_network") or []
        relationship = None
        for relation in social_network:
            if relation.target_id == target:
                relationship = relation
                break
        assert (
            relationship is not None
        ), f"MessagePromptManager: No relation found for target {target}"
        relationship_type = relationship.kind
        relationship_strength = f"Relationship Strength (0-1 Scale): Affinity {relationship.affinity}, Familiarity {relationship.familiarity}, Trust {relationship.trust}"
        chat_histories = await memory.status.get("chat_histories") or {}

        # Build discussion topic constraints
        discussion_constraint = ""
        topics = await memory.status.get("attitude")
        topics = topics.keys()
        if topics:
            topics = ", ".join(f'"{topic}"' for topic in topics)
            discussion_constraint = (
                f"Limit your discussion to the following topics: {topics}."
            )

        # Get Big Five personality traits
        big5 = await memory.status.get("big5", {})

        # Get household and life stage
        household = await memory.status.get("household", "unknown")
        life_stage = await memory.status.get("life_stage", "unknown")
        hobbies = await memory.status.get("hobbies", [])
        hobbies_str = ", ".join(hobbies) if isinstance(hobbies, list) else str(hobbies)

        # Get preferences
        preferences = await memory.status.get("preferences", {})
        social_frequency = preferences.get("social_frequency", 0.5)

        # Format prompt
        format_prompt = FormatPrompt(template)
        await format_prompt.format(
            name=await memory.status.get("name", "unknown"),
            gender=await memory.status.get("gender", "unknown"),
            occupation=await memory.status.get("occupation", "unknown"),
            education=await memory.status.get("education", "unknown"),
            personality=await memory.status.get("personality", "unknown"),
            emotion_types=await memory.status.get("emotion_types", "unknown"),
            thought=await memory.status.get("thought", "unknown"),
            background_story=await memory.status.get("background_story", "unknown"),
            relationship_type=relationship_type,
            relationship_strength=relationship_strength,
            chat_history=(
                chat_histories.get(target, "")
                if isinstance(chat_histories, dict)
                else ""
            ),
            intention=step.get("intention", ""),
            discussion_constraint=discussion_constraint,
            environment_info=environment_info,
            household=household,
            life_stage=life_stage,
            hobbies=hobbies_str,
            openness=big5.get("openness", 2),
            conscientiousness=big5.get("conscientiousness", 2),
            extraversion=big5.get("extraversion", 2),
            agreeableness=big5.get("agreeableness", 2),
            neuroticism=big5.get("neuroticism", 2),
            social_frequency=social_frequency,
        )

        return format_prompt.to_dialog()


class SocialNoneBlock(Block):
    """
    NoneBlock
    """

    name = "SocialNoneBlock"
    description = "Handle all other cases if you are not trying to determine the social target or send a message to someone"

    def __init__(self, toolbox: AgentToolbox, agent_memory: Memory):
        super().__init__(toolbox=toolbox, agent_memory=agent_memory)
        self.guidance_prompt = FormatPrompt(template=TIME_ESTIMATE_PROMPT)

    async def forward(self, context):
        """Executes default behavior when no specific block matches the intention.

        Args:
            step: Current workflow step with 'intention' and other metadata.
            context: Additional execution context (e.g., agent's plan).

        Returns:
            A result dictionary indicating success/failure, time consumed, and execution details.
        """
        intention = str(context["current_step"].get("intention", "socialize"))

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
        chronotype = preferences.get("chronotype", "standard")
        work_ethic = preferences.get("work_ethic", 0.5)
        leisure_preference = preferences.get("leisure_preference", "indoor")
        social_frequency = preferences.get("social_frequency", 0.5)

        await self.guidance_prompt.format(
            plan=context["plan_context"]["plan"],
            intention=intention,
            emotion_types=await self.memory.status.get("emotion_types"),
            household=household,
            life_stage=life_stage,
            hobbies=hobbies_str,
            goals=goals_str,
            openness=big5.get("openness", 2),
            conscientiousness=big5.get("conscientiousness", 2),
            extraversion=big5.get("extraversion", 2),
            agreeableness=big5.get("agreeableness", 2),
            neuroticism=big5.get("neuroticism", 2),
            chronotype=chronotype,
            work_ethic=work_ethic,
            leisure_preference=leisure_preference,
        )
        result = await self.llm.atext_request(
            self.guidance_prompt.to_dialog(),
            response_format={"type": "json_object"},
            context={
                "block_name": self.name,
                "func_name": "forward",
                "agent_id": self.agent.id,
            },
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

        # configurable fields
        self.default_message_template = """
My name is {name}, I am a {gender}
My occupation is {occupation}. 
My education level is {education}.
My personality is {personality}.
My current emotion is: {emotion_types}.
My current thought is: {thought}.
My background story is: {background_story}.
Household type: {household}
Life stage: {life_stage}
Hobbies: {hobbies}

Big Five Personality Traits (1=Low, 2=Medium, 3=High):
- Openness: {openness}
- Conscientiousness: {conscientiousness}
- Extraversion: {extraversion}
- Agreeableness: {agreeableness}
- Neuroticism: {neuroticism}

Now, I want to generate a social message to a target, my relationship with him/her:
Our relationship type is: {relationship_type}
Our relationship strength: {relationship_strength} (0-1, higher is stronger)
My previous chat history with him/her is:
{chat_history}

My intention is: {intention}.

Environment Information:
{environment_info}

Please generate a natural and contextually appropriate message.
Keep it under 100 characters.
The message should reflect my personality and background.

{discussion_constraint}

Please output the message from a first-person perspective, without any other text
"""

        self.prompt_manager = MessagePromptManager()

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

            # Get formatted prompt using prompt manager
            formatted_prompt = await self.prompt_manager.get_prompt(
                self.memory,
                context["current_step"],
                environment_info,
                target,
                self.default_message_template,
            )

            # Generate message
            message = await self.llm.atext_request(formatted_prompt, timeout=300)

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