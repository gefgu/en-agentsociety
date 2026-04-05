import asyncio
import datetime
import time
from typing import Awaitable, Callable, Optional, Protocol, Sequence

from ..logger import get_logger


class _LoadBalancerConfig(Protocol):
    concurrency: int
    base_url: Optional[str]


class LLMLoadBalancer:
    """Coordinates per-provider capacity, cooldown, and circuit breaker state."""

    def __init__(
        self,
        configs: Sequence[_LoadBalancerConfig],
        cooldown_duration: float = 300.0,
        max_consecutive_failures: int = 3,
        all_servers_down_log_interval: float = 300.0,
    ):
        self._configs = configs
        self._active_requests = [0] * len(configs)
        self._cooldown_until = [0.0] * len(configs)
        self._consecutive_failures = [0] * len(configs)
        self.cooldown_duration = cooldown_duration
        self.max_consecutive_failures = max_consecutive_failures
        self._routing_condition = asyncio.Condition()
        self._last_all_servers_down_warning = 0.0
        self._all_servers_down_log_interval = all_servers_down_log_interval

    async def acquire_client(
        self,
        health_check_request: Callable[[int], Awaitable[tuple[bool, str]]],
    ) -> int:
        """Select a server and reserve one in-flight slot for it."""
        async with self._routing_condition:
            while True:
                current_time = time.time()

                available_indices = [
                    i
                    for i in range(len(self._configs))
                    if self._active_requests[i] < self._configs[i].concurrency
                    and current_time >= self._cooldown_until[i]
                ]

                if available_indices:
                    healthy_indices = []
                    for i in available_indices:
                        if self._cooldown_until[i] > 0 and current_time >= self._cooldown_until[i]:
                            if await self._health_check(i, health_check_request):
                                healthy_indices.append(i)
                                self._cooldown_until[i] = 0.0
                            else:
                                self._cooldown_until[i] = current_time + self.cooldown_duration
                                get_logger().warning(
                                    f"GPU {i} ({self._configs[i].base_url}) - Health check failed, extending cooldown for {self.cooldown_duration}s"
                                )
                        else:
                            healthy_indices.append(i)

                    if healthy_indices:
                        client_i = min(
                            healthy_indices,
                            key=lambda i: self._active_requests[i] / self._configs[i].concurrency,
                        )
                        self._active_requests[client_i] += 1
                        return client_i

                servers_in_cooldown = [
                    i
                    for i in range(len(self._configs))
                    if current_time < self._cooldown_until[i]
                ]

                if (
                    servers_in_cooldown
                    and current_time - self._last_all_servers_down_warning
                    >= self._all_servers_down_log_interval
                ):
                    cooldown_info = [
                        f"GPU {i} ({self._configs[i].base_url}): cooldown until {datetime.datetime.fromtimestamp(self._cooldown_until[i]).strftime('%H:%M:%S') if self._cooldown_until[i] > current_time else 'available'}, active: {self._active_requests[i]}/{self._configs[i].concurrency}"
                        for i in servers_in_cooldown
                    ]
                    get_logger().warning(
                        "⚠️  ALL SERVERS DOWN - Waiting for manual intervention. Status:\n"
                        + "\n".join(cooldown_info)
                    )
                    self._last_all_servers_down_warning = current_time

                try:
                    await asyncio.wait_for(self._routing_condition.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    pass

    async def _health_check(
        self,
        client_i: int,
        health_check_request: Callable[[int], Awaitable[tuple[bool, str]]],
    ) -> bool:
        """Probe a server after cooldown and log health-check outcome."""
        try:
            success, message = await health_check_request(client_i)
            if success:
                get_logger().info(
                    f"✅ GPU {client_i} ({self._configs[client_i].base_url}) - Health check PASSED"
                )
                return True

            get_logger().warning(
                f"❌ GPU {client_i} ({self._configs[client_i].base_url}) - Health check FAILED: {message[:100]}"
            )
            return False
        except Exception as e:
            get_logger().warning(
                f"❌ GPU {client_i} ({self._configs[client_i].base_url}) - Health check ERROR: {str(e)[:100]}"
            )
            return False

    async def release_client(self, client_i: int) -> None:
        """Release one in-flight slot for a previously acquired server."""
        async with self._routing_condition:
            self._active_requests[client_i] -= 1
            self._routing_condition.notify_all()

    async def mark_request_success(self, client_i: int) -> None:
        """Reset server failure counter after a successful request."""
        async with self._routing_condition:
            self._consecutive_failures[client_i] = 0

    async def mark_request_failure(
        self,
        client_i: int,
        should_cooldown: bool,
        error_message: str,
    ) -> None:
        """Update failure counters and trigger cooldown when configured threshold is reached."""
        async with self._routing_condition:
            current_time = time.time()
            already_in_cooldown = current_time < self._cooldown_until[client_i]

            if should_cooldown and not already_in_cooldown:
                self._consecutive_failures[client_i] += 1

                if self._consecutive_failures[client_i] >= self.max_consecutive_failures:
                    cooldown_end = current_time + self.cooldown_duration
                    self._cooldown_until[client_i] = cooldown_end
                    get_logger().warning(
                        f"🔴 GPU {client_i} ({self._configs[client_i].base_url}) - CIRCUIT BREAKER TRIGGERED after {self._consecutive_failures[client_i]} failed requests. "
                        f"Cooldown {self.cooldown_duration}s until {datetime.datetime.fromtimestamp(cooldown_end).strftime('%H:%M:%S')}. Error: {error_message[:100]}"
                    )
                    self._consecutive_failures[client_i] = 0
                    self._routing_condition.notify_all()
                else:
                    get_logger().warning(
                        f"⚠️  GPU {client_i} ({self._configs[client_i].base_url}) - Request failure {self._consecutive_failures[client_i]}/{self.max_consecutive_failures}. "
                        f"Error: {error_message[:100]}"
                    )
            elif already_in_cooldown:
                get_logger().debug(
                    f"GPU {client_i} request failed but server already in cooldown (expires at {datetime.datetime.fromtimestamp(self._cooldown_until[client_i]).strftime('%H:%M:%S')})"
                )
