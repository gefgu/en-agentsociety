import logging
import random

from agentsociety.llm import LLM
from agentsociety.workflow import Block, FormatPrompt

logger = logging.getLogger("agentsociety")

DISPATCHER_PROMPT = """
Based on the task information (which describes the needs of the user), select the most appropriate block to handle the task.
Each block has its specific functionality as described in the function schema.
        
Task information:
{step}
"""


class BlockDispatcher:
    """Orchestrates task routing between registered processing blocks.

    Attributes:
        llm: Language model interface for decision-making
        blocks: Registry of available processing blocks (name -> Block mapping)
        prompt: Formatted prompt template for LLM instructions
    """

    def __init__(self, llm: LLM):
        """Initialize dispatcher with LLM interface.

        Args:
            llm: Language model for block selection decisions
        """
        self.llm = llm
        self.blocks: dict[str, Block] = {}
        self.prompt = FormatPrompt(DISPATCHER_PROMPT)

    def register_blocks(self, blocks: list[Block]) -> None:
        """Register multiple processing blocks for dispatching.

        Args:
            blocks: List of Block instances to register
        """
        for block in blocks:
            block_name = block.__class__.__name__.lower()
            self.blocks[block_name] = block

    def _get_function_schema(self) -> dict:
        """Generate LLM function calling schema describing available blocks.

        Returns:
            Function schema dictionary compatible with OpenAI-style function calling

        Structure:
            - Defines 'select_block' function with enum of registered block names
            - Includes block descriptions to help LLM make informed choices
        """
        # create block descriptions
        block_descriptions = {
            name: block.description  # type: ignore
            for name, block in self.blocks.items()
        }

        return {
            "type": "function",
            "function": {
                "name": "select_block",
                "description": "Select the most appropriate block based on the step information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "block_name": {
                            "type": "string",
                            "enum": list(self.blocks.keys()),
                            "description": f"Available blocks and their descriptions: {block_descriptions}",
                        }
                    },
                    "required": ["block_name"],
                },
            },
        }

    async def dispatch(self, step: dict) -> Block:
        """Route a task step to the most appropriate processing block.

        Args:
            step: Dictionary containing task information with 'intention' key

        Returns:
            Selected Block instance for handling the task

        Behavior:
            - Uses LLM with function calling to make selection
            - Falls back to random choice on failures
            - Validates LLM's selection against registered blocks

        Raises:
            ValueError: If LLM returns unregistered block (caught internally)
        """
        try:
            function_schema = self._get_function_schema()
            self.prompt.format(step=step["intention"])

            # Call LLM with tools schema
            function_args = await self.llm.atext_request(
                self.prompt.to_dialog(),
                tools=[function_schema],
                tool_choice={"type": "function", "function": {"name": "select_block"}},
            )

            selected_block = function_args.get("block_name")  # type: ignore

            if selected_block not in self.blocks:
                raise ValueError(
                    f"Selected block '{selected_block}' not found in registered blocks"
                )

            return self.blocks[selected_block]

        except Exception as e:
            logger.warning(f"Failed to dispatch block: {e}")
            return random.choice(list(self.blocks.values()))
