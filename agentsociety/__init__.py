"""
agentsociety: City agent building framework
"""

import logging

from .agent import Agent, AgentType, CitizenAgent, InstitutionAgent
from .environment import Simulator
from .llm import SentenceEmbedding
from .simulation import AgentSimulation

# Create an agentsociety logger
logger = logging.getLogger("agentsociety")
logger.setLevel(logging.WARNING) # Default level

# If there is no handler, add one
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

__all__ = [
    "Agent",
    "Simulator",
    "CitizenAgent",
    "InstitutionAgent",
    "SentenceEmbedding",
    "AgentSimulation",
    "AgentType",
]
