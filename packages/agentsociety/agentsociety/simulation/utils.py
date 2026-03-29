"""Shared helper functions for simulation modules."""

from typing import Callable, Optional, cast

from ..agent import Agent, MemoryAttribute
from ..agent.distribution import Distribution
from ..agent.memory_config_generator import (
	MemoryConfig,
	MemoryConfigGenerator,
	default_memory_config_citizen,
	default_memory_config_supervisor,
)
from ..configs import AgentConfig, Config
from ..s3 import S3Config


def set_default_agent_config(config: Config) -> Config:
	"""
	Validates configuration options to ensure the user selects the correct combination.

	- **Description**:
		- Sets default memory_config_func for citizen/supervisor agents if not specified.

	- **Returns**:
		- `Config`: The validated configuration instance.
	"""
	for agent_config in config.agents.citizens:
		if agent_config.memory_config_func is None:
			agent_config.memory_config_func = default_memory_config_citizen

	if config.agents.supervisor is not None:
		if config.agents.supervisor.memory_config_func is None:
			config.agents.supervisor.memory_config_func = default_memory_config_supervisor

	return config


def init_agent_class(agent_config: AgentConfig, s3config: S3Config):
	"""
	Initialize the agent class.

	- **Args**:
		- `agent_config` (AgentConfig): The agent configuration.

	- **Returns**:
		- `agents`: A list of tuples, each containing an agent class, a memory config generator, and an index.
	"""
	agent_class: type[Agent] = agent_config.agent_class
	n: int = agent_config.number
	memory_config_func = cast(
		Callable[
			[dict[str, Distribution], Optional[list[MemoryAttribute]]],
			MemoryConfig,
		],
		agent_config.memory_config_func,
	)
	generator = MemoryConfigGenerator(
		memory_config_func,
		agent_class.StatusAttributes,
		agent_config.number,
		agent_config.memory_from_file,
		(
			agent_config.memory_distributions
			if agent_config.memory_distributions is not None
			else {}
		),
		s3config,
	)
	agent_params = agent_config.agent_params
	if agent_params is None:
		agent_params = agent_class.ParamsType()
	else:
		agent_params = agent_class.ParamsType.model_validate(agent_params)
	blocks = agent_config.blocks
	agents = [(agent_class, generator, i, agent_params, blocks) for i in range(n)]
	return agents, generator


def evaluate_filter(filter_str: str, profile: dict) -> bool:
	"""
	Evaluate a filter string against a profile dictionary.

	- **Args**:
		- `filter_str` (str): The filter string to evaluate, e.g. "${profile.age} > 0"
		- `profile` (dict): The profile dictionary to evaluate against

	- **Returns**:
		- `bool`: True if the filter matches, False otherwise

	- **Note**:
		- Returns False if profile is empty
		- Returns False if any key in filter_str is not in profile
	"""
	if not profile:
		return False

	import re

	pattern = r"\${profile\.([^}]+)}"
	required_keys = set(re.findall(pattern, filter_str))

	for key in required_keys:
		current = profile
		for part in key.split("."):
			if not isinstance(current, dict) or part not in current:
				return False
			current = current[part]

	for key in required_keys:
		current = profile
		for part in key.split("."):
			current = current[part]
		filter_str = filter_str.replace(f"${{profile.{key}}}", repr(current))

	try:
		return eval(filter_str)
	except Exception:
		return False

