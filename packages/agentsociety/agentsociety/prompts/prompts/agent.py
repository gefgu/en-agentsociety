"""Python prompt classes for Agent-level prompts (block dispatcher)."""

from __future__ import annotations

from typing import ClassVar, Optional

from pydantic import Field

from ..base import BasePrompt


def _s(v: object, d: str = "unknown") -> object:
    """Return *v* if not None, else *d*."""
    return v if v is not None else d


# ---------------------------------------------------------------------------
# block_dispatcher
# ---------------------------------------------------------------------------


class BlockDispatcherAgentsociety(BasePrompt):
    """Select the most appropriate registered block to handle an agent's current intention — agentsociety origin.

    This prompt produces free-text / function-calling output (no structured Output class).
    ``requires_free_text_generation()`` returns True automatically.
    """

    name: ClassVar[str] = "block_dispatcher"
    version: ClassVar[str] = "1.0.0"
    origin: ClassVar[str] = "agentsociety"
    description: ClassVar[str] = (
        "Select the most appropriate registered block to handle an agent's current intention"
    )

    current_intention: Optional[str] = Field(
        None,
        description="The agent's current intention describing the task to be dispatched.",
    )

    # No Output class — this prompt drives LLM function-calling, not JSON parsing.

    def format_prompt(self) -> str:
        return f"""Based on the task information (which describes the needs of the user), select the most appropriate block to handle the task.
Each block has its specific functionality as described in the function schema.

Task information:
{_s(self.current_intention)}
"""


class BlockDispatcherCitysim(BlockDispatcherAgentsociety):
    """Select the most appropriate registered block to handle an agent's current intention — citysim origin."""

    origin: ClassVar[str] = "citysim"

    # Template is identical to agentsociety; citysim adds no extra fields.
    # format_prompt() is inherited.
