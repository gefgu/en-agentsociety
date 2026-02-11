import re
import time
from typing import Any, List
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
    ):
        """Initialize dispatcher with LLM interface.

        Args:
            llm: Language model for block selection decisions
        """
        self.toolbox = toolbox
        self.memory = agent_memory
        self.blocks: dict[str, Block] = {}
        self.dispatcher_prompt = FormatPrompt(selection_prompt, memory=self.memory)

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
            catboost_tool = self.toolbox.get_tool("catboost_dispatcher_actor")
            metrics_tool = self.toolbox.get_tool("metrics_actor")

            success = False
            selected_block = None
            if catboost_tool is not None:
                start_time = time.perf_counter()
                success, predicted_block = await catboost_tool.get_tool().predict.remote(  # type: ignore
                    function_schema=function_schema,
                    context=context,
                    agent_id=agent_id,
                )
                if success and predicted_block != "no_suitable_block":
                    if predicted_block in self.blocks:
                        get_logger().debug(
                            f"Dispatched intention to block: {predicted_block} using CatBoost."
                        )
                        end_time = time.perf_counter()
                        duration = end_time - start_time
                        if metrics_tool is not None:
                            metrics_tool.get_tool().record_block_performance.remote(
                                block_name="BlockDispatcher",
                                func_name="dispatch",
                                actor="catboost",
                                agent_id=agent_id,
                                duration=round(duration, 4),
                                token_input=0,
                                token_output=0,
                            )
                            metrics_tool.get_tool().record_routing.remote(  # type: ignore
                                block_name="BlockDispatcher",
                                func_name="dispatch",
                                agent_id=str(agent_id),
                                routed=False,
                            )
                        return self.blocks[predicted_block]
                    else:
                        get_logger().warning(
                            f"Predicted block '{predicted_block}' not found in registered blocks."
                        )

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

            get_logger().info(f"LLM response for block dispatching: {response}")
            
            # Handle various response formats from different LLM providers
            if isinstance(function_args, list):
                function_args = function_args[1][0]  # Mistral format
            
            if isinstance(function_args, str):
                get_logger().warning(f"Function arguments is a string, attempting to parse: {function_args}")
                try:
                    function_args = json_repair.loads(function_args)
                except Exception as e:
                    get_logger().warning(f"Failed to parse function_args string: {e}")
                    function_args = {}

            # Handle nested arguments structure
            if isinstance(function_args, dict) and "arguments" in function_args and isinstance(
                function_args["arguments"], dict
            ):
                function_args = function_args["arguments"]

            # Ensure function_args is a dict
            if not isinstance(function_args, dict):
                get_logger().warning(f"Unexpected function_args type: {type(function_args)}. {function_args}, defaulting to empty dict")
                function_args = {}

            selected_block = function_args.get("block_name")
            reason = function_args.get("reason", "No reason provided")


            if selected_block is None:
                selected_block = "no_suitable_block"
                reason = "Failed to parse LLM response or no block name provided"

            if (metrics_tool is not None) and catboost_tool is not None:
                await metrics_tool.get_tool().record_routing.remote(  # type: ignore
                    block_name="BlockDispatcher",
                    func_name="dispatch",
                    agent_id=str(agent_id),
                    routed=True,
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
