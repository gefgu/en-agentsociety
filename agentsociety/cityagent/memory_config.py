import copy
import random
from abc import abstractmethod
from collections import deque
from typing import Any, Callable, List, Optional, Union

import jsonc
import numpy as np

from ..agent.distribution import (ChoiceDistribution, ConstantDistribution,
                                  Distribution, UniformIntDistribution,
                                  sample_field_value)
from ..agent.memory_config_generator import MemoryT
from ..environment.economy import EconomyEntityType

pareto_param = 8
payment_max_skill_multiplier_base = 950
payment_max_skill_multiplier = float(payment_max_skill_multiplier_base)
pmsm = payment_max_skill_multiplier
pareto_samples = np.random.pareto(pareto_param, size=(1000, 10))
clipped_skills = np.minimum(pmsm, (pmsm - 1) * pareto_samples + 1)
sorted_clipped_skills = np.sort(clipped_skills, axis=1)
agent_skills = list(sorted_clipped_skills.mean(axis=0))

__all__ = [
    "memory_config_societyagent",
    "memory_config_firm",
    "memory_config_government",
    "memory_config_bank",
    "memory_config_nbs",
    "DEFAULT_DISTRIBUTIONS",
]


# Default distributions for different profile fields
DEFAULT_DISTRIBUTIONS: dict[str, Distribution] = {
    "name": ChoiceDistribution(
        choices=[
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
    "gender": ChoiceDistribution(choices=["male", "female"]),
    "age": UniformIntDistribution(min_value=18, max_value=65),
    "education": ChoiceDistribution(
        choices=["Doctor", "Master", "Bachelor", "College", "High School"]
    ),
    "skill": ChoiceDistribution(
        choices=[
            "Good at problem-solving",
            "Good at communication",
            "Good at creativity",
            "Good at teamwork",
            "Other",
        ]
    ),
    "occupation": ChoiceDistribution(
        choices=[
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
    "family_consumption": ChoiceDistribution(choices=["low", "medium", "high"]),
    "consumption": ChoiceDistribution(
        choices=["low", "slightly low", "medium", "slightly high", "high"]
    ),
    "personality": ChoiceDistribution(
        choices=["outgoint", "introvert", "ambivert", "extrovert"]
    ),
    "income": UniformIntDistribution(min_value=1000, max_value=20000),
    "currency": UniformIntDistribution(min_value=1000, max_value=100000),
    "residence": ChoiceDistribution(choices=["city", "suburb", "rural"]),
    "city": ConstantDistribution(value="New York"),
    "race": ChoiceDistribution(
        choices=[
            "Chinese",
            "American",
            "British",
            "French",
            "German",
            "Japanese",
            "Korean",
            "Russian",
            "Other",
        ]
    ),
    "religion": ChoiceDistribution(
        choices=["none", "Christian", "Muslim", "Buddhist", "Hindu", "Other"]
    ),
    "marital_status": ChoiceDistribution(
        choices=["not married", "married", "divorced", "widowed"]
    ),
}


def memory_config_societyagent(
    distributions: dict[str, Distribution],
) -> tuple[dict[str, MemoryT], dict[str, MemoryT], dict[str, Any]]:
    EXTRA_ATTRIBUTES = {
        "type": (str, "citizen"),
        # Needs Model
        "hunger_satisfaction": (float, 0.9, False),  # hunger satisfaction
        "energy_satisfaction": (float, 0.9, False),  # energy satisfaction
        "safety_satisfaction": (float, 0.4, False),  # safety satisfaction
        "social_satisfaction": (float, 0.6, False),  # social satisfaction
        "current_need": (str, "none", False),
        # Plan Behavior Model
        "current_plan": (dict, {}, False),
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
        "firm_id": (int, sample_field_value(distributions, "firm_id"), False),
        "government_id": (
            int,
            sample_field_value(distributions, "government_id"),
            False,
        ),
        "bank_id": (int, sample_field_value(distributions, "bank_id"), False),
        "nbs_id": (int, sample_field_value(distributions, "nbs_id"), False),
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
        "public_friends": (list, [], False),  # public friends list
        "relationships": (dict, {}, False),  # relationship strength with each friend
        "relation_types": (dict, {}, False),
        "chat_histories": (dict, {}, False),  # all chat histories
        "interactions": (dict, {}, False),  # all interaction records
        # mobility
        "number_poi_visited": (int, 1, False),
        "location_knowledge": (dict, {}, False),  # location knowledge
    }

    PROFILE = {
        "name": (str, sample_field_value(distributions, "name"), True),
        "gender": (str, sample_field_value(distributions, "gender"), True),
        "age": (int, sample_field_value(distributions, "age"), True),
        "education": (str, sample_field_value(distributions, "education"), True),
        "skill": (str, sample_field_value(distributions, "skill"), True),
        "occupation": (str, sample_field_value(distributions, "occupation"), True),
        "family_consumption": (
            str,
            sample_field_value(distributions, "family_consumption"),
            True,
        ),
        "consumption": (str, sample_field_value(distributions, "consumption"), True),
        "personality": (str, sample_field_value(distributions, "personality"), True),
        "income": (float, sample_field_value(distributions, "income"), True),
        "currency": (float, sample_field_value(distributions, "currency"), True),
        "residence": (str, sample_field_value(distributions, "residence"), True),
        "city": (str, sample_field_value(distributions, "city"), True),
        "race": (str, sample_field_value(distributions, "race"), True),
        "religion": (str, sample_field_value(distributions, "religion"), True),
        "marital_status": (
            str,
            sample_field_value(distributions, "marital_status"),
            True,
        ),
    }

    BASE = {
        "home": {
            "aoi_position": {"aoi_id": sample_field_value(distributions, "home_aoi_id")}
        },
        "work": {
            "aoi_position": {"aoi_id": sample_field_value(distributions, "work_aoi_id")}
        },
    }

    return EXTRA_ATTRIBUTES, PROFILE, BASE


def memory_config_firm(
    distributions: dict[str, Distribution],
) -> tuple[dict[str, MemoryT], dict[str, Union[MemoryT, float]], dict[str, Any]]:
    EXTRA_ATTRIBUTES = {
        "type": (int, EconomyEntityType.Firm),
        "location": {
            "aoi_position": {"aoi_id": sample_field_value(distributions, "aoi_id")}
        },
        "price": (float, float(np.mean(agent_skills))),
        "inventory": (int, 0),
        "employees": (list, []),
        "employees_agent_id": (list, []),
        "nominal_gdp": (list, []),  # useless
        "real_gdp": (list, []),
        "unemployment": (list, []),
        "wages": (list, []),
        "demand": (int, 0),
        "sales": (int, 0),
        "prices": (list, [float(np.mean(agent_skills))]),
        "working_hours": (list, []),
        "depression": (list, []),
        "consumption_currency": (list, []),
        "income_currency": (list, []),
        "locus_control": (list, []),
        "bracket_cutoffs": (
            list,
            list(np.array([0, 9875, 40125, 85525, 163300, 207350, 518400]) / 12),
        ),
        "bracket_rates": (list, [0.1, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]),
        "interest_rate": (float, 0.03),
        "citizen_ids": (list, []),
        "firm_id": (int, 0),
    }
    return EXTRA_ATTRIBUTES, {"currency": 1e12}, {}


def memory_config_government(
    distributions: dict[str, Distribution],
) -> tuple[dict[str, MemoryT], dict[str, Union[MemoryT, float]], dict[str, Any]]:
    EXTRA_ATTRIBUTES = {
        "type": (int, EconomyEntityType.Government),
        # 'bracket_cutoffs': (list, list(np.array([0, 97, 394.75, 842, 1607.25, 2041, 5103])*100/12)),
        "bracket_cutoffs": (
            list,
            list(np.array([0, 9875, 40125, 85525, 163300, 207350, 518400]) / 12),
        ),
        "bracket_rates": (list, [0.1, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]),
        "citizen_ids": (list, []),
        "citizens_agent_id": (list, []),
        "nominal_gdp": (list, []),  # useless
        "real_gdp": (list, []),
        "unemployment": (list, []),
        "wages": (list, []),
        "prices": (list, [float(np.mean(agent_skills))]),
        "working_hours": (list, []),
        "depression": (list, []),
        "consumption_currency": (list, []),
        "income_currency": (list, []),
        "locus_control": (list, []),
        "inventory": (int, 0),
        "interest_rate": (float, 0.03),
        "price": (float, float(np.mean(agent_skills))),
        "employees": (list, []),
        "firm_id": (int, 0),
    }
    return EXTRA_ATTRIBUTES, {"currency": 1e12}, {}


def memory_config_bank(
    distributions: dict[str, Distribution],
) -> tuple[dict[str, MemoryT], dict[str, Union[MemoryT, float]], dict[str, Any]]:
    EXTRA_ATTRIBUTES = {
        "type": (int, EconomyEntityType.Bank),
        "interest_rate": (float, 0.03),
        "citizen_ids": (list, []),
        "bracket_cutoffs": (
            list,
            list(np.array([0, 9875, 40125, 85525, 163300, 207350, 518400]) / 12),
        ),  # useless
        "bracket_rates": (list, [0.1, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]),
        "inventory": (int, 0),
        "nominal_gdp": (list, []),  # useless
        "real_gdp": (list, []),
        "unemployment": (list, []),
        "wages": (list, []),
        "prices": (list, [float(np.mean(agent_skills))]),
        "working_hours": (list, []),
        "depression": (list, []),
        "consumption_currency": (list, []),
        "income_currency": (list, []),
        "locus_control": (list, []),
        "price": (float, float(np.mean(agent_skills))),
        "employees": (list, []),
        "firm_id": (int, 0),
    }
    return EXTRA_ATTRIBUTES, {"currency": 1e12}, {}


def memory_config_nbs(
    distributions: dict[str, Distribution],
) -> tuple[dict[str, MemoryT], dict[str, Union[MemoryT, float]], dict[str, Any]]:
    EXTRA_ATTRIBUTES = {
        "type": (int, EconomyEntityType.NBS),
        # economy simulator
        "citizen_ids": (list, []),
        "nominal_gdp": (dict, {}),
        "real_gdp": (dict, {}),
        "unemployment": (dict, {}),
        "wages": (dict, {}),
        "prices": (dict, {"0": float(np.mean(agent_skills))}),
        "working_hours": (dict, {}),
        "depression": (dict, {}),
        "consumption_currency": (dict, {}),
        "income_currency": (dict, {}),
        "locus_control": (dict, {}),
        # other
        "firm_id": (int, 0),
        "bracket_cutoffs": (
            list,
            list(np.array([0, 9875, 40125, 85525, 163300, 207350, 518400]) / 12),
        ),  # useless
        "bracket_rates": (list, [0.1, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]),
        "inventory": (int, 0),
        "interest_rate": (float, 0.03),
        "price": (float, float(np.mean(agent_skills))),
        "employees": (list, []),
        "forward_times": (int, 0),
    }
    return EXTRA_ATTRIBUTES, {"currency": 1e12}, {}
