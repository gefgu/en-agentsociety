import json
import random
from collections import deque

import numpy as np

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


def memory_config_societyagent_hurrican():
    if not hasattr(memory_config_societyagent_hurrican, "profile_list"):
        with open("profiles_with_aoi.json", "r") as f:
            setattr(memory_config_societyagent_hurrican, "profile_list", json.load(f))
    profile_list = getattr(memory_config_societyagent_hurrican, "profile_list")
    index = random.randint(0, len(profile_list) - 1)
    profile = profile_list[index]

    EXTRA_ATTRIBUTES = {
        "type": (str, "citizen"),
        "city": (str, "Columbia", True),
        # Needs Model
        "hunger_satisfaction": (float, 0.8, False),  # hunger satisfaction
        "energy_satisfaction": (float, 0.9, False),  # energy satisfaction
        "safety_satisfaction": (float, 0.3, False),  # safety satisfaction
        "social_satisfaction": (float, 0.5, False),  # social satisfaction
        "current_need": (str, "none", False),
        # Plan Behavior Model
        "current_plan": (list, [], False),
        "current_step": (dict, {"intention": "", "type": ""}, False),
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
        "gender": (str, profile["gender"], True),
        "age": (int, profile["age"], True),
        "education": (
            str,
            profile["education"],
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
        "consumption": (str, profile["consumption"], True),
        "personality": (
            str,
            random.choice(["outgoint", "introvert", "ambivert", "extrovert"]),
            True,
        ),
        "income": (float, profile["income"], True),
        "currency": (float, random.randint(1000, 100000), True),
        "residence": (str, random.choice(["city", "suburb", "rural"]), True),
        "race": (
            str,
            profile["race"],
            True,
        ),
        "religion": (
            str,
            random.choice(
                ["none", "Christian", "Muslim", "Buddhist", "Hindu", "Other"]
            ),
            True,
        ),
        "marital_status": (
            str,
            random.choice(["not married", "married", "divorced", "widowed"]),
            True,
        ),
    }

    BASE = {
        "home": {"aoi_position": {"aoi_id": profile["home"]}},
        "work": {"aoi_position": {"aoi_id": profile["work"]}},
    }

    return EXTRA_ATTRIBUTES, PROFILE, BASE
