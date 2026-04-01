import re
import time
from typing import Any
import json_repair
from openai.types.chat import ChatCompletionToolParam

from ..logger import get_logger
from ..memory import Memory
from .block import Block
from .context import DotDict
from .prompt import FormatPrompt
from .toolbox import AgentToolbox

DISPATCHER_PROMPT = """
Based on the task information (which describes the needs of the user), select the most appropriate block to handle the task.
Each block has its specific functionality as described in the function schema.
        
Task information:
${context.current_intention}
"""


class BlockDispatcher:
    """Orchestrates task routing between registered processing blocks.

    Attributes:
        toolbox: AgentToolbox
        blocks: Registry of available processing blocks (name -> Block mapping)
        prompt: Formatted prompt template for LLM instructions
    """

    def __init__(
        self,
        toolbox: AgentToolbox,
        agent_memory: Memory,
        selection_prompt: str = DISPATCHER_PROMPT,
        use_cache: bool = True,
        cache_min_sample_size: int = 100,
        cache_agreement_threshold: float = 0.999,
    ):
        """Initialize dispatcher with LLM interface.

        Args:
            llm: Language model for block selection decisions
        """
        self.toolbox = toolbox
        self.memory = agent_memory
        self.blocks: dict[str, Block] = {}
        self.dispatcher_prompt = FormatPrompt(selection_prompt, memory=self.memory)
        self.dispatcher_cache: DispatcherCache | None = None
        if use_cache:
            self.dispatcher_cache = DispatcherCache(
                min_sample_size=cache_min_sample_size,
                agreement_threshold=cache_agreement_threshold,
            )

    def register_dispatcher_prompt(self, dispatcher_prompt: str) -> None:
        """Register a dispatcher prompt.

        Args:
            dispatcher_prompt: Dispatcher prompt
        """
        self.dispatcher_prompt = FormatPrompt(dispatcher_prompt, memory=self.memory)

    def register_blocks(self, blocks: list[Block]) -> None:
        """Register multiple processing blocks for dispatching.

        Args:
            blocks: List of Block instances to register
        """
        for block in blocks:
            block_name = block.__class__.__name__.lower()
            self.blocks[block_name] = block

    def _get_function_schema(self) -> ChatCompletionToolParam:
        """
        Generate LLM function calling schema describing available blocks.

        - **Description**:
            - Creates a schema for the LLM to select appropriate blocks or indicate no suitable block exists.

        - **Returns**:
            - `ChatCompletionToolParam`: Function schema dictionary compatible with OpenAI-style function calling
        """
        # create block descriptions
        block_descriptions = {
            name: block.description for name, block in self.blocks.items()
        }

        return {
            "type": "function",
            "function": {
                "name": "select_block",
                "description": "Select the most appropriate block based on the step information, or indicate no suitable block exists",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "block_name": {
                            "type": "string",
                            "enum": list(self.blocks.keys()) + ["no_suitable_block"],
                            "description": f"Available blocks and their descriptions: {block_descriptions}. Use 'no_suitable_block' if none of the blocks are appropriate for the given intention.",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Explanation for why the selected block is appropriate or why no suitable block exists",
                        },
                    },
                    "required": ["block_name", "reason"],
                },
            },
        }

    async def dispatch(self, context: DotDict) -> Block | None:
        """
        Route a task step to the most appropriate processing block.

        - **Description**:
            - Uses LLM to select the best block for handling the given task intention.
            - Can return None if no suitable block is found.

        - **Args**:
            - `context` (DotDict): Context dictionary containing task information

        - **Returns**:
            - `Block | None`: Selected Block instance for handling the task, or None if no suitable block exists
        """
        try:
            if not isinstance(context, DotDict):
                # If it's a regular dict, convert to DotDict
                context = DotDict(context)

            get_logger().debug(f"Dispatching with context: {context}")

            function_schema = self._get_function_schema()
            await self.dispatcher_prompt.format(context=context)
            agent_id = await self.memory.status.get("id")
            db_tool = self.toolbox.get_tool("db_actor")
            selected_block = None
            possible_blocks = function_schema["function"]["parameters"]["properties"][
                "block_name"
            ]["enum"]
            ctx_intention = str(context.get("current_intention", ""))

            if self.dispatcher_cache is not None:
                cached_block = self.dispatcher_cache.check_cache(
                    possible_blocks=possible_blocks,
                    ctx_intention=ctx_intention,
                )
                if cached_block is not None:
                    selected_block = cached_block
                    reason = "Cache hit"
                    get_logger().debug(
                        f"Dispatcher cache hit. Intention: {ctx_intention}, selected: {selected_block}"
                    )

                    if db_tool is not None:
                        await self.log_dispatch(  # type: ignore
                            db_tool=db_tool,
                            agent_id=agent_id,
                            selected_block=selected_block,
                            reason=reason,
                            function_schema=function_schema,
                            context=context,
                        )

                    if selected_block == "no_suitable_block":
                        return None

                    if selected_block not in self.blocks:
                        raise ValueError(
                            f"Selected block '{selected_block}' not found in registered blocks"
                        )

                    return self.blocks[selected_block]

            # Call LLM with tools schema
            response = await self.toolbox.llm.atext_request(
                self.dispatcher_prompt.to_dialog(),
                tools=[function_schema],
                tool_choice={"type": "function", "function": {"name": "select_block"}},
                context={
                    "block_name": "BlockDispatcher",
                    "func_name": "dispatch",
                    "agent_id": str(agent_id),
                },
            )
            function_args: Any = json_repair.loads(
                response.choices[0].message.tool_calls[0].function.arguments
            )

            get_logger().debug(f"LLM response for block dispatching: {function_args}")
            if isinstance(function_args, list):
                function_args = function_args[1][0]  # Mistral
            if isinstance(function_args, str):
                get_logger().debug(
                    f"Function arguments is a string, attempting to parse: {response}"
                )

            if "arguments" in function_args and isinstance(
                function_args["arguments"], dict
            ):
                function_args = function_args["arguments"]

            selected_block = function_args.get("block_name")

            reason = function_args.get("reason", "No reason provided")

            if self.dispatcher_cache is not None and selected_block is not None:
                self.dispatcher_cache.update_cache(
                    possible_blocks=possible_blocks,
                    ctx_intention=ctx_intention,
                    target_block=selected_block,
                )

            if db_tool is not None:
                await self.log_dispatch(  # type: ignore
                    db_tool=db_tool,
                    agent_id=agent_id,
                    selected_block=selected_block,
                    reason=reason,
                    function_schema=function_schema,
                    context=context,
                )

            if selected_block == "no_suitable_block":
                get_logger().debug(
                    f"No suitable block found for intention. Reason: {reason}"
                )
                return None

            if selected_block not in self.blocks:
                raise ValueError(
                    f"Selected block '{selected_block}' not found in registered blocks"
                )

            get_logger().debug(
                f"Dispatched intention to block: {selected_block}. Reason: {reason}"
            )
            return self.blocks[selected_block]

        except Exception as e:
            get_logger().warning(f"Failed to dispatch block: {e}")
            return None

    async def log_dispatch(
        self,
        db_tool: Any,
        agent_id: int,
        selected_block: str,
        reason: str,
        function_schema: dict,
        context: dict,
    ) -> None:
        """Log dispatcher activity.

        Args:
            context: Context dictionary
            dialog: Conversation dialog
            content: LLM response content
            tools: Tools used in the LLM call
        """

        def _parse_temperature(temp_str: str) -> float:
            """Extracts numerical temperature from strings like '15C' or 'Temp is 22.5°'."""
            try:
                # Matches integers or decimals. Handles negative numbers.
                match = re.search(r"([-+]?\d*\.?\d+)", temp_str)
                return int(match.group(1)) if match else 0
            except (ValueError, AttributeError):
                return 0

        try:
            possible_blocks = function_schema["function"]["parameters"]["properties"][
                "block_name"
            ]["enum"]
            raw_temp_str = context.get("temperature", "0")
            temp_value = _parse_temperature(raw_temp_str)
            plan_target = context.get("plan_target", "")
            if isinstance(plan_target, list):
                plan_target = plan_target[0] if len(plan_target) > 0 else ""

            db_tool.get_tool().insert_block_dispatcher_record.remote(
                agent_id=agent_id,
                timestamp=time.time(),
                target_block=selected_block,
                reason=reason,
                possible_blocks=possible_blocks,
                ctx_time=context.get("current_time", ""),
                ctx_need=context.get("current_need", ""),
                ctx_intention=context.get("current_intention", ""),
                ctx_emotion=context.get("current_emotion", ""),
                ctx_thought=context.get("current_thought", ""),
                ctx_location=context.get("current_location", ""),
                ctx_area_info=context.get("area_information", ""),
                ctx_weather=context.get("weather", ""),
                ctx_temperature=temp_value,
                ctx_other_info=context.get("other_information", ""),
                ctx_plan_target=context.get("plan_target", ""),
            )
        except Exception as e:
            get_logger().warning(f"Failed to log dispatcher activity: {e}")


class DispatcherCache:
    """Manages statistical caching for LLM-based block dispatching."""

    def __init__(self, min_sample_size=100, agreement_threshold=0.999):
        self.cache = {}
        self.min_sample_size = min_sample_size
        self.agreement_threshold = agreement_threshold

    def _build_key(self, possible_blocks: list, ctx_intention: str) -> tuple:
        # Using a tuple is faster for dictionary keys and avoids string memory allocation
        return (tuple(sorted(possible_blocks)), ctx_intention)

    def check_cache(self, possible_blocks: list, ctx_intention: str):
        key = self._build_key(possible_blocks, ctx_intention)

        if key in self.cache:
            value = self.cache[key]
            if (value["count"] >= self.min_sample_size) and (
                value["agreement_rate"] >= self.agreement_threshold
            ):
                value["cache_hit_count"] += 1
                return value["most_common_block"]
        return None

    def update_cache(
        self, possible_blocks: list, ctx_intention: str, target_block: str
    ):
        key = self._build_key(possible_blocks, ctx_intention)

        if key not in self.cache:
            self.cache[key] = {
                "block_counts": {},
                "most_common_block": None,
                "agreement_rate": 0.0,
                "count": 0,
                "cache_hit_count": 0,
            }

        value = self.cache[key]
        value["count"] += 1
        value["block_counts"][target_block] = (
            value["block_counts"].get(target_block, 0) + 1
        )

        # Update most common block and agreement rate
        most_common_block, most_common_count = max(
            value["block_counts"].items(), key=lambda x: x[1]
        )
        value["most_common_block"] = most_common_block
        value["agreement_rate"] = most_common_count / value["count"]
