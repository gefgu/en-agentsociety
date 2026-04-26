from typing import Any, Awaitable, Callable


class PromptMemoryHandler:
    def __init__(self):
        self._handlers = self.build_handlers()

    async def _get_position_now(self, memory: Any) -> Any:
        return await memory.status.get("position", {})

    async def _get_home_location(self, memory: Any) -> Any:
        return await memory.status.get("home", {})

    async def _get_work_location(self, memory: Any) -> Any:
        return await memory.status.get("work", {})

    async def _get_location_knowledge(self, memory: Any) -> Any:
        return await memory.status.get("location_knowledge", {})

    async def _get_persona_parts(self, memory: Any) -> dict[str, Any]:
        return {
            "name": await memory.status.get("name", "unknown"),
            "age": await memory.status.get("age", "unknown"),
            "gender": await memory.status.get("gender", "unknown"),
            "occupation": await memory.status.get("occupation", "unknown"),
            "personality": await memory.status.get("personality", "unknown"),
        }

    async def _get_big5(self, memory: Any) -> dict[str, Any]:
        loaded = await memory.status.get("big5", {})
        return loaded if isinstance(loaded, dict) else {}

    async def _get_preferences(self, memory: Any) -> dict[str, Any]:
        loaded = await memory.status.get("preferences", {})
        return loaded if isinstance(loaded, dict) else {}

    @staticmethod
    def normalize(value: Any) -> Any:
        return ", ".join(str(v) for v in value) if isinstance(value, list) else value

    async def _get_current_plan(self, memory: Any) -> dict[str, Any]:
        loaded = await memory.status.get("current_plan", {})
        return loaded if isinstance(loaded, dict) else {}

    async def resolve_plan(self, _: str, memory: Any) -> Any:
        return await memory.status.get("plan", "unknown")

    async def resolve_intention(self, field: str, memory: Any) -> Any:
        if field != "current_intention":
            return "unknown"
        plan_cache = await self._get_current_plan(memory)
        if not plan_cache.get("steps"):
            return "unknown"
        idx = plan_cache.get("index", 0)
        try:
            return plan_cache["steps"][idx].get("intention", "unknown")
        except Exception:
            return "unknown"

    async def resolve_emotion(self, _: str, memory: Any) -> Any:
        return await memory.status.get("emotion_types", "unknown")

    async def resolve_current_emotion(self, _: str, memory: Any) -> Any:
        return await memory.status.get("emotion_types", "unknown")

    async def resolve_current_thought(self, _: str, memory: Any) -> Any:
        return await memory.status.get("thought", "unknown")

    async def resolve_memory_field(self, field: str, memory: Any) -> Any:
        return await memory.status.get(field, "unknown")

    async def resolve_list_memory_field(self, field: str, memory: Any) -> Any:
        value = await memory.status.get(field, [])
        return self.normalize(value)

    async def resolve_plan_target(self, _: str, memory: Any) -> Any:
        plan_cache = await self._get_current_plan(memory)
        return plan_cache.get("target", "unknown")

    async def resolve_location(self, _: str, memory: Any) -> Any:
        position_now = await self._get_position_now(memory)
        home_location = await self._get_home_location(memory)
        work_location = await self._get_work_location(memory)
        location_knowledge = await self._get_location_knowledge(memory)

        current_location = "Outside"
        if (
            isinstance(position_now, dict)
            and isinstance(home_location, dict)
            and "aoi_position" in position_now
            and position_now["aoi_position"] == home_location.get("aoi_position")
        ):
            current_location = "At home"
        elif (
            isinstance(position_now, dict)
            and isinstance(work_location, dict)
            and "aoi_position" in position_now
            and position_now["aoi_position"] == work_location.get("aoi_position")
        ):
            current_location = "At workplace"
        elif (
            isinstance(position_now, dict)
            and isinstance(location_knowledge, dict)
            and "aoi_position" in position_now
        ):
            known_locations = {
                info.get("id")
                for info in location_knowledge.values()
                if isinstance(info, dict)
            }
            if position_now["aoi_position"] in known_locations:
                current_location = str(position_now["aoi_position"])

        return current_location

    async def resolve_big5(self, field: str, memory: Any) -> Any:
        big5 = await self._get_big5(memory)
        return big5.get(field, 2)

    async def resolve_preference(self, field: str, memory: Any) -> Any:
        preferences = await self._get_preferences(memory)
        preference_defaults: dict[str, Any] = {
            "work_ethic": 0.5,
            "chronotype": "standard",
            "social_frequency": 0.5,
            "leisure_preference": "indoor",
            "risk_tolerance": 0.5,
            "spending_tendency": 0.5,
        }
        return preferences.get(field, preference_defaults[field])

    async def resolve_current_time(self, _: str, memory: Any) -> Any:
        return await memory.status.get("current_time", "unknown")

    async def resolve_consumption_level(self, _: str, memory: Any) -> Any:
        return await memory.status.get("consumption", "unknown")

    async def resolve_persona(self, _: str, memory: Any) -> Any:
        persona_parts = await self._get_persona_parts(memory)
        return (
            f"Name: {persona_parts['name']}, "
            f"Age: {persona_parts['age']}, "
            f"Gender: {persona_parts['gender']}, "
            f"Occupation: {persona_parts['occupation']}, "
            f"Personality: {persona_parts['personality']}"
        )

    def build_handlers(
        self,
    ) -> dict[str, Callable[[str, Any], Awaitable[Any]]]:
        handlers: dict[str, Callable[[str, Any], Awaitable[Any]]] = {
            "plan": self.resolve_plan,
            "current_intention": self.resolve_intention,
            "intention": self.resolve_intention,
            "emotion_types": self.resolve_emotion,
            "dominant_emotion": self.resolve_emotion,
            "current_emotion": self.resolve_current_emotion,
            "current_thought": self.resolve_current_thought,
            "household": self.resolve_memory_field,
            "life_stage": self.resolve_memory_field,
            "hobbies": self.resolve_list_memory_field,
            "goals": self.resolve_list_memory_field,
            "current_plan_target": self.resolve_plan_target,
            "plan_target": self.resolve_plan_target,
            "current_location": self.resolve_location,
            "current_position": self.resolve_location,
            "current_time": self.resolve_current_time,
            "consumption_level": self.resolve_consumption_level,
            "persona": self.resolve_persona,
        }

        for trait in {
            "openness",
            "conscientiousness",
            "extraversion",
            "agreeableness",
            "neuroticism",
        }:
            handlers[trait] = self.resolve_big5

        for pref in {
            "work_ethic",
            "chronotype",
            "social_frequency",
            "leisure_preference",
            "risk_tolerance",
            "spending_tendency",
        }:
            handlers[pref] = self.resolve_preference

        return handlers

    async def resolve_field(self, field: str, memory: Any) -> Any:
        handler = self._handlers.get(field)
        if handler is not None:
            return self.normalize(await handler(field, memory))

        # Generic fallback: resolve arbitrary memory status fields only when requested.
        return self.normalize(await memory.status.get(field, "unknown"))
