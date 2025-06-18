from typing import NamedTuple, Optional

from fastembed import SparseTextEmbedding

from ..environment.environment import Environment
from ..llm.llm import LLM
from ..message import Messager
from ..storage import DatabaseWriter

__all__ = ["AgentToolbox"]


class AgentToolbox(NamedTuple):
    """
    A named tuple representing the toolbox of an agent.
    """

    llm: LLM
    environment: Environment
    messager: Messager
    embedding: SparseTextEmbedding
    database_writer: Optional[DatabaseWriter]
