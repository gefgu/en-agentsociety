from typing import Any, Callable, Optional

from ..prompts.prompt_manager import PromptManager, PromptResult, ResponseMode
from pydantic import BaseModel
from ..logger import get_logger
from ..environment import Environment
from ..llm import LLM
from ..memory import KVMemory, Memory
from .context import BlockContext, DotDict, auto_deepcopy_dotdict, context_to_dot_dict
from .memory_config_generator import MemoryConfig
from .toolbox import AgentToolbox
from pathlib import Path

TRIGGER_INTERVAL = 1

__all__ = [
    "Block",
    "BlockParams",
    "BlockOutput",
]


class BlockParams(BaseModel):
    # TODO: unused
    block_memory: Optional[dict[str, Any]] = None


class BlockOutput(BaseModel): ...


# Behavior Block, used for augmenting agent's behavior capabilities
class Block:
    """
    A foundational component similar to a layer in PyTorch, used for building complex systems.
    """

    ParamsType = BlockParams
    Context = BlockContext
    OutputType = None
    NeedAgent: bool = (
        False  # Whether the block needs an agent, if True, the associated agent will be set automatically
    )
    name: str = ""
    description: str = ""
    actions: dict[str, str] = {}
    _shared_prompt_manager: Optional[PromptManager] = None
    _simulation_mode: str = "citysim"
    prompt_manager: Optional[PromptManager] = None

    def __init__(
        self,
        toolbox: AgentToolbox,
        agent_memory: Optional[Memory] = None,
        block_params: Optional[Any] = None,
    ):
        """
        - **Description**:
            - Initializes a new instance of the Block class with optional LLM, Memory, Simulator, and Trigger components.

        - **Args**:
            - `name` (str): The name of the block.
            - `llm` (Optional[LLM], optional): An instance of LLM. Defaults to None.
            - `environment` (Optional[Environment], optional): An instance of Environment. Defaults to None.
            - `memory` (Optional[Memory], optional): An instance of Memory. Defaults to None.
        """
        self._toolbox = toolbox
        self._agent_memory = agent_memory
        self._agent = None
        self.prompt_manager = self._get_or_create_prompt_manager(None)

        # parse block_params
        if block_params is None:
            block_params = self.default_params()
        self.params = block_params
        for key, value in self.params.model_dump().items():
            if key == "block_memory":
                # TODO: remove this after we have a better way to handle block memory
                if isinstance(value, MemoryConfig):
                    self._block_memory = KVMemory(
                        value,
                        embedding=self._toolbox.embedding,
                    )
            else:
                setattr(self, key, value)

        # initialize context
        context = self.default_context()
        self.context = context_to_dot_dict(context)

    @classmethod
    def default_params(cls) -> ParamsType:
        return cls.ParamsType()

    @classmethod
    def default_context(cls) -> Context:
        return cls.Context()

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Create a new dictionary that inherits from parent
        cls.get_functions = dict(cls.__base__.get_functions) if hasattr(cls.__base__, "get_functions") else {}  # type: ignore

        # Register all methods with _register_info
        for name, method in cls.__dict__.items():
            if hasattr(method, "_register_info"):
                info = method._register_info
                cls.get_functions[info["function_name"]] = info

    def set_agent(self, agent: Any):
        self._agent = agent

    @property
    def agent(self) -> Any:
        if self._agent is None:
            raise RuntimeError(
                "Agent access before assignment, please `set_agent` first!"
            )
        return self._agent

    @property
    def toolbox(self) -> AgentToolbox:
        return self._toolbox

    @property
    def llm(self) -> LLM:
        return self._toolbox.llm

    @property
    def memory(self) -> Memory:
        if self._agent_memory is None:
            raise RuntimeError(
                "Memory access before assignment, please `set_memory` first!"
            )
        return self._agent_memory

    @property
    def agent_memory(self) -> Memory:
        if self._agent_memory is None:
            raise RuntimeError(
                "Memory access before assignment, please `set_memory` first!"
            )
        return self._agent_memory

    @property
    def block_memory(self) -> KVMemory:
        if self._block_memory is None:
            raise RuntimeError(
                "Block memory access before assignment, please `set_block_memory` first!"
            )
        return self._block_memory

    @property
    def environment(self) -> Environment:
        return self._toolbox.environment

    async def execute_prompt(
        self,
        prompt_name: str,
        context: dict[str, Any],
        *,
        func_name: str,
        response_mode: ResponseMode = ResponseMode.JSON,
        max_retries: int = 0,
        validate: Optional[Callable[[Any], bool]] = None,
        timeout: int = 300,
        temperature: float = 1,
        max_tokens: Optional[int] = None,
        dialog_override: Optional[list[dict[str, str]]] = None,
    ) -> PromptResult:
        """Execute a prompt end-to-end via :meth:`PromptManager.execute_prompt`.

        This is a convenience wrapper that fills in ``llm``, ``memory``,
        ``block_name``, and ``agent_id`` from the block instance.
        """
        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")
        agent_ref = self._agent
        agent_id = str(getattr(agent_ref, "id", getattr(self, "id", "unknown")))
        return await self.prompt_manager.execute_prompt(
            prompt_name=prompt_name,
            llm=self.llm,
            memory=self.memory,
            context=context,
            block_name=self.name,
            func_name=func_name,
            agent_id=agent_id,
            response_mode=response_mode,
            max_retries=max_retries,
            validate=validate,
            timeout=timeout,
            temperature=temperature,
            max_tokens=max_tokens,
            dialog_override=dialog_override,
        )

    def build_llm_prompt_context(
        self,
        *,
        prompt_name: str,
        state_dict: dict[str, Any],
        func_name: str,
        block_name: Optional[str] = None,
    ) -> dict[str, Any]:
        if self.prompt_manager is None:
            raise RuntimeError("PromptManager is not initialized")

        # Avoid raising when a block is invoked before set_agent; fall back to block-level id.
        agent_ref = self._agent
        agent_id = getattr(agent_ref, "id", None)
        if agent_id is None:
            agent_id = getattr(self, "id", "unknown")

        return {
            "block_name": block_name or self.name,
            "func_name": func_name,
            "agent_id": str(agent_id),
            "prompt_identity": self.prompt_manager.get_prompt_identity(prompt_name),
            "prompt_requires_free_text": self.prompt_manager.requires_free_text_generation(prompt_name),
            "prompt_inputs": {
                key: state_dict[key]
                for key in self.prompt_manager.get_typed_input_fields(prompt_name)
                if key in state_dict
            },
            "prompt_input_schema": self.prompt_manager.get_input_schema(prompt_name),
            "prompt_output_schema": self.prompt_manager.get_output_schema(prompt_name),
        }
    
    @classmethod
    def set_simulation_mode(cls, mode: str) -> None:
        """Set the simulation mode and reset PromptManager so it reinitializes with the correct origin."""
        Block._simulation_mode = mode
        Block._shared_prompt_manager = None

    @classmethod
    def _get_or_create_prompt_manager(cls, simulation_prompt_config: Optional[dict]) -> Optional[PromptManager]:
        if Block._shared_prompt_manager is not None:
            cls._shared_prompt_manager = Block._shared_prompt_manager
            return cls._shared_prompt_manager

        try:
            prompts_dir = str(Path(__file__).resolve().parents[1] / "prompts")
            active_config = simulation_prompt_config
            if active_config is None:
                active_config = cls._build_origin_config(prompts_dir, Block._simulation_mode)
            manager = PromptManager(
                prompts_dir=prompts_dir,
                active_config=active_config,
            )
            Block._shared_prompt_manager = manager
            cls._shared_prompt_manager = manager
        except Exception as e:
            get_logger().warning(
                f"Failed to initialize PromptManager: {e}"
            )
            Block._shared_prompt_manager = None
            cls._shared_prompt_manager = None
        return cls._shared_prompt_manager

    @staticmethod
    def _build_origin_config(prompts_dir: str, mode: str) -> dict:
        """Scan all TOMLs and build active_config that selects the correct origin for each prompt name."""
        import os
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib  # type: ignore

        from ..prompts.prompt_manager import parse_version

        candidates: dict[str, list[dict]] = {}
        for root, _, files in os.walk(prompts_dir):
            for f in files:
                if not f.endswith(".toml"):
                    continue
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, "rb") as fh:
                        data = tomllib.load(fh)
                    name = data.get("metadata", {}).get("name")
                    origin = data.get("metadata", {}).get("origin", "unknown")
                    version = data.get("metadata", {}).get("version", "0.0.0")
                    if name:
                        candidates.setdefault(name, []).append({
                            "name": name, "origin": origin, "version": version,
                        })
                except Exception:
                    pass

        config: dict[str, dict[str, str]] = {}
        for name, entries in candidates.items():
            exact = [e for e in entries if e["origin"] == mode]
            if exact:
                best = max(exact, key=lambda e: parse_version(e["version"]))
                config[name] = {"origin": mode, "version": best["version"]}
            else:
                best = max(entries, key=lambda e: parse_version(e["version"]))
                config[name] = {"origin": best["origin"], "version": best["version"]}
        return config

    async def before_forward(self):
        """
        Before forward - prepare context
        """
        pass

    async def after_forward(self):
        """
        After forward - update/clean context
        """
        pass

    @auto_deepcopy_dotdict
    async def forward(self, agent_context: DotDict):
        """
        - **Description**:
            - Each block performs a specific reasoning task. This method should be overridden by subclasses.
            - Subclasses can define their own parameters as needed.

        - **Args**:
            - `*args`: Variable length argument list.
            - `**kwargs`: Arbitrary keyword arguments.

        - **Raises**:
            - `NotImplementedError`: Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses should implement this method")
