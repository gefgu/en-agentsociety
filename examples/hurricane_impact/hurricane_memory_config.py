import json
import random
from collections import deque

import numpy as np
from typing import Any, Optional
from agentsociety.agent.memory_config_generator import Distribution, MemoryT, StatusAttribute

pareto_param = 8
payment_max_skill_multiplier_base = 950
payment_max_skill_multiplier = float(payment_max_skill_multiplier_base)
pmsm = payment_max_skill_multiplier
pareto_samples = np.random.pareto(pareto_param, size=(1000, 10))
clipped_skills = np.minimum(pmsm, (pmsm - 1) * pareto_samples + 1)
sorted_clipped_skills = np.sort(clipped_skills, axis=1)
agent_skills = list(sorted_clipped_skills.mean(axis=0))

import threading

index_lock = threading.Lock()


def memory_config_societyagent_hurrican(
    distributions: dict[str, Distribution],
    class_config: Optional[list[StatusAttribute]] = None,
) -> tuple[dict[str, MemoryT], dict[str, MemoryT], dict[str, Any]]:
    EXTRA_ATTRIBUTES = {
        "type": (str, "citizen"),
        # Needs Model
        "hunger_satisfaction": (float, 0.8, False),  # hunger satisfaction
        "energy_satisfaction": (float, 0.9, False),  # energy satisfaction
        "safety_satisfaction": (float, 0.3, False),  # safety satisfaction
        "social_satisfaction": (float, 0.5, False),  # social satisfaction
        "current_need": (str, "none", False),
        # Plan Behavior Model
        "current_plan": (list, [], False),
        "execution_context": (dict, {}, False),
        "plan_history": (list, [], False),
        # cognition
        "emotion": (
            dict,
            {
                "sadness": 5,
                "joy": 5,
                "fear": 5,
                "disgust": 5,
                "anger": 5,
                "surprise": 5,
            },
            False,
        ),
        "attitude": (dict, {}, True),
        "thought": (str, "Currently nothing good or bad is happening", True),
        "emotion_types": (str, "Relief", True),
        # economy
        "work_skill": (
            float,
            random.choice(agent_skills),
            True,
        ),  # work skill
        "tax_paid": (float, 0.0, False),  # tax paid
        "consumption_currency": (float, 0.0, False),  # consumption
        "goods_demand": (int, 0, False),
        "goods_consumption": (int, 0, False),
        "work_propensity": (float, 0.0, False),
        "consumption_propensity": (float, 0.0, False),
        "to_consumption_currency": (float, 0.0, False),
        "firm_id": (int, 0, False),
        "government_id": (int, 0, False),
        "bank_id": (int, 0, False),
        "nbs_id": (int, 0, False),
        "dialog_queue": (deque(maxlen=3), [], False),
        "firm_forward": (int, 0, False),
        "bank_forward": (int, 0, False),
        "nbs_forward": (int, 0, False),
        "government_forward": (int, 0, False),
        "forward": (int, 0, False),
        "depression": (float, 0.0, False),
        "ubi_opinion": (list, [], False),
        "working_experience": (list, [], False),
        "work_hour_month": (float, 160, False),
        "work_hour_finish": (float, 0, False),
        # social
        "friends": (list, [], False),  # friends list
        "relationships": (dict, {}, False),  # relationship strength with each friend
        "relation_types": (dict, {}, False),
        "chat_histories": (dict, {}, False),  # all chat histories
        "interactions": (dict, {}, False),  # all interaction records
        "to_discuss": (dict, {}, False),
        # mobility
        "number_poi_visited": (int, 1, False),
        "location_knowledge": (dict, {}, False),  # location knowledge
    }

    PROFILE = {
        "name": (
            str,
            random.choice(
                [
                    "Alice",
                    "Bob",
                    "Charlie",
                    "David",
                    "Eve",
                    "Frank",
                    "Grace",
                    "Helen",
                    "Ivy",
                    "Jack",
                    "Kelly",
                    "Lily",
                    "Mike",
                    "Nancy",
                    "Oscar",
                    "Peter",
                    "Queen",
                    "Rose",
                    "Sam",
                    "Tom",
                    "Ulysses",
                    "Vicky",
                    "Will",
                    "Xavier",
                    "Yvonne",
                    "Zack",
                ]
            ),
            True,
        ),
        "gender": (str, "unknown", True),
        "age": (int, 0, True),
        "education": (
            str,
            "unknown",
            True,
        ),
        "skill": (
            str,
            random.choice(
                [
                    "Good at problem-solving",
                    "Good at communication",
                    "Good at creativity",
                    "Good at teamwork",
                    "Other",
                ]
            ),
            True,
        ),
        "occupation": (
            str,
            random.choice(
                [
                    "Student",
                    "Teacher",
                    "Doctor",
                    "Engineer",
                    "Manager",
                    "Businessman",
                    "Artist",
                    "Athlete",
                    "Other",
                ]
            ),
            True,
        ),
        "family_consumption": (str, random.choice(["low", "medium", "high"]), True),
        "consumption": (str, "unknown", True),
        "personality": (
            str,
            random.choice(["outgoint", "introvert", "ambivert", "extrovert"]),
            True,
        ),
        "income": (float, 0, True),
        "currency": (float, random.randint(1000, 100000), True),
        "residence": (str, random.choice(["city", "suburb", "rural"]), True),
        "race": (
            str,
            "unknown",
            True,
        ),
        "religion": (
            str,
            random.choice(
                ["none", "Christian", "Muslim", "Buddhist", "Hindu", "Other"]
            ),
            True,
        ),
        "marriage_status": (
            str,
            random.choice(["not married", "married", "divorced", "widowed"]),
            True,
        ),
    }

    BASE = {
        "home": {"aoi_position": {"aoi_id": 0}},
        "work": {"aoi_position": {"aoi_id": 0}},
    }

    return EXTRA_ATTRIBUTES, PROFILE, BASE
