"""Shared Ray actor that batches dense text-embedding requests.

EmbedActor coalesces single-text embedding requests from many concurrent Ray
worker processes into single ONNX inference calls, exploiting the model's
internal batching to reduce per-request overhead.

Usage
-----
Constructed once by InfrastructureManager and passed by reference to
QdrantCacheActor; not used directly by agent actors.
"""

import asyncio
import os
from typing import Any, Optional

import ray
from fastembed import TextEmbedding

from ...logger import get_logger


@ray.remote
class EmbedActor:
    """Ray actor that batches text-embedding calls across concurrent callers.

    Receives individual embed_batch() calls from QdrantCacheActor, coalesces
    them into a single fastembed ONNX inference call, and resolves all waiting
    callers with their respective slices of the result.

    The actor's methods are async; Ray schedules them concurrently via its
    async actor runtime, so multiple callers can have their futures pending
    while the background batch-processing loop accumulates texts.

    :param embedding_model: fastembed model name (e.g. "BAAI/bge-small-en-v1.5").
    :param embedding_cache_dir: Directory where fastembed caches model weights.
    :param batch_timeout_ms: Maximum milliseconds to wait before firing an
        incomplete batch.
    :param max_batch_size: Maximum texts coalesced into a single ONNX call.
    :param metrics_actor: Optional PrometheusActor for recording batch-size
        histogram metrics.

    Called from: InfrastructureManager._init_llm_cache_actor
        (simulation/infrastructuremanager.py).
    """

    def __init__(
        self,
        embedding_model: str,
        embedding_cache_dir: Optional[str],
        batch_timeout_ms: int = 25,
        max_batch_size: int = 256,
        metrics_actor: Optional[Any] = None,
    ) -> None:
        self._model = TextEmbedding(
            model_name=embedding_model,
            cache_dir=embedding_cache_dir,
            threads=max(1, os.cpu_count() or 1),
        )
        self._batch_timeout_s = batch_timeout_ms / 1000.0
        self._max_batch_size = max_batch_size
        self._metrics_actor = metrics_actor

        # Queue items are (texts: list[str], future: asyncio.Future).
        self._queue: asyncio.Queue = asyncio.Queue()
        self._processor_task: Optional[asyncio.Task] = None

        # Kick off the background batch-processing loop.
        self._processor_task = asyncio.ensure_future(self._batch_processor())
        get_logger().info(
            f"EmbedActor initialized with model={embedding_model}, "
            f"timeout_ms={batch_timeout_ms}, max_batch_size={max_batch_size}"
        )

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts and return their dense vectors.

        Puts the request on the internal queue and awaits resolution by the
        background batch-processing loop. Multiple concurrent calls are
        coalesced into a single ONNX inference call up to max_batch_size.

        :param texts: List of text strings to embed.
        :returns: List of embedding vectors (each as a plain Python list of
            floats) in the same order as ``texts``.

        Called from: QdrantCacheActor._embed_typed_fields_via_actor
            (llm/cache/ray_actor.py).
        """
        if not texts:
            return []

        loop = asyncio.get_event_loop()
        future: asyncio.Future = loop.create_future()
        await self._queue.put((texts, future))
        return await future

    async def _batch_processor(self) -> None:
        """Background coroutine that drains the queue and runs ONNX inference.

        Each iteration of the outer loop waits for the first item (blocking
        indefinitely), then tries to accumulate more items within
        batch_timeout_s until max_batch_size would be exceeded. Items whose
        text count would overflow the batch are put back on the queue and
        picked up by the next iteration.

        Each caller's future is resolved with exactly the slice of result
        vectors corresponding to their original texts list.

        Side effect: Resolves all pending asyncio.Future objects and, if a
            metrics_actor is configured, fires a record_embed_batch_size
            remote call.
        """
        while True:
            # Wait for the first item, blocking indefinitely.
            try:
                first_texts, first_future = await self._queue.get()
            except asyncio.CancelledError:
                return

            # Accumulate more items up to max_batch_size or until timeout.
            # Each entry is (texts, future); sizes tracks per-caller text counts.
            batch_texts: list[str] = list(first_texts)
            batch_futures: list[asyncio.Future] = [first_future]
            batch_sizes: list[int] = [len(first_texts)]

            while len(batch_texts) < self._max_batch_size:
                try:
                    texts, fut = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=self._batch_timeout_s,
                    )
                except asyncio.TimeoutError:
                    break
                except asyncio.CancelledError:
                    # Resolve pending futures with an error before exiting.
                    for f in batch_futures:
                        if not f.done():
                            f.set_exception(RuntimeError("EmbedActor shutting down"))
                    return

                if len(batch_texts) + len(texts) > self._max_batch_size:
                    # This item would overflow — put it back and stop accumulating.
                    # It will be the first item of the next batch.
                    await self._queue.put((texts, fut))
                    break

                batch_texts.extend(texts)
                batch_sizes.append(len(texts))
                batch_futures.append(fut)

            # Run ONNX inference off the event loop.
            total = len(batch_texts)
            try:
                raw: list[list[float]] = await asyncio.to_thread(
                    _embed_sync, self._model, batch_texts
                )
            except Exception as exc:
                for fut in batch_futures:
                    if not fut.done():
                        fut.set_exception(exc)
                continue

            # Emit metric fire-and-forget.
            if self._metrics_actor is not None:
                try:
                    self._metrics_actor.record_embed_batch_size.remote(total)
                except Exception:
                    pass

            # Resolve each future with its slice of results.
            offset = 0
            for fut, size in zip(batch_futures, batch_sizes):
                slice_ = raw[offset : offset + size]
                offset += size
                if not fut.done():
                    fut.set_result(slice_)

    async def close(self) -> None:
        """Cancel the background processor task and log shutdown.

        Side effect: Cancels the asyncio.Task started in __init__.
        Called from: InfrastructureManager.close (simulation/infrastructuremanager.py).
        """
        if self._processor_task is not None and not self._processor_task.done():
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        get_logger().info("EmbedActor closed")


def _embed_sync(model: TextEmbedding, texts: list[str]) -> list[list[float]]:
    """Run synchronous fastembed inference and return plain Python lists.

    This function is designed to be called from asyncio.to_thread so that
    the ONNX session does not block the actor event loop.

    :param model: Loaded fastembed TextEmbedding instance.
    :param texts: List of text strings to embed.
    :returns: List of embedding vectors as plain Python lists of floats.
        Plain lists are used (not numpy arrays) because they serialise more
        efficiently across Ray process boundaries.

    Called from: EmbedActor._batch_processor via asyncio.to_thread.
    """
    return [vec.tolist() for vec in model.embed(texts)]
