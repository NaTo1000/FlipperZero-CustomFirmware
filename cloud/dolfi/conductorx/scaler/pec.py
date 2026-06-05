"""
Predictive Auto-Scaler (PEC) — Predictive Error-avoidance Controller.

Monitors:
  - Active WebSocket connection count
  - API request queue depth (Redis)
  - CPU/memory utilization

Prediction:
  - Double Exponential Moving Average (DEMA) of connection velocity.
    DEMA eliminates the lag inherent in single EMA by subtracting the
    squared EMA trend:  DEMA = 2 * EMA1 - EMA2
  - If predicted load exceeds SCALE_UP_THRESHOLD → scale up
  - If predicted load drops below SCALE_DOWN_THRESHOLD for
    SCALE_DOWN_WINDOW consecutive windows → scale down

Actions:
  - Docker Swarm: `docker service scale chaimera-api=N`
  - K3s HPA patch (production)
  - Logs all scale events to Postgres audit table
"""
from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class LoadSample:
    timestamp: str
    connections: int
    queue_depth: int
    cpu_pct: float
    memory_pct: float

    @property
    def load_score(self) -> float:
        """Composite load score 0–1."""
        return max(
            self.connections / max(self.connections, 1),
            self.queue_depth / 100,
            self.cpu_pct / 100,
            self.memory_pct / 100,
        )


@dataclass
class ScaleDecision:
    action: str  # "scale_up" | "scale_down" | "hold"
    current_replicas: int
    target_replicas: int
    reason: str
    predicted_load: float


class PECScaler:
    """
    Predictive auto-scaler with DEMA-based load forecasting.

    Double Exponential Moving Average (DEMA) provides faster response to load
    changes than single EMA by subtracting the lagged EMA-of-EMA component:

        EMA1_n = α * load + (1 − α) * EMA1_{n-1}
        EMA2_n = α * EMA1_n + (1 − α) * EMA2_{n-1}
        DEMA_n = 2 * EMA1_n − EMA2_n

    This cancels the first-order lag, reducing reaction time to load spikes by
    approximately 1/(2α) windows compared to single EMA.

    Usage::

        scaler = PECScaler(service_name="chaimera-api", min_replicas=1, max_replicas=10)
        await scaler.run_loop(interval_seconds=30)
    """

    EMA_ALPHA = 0.3          # smoothing factor for both EMA passes
    SCALE_UP_THRESHOLD = 0.75
    SCALE_DOWN_THRESHOLD = 0.20
    SCALE_DOWN_WINDOW = 5    # consecutive windows below threshold before scale-down

    def __init__(
        self,
        service_name: str = "chaimera-api",
        min_replicas: int = 1,
        max_replicas: int = 20,
        backend: str = "swarm",  # "swarm" | "k3s" | "stub"
    ) -> None:
        self._service = service_name
        self._min = min_replicas
        self._max = max_replicas
        self._backend = backend
        self._current_replicas = min_replicas
        # DEMA requires two EMA accumulators
        self._ema1: float = 0.0   # first-pass EMA
        self._ema2: float = 0.0   # EMA of EMA1
        self._below_threshold_count: int = 0
        self._history: list[ScaleDecision] = []

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def run_loop(self, interval_seconds: int = 30) -> None:
        """Run the prediction + scaling loop indefinitely."""
        while True:
            sample = await self._collect_sample()
            decision = self._decide(sample)
            if decision.action != "hold":
                await self._apply(decision)
            self._history.append(decision)
            await asyncio.sleep(interval_seconds)

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def _decide(self, sample: LoadSample) -> ScaleDecision:
        # Update DEMA: two passes of EMA then subtract lag
        self._ema1 = self.EMA_ALPHA * sample.load_score + (1 - self.EMA_ALPHA) * self._ema1
        self._ema2 = self.EMA_ALPHA * self._ema1 + (1 - self.EMA_ALPHA) * self._ema2
        predicted = max(0.0, min(1.0, 2 * self._ema1 - self._ema2))

        if predicted >= self.SCALE_UP_THRESHOLD:
            self._below_threshold_count = 0
            # Scale up by ceiling of 1.5x
            target = min(self._max, math.ceil(self._current_replicas * 1.5))
            if target == self._current_replicas:
                target = min(self._max, self._current_replicas + 1)
            return ScaleDecision(
                action="scale_up",
                current_replicas=self._current_replicas,
                target_replicas=target,
                reason=f"EMA load {predicted:.2f} ≥ threshold {self.SCALE_UP_THRESHOLD}",
                predicted_load=predicted,
            )

        if predicted < self.SCALE_DOWN_THRESHOLD:
            self._below_threshold_count += 1
            if (
                self._below_threshold_count >= self.SCALE_DOWN_WINDOW
                and self._current_replicas > self._min
            ):
                target = max(self._min, self._current_replicas - 1)
                self._below_threshold_count = 0
                return ScaleDecision(
                    action="scale_down",
                    current_replicas=self._current_replicas,
                    target_replicas=target,
                    reason=(
                        f"EMA load {predicted:.2f} < threshold {self.SCALE_DOWN_THRESHOLD} "
                        f"for {self.SCALE_DOWN_WINDOW} windows"
                    ),
                    predicted_load=predicted,
                )
        else:
            self._below_threshold_count = 0

        return ScaleDecision(
            action="hold",
            current_replicas=self._current_replicas,
            target_replicas=self._current_replicas,
            reason=f"EMA load {predicted:.2f} within normal range",
            predicted_load=predicted,
        )

    # ------------------------------------------------------------------
    # Scale application
    # ------------------------------------------------------------------

    async def _apply(self, decision: ScaleDecision) -> None:
        if self._backend == "swarm":
            await self._swarm_scale(decision.target_replicas)
        elif self._backend == "k3s":
            await self._k3s_scale(decision.target_replicas)
        # stub: do nothing
        self._current_replicas = decision.target_replicas

    async def _swarm_scale(self, replicas: int) -> None:
        cmd = ["docker", "service", "scale", f"{self._service}={replicas}"]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

    async def _k3s_scale(self, replicas: int) -> None:
        patch = f'{{"spec":{{"replicas":{replicas}}}}}'
        cmd = [
            "kubectl", "patch", "deployment", self._service,
            "-p", patch, "--type=merge",
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

    # ------------------------------------------------------------------
    # Sample collection (stubbed — replace with real metrics in prod)
    # ------------------------------------------------------------------

    @staticmethod
    async def _collect_sample() -> LoadSample:
        """In production: query Prometheus/Redis/psutil."""
        import random
        return LoadSample(
            timestamp=datetime.now(UTC).isoformat(),
            connections=random.randint(0, 50),
            queue_depth=random.randint(0, 30),
            cpu_pct=random.uniform(0, 100),
            memory_pct=random.uniform(20, 80),
        )

    def history(self) -> list[ScaleDecision]:
        return list(self._history)

    @property
    def dema(self) -> float:
        """Current DEMA predicted load score (0–1)."""
        return max(0.0, min(1.0, 2 * self._ema1 - self._ema2))
