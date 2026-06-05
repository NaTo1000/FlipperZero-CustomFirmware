"""
Circuit Breaker Protocol — ConductorX inter-agent resilience layer.

Implements the classic three-state circuit breaker pattern for all
agent-to-agent and agent-to-service calls:

    CLOSED  ──(failure_threshold exceeded)──► OPEN
    OPEN    ──(reset_timeout elapsed)────────► HALF_OPEN
    HALF_OPEN ──(probe succeeds)─────────────► CLOSED
    HALF_OPEN ──(probe fails)────────────────► OPEN

Benefits over naive retry loops:
  - Prevents thundering herd on a failing dependency
  - Provides fast-fail with a meaningful error instead of waiting for timeout
  - Self-heals via HALF_OPEN probe without operator intervention
  - Configurable per dependency (each ConductorX agent gets its own breaker)

Usage::

    breaker = CircuitBreaker(name="qdrant", failure_threshold=3, reset_timeout=30)

    try:
        result = breaker.call(qdrant_client.search, ...)
    except CircuitOpenError:
        result = cached_fallback()
"""
from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

F = TypeVar("F")


class CircuitState(str, Enum):
    CLOSED = "closed"      # Normal operation — calls pass through
    OPEN = "open"          # Dependency broken — calls fast-fail
    HALF_OPEN = "half_open"  # Probing — one call allowed through


class CircuitOpenError(RuntimeError):
    """Raised when a call is attempted while the circuit is OPEN."""

    def __init__(self, name: str, opens_at: float, reset_timeout: float) -> None:
        remaining = max(0.0, (opens_at + reset_timeout) - time.monotonic())
        super().__init__(
            f"Circuit '{name}' is OPEN. Retry in {remaining:.1f}s."
        )
        self.name = name
        self.remaining_seconds = remaining


@dataclass
class BreakerMetrics:
    """Rolling metrics tracked by a CircuitBreaker instance."""
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: float | None = None
    last_state_change: float = field(default_factory=time.monotonic)


class CircuitBreaker:
    """
    Thread-safe (GIL-protected) circuit breaker for synchronous calls.
    For async calls use ``async_call``.

    Parameters
    ----------
    name:
        Human-readable identifier (appears in logs and errors).
    failure_threshold:
        Number of consecutive failures before the circuit opens.
    reset_timeout:
        Seconds to wait in OPEN state before transitioning to HALF_OPEN.
    success_threshold:
        Consecutive successes in HALF_OPEN needed to close the circuit.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        success_threshold: int = 1,
    ) -> None:
        self._name = name
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._opened_at: float | None = None
        self._metrics = BreakerMetrics()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> CircuitState:
        self._maybe_transition_to_half_open()
        return self._state

    @property
    def name(self) -> str:
        return self._name

    @property
    def metrics(self) -> BreakerMetrics:
        return self._metrics

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute *fn* through the circuit breaker.

        Raises ``CircuitOpenError`` if the circuit is OPEN.
        Propagates the original exception on failure (and records it).
        """
        self._maybe_transition_to_half_open()

        if self._state == CircuitState.OPEN:
            raise CircuitOpenError(self._name, self._opened_at or 0.0, self._reset_timeout)

        self._metrics.total_calls += 1
        try:
            result = fn(*args, **kwargs)
            self._record_success()
            return result
        except Exception:
            self._record_failure()
            raise

    async def async_call(self, coro_fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Async variant — awaits the coroutine returned by *coro_fn*.
        """
        self._maybe_transition_to_half_open()

        if self._state == CircuitState.OPEN:
            raise CircuitOpenError(self._name, self._opened_at or 0.0, self._reset_timeout)

        self._metrics.total_calls += 1
        try:
            result = await coro_fn(*args, **kwargs)
            self._record_success()
            return result
        except Exception:
            self._record_failure()
            raise

    def reset(self) -> None:
        """Manually force the circuit to CLOSED (for operator intervention)."""
        self._state = CircuitState.CLOSED
        self._opened_at = None
        self._metrics.consecutive_failures = 0
        self._metrics.last_state_change = time.monotonic()

    # ------------------------------------------------------------------
    # Internal state machine
    # ------------------------------------------------------------------

    def _record_success(self) -> None:
        self._metrics.total_successes += 1
        self._metrics.consecutive_failures = 0
        self._metrics.consecutive_successes += 1

        if self._state == CircuitState.HALF_OPEN:
            if self._metrics.consecutive_successes >= self._success_threshold:
                self._transition(CircuitState.CLOSED)

    def _record_failure(self) -> None:
        self._metrics.total_failures += 1
        self._metrics.consecutive_failures += 1
        self._metrics.consecutive_successes = 0
        self._metrics.last_failure_time = time.monotonic()

        if self._state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
            if self._metrics.consecutive_failures >= self._failure_threshold:
                self._transition(CircuitState.OPEN)

    def _maybe_transition_to_half_open(self) -> None:
        if (
            self._state == CircuitState.OPEN
            and self._opened_at is not None
            and (time.monotonic() - self._opened_at) >= self._reset_timeout
        ):
            self._transition(CircuitState.HALF_OPEN)

    def _transition(self, new_state: CircuitState) -> None:
        self._state = new_state
        self._metrics.last_state_change = time.monotonic()
        if new_state == CircuitState.OPEN:
            self._opened_at = time.monotonic()
            self._metrics.consecutive_successes = 0
        elif new_state == CircuitState.CLOSED:
            self._opened_at = None
            self._metrics.consecutive_failures = 0
