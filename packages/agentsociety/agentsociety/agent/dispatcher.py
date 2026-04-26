import re
import time
from typing import Any
import json_repair
from openai.types.chat import ChatCompletionToolParam

from ..logger import get_logger
from ..memory import Memory
from .block import Block
from .context import DotDict
from .toolbox import AgentToolbox

DISPATCHER_PROMPT = """Based on the task information (which describes the needs of the user), select the most appropriate block to handle the task.
Each block has its specific functionality as described in the function schema.

Task information:
{current_intention}
"""


class BlockDispatcher:
    """Orchestrates task routing between registered processing blocks.

    Attributes:
        toolbox: AgentToolbox
        blocks: Registry of available processing blocks (name -> Block mapping)
        prompt_manager: PromptManager instance for building dispatcher dialog
    """

    def __init__(
        self,
        toolbox: AgentToolbox,
        agent_memory: Memory,
        selection_prompt: str = DISPATCHER_PROMPT,
        use_cache: bool = True,
    ):
        """Initialize dispatcher with LLM interface.

        Args:
            toolbox: Agent toolbox providing LLM access
            agent_memory: Agent memory for reading agent state
            selection_prompt: Prompt template; {current_intention} is substituted at dispatch time
            use_cache: Whether to use the global dispatcher cache
        """
        self.toolbox = toolbox
        self.memory = agent_memory
        self.blocks: dict[str, Block] = {}
        self.prompt_manager = Block._get_or_create_prompt_manager(None)
        # Store the active template so register_dispatcher_prompt can override it.
        # None means "use prompt_manager with the TOML-backed 'block_dispatcher' prompt".
        self._custom_dispatch_template: str | None = (
            None if selection_prompt == DISPATCHER_PROMPT else selection_prompt
        )
        self.use_cache = use_cache

    def register_dispatcher_prompt(self, dispatcher_prompt: str) -> None:
        """Register a custom dispatcher prompt template.

        The template is formatted with Python str.format(), so use {current_intention}
        as the placeholder for the agent's current intention text.  When the provided
        string equals the default DISPATCHER_PROMPT constant the built-in TOML-backed
        prompt is used instead, which is equivalent.

        Args:
            dispatcher_prompt: Prompt template string with {current_intention} placeholder
        """
        self._custom_dispatch_template = (
            None if dispatcher_prompt == DISPATCHER_PROMPT else dispatcher_prompt
        )

    def _build_dispatch_dialog(self, current_intention: str) -> list[dict[str, str]]:
        """Build the LLM dialog for block selection from the active prompt template.

        Uses the TOML-backed PromptManager when no custom template has been registered;
        falls back to str.format() substitution on the custom template string otherwise.

        Args:
            current_intention: The agent's current intention text to embed in the prompt

        Returns:
            A list of chat message dicts ready for the LLM (role/content pairs)

        @usedBy: BlockDispatcher.dispatch
        """
        if self._custom_dispatch_template is not None:
            try:
                content = self._custom_dispatch_template.format(
                    current_intention=current_intention
                )
            except KeyError:
                # Template uses unknown placeholders — emit as-is with intention appended.
                get_logger().warning(
                    "Custom dispatcher template has unrecognised placeholders; "
                    "appending current_intention verbatim."
                )
                content = self._custom_dispatch_template + "\n" + current_intention
            return [{"role": "user", "content": content}]

        if self.prompt_manager is not None:
            try:
                return self.prompt_manager.format_prompt_to_dialog(
                    "block_dispatcher",
                    {"current_intention": current_intention},
                )
            except Exception as e:
                get_logger().warning(
                    f"PromptManager failed to build dispatcher dialog: {e}; "
                    "falling back to inline template."
                )

        # Last-resort fallback: build the dialog inline without any dependency.
        content = DISPATCHER_PROMPT.format(current_intention=current_intention)
        return [{"role": "user", "content": content}]

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
            agent_id = await self.memory.status.get("id")
            db_tool = self.toolbox.get_tool("db_actor")
            dispatcher_cache_tool = self.toolbox.get_tool("dispatcher_cache_actor")
            global_dispatcher_cache = (
                dispatcher_cache_tool.get_tool()
                if dispatcher_cache_tool is not None
                else None
            )
            selected_block = None
            possible_blocks = function_schema["function"]["parameters"]["properties"][
                "block_name"
            ]["enum"]
            ctx_intention = str(context.get("current_intention", ""))

            cached_block = None
            if self.use_cache and global_dispatcher_cache is not None:
                try:
                    cached_block = await global_dispatcher_cache.check_cache.remote(
                        possible_blocks=possible_blocks,
                        ctx_intention=ctx_intention,
                    )
                except Exception as e:
                    get_logger().warning(
                        f"Global dispatcher cache check failed: {e}"
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

            # Build the dialog and call LLM with tools schema
            dispatch_dialog = self._build_dispatch_dialog(ctx_intention)
            response = await self.toolbox.llm.atext_request(
                dispatch_dialog,
                tools=[function_schema],
                tool_choice={"type": "function", "function": {"name": "select_block"}},
                context={
                    "block_name": "BlockDispatcher",
                    "func_name": "dispatch",
                    "agent_id": str(agent_id),
                },
            )
            # Try structured tool_calls first; fall back to plain content (some LLMs)
            try:
                raw_args = response.choices[0].message.tool_calls[0].function.arguments
            except (AttributeError, IndexError, TypeError):
                # No tool_calls — try to extract block_name from plain text content
                raw_args = response.choices[0].message.content or "{}"

            function_args: Any = json_repair.loads(raw_args)

            get_logger().debug(f"LLM response for block dispatching: {function_args}")
            if isinstance(function_args, list):
                function_args = function_args[1][0]  # Mistral nested list format
            if isinstance(function_args, str):
                function_args = json_repair.loads(function_args)
            if not isinstance(function_args, dict):
                function_args = {}

            if "arguments" in function_args and isinstance(
                function_args["arguments"], dict
            ):
                function_args = function_args["arguments"]

            selected_block = function_args.get("block_name")
            # Normalise: block names are registered lowercased; LLM may use other casing
            if selected_block is not None and selected_block != "no_suitable_block":
                if selected_block not in self.blocks:
                    normalised = selected_block.lower().replace("-", "").replace("_", "").replace(" ", "")
                    for key in self.blocks:
                        if key.lower().replace("-", "").replace("_", "") == normalised:
                            selected_block = key
                            break

            reason = function_args.get("reason", "No reason provided")

            if selected_block is not None:
                if self.use_cache and global_dispatcher_cache is not None:
                    try:
                        await global_dispatcher_cache.update_cache.remote(
                            possible_blocks=possible_blocks,
                            ctx_intention=ctx_intention,
                            target_block=selected_block,
                        )
                    except Exception as e:
                        get_logger().warning(
                            f"Global dispatcher cache update failed: {e}"
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

        def _safe_extract_plan_target(value: Any) -> str:
            """Safely extracts plan_target, handling None and list values."""
            if value is None:
                get_logger().warning("plan_target is None in context")
                return ""
            if isinstance(value, list):
                if len(value) == 0:
                    get_logger().warning("plan_target is empty list in context")
                    return ""
                return str(value[0])
            return str(value)

        try:
            possible_blocks = function_schema["function"]["parameters"]["properties"][
                "block_name"
            ]["enum"]
            raw_temp_str = context.get("temperature", "0")
            temp_value = _parse_temperature(raw_temp_str)
            plan_target = context.get("plan_target", "")
            plan_target = _safe_extract_plan_target(plan_target)

            # Log all extracted context values for debugging
            get_logger().debug(
                f"Dispatcher logging for agent_id={agent_id}: "
                f"target_block={selected_block}, "
                f"ctx_time={context.get('current_time', '')}, "
                f"ctx_plan_target={plan_target}, "
                f"ctx_intention={context.get('current_intention', '')}"
            )

            db_tool.get_tool().insert_block_dispatcher_record.remote(
                agent_id=agent_id,
                timestamp=time.time(),
                target_block=selected_block,
                reason=reason,
                possible_blocks=possible_blocks,
                ctx_time=str(context.get("current_time", "")),
                ctx_need=str(context.get("current_need", "")),
                ctx_intention=str(context.get("current_intention", "")),
                ctx_emotion=str(context.get("current_emotion", "")),
                ctx_thought=str(context.get("current_thought", "")),
                ctx_location=str(context.get("current_location", "")),
                ctx_area_info=str(context.get("area_information", "")),
                ctx_weather=str(context.get("weather", "")),
                ctx_temperature=temp_value,
                ctx_other_info=str(context.get("other_information", "")),
                ctx_plan_target=plan_target,
            )
        except Exception as e:
            get_logger().warning(
                f"Failed to log dispatcher activity: {e}. "
                f"Context keys available: {list(context.keys()) if isinstance(context, dict) else 'N/A'}"
            )
