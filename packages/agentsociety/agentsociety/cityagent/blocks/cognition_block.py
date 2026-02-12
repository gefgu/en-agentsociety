from typing import Any, Optional
from .utils import clean_json_response
import json_repair
from pydantic import Field
from ...logger import get_logger
from ...memory import Memory
from ...agent import AgentToolbox, Block, FormatPrompt, BlockParams

__all__ = ["CognitionBlock"]


INITIAL_BIG5_PROMPT = """You are an intelligent agent psychographic initialization system. Based on the profile information below, please help initialize the agent's Big Five personality traits.

Profile Information:
- Gender: ${profile.gender}
- Education Level: ${profile.education} 
- Consumption Level: ${profile.consumption}
- Occupation: ${profile.occupation}
- Age: ${profile.age}
- Monthly Income: ${profile.income}
- Background Story: ${profile.background_story}

Please initialize the agent's Big Five personality traits based on the profile above. Consider generally accepted associations between the provided demographic/socioeconomic factors and personality (e.g., occupation requirements, age maturity principles).

Return the values in JSON format with the following structure:

Psychographic Traits (Integer values 1-3, where 1=Low, 2=Medium, 3=High):
- openness: Openness to experience (creativity, curiosity, preference for novelty)
- conscientiousness: Conscientiousness (discipline, organization, dependability)
- extraversion: Extraversion (sociability, energy, assertiveness)
- agreeableness: Agreeableness (compassion, cooperativeness, trust)
- neuroticism: Neuroticism (emotional instability, anxiety, moodiness)

Please response in json format, example:
{{
    "psychographic_traits": {{
        "openness": 2,
        "conscientiousness": 3,
        "extraversion": 2,
        "agreeableness": 2,
        "neuroticism": 1
    }}
}}
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
"""

INITIAL_HOBBIES_PROMPT = """You are an intelligent agent profile generator. Based on the demographic and psychographic information below, please generate a list of suitable hobbies for this agent.

Profile Information:
- Gender: ${profile.gender}
- Age: ${profile.age}
- Occupation: ${profile.occupation}
- Income: ${profile.income}
- Education: ${profile.education}
- Household type: {household}
- Life stage: {life_stage}

Psychographic Traits (1-3 scale):
- Openness: {openness}
- Conscientiousness: {conscientiousness}
- Extraversion: {extraversion}
- Agreeableness: {agreeableness}
- Neuroticism: {neuroticism}

Please generate a list of 2-5 hobbies. 
- Ensure the hobbies fit the agent's income level and age (e.g., "Golf" for higher income, "Video Games" for younger cohorts).
- Ensure the hobbies reflect their Big 5 personality (e.g., High Extraversion -> Team Sports; High Openness -> Painting/Travel; High Conscientiousness -> Gardening/Chess).
- These hobbies will be used to determine the agent's daily locations and routines.

Return the values in JSON format with the following structure:

{{
    "hobbies": [
        "Hobby Name 1",
        "Hobby Name 2",
        "Hobby Name 3"
    ]
}}

Example Response:
{{
    "hobbies": [
        "Photography",
        "Hiking",
        "Reading Sci-Fi"
    ]
}}

DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
"""

INITIAL_PREFERENCES_PROMPT = """You are an intelligent agent behavioral analyst. Based on the demographic and psychographic profile below, please initialize the agent's daily habits and behavioral preferences.

Profile Information:
- Age: ${profile.age}
- Occupation: ${profile.occupation}
- Income: ${profile.income}
- Household Composition: ${profile.household}

Psychographic Traits (1-3 scale):
- Openness: {openness}
- Conscientiousness: {conscientiousness}
- Extraversion: {extraversion}
- Agreeableness: {agreeableness}
- Neuroticism: {neuroticism}

Please generate specific behavioral parameters. Use the personality traits to guide these values (e.g., High Conscientiousness = Early Riser, Low Consumption; High Extraversion = High Social Frequency).

Return the values in JSON format with the following structure:

- chronotype: "early_bird" (wakes ~6am), "night_owl" (wakes ~10am), or "standard" (wakes ~7-8am).
- risk_tolerance: Float 0.0-1.0 (propensity to take financial or physical risks).
- spending_tendency: Float 0.0-1.0 (0=Frugal/Saver, 1=Impulsive/Spender).
- social_frequency: Float 0.0-1.0 (desired probability of initiating social interactions per day).
- work_ethic: Float 0.0-1.0 (tendency to work overtime or prioritize work tasks).
- leisure_preference: "outdoor", "indoor", "social", or "solitary" (dominant preference for free time).

Example Response:
{{
    "preferences": {{
        "chronotype": "night_owl",
        "risk_tolerance": 0.7,
        "spending_tendency": 0.8,
        "social_frequency": 0.9,
        "work_ethic": 0.3,
        "leisure_preference": "social"
    }}
}}

DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
DO NOT INCLUDE ANY COMMENTS IN YOUR RESPONSE.
"""



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
        agent_id: str,
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
        self.agent_id = agent_id
        self.initialized_big5 = False
        self.initialized_hobbies = False
        self.initialized_preferences = False

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
        attitude = await self.memory.status.get("attitude")
        big5 = await self.memory.status.get("big5", {})
        prompt_data = {
            "gender": await self.memory.status.get("gender"),
            "age": await self.memory.status.get("age"),
            "race": await self.memory.status.get("race"),
            "religion": await self.memory.status.get("religion"),
            "marriage_status": await self.memory.status.get("marriage_status"),
            "residence": await self.memory.status.get("residence"),
            "occupation": await self.memory.status.get("occupation"),
            "education": await self.memory.status.get("education"),
            "personality": await self.memory.status.get("personality"),
            "consumption": await self.memory.status.get("consumption"),
            "family_consumption": await self.memory.status.get("family_consumption"),
            "income": await self.memory.status.get("income"),
            "skill": await self.memory.status.get("skill"),
            "thought": await self.memory.status.get("thought"),
            "emotion_types": await self.memory.status.get("emotion_types"),
            "openness": big5.get("openness", 2),
            "conscientiousness": big5.get("conscientiousness", 2),
            "extraversion": big5.get("extraversion", 2),
            "agreeableness": big5.get("agreeableness", 2),
            "neuroticism": big5.get("neuroticism", 2),
        }
        for topic in attitude:
            description_prompt = """
            You are a {gender}, aged {age}, belonging to the {race} race and identifying as {religion}. 
            Your marital status is {marriage_status}, and you currently reside in a {residence} area. 
            Your occupation is {occupation}, and your education level is {education}. 
            You are {personality}, with a consumption level of {consumption} and a family consumption level of {family_consumption}. 
            Your income is {income}, and you are skilled in {skill}.
            My current emotion intensities are (0 meaning not at all, 10 meaning very much):
            sadness: {sadness}, joy: {joy}, fear: {fear}, disgust: {disgust}, anger: {anger}, surprise: {surprise}.
            Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
            openness: {openness}, conscientiousness: {conscientiousness}, extraversion: {extraversion}, agreeableness: {agreeableness}, neuroticism: {neuroticism}.
            You have the following thoughts: {thought}.
            In the following 21 words, I have chosen {emotion_types} to represent your current status:
            Joy, Distress, Resentment, Pity, Hope, Fear, Satisfaction, Relief, Disappointment, Pride, Admiration, Shame, Reproach, Liking, Disliking, Gratitude, Anger, Gratification, Remorse, Love, Hate.
            """
            incident_str = await self.memory.stream.search(
                query=topic, top_k=self.params.top_k
            )
            if incident_str:
                incident_prompt = "Today, these incidents happened:"
                incident_prompt += incident_str
            else:
                incident_prompt = "No incidents happened today."
            previous_attitude = str(attitude[topic])  # Convert to string
            problem_prompt = (
                f"You need to decide your attitude towards topic: {topic}, "
                f"which you previously rated your attitude towards this topic as: {previous_attitude} "
                "(0 meaning oppose, 10 meaning support). "
                'Please return a new attitude rating (0-10, smaller meaning oppose, larger meaning support) in JSON format, and explain, e.g. {{"attitude": 5}}'
            )
            question_prompt = description_prompt + incident_prompt + problem_prompt
            question_prompt = FormatPrompt(question_prompt)
            emotion = await self.memory.status.get("emotion")
            sadness = emotion["sadness"]
            joy = emotion["joy"]
            fear = emotion["fear"]
            disgust = emotion["disgust"]
            anger = emotion["anger"]
            surprise = emotion["surprise"]
            prompt_data["sadness"] = sadness
            prompt_data["joy"] = joy
            prompt_data["fear"] = fear
            prompt_data["disgust"] = disgust
            prompt_data["anger"] = anger
            prompt_data["surprise"] = surprise

            await question_prompt.format(**prompt_data)
            evaluation = True
            response = {}
            for retry in range(10):
                try:
                    _response = await self.llm.atext_request(
                        question_prompt.to_dialog(),
                        timeout=300,
                        response_format={"type": "json_object"},
                        context={
                            "block_name": self.name,
                            "func_name": "attitude_update",
                            "agent_id": self.agent_id
                        }
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
        description_prompt = """
        You are a {gender}, aged {age}, belonging to the {race} race and identifying as {religion}. 
        Your marital status is {marriage_status}, and you currently reside in a {residence} area. 
        Your occupation is {occupation}, and your education level is {education}. 
        You are {personality}, with a consumption level of {consumption} and a family consumption level of {family_consumption}. 
        Your income is {income}, and you are skilled in {skill}.
        My current emotion intensities are (0 meaning not at all, 10 meaning very much):
        sadness: {sadness}, joy: {joy}, fear: {fear}, disgust: {disgust}, anger: {anger}, surprise: {surprise}.
        Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
        openness: {openness}, conscientiousness: {conscientiousness}, extraversion: {extraversion}, agreeableness: {agreeableness}, neuroticism: {neuroticism}.
        You have the following thoughts: {thought}.
        In the following 21 words, I have chosen {emotion_types} to represent your current status:
        Joy, Distress, Resentment, Pity, Hope, Fear, Satisfaction, Relief, Disappointment, Pride, Admiration, Shame, Reproach, Liking, Disliking, Gratitude, Anger, Gratification, Remorse, Love, Hate.
        """
        incident_str = await self.memory.stream.search_today(top_k=20)
        if incident_str:
            incident_prompt = "Today, these incidents happened:\n" + incident_str
        else:
            incident_prompt = "No incidents happened today."
        question_prompt = """
            Please review what happened today and share your thoughts and feelings about it.
            Consider your current emotional state and experiences, then:
            1. Summarize your thoughts and reflections on today's events
            2. Choose one word that best describes your current emotional state from: Joy, Distress, Resentment, Pity, Hope, Fear, Satisfaction, Relief, Disappointment, Pride, Admiration, Shame, Reproach, Liking, Disliking, Gratitude, Anger, Gratification, Remorse, Love, Hate.
            Return in JSON format, e.g. {{"thought": "Currently nothing good or bad is happening, I think ...."}}"""
        question_prompt = description_prompt + incident_prompt + question_prompt
        question_prompt = FormatPrompt(question_prompt)
        emotion = await self.memory.status.get("emotion")
        sadness = emotion["sadness"]
        joy = emotion["joy"]
        fear = emotion["fear"]
        disgust = emotion["disgust"]
        anger = emotion["anger"]
        surprise = emotion["surprise"]
        big5 = await self.memory.status.get("big5", {})
        await question_prompt.format(
            gender=await self.memory.status.get("gender"),
            age=await self.memory.status.get("age"),
            race=await self.memory.status.get("race"),
            religion=await self.memory.status.get("religion"),
            marriage_status=await self.memory.status.get("marriage_status"),
            residence=await self.memory.status.get("residence"),
            occupation=await self.memory.status.get("occupation"),
            education=await self.memory.status.get("education"),
            personality=await self.memory.status.get("personality"),
            consumption=await self.memory.status.get("consumption"),
            family_consumption=await self.memory.status.get("family_consumption"),
            income=await self.memory.status.get("income"),
            skill=await self.memory.status.get("skill"),
            sadness=sadness,
            joy=joy,
            fear=fear,
            disgust=disgust,
            anger=anger,
            surprise=surprise,
            emotion=await self.memory.status.get("emotion"),
            thought=await self.memory.status.get("thought"),
            emotion_types=await self.memory.status.get("emotion_types"),
            openness=big5.get("openness", 2),
            conscientiousness=big5.get("conscientiousness", 2),
            extraversion=big5.get("extraversion", 2),
            agreeableness=big5.get("agreeableness", 2),
            neuroticism=big5.get("neuroticism", 2),
        )

        evaluation = True
        response = {}
        for retry in range(10):
            try:
                _response = await self.llm.atext_request(
                    question_prompt.to_dialog(),
                    timeout=300,
                    response_format={"type": "json_object"},
                    context={
                        "block_name": self.name,
                        "func_name": "thought_update",
                        "agent_id": self.agent_id
                    }
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
            return False
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
        description_prompt = """
        You are a {gender}, aged {age}, belonging to the {race} race and identifying as {religion}. 
        Your marital status is {marriage_status}, and you currently reside in a {residence} area. 
        Your occupation is {occupation}, and your education level is {education}. 
        You are {personality}, with a consumption level of {consumption} and a family consumption level of {family_consumption}. 
        Your income is {income}, and you are skilled in {skill}.
        My current emotion intensities are (0 meaning not at all, 10 meaning very much):
        sadness: {sadness}, joy: {joy}, fear: {fear}, disgust: {disgust}, anger: {anger}, surprise: {surprise}.
        Your Big Five personality traits are: (1=Low, 2=Medium, 3=High)
        openness: {openness}, conscientiousness: {conscientiousness}, extraversion: {extraversion}, agreeableness: {agreeableness}, neuroticism: {neuroticism}.
        You have the following thoughts: {thought}.
        In the following 21 words, choose one word to represent your current status:
        [Joy, Distress, Resentment, Pity, Hope, Fear, Satisfaction, Relief, Disappointment, Pride, Admiration, Shame, Reproach, Liking, Disliking, Gratitude, Anger, Gratification, Remorse, Love, Hate].
        """

        incident_prompt = f"{incident}"  # waiting for incident port
        question_prompt = """
            Please reconsider your emotion intensities: 
            sadness, joy, fear, disgust, anger, surprise (0 meaning not at all, 10 meaning very much).
            Return in JSON format, e.g. {{"sadness": 5, "joy": 5, "fear": 5, "disgust": 5, "anger": 5, "surprise": 5, "conclusion": "I feel ...", "word": "Relief"}}"""
        question_prompt = description_prompt + incident_prompt + question_prompt
        question_prompt = FormatPrompt(question_prompt)
        emotion = await self.memory.status.get("emotion")
        sadness = emotion["sadness"]
        joy = emotion["joy"]
        fear = emotion["fear"]
        disgust = emotion["disgust"]
        anger = emotion["anger"]
        surprise = emotion["surprise"]
        big5 = await self.memory.status.get("big5", {})
        await question_prompt.format(
            gender=await self.memory.status.get("gender"),
            age=await self.memory.status.get("age"),
            race=await self.memory.status.get("race"),
            religion=await self.memory.status.get("religion"),
            marriage_status=await self.memory.status.get("marriage_status"),
            residence=await self.memory.status.get("residence"),
            occupation=await self.memory.status.get("occupation"),
            education=await self.memory.status.get("education"),
            personality=await self.memory.status.get("personality"),
            consumption=await self.memory.status.get("consumption"),
            family_consumption=await self.memory.status.get("family_consumption"),
            income=await self.memory.status.get("income"),
            skill=await self.memory.status.get("skill"),
            sadness=sadness,
            joy=joy,
            fear=fear,
            disgust=disgust,
            anger=anger,
            surprise=surprise,
            emotion=await self.memory.status.get("emotion"),
            thought=await self.memory.status.get("thought"),
            emotion_types=await self.memory.status.get("emotion_types"),
            openness=big5.get("openness", 2),
            conscientiousness=big5.get("conscientiousness", 2),
            extraversion=big5.get("extraversion", 2),
            agreeableness=big5.get("agreeableness", 2),
            neuroticism=big5.get("neuroticism", 2),
        )

        evaluation = True
        exceptions = []
        response = {}
        for retry in range(10):
            try:
                _response = await self.llm.atext_request(
                    question_prompt.to_dialog(),
                    timeout=300,
                    response_format={"type": "json_object"},
                    context={
                        "block_name": self.name,
                        "func_name": "emotion_update",
                        "agent_id": self.agent_id
                    }
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

        profile = {
            "gender": await self.memory.status.get("gender"),
            "education": await self.memory.status.get("education"),
            "consumption": await self.memory.status.get("consumption"),
            "occupation": await self.memory.status.get("occupation"),
            "age": await self.memory.status.get("age"),
            "income": await self.memory.status.get("income"),
            "background_story": await self.memory.status.get("background_story"),
        }

        prompt = FormatPrompt(INITIAL_BIG5_PROMPT)
        await prompt.format(profile=profile)

        response = await self.llm.atext_request(
            prompt.to_dialog(),
            response_format={"type": "json_object"},
            context={
                "block_name": self.name,
                "func_name": "initialize_big5",
                "agent_id": self.agent_id
            })
        
        response = clean_json_response(response)
        retry = 3
        while retry > 0:
            try:
                response = json_repair.loads(response)

                psychographic_traits = response["psychographic_traits"]
                await self.memory.status.update("big5", psychographic_traits)

                break
            except Exception:
                get_logger().warning(f"CognitionBlock.initalize_big5: Failed to parse JSON response, retrying... ({3 - retry + 1}/3)")
                retry -= 1
        if retry == 0:
            get_logger().warning(f"CognitionBlock.initalize_big5: Failed to parse JSON response after 3 attempts. Final response: {response}")
        else:
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

        profile = {
            "gender": await self.memory.status.get("gender"),
            "age": await self.memory.status.get("age"),
            "occupation": await self.memory.status.get("occupation"),
            "income": await self.memory.status.get("income"),
            "education": await self.memory.status.get("education"),
        }

        big5 = await self.memory.status.get("big5", {})

        household = await self.memory.status.get("household")
        life_stage = await self.memory.status.get("life_stage")

        prompt = FormatPrompt(INITIAL_HOBBIES_PROMPT)
        await prompt.format(
            profile=profile,
            openness=big5.get("openness", 2),
            conscientiousness=big5.get("conscientiousness", 2),
            extraversion=big5.get("extraversion", 2),
            agreeableness=big5.get("agreeableness", 2),
            neuroticism=big5.get("neuroticism", 2),
            household=household,
            life_stage=life_stage
        )

        response = await self.llm.atext_request(
            prompt.to_dialog(),
            response_format={"type": "json_object"},
            context={
                "block_name": self.name,
                "func_name": "initialize_hobbies",
                "agent_id": self.agent_id
            }
        )
        response = clean_json_response(response)
        retry = 3
        while retry > 0:
            try:
                response = json_repair.loads(response)
                hobbies = response["hobbies"]
                await self.memory.status.update("hobbies", hobbies)
                break
            except Exception:
                get_logger().warning(f"CognitionBlock.initalize_hobbies: Failed to parse JSON response, retrying... ({3 - retry + 1}/3)")
                retry -= 1
        if retry == 0:            
            get_logger().warning(f"CognitionBlock.initalize_hobbies: Failed to parse JSON response after 3 attempts. Final response: {response}")
        else:
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

        profile = {
            "age": await self.memory.status.get("age"),
            "occupation": await self.memory.status.get("occupation"),
            "income": await self.memory.status.get("income"),
            "household": await self.memory.status.get("household"),
        }

        big5 = await self.memory.status.get("big5", {})

        prompt = FormatPrompt(INITIAL_PREFERENCES_PROMPT)
        await prompt.format(
            profile=profile,
            openness=big5.get("openness", 2),
            conscientiousness=big5.get("conscientiousness", 2),
            extraversion=big5.get("extraversion", 2),
            agreeableness=big5.get("agreeableness", 2),
            neuroticism=big5.get("neuroticism", 2),
        )

        response = await self.llm.atext_request(
            prompt.to_dialog(),
            response_format={"type": "json_object"},
            context={
                "block_name": self.name,
                "func_name": "initialize_preferences",
                "agent_id": self.agent_id
            }
        )
        response = clean_json_response(response)
        retry = 3
        while retry > 0:
            try:
                response = json_repair.loads(response)
                preferences = response["preferences"]
                await self.memory.status.update("preferences", preferences)
                break
            except Exception:
                get_logger().warning(f"CognitionBlock.initalize_preferences: Failed to parse JSON response, retrying... ({3 - retry + 1}/3)")
                retry -= 1
        if retry == 0:
            get_logger().warning(f"CognitionBlock.initalize_preferences: Failed to parse JSON response after 3 attempts. Final response: {response}")
        else:
            self.initialized_preferences = True
