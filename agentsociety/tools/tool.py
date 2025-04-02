import asyncio
import time
from collections import defaultdict
from collections.abc import Callable, Sequence
from typing import Any, Optional, Union

from mlflow.entities import Metric

from ..agent import Agent, Block
from ..utils.decorators import lock_decorator

__all__ = [
    "Tool",
    "ExportMlflowMetrics",
    "UpdateWithSimulator",
    "ResetAgentPosition",
]


class Tool:
    """Abstract tool class for callable tools. Can be bound to an `Agent` or `Block` instance.

    This class serves as a base for creating various tools that can perform different operations.
    It is intended to be subclassed by specific tool implementations.

    - **Attributes**:
        - `_instance`: A reference to the instance (`Agent` or `Block`) this tool is bound to.
    """

    def __get__(self, instance: Union[Agent, Block], owner):
        """
        Descriptor method for binding the tool to an instance.

        - **Args**:
            - `instance`: The instance that the tool is being accessed through.
            - `owner`: The type of the owner class.

        - **Returns**:
            - `Tool`: An instance of the tool bound to the given instance.

        - **Description**:
            - If accessed via the class rather than an instance, returns the descriptor itself.
            - Otherwise, it checks if the tool has already been instantiated for this instance,
              and if not, creates and stores a new tool instance specifically for this instance.
        """
        assert instance is not None
        subclass = type(self)
        if not hasattr(instance, "_tools"):
            setattr(instance, "_tools", {})
        instance_tools = getattr(instance, "_tools")
        if subclass not in instance_tools:
            tool_instance = subclass()
            setattr(tool_instance, "_instance", instance)
            instance_tools[subclass] = tool_instance
        return instance_tools[subclass]

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        """Invoke the tool's functionality.

        This method must be implemented by subclasses to provide specific behavior.

        - **Raises**:
            - `NotImplementedError`: When called directly on the base class.
        """
        raise NotImplementedError

    @property
    def agent(self) -> Agent:
        """
        Access the `Agent` this tool is bound to.

        - **Returns**:
            - `Agent`: The agent instance.

        - **Raises**:
            - `RuntimeError`: If the tool is not bound to an `Agent`.
        """
        instance = getattr(self, "_instance", None)
        if not isinstance(instance, Agent):
            raise RuntimeError(
                f"Tool bind to object `{type(instance).__name__}`, not an `Agent` object!"
            )
        return instance

    @property
    def block(self) -> Block:
        """
        Access the `Block` this tool is bound to.

        - **Returns**:
            - `Block`: The block instance.

        - **Raises**:
            - `RuntimeError`: If the tool is not bound to a `Block`.
        """
        instance = getattr(self, "_instance", None)
        if not isinstance(instance, Block):
            raise RuntimeError(
                f"Tool bind to object `{type(instance).__name__}`, not an `Block` object!"
            )
        return instance


class UpdateWithSimulator(Tool):
    """Automatically update status memory from simulator"""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    async def _update_motion_with_sim(
        self,
    ):
        agent = self.agent
        environment = agent.environment
        status = agent.status
        person_id = await status.get("id")
        resp = await environment.get_person(person_id)
        resp_dict = resp["person"]
        for k, v in resp_dict.get("motion", {}).items():
            try:
                await status.get(k)
                await status.update(
                    k, v, mode="replace", protect_llm_read_only_fields=False
                )
            except KeyError as e:
                continue

    @lock_decorator
    async def __call__(
        self,
    ):
        await self._update_motion_with_sim()


class ResetAgentPosition(Tool):
    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    @lock_decorator
    async def __call__(
        self,
        aoi_id: Optional[int] = None,
        poi_id: Optional[int] = None,
        lane_id: Optional[int] = None,
        s: Optional[float] = None,
    ):
        """
        Reset the position of the agent associated with this tool.

        - **Args**:
            - `aoi_id` (Optional[int], optional): Area of interest ID. Defaults to None.
            - `poi_id` (Optional[int], optional): Point of interest ID. Defaults to None.
            - `lane_id` (Optional[int], optional): Lane ID. Defaults to None.
            - `s` (Optional[float], optional): Position along the lane. Defaults to None.

        - **Description**:
            - Resets the agent's position based on the provided parameters using the simulator.
        """
        agent = self.agent
        status = agent.status
        await agent.environment.reset_person_position(
            person_id=await status.get("id"),
            aoi_id=aoi_id,
            poi_id=poi_id,
            lane_id=lane_id,
            s=s,
        )


class ExportMlflowMetrics(Tool):
    """
    A tool for exporting metrics to MLflow in batches.

    - **Attributes**:
        - `_log_batch_size` (int): The number of metrics to log in each batch.
        - `metric_log_cache` (Dict[str, List[Metric]]): Cache for storing metrics before batching.
        - `_lock` (asyncio.Lock): Ensures thread-safe operations when logging metrics.
    """

    def __init__(self, log_batch_size: int = 100) -> None:
        """
        Initialize the ExportMlflowMetrics tool with a specified batch size and an asynchronous lock.

        - **Args**:
            - `log_batch_size` (int, optional): Number of metrics per batch. Defaults to 100.
        """
        self._log_batch_size = log_batch_size
        # TODO: support other log types
        self.metric_log_cache: dict[str, list[Metric]] = defaultdict(list)
        self._lock = asyncio.Lock()

    @lock_decorator
    async def __call__(
        self,
        metric: Union[Sequence[Union[Metric, dict]], Union[Metric, dict]],
        clear_cache: bool = False,
    ):
        """
        Add metrics to the cache and export them to MLflow in batches if the batch size limit is reached.

        - **Args**:
            - `metric` (Union[Sequence[Union[Metric, dict]], Union[Metric, dict]]): A single metric or a sequence of metrics.
            - `clear_cache` (bool, optional): Flag indicating whether to clear the cache after logging. Defaults to False.

        - **Description**:
            - Adds metrics to the cache. If the cache exceeds the batch size, logs a batch of metrics to MLflow.
            - Optionally clears the entire cache.
        """
        agent = self.agent
        batch_size = self._log_batch_size
        if not isinstance(metric, Sequence):
            metric = [metric]
        for _metric in metric:
            if isinstance(_metric, Metric):
                item = _metric
                metric_key = item.key
            else:
                item = Metric(
                    key=_metric["key"],
                    value=_metric["value"],
                    timestamp=_metric.get("timestamp", int(1000 * time.time())),
                    step=_metric["step"],
                )
                metric_key = _metric["key"]
            self.metric_log_cache[metric_key].append(item)
        client = agent.mlflow_client
        assert client is not None, "MLflow client is not enabled!"
        for metric_key, _cache in self.metric_log_cache.items():
            if len(_cache) > batch_size:
                await client.log_batch(
                    metrics=_cache[:batch_size],
                )
                _cache = _cache[batch_size:]
        if clear_cache:
            await self._clear_cache()

    async def _clear_cache(
        self,
    ):
        """
        Log any remaining metrics from the cache to MLflow and then clear the cache.
        """
        agent = self.agent
        client = agent.mlflow_client
        assert client is not None, "MLflow client is not enabled!"
        for metric_key, _cache in self.metric_log_cache.items():
            if len(_cache) > 0:
                await client.log_batch(
                    metrics=_cache,
                )
                _cache = []
