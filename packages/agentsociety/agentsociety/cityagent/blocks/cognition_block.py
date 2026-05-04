from typing import Optional
from pydantic import Field
from ...logger import get_logger
from ...memory import Memory
from ...agent import AgentToolbox, Block, BlockParams, Agent

__all__ = ["CognitionBlock"]


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
        """Update agent's attitudes toward specific topics based on daily experiences."""
        attitude = await self.memory.status.get("attitude")
        if not isinstance(attitude, dict):
            get_logger().warning(f"attitude is not a dict ({type(attitude).__name__}), skipping attitude update")
            return
        for topic in attitude:
            incident_str = await self.memory.stream.search(
                query=topic, top_k=self.params.top_k
            )
            emotion = await self.memory.status.get("emotion")
            incident_text = (
                "Today, these incidents happened:" + incident_str
                if incident_str
                else "No incidents happened today."
            )

            result = await self.execute_prompt(
                self.attitude_prompt_name,
                {
                    "topic": topic,
                    "previous_attitude": str(attitude[topic]),
                    "incident_text": incident_text,
                    "sadness": emotion["sadness"],
                    "joy": emotion["joy"],
                    "fear": emotion["fear"],
                    "disgust": emotion["disgust"],
                    "anger": emotion["anger"],
                    "surprise": emotion["surprise"],
                },
                func_name="attitude_update",
                max_retries=9,
                timeout=300,
                validate=lambda p: "attitude" in p,
            )

            if not result.success:
                raise Exception(f"Request for attitude:{topic} update failed: {result.error}")

            if "attitude" not in result.parsed:
                get_logger().warning(
                    f"LLM response missing 'attitude' key for topic '{topic}', keeping previous value."
                )
            attitude[topic] = result.parsed.get("attitude", attitude[topic])
        await self.memory.status.update("attitude", attitude)

    async def thought_update(self):
        """Generate daily reflections based on experiences and emotional state.

        Returns:
            Generated thought string.
        """
        incident_str = await self.memory.stream.search_today(top_k=20)
        emotion = await self.memory.status.get("emotion")
        incident_text = (
            "Today, these incidents happened:\n" + incident_str
            if incident_str
            else "No incidents happened today."
        )

        result = await self.execute_prompt(
            self.thought_prompt_name,
            {
                "incident_text": incident_text,
                "sadness": emotion["sadness"],
                "joy": emotion["joy"],
                "fear": emotion["fear"],
                "disgust": emotion["disgust"],
                "anger": emotion["anger"],
                "surprise": emotion["surprise"],
            },
            func_name="thought_update",
            max_retries=9,
            timeout=300,
            validate=lambda p: "thought" in p,
        )

        if not result.success:
            raise Exception(f"Request for cognition update failed: {result.error}")

        if "thought" not in result.parsed:
            get_logger().warning("LLM response missing 'thought' key, using default.")
        thought = str(result.parsed.get("thought", "Nothing in particular happened today."))
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
        if await self.cross_day():
            await self.thought_update()
            await self.attitude_update()
            if self.agent.params.simulation_mode == "citysim":
                await self.memory.spatial.decay_beliefs()
                await self.agent.daily_schedule_block.forward()

    async def emotion_update(self, incident):
        """Update emotion intensities based on a specific incident.

        Args:
            incident: Description of the triggering event.

        Returns:
            Natural language conclusion about emotional state.
        """
        _emotion_keys = {"sadness", "joy", "fear", "disgust", "anger", "surprise", "word", "conclusion"}
        emotion = await self.memory.status.get("emotion")

        result = await self.execute_prompt(
            self.emotion_prompt_name,
            {
                "incident_text": incident,
                "sadness": emotion["sadness"],
                "joy": emotion["joy"],
                "fear": emotion["fear"],
                "disgust": emotion["disgust"],
                "anger": emotion["anger"],
                "surprise": emotion["surprise"],
            },
            func_name="emotion_update",
            max_retries=9,
            timeout=300,
            validate=lambda p: _emotion_keys.issubset(p.keys()),
        )

        if not result.success:
            raise Exception(f"Request for cognition update failed: {result.error}")

        parsed = result.parsed
        missing = _emotion_keys - parsed.keys()
        if missing:
            get_logger().warning(f"LLM response missing emotion keys {missing}, using defaults.")
        await self.memory.status.update(
            "emotion",
            {
                "sadness": int(parsed.get("sadness", emotion["sadness"])),
                "joy": int(parsed.get("joy", emotion["joy"])),
                "fear": int(parsed.get("fear", emotion["fear"])),
                "disgust": int(parsed.get("disgust", emotion["disgust"])),
                "anger": int(parsed.get("anger", emotion["anger"])),
                "surprise": int(parsed.get("surprise", emotion["surprise"])),
            },
        )
        await self.memory.status.update("emotion_types", str(parsed.get("word", "neutral")))
        return parsed.get("conclusion", "")

    async def initialize_big5(self):
        """Initialize the agent's Big Five personality traits based on profile information."""
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

        result = await self.execute_prompt(
            self.big5_prompt_name,
            {},
            func_name="initialize_big5",
        )

        if result.success and "psychographic_traits" in result.parsed:
            psychographic_traits = result.parsed["psychographic_traits"]
        else:
            get_logger().warning(
                f"LLM response missing 'psychographic_traits', using defaults. Error: {result.error}"
            )
            psychographic_traits = {
                "openness": 2, "conscientiousness": 2, "extraversion": 2,
                "agreeableness": 2, "neuroticism": 2,
            }
        await self.memory.status.update("big5", psychographic_traits)
        self.initialized_big5 = True

    async def initialize_hobbies(self):
        """Initialize the agent's hobbies based on profile and psychographic information."""
        if self.initialized_hobbies:
            return

        current_hobbies = await self.memory.status.get("hobbies")
        if len(current_hobbies) > 0:
            return

        result = await self.execute_prompt(
            self.hobbies_prompt_name,
            {},
            func_name="initialize_hobbies",
        )

        if result.success and "hobbies" in result.parsed:
            hobbies = result.parsed["hobbies"]
        else:
            get_logger().warning(
                f"LLM response missing 'hobbies', keeping existing. Error: {result.error}"
            )
            hobbies = current_hobbies
        await self.memory.status.update("hobbies", hobbies)
        self.initialized_hobbies = True

    async def initialize_preferences(self):
        """Initialize the agent's behavioral preferences based on profile and psychographic information."""
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

        result = await self.execute_prompt(
            self.preferences_prompt_name,
            {},
            func_name="initialize_preferences",
        )

        if result.success and "preferences" in result.parsed:
            preferences = result.parsed["preferences"]
        else:
            get_logger().warning(
                f"LLM response missing 'preferences', keeping existing. Error: {result.error}"
            )
            preferences = current_preferences
        await self.memory.status.update("preferences", preferences)
        self.initialized_preferences = True
