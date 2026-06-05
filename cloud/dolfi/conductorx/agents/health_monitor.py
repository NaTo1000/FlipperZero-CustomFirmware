"""
HealthMonitor Agent — proactive system health surveillance.

Continuously polls registered services and agents, classifies their
health state, and surfaces actionable alerts.  In Speed 3/4 it can
trigger RecoveryAgent or PECScaler responses automatically.

Health classification:
  HEALTHY   — all checks pass within thresholds
  DEGRADED  — one or more checks exceed warn thresholds
  CRITICAL  — one or more checks exceed critical thresholds or are unreachable

Each check is represented as a ``HealthCheck`` dataclass.  Results
are accumulated in a rolling ``HealthReport`` with a human-readable
markdown summary.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """
    Specification for a single health-check probe.

    Parameters
    ----------
    name:
        Human-readable service name (e.g. "postgres", "redis", "qdrant").
    probe:
        Zero-argument callable returning a numeric metric (e.g. latency in ms,
        queue depth, error rate).  Raises on connectivity failure.
    warn_threshold:
        Metric value above which status → DEGRADED.
    critical_threshold:
        Metric value above which status → CRITICAL.
    unit:
        Display unit string (e.g. "ms", "items", "%").
    """
    name: str
    probe: Callable[[], float]
    warn_threshold: float
    critical_threshold: float
    unit: str = ""


@dataclass
class CheckResult:
    name: str
    status: HealthStatus
    value: float | None
    message: str
    checked_at: float = field(default_factory=time.monotonic)


@dataclass
class HealthReport:
    overall: HealthStatus
    results: list[CheckResult]
    checked_at: float = field(default_factory=time.monotonic)

    def markdown(self) -> str:
        icon = {"healthy": "✅", "degraded": "⚠️", "critical": "🔴", "unknown": "❓"}
        lines = [
            "## ConductorX Health Report",
            f"**Overall**: {icon.get(self.overall.value, '?')} {self.overall.value.upper()}",
            "",
            "| Service | Status | Value | Message |",
            "|---------|--------|-------|---------|",
        ]
        for r in self.results:
            val_str = f"{r.value:.2f}" if r.value is not None else "N/A"
            lines.append(
                f"| {r.name} | {icon.get(r.status.value, '?')} {r.status.value} "
                f"| {val_str} | {r.message} |"
            )
        return "\n".join(lines)


class HealthMonitorAgent:
    """
    Runs registered health checks and aggregates results into a HealthReport.

    Usage::

        monitor = HealthMonitorAgent()
        monitor.register(HealthCheck(
            name="postgres",
            probe=lambda: ping_postgres_latency_ms(),
            warn_threshold=100.0,
            critical_threshold=500.0,
            unit="ms",
        ))
        report = monitor.check_all()
        print(report.markdown())
    """

    def __init__(self) -> None:
        self._checks: list[HealthCheck] = []
        self._history: list[HealthReport] = []

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, check: HealthCheck) -> None:
        """Register a health check probe."""
        self._checks.append(check)

    def unregister(self, name: str) -> bool:
        """Remove a check by name.  Returns True if found and removed."""
        before = len(self._checks)
        self._checks = [c for c in self._checks if c.name != name]
        return len(self._checks) < before

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def check_all(self) -> HealthReport:
        """Run all registered probes and return a consolidated HealthReport."""
        results: list[CheckResult] = []
        for check in self._checks:
            results.append(self._run_check(check))

        overall = self._aggregate(results)
        report = HealthReport(overall=overall, results=results)
        self._history.append(report)
        return report

    def check_one(self, name: str) -> CheckResult | None:
        """Run a single named check.  Returns None if not found."""
        for check in self._checks:
            if check.name == name:
                return self._run_check(check)
        return None

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def last_report(self) -> HealthReport | None:
        return self._history[-1] if self._history else None

    def history(self) -> list[HealthReport]:
        return list(self._history)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run_check(self, check: HealthCheck) -> CheckResult:
        try:
            value = check.probe()
        except Exception as exc:
            return CheckResult(
                name=check.name,
                status=HealthStatus.CRITICAL,
                value=None,
                message=f"Probe raised: {exc!s}",
            )

        if value >= check.critical_threshold:
            status = HealthStatus.CRITICAL
            msg = (
                f"{value:.2f}{check.unit} ≥ critical threshold "
                f"{check.critical_threshold}{check.unit}"
            )
        elif value >= check.warn_threshold:
            status = HealthStatus.DEGRADED
            msg = (
                f"{value:.2f}{check.unit} ≥ warn threshold "
                f"{check.warn_threshold}{check.unit}"
            )
        else:
            status = HealthStatus.HEALTHY
            msg = f"{value:.2f}{check.unit} within normal range"

        return CheckResult(name=check.name, status=status, value=value, message=msg)

    @staticmethod
    def _aggregate(results: list[CheckResult]) -> HealthStatus:
        if not results:
            return HealthStatus.UNKNOWN
        statuses = {r.status for r in results}
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        if all(r.status == HealthStatus.HEALTHY for r in results):
            return HealthStatus.HEALTHY
        return HealthStatus.UNKNOWN
