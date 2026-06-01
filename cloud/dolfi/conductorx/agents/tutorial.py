"""
TutorialAgent — Speed 2 overlay: step-by-step narration and code proofing.

Wraps every agent action with:
  - Pre-step explanation (what is about to happen and why)
  - Post-step confirmation (what happened and what it means)
  - Code annotation (inline comments added to generated code)
  - Workflow algorithm display
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class TutorialStep:
    step_number: int
    title: str
    pre_explanation: str
    action_label: str
    post_explanation: str
    code_snippet: Optional[str] = None
    annotated_code: Optional[str] = None
    rag_sources: list[str] = field(default_factory=list)


class TutorialAgent:
    """
    Generates step-by-step tutorial overlays for Speed 2 mode.
    """

    # ------------------------------------------------------------------
    # Step building
    # ------------------------------------------------------------------

    def build_flash_tutorial(self, firmware_version: str) -> list[TutorialStep]:
        """Tutorial overlay for firmware flashing workflow."""
        return [
            TutorialStep(
                step_number=1,
                title="Verify device connection",
                pre_explanation=(
                    "Before flashing, we confirm the Flipper Zero is connected and "
                    "responding. This prevents attempting a flash on an unresponsive device, "
                    "which could corrupt the firmware."
                ),
                action_label="device_info()",
                post_explanation=(
                    "The device responded with its hardware info. "
                    "This confirms the serial connection is stable."
                ),
            ),
            TutorialStep(
                step_number=2,
                title=f"Download firmware {firmware_version}",
                pre_explanation=(
                    f"We fetch firmware version {firmware_version} from the official release "
                    "registry. The download is verified against its published SHA-256 hash "
                    "before proceeding."
                ),
                action_label=f"download_firmware({firmware_version!r})",
                post_explanation=(
                    "Firmware downloaded and hash verified. "
                    "The binary is safe to flash."
                ),
            ),
            TutorialStep(
                step_number=3,
                title="Reboot to DFU mode",
                pre_explanation=(
                    "DFU (Device Firmware Update) mode allows direct flash access. "
                    "The Flipper will appear unresponsive during this reboot — that is normal."
                ),
                action_label="reboot(dfu=True)",
                post_explanation=(
                    "Device is now in DFU mode. "
                    "The blue LED should be solid. Proceeding to flash."
                ),
            ),
            TutorialStep(
                step_number=4,
                title="Flash firmware",
                pre_explanation=(
                    "Writing firmware to internal flash memory. "
                    "⚠️ Do not disconnect the device during this step."
                ),
                action_label="flash_firmware(path)",
                post_explanation=(
                    "Flash complete. The device will reboot automatically into the new firmware."
                ),
            ),
            TutorialStep(
                step_number=5,
                title="Verify new firmware version",
                pre_explanation=(
                    "After reboot, we query device info again to confirm the new "
                    f"firmware version {firmware_version} is running."
                ),
                action_label="device_info()",
                post_explanation=(
                    f"Firmware {firmware_version} confirmed. "
                    "Flash workflow complete. ✅"
                ),
            ),
        ]

    def annotate_code(self, code: str, language: str = "python") -> str:
        """Add inline tutorial comments to a code snippet."""
        if language == "python":
            return self._annotate_python(code)
        return code

    def workflow_diagram(self, steps: list[TutorialStep]) -> str:
        """Generate an ASCII workflow diagram for a sequence of steps."""
        lines = ["```"]
        for i, step in enumerate(steps):
            connector = "↓" if i < len(steps) - 1 else "✅"
            lines.append(f"[{step.step_number}] {step.title}")
            lines.append(f"    → {step.action_label}")
            lines.append(f"    {connector}")
        lines.append("```")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _annotate_python(code: str) -> str:
        """Add tutorial-style comments to Python code."""
        annotations = {
            "async def ": "# Async function — awaitable, non-blocking\n",
            "await ": "# Await suspends execution until this coroutine completes\n",
            "try:": "# Exception handling block — errors caught below\n",
            "except": "# Handle specific exception type here\n",
            "return": "# Return value to caller\n",
        }
        lines = code.splitlines()
        annotated = []
        for line in lines:
            stripped = line.lstrip()
            for keyword, comment in annotations.items():
                if stripped.startswith(keyword) and not stripped.startswith("#"):
                    indent = " " * (len(line) - len(stripped))
                    annotated.append(f"{indent}{comment.rstrip()}")
                    break
            annotated.append(line)
        return "\n".join(annotated)
