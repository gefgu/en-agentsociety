from typing import Any, Optional
from .utils import clean_json_response
import json_repair
from pydantic import Field
from ...logger import get_logger
from ...memory import Memory
from ...agent import AgentToolbox, Block, BlockParams, Agent

__all__ = ["CognitionBlock"]


def extract_json(output_str):
    """Extract JSON substring from a raw string response.

    Args:
        output_str: Raw string output that may contain JSON data.

    Returns:
        Extracted JSON string if valid, otherwise None.

    Note:
        Searches for the first '{' and last '}' to isolate JSON content.
        Catches JSON decoding errors and logs warnings.
    """
    try:
        # Find the positions of the first '{' and the last '}'
        start = output_str.find("{")
        end = output_str.rfind("}")

        # Extract the substring containing the JSON
        json_str = output_str[start : end + 1]

        # Convert the JSON string to a dictionary
        return json_str
    except ValueError as e:
        get_logger().warning(f"Failed to extract JSON: {e}")
        return None


class CognitionBlockParams(BlockParams):
    top_k: int = Field(
        default=20, description="Number of most relevant memories to return"
    )


class CognitionBlock(Block):
    """A cognitive processing block handling daily updates of attitudes, thoughts, and emotions.

    Attributes:
        configurable_fields: List of configurable parameters (top_k).
        default_values: Default values for configurable parameters.
        fields_description: Metadata descriptions for configurable parameters.
        top_k: Number of most relevant memories retrieved for processing.
        last_check_time: Timestamp tracker for daily update cycles.
    """

    ParamsType = CognitionBlockParams
    name = "CognitionBlock"
    description = "Handles daily updates of attitudes, thoughts, and emotions"
    actions = {}
    NeedAgent = True

    def __init__(
        self,
        agent: Agent,
        toolbox: AgentToolbox,
        agent_memory: Memory,
        block_params: Optional[CognitionBlockParams] = None,
    ):
        """Initialize CognitionBlock with dependencies.

        Args:
            llm: Language Model interface for cognitive processing.
            environment: Environment for time-based operations.
            memory: Memory system to store/retrieve agent status and experiences.
        """
        super().__init__(
            toolbox=toolbox,
            agent_memory=agent_memory,
            block_params=block_params,
        )
        self.last_check_day = None
        self.set_agent(agent)
        self.agent_id = agent.id
        self.initialized_big5 = False
        self.initialized_hobbies = False
        self.initialized_preferences = False
        self.big5_prompt_name = "cognition_initialize_big5"
        self.hobbies_prompt_name = "cognition_initialize_hobbies"
        self.preferences_prompt_name = "cognition_initialize_preferences"
        self.attitude_prompt_name = "cognition_attitude_update"
        self.thought_prompt_name = "cognition_thought_update"
        self.emotion_prompt_name = "cognition_emotion_update"

    async def set_status(self, status):
        """Update multiple status fields in memory.

        Args:
            status: Dictionary of key-value pairs to update.
        """
        for key in status:
            await self.memory.status.update(key, status[key])
        return

    async def attitude_update(self):
        """Update agent's attitudes toward specific topics based on daily experiences.

        Workflow:
        1. Fetch agent's profile and current emotional state from memory.
        2. Retrieve relevant incidents using topic-based memory search.
        3. Construct a structured prompt combining profile, incidents, and previous attitude.
        4. Query LLM to generate updated attitude scores (0-10 scale).
        5. Retry up to 10 times on LLM failures.
        6. Persist updated attitudes to memory.

        Raises:
            Exception: If all LLM retries fail.
        """
        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        attitude = await self.memory.status.get("attitude")
        required_fields = self.prompt_manager.get_required_fields(self.attitude_prompt_name)
        for topic in attitude:
            incident_str = await self.memory.stream.search(
                query=topic, top_k=self.params.top_k
            )
            emotion = await self.memory.status.get("emotion")
            if incident_str:
                incident_text = "Today, these incidents happened:" + incident_str
            else:
                incident_text = "No incidents happened today."

            context = {
                "topic": topic,
                "previous_attitude": str(attitude[topic]),
                "incident_text": incident_text,
                "sadness": emotion["sadness"],
                "joy": emotion["joy"],
                "fear": emotion["fear"],
                "disgust": emotion["disgust"],
                "anger": emotion["anger"],
                "surprise": emotion["surprise"],
            }
            state_dict = await self.prompt_manager.build_agent_state(
                required_fields=required_fields,
                context=context,
                memory=self.memory,
            )
            dialog = self.prompt_manager.format_prompt_to_dialog(
                self.attitude_prompt_name, state_dict
            )
            evaluation = True
            response = {}
            for retry in range(10):
                try:
                    _response = await self.llm.atext_request(
                        dialog,
                        timeout=300,
                        response_format={"type": "json_object"},
                        context=self.build_llm_prompt_context(
                            prompt_name=self.attitude_prompt_name,
                            state_dict=state_dict,
                            func_name="attitude_update",
                        ),
                    )
                    json_str = extract_json(_response)
                    if json_str:
                        response: Any = json_repair.loads(json_str)
                        evaluation = False
                        break
                except Exception:
                    pass
            if evaluation:
                raise Exception(f"Request for attitude:{topic} update failed")
            attitude[topic] = response["attitude"]
        await self.memory.status.update("attitude", attitude)

    async def thought_update(self):
        """Generate daily reflections based on experiences and emotional state.

        Workflow:
        1. Build profile and emotion context from memory.
        2. Retrieve today's incidents.
        3. Construct a reflection prompt.
        4. Query LLM to generate thought summary and emotional keyword.
        5. Retry up to 10 times on LLM failures.
        6. Update memory with new thought and log cognition.

        Returns:
            Generated thought string.

        Raises:
            Exception: If all LLM retries fail.
        """
        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        required_fields = self.prompt_manager.get_required_fields(self.thought_prompt_name)
        incident_str = await self.memory.stream.search_today(top_k=20)
        emotion = await self.memory.status.get("emotion")
        if incident_str:
            incident_text = "Today, these incidents happened:\n" + incident_str
        else:
            incident_text = "No incidents happened today."

        state_dict = await self.prompt_manager.build_agent_state(
            required_fields=required_fields,
            context={
                "incident_text": incident_text,
                "sadness": emotion["sadness"],
                "joy": emotion["joy"],
                "fear": emotion["fear"],
                "disgust": emotion["disgust"],
                "anger": emotion["anger"],
                "surprise": emotion["surprise"],
            },
            memory=self.memory,
        )
        dialog = self.prompt_manager.format_prompt_to_dialog(
            self.thought_prompt_name, state_dict
        )

        evaluation = True
        response = {}
        for retry in range(10):
            try:
                _response = await self.llm.atext_request(
                    dialog,
                    timeout=300,
                    response_format={"type": "json_object"},
                    context=self.build_llm_prompt_context(
                        prompt_name=self.thought_prompt_name,
                        state_dict=state_dict,
                        func_name="thought_update",
                    ),
                )
                json_str = extract_json(_response)
                if json_str:
                    response: Any = json_repair.loads(json_str)
                    evaluation = False
                    break
            except Exception:
                pass
        if evaluation:
            raise Exception("Request for cognition update failed")

        thought = str(response["thought"])
        await self.memory.status.update("thought", thought)
        await self.memory.stream.add(topic="cognition", description=thought)

        return thought

    async def cross_day(self):
        """Check if a new day has started in the simulation environment.

        Returns:
            True if a new day is detected, False otherwise.
        """
        day, _ = self.environment.get_datetime()
        if self.last_check_day is None:
            self.last_check_day = day
            return True
        if day > self.last_check_day:
            self.last_check_day = day
            return True
        else:
            return False

    async def forward(self):
        """Main daily cognitive update entry point.

        Triggers:
            - thought_update()
            - attitude_update()
        Only executes when cross_day() detects a new day.
        """
        # cognition update: thought and attitude
        if await self.cross_day():
            await self.thought_update()
            await self.attitude_update()
            await self.memory.spatial.decay_beliefs()
            await self.agent.daily_schedule_block.forward()

    async def emotion_update(self, incident):
        """Update emotion intensities based on a specific incident.

        Args:
            incident: Description of the triggering event.

        Returns:
            Natural language conclusion about emotional state.

        Raises:
            Exception: If LLM requests fail after 10 retries.

        Workflow:
            1. Build emotion context from current state
            2. Incorporate incident details into prompt
            3. Query LLM for updated emotion scores and summary
            4. Update memory with new emotional state
        """
        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        required_fields = self.prompt_manager.get_required_fields(self.emotion_prompt_name)
        emotion = await self.memory.status.get("emotion")
        state_dict = await self.prompt_manager.build_agent_state(
            required_fields=required_fields,
            context={
                "incident_text": incident,
                "sadness": emotion["sadness"],
                "joy": emotion["joy"],
                "fear": emotion["fear"],
                "disgust": emotion["disgust"],
                "anger": emotion["anger"],
                "surprise": emotion["surprise"],
            },
            memory=self.memory,
        )
        dialog = self.prompt_manager.format_prompt_to_dialog(
            self.emotion_prompt_name, state_dict
        )

        evaluation = True
        exceptions = []
        response = {}
        for retry in range(10):
            try:
                _response = await self.llm.atext_request(
                    dialog,
                    timeout=300,
                    response_format={"type": "json_object"},
                    context=self.build_llm_prompt_context(
                        prompt_name=self.emotion_prompt_name,
                        state_dict=state_dict,
                        func_name="emotion_update",
                    ),
                )
                json_str = extract_json(_response)
                if json_str:
                    response: Any = json_repair.loads(json_str)
                    evaluation = False
                    break
            except Exception as e:
                exceptions.append(e)
                pass
        if evaluation:
            raise Exception("Request for cognition update failed, exceptions: " + str(exceptions))

        await self.memory.status.update(
            "emotion",
            {
                "sadness": int(response["sadness"]),
                "joy": int(response["joy"]),
                "fear": int(response["fear"]),
                "disgust": int(response["disgust"]),
                "anger": int(response["anger"]),
                "surprise": int(response["surprise"]),
            },
        )
        await self.memory.status.update("emotion_types", str(response["word"]))
        return response["conclusion"]

    async def initialize_big5(self):
        """Initialize the agent's Big Five personality traits based on profile information.

        Workflow:
        1. Retrieve agent's profile details from memory.
        2. Construct a prompt using the INITIAL_BIG5_PROMPT template.
        3. Query LLM to generate Big Five trait scores (1-3 scale).
        4. Retry up to 10 times on LLM failures.
        5. Update memory with initialized personality traits.

        Raises:
            Exception: If all LLM retries fail.
        """
        if self.initialized_big5:
            return

        current_big5 = await self.memory.status.get("big5", {})
        current_openness = current_big5.get("openness", 2)
        current_conscientiousness = current_big5.get("conscientiousness", 2)
        current_extraversion = current_big5.get("extraversion", 2)
        current_agreeableness = current_big5.get("agreeableness", 2)
        current_neuroticism = current_big5.get("neuroticism", 2)

        # See if already set
        if (current_openness != 2 or current_conscientiousness != 2 or current_extraversion != 2 or current_agreeableness != 2 or current_neuroticism != 2):
            self.initialized_big5 = True
            return

        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        required_fields = self.prompt_manager.get_required_fields(self.big5_prompt_name)
        state_dict = await self.prompt_manager.build_agent_state(
            required_fields=required_fields,
            context={},
            memory=self.memory,
        )
        dialog = self.prompt_manager.format_prompt_to_dialog(
            self.big5_prompt_name, state_dict
        )

        response = await self.llm.atext_request(
            dialog,
            response_format={"type": "json_object"},
            context=self.build_llm_prompt_context(
                prompt_name=self.big5_prompt_name,
                state_dict=state_dict,
                func_name="initialize_big5",
            ),
        )
        
        response = clean_json_response(response)
        response = json_repair.loads(response)
        psychographic_traits = response["psychographic_traits"]
        await self.memory.status.update("big5", psychographic_traits)
        self.initialized_big5 = True

    async def initialize_hobbies(self):
        """Initialize the agent's hobbies based on profile and psychographic information.

        Workflow:
        1. Retrieve agent's profile and Big Five traits from memory.
        2. Construct a prompt using the INITIAL_HOBBIES_PROMPT template.
        3. Query LLM to generate a list of suitable hobbies.
        4. Retry up to 10 times on LLM failures.
        5. Update memory with initialized hobbies.

        Raises:
            Exception: If all LLM retries fail.
        """

        if self.initialized_hobbies:
            return

        current_hobbies = await self.memory.status.get("hobbies")
        if len(current_hobbies) > 0:
            return

        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        required_fields = self.prompt_manager.get_required_fields(self.hobbies_prompt_name)
        state_dict = await self.prompt_manager.build_agent_state(
            required_fields=required_fields,
            context={},
            memory=self.memory,
        )
        dialog = self.prompt_manager.format_prompt_to_dialog(
            self.hobbies_prompt_name, state_dict
        )

        response = await self.llm.atext_request(
            dialog,
            response_format={"type": "json_object"},
            context=self.build_llm_prompt_context(
                prompt_name=self.hobbies_prompt_name,
                state_dict=state_dict,
                func_name="initialize_hobbies",
            ),
        )
        response = clean_json_response(response)
        response = json_repair.loads(response)
        hobbies = response["hobbies"]
        await self.memory.status.update("hobbies", hobbies)
        self.initialized_hobbies = True

    async def initialize_preferences(self):
        """Initialize the agent's behavioral preferences based on profile and psychographic information.

        Workflow:
        1. Retrieve agent's profile and Big Five traits from memory.
        2. Construct a prompt using the INITIAL_PREFERENCES_PROMPT template.
        3. Query LLM to generate specific behavioral parameters.
        4. Retry up to 10 times on LLM failures.
        5. Update memory with initialized preferences.

        Raises:
            Exception: If all LLM retries fail.
        """
        if self.initialized_preferences:
            return

        current_preferences = await self.memory.status.get("preferences")
        if current_preferences and (
            current_preferences.get("chronotype") != "standard" or
            current_preferences.get("risk_tolerance") != 0.5 or
            current_preferences.get("spending_tendency") != 0.5 or
            current_preferences.get("social_frequency") != 0.5 or 
            current_preferences.get("work_ethic") != 0.5 or
            current_preferences.get("leisure_preference") != "indoor"
        ):
            return

        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        required_fields = self.prompt_manager.get_required_fields(
            self.preferences_prompt_name
        )
        state_dict = await self.prompt_manager.build_agent_state(
            required_fields=required_fields,
            context={},
            memory=self.memory,
        )
        dialog = self.prompt_manager.format_prompt_to_dialog(
            self.preferences_prompt_name, state_dict
        )

        response = await self.llm.atext_request(
            dialog,
            response_format={"type": "json_object"},
            context=self.build_llm_prompt_context(
                prompt_name=self.preferences_prompt_name,
                state_dict=state_dict,
                func_name="initialize_preferences",
            ),
        )
        response = clean_json_response(response)
        response = json_repair.loads(response)
        preferences = response["preferences"]
        await self.memory.status.update("preferences", preferences)
        self.initialized_preferences = True
