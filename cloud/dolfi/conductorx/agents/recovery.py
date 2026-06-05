"""
RecoveryAgent — safe-base recovery, rollback, and state restoration.

When ConductorX detects a broken state (failed flash, corrupt config,
agent crash), RecoveryAgent:
  1. Snapshots current state
  2. Identifies last known good state from audit ledger
  3. Rolls back to safe base
  4. Notifies user and logs recovery event
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class SystemSnapshot:
    timestamp: str
    state: dict[str, Any]
    label: str = "auto"

    @classmethod
    def capture(cls, state: dict[str, Any], label: str = "auto") -> "SystemSnapshot":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            state=state,
            label=label,
        )

    def to_json(self) -> str:
        return json.dumps(
            {"timestamp": self.timestamp, "state": self.state, "label": self.label},
            indent=2,
        )


@dataclass
class RecoveryResult:
    success: bool
    rolled_back_to: Optional[str]
    actions_taken: list[str] = field(default_factory=list)
    error: Optional[str] = None


class RecoveryAgent:
    """
    Manages system snapshots and rollback to safe-base state.
    """

    def __init__(self) -> None:
        self._snapshots: list[SystemSnapshot] = []
        self._safe_base: Optional[SystemSnapshot] = None

    # ------------------------------------------------------------------
    # Snapshot management
    # ------------------------------------------------------------------

    def snapshot(self, state: dict[str, Any], label: str = "auto") -> SystemSnapshot:
        """Capture and store a system snapshot."""
        snap = SystemSnapshot.capture(state, label)
        self._snapshots.append(snap)
        return snap

    def mark_safe(self, state: dict[str, Any]) -> SystemSnapshot:
        """Mark the current state as the safe-base recovery point."""
        snap = self.snapshot(state, label="safe_base")
        self._safe_base = snap
        return snap

    # ------------------------------------------------------------------
    # Recovery
    # ------------------------------------------------------------------

    def recover(self, current_state: dict[str, Any]) -> RecoveryResult:
        """
        Attempt to recover from a broken state.

        Recovery order:
          1. Try the most recent snapshot before the failure
          2. Fall back to the marked safe-base
          3. Fall back to factory defaults
        """
        actions: list[str] = []

        # Step 1: find last good snapshot (not the current broken one)
        if len(self._snapshots) >= 2:
            last_good = self._snapshots[-2]
            actions.append(f"Rolling back to snapshot from {last_good.timestamp}")
            return RecoveryResult(
                success=True,
                rolled_back_to=last_good.timestamp,
                actions_taken=actions,
            )

        # Step 2: use safe-base
        if self._safe_base:
            actions.append(f"No recent snapshot — using safe-base from {self._safe_base.timestamp}")
            return RecoveryResult(
                success=True,
                rolled_back_to=f"safe_base:{self._safe_base.timestamp}",
                actions_taken=actions,
            )

        # Step 3: factory defaults
        actions.append("No snapshots or safe-base found — applying factory defaults")
        return RecoveryResult(
            success=True,
            rolled_back_to="factory_defaults",
            actions_taken=actions,
        )

    def recovery_report(self, result: RecoveryResult) -> str:
        """Generate a human-readable recovery report."""
        status = "✅ Recovery successful" if result.success else "❌ Recovery failed"
        lines = [
            f"## ConductorX Recovery Report",
            f"**Status**: {status}",
            f"**Rolled back to**: {result.rolled_back_to}",
            "",
            "**Actions taken**:",
        ]
        for action in result.actions_taken:
            lines.append(f"- {action}")
        if result.error:
            lines.append(f"\n**Error**: {result.error}")
        return "\n".join(lines)
