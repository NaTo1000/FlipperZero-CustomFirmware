"""
3SP Mode Controller — ConductorX Three Speed Protocol.

Speed 1: Guidance  — respond only when asked, minimal output
Speed 2: Overlay   — full tutorial, code proofing, step narration
Speed 3: Full Auto — autonomous orchestration, CI/CD, deployments
"""
from __future__ import annotations

import os
from enum import IntEnum
from typing import Optional

SPEED_ENV_VAR = "CONDUCTORX_SPEED"


class Speed(IntEnum):
    GUIDANCE = 1
    OVERLAY = 2
    FULL_AUTO = 3


# Descriptions used in system prompts
SPEED_SYSTEM_PROMPTS: dict[Speed, str] = {
    Speed.GUIDANCE: (
        "You are ConductorX in Guidance mode. "
        "Respond ONLY when directly asked. "
        "Keep answers minimal, precise, and grounded in retrieved context. "
        "Do not trigger any automation unless explicitly requested."
    ),
    Speed.OVERLAY: (
        "You are ConductorX in Overlay/Tutorial mode. "
        "Annotate every action with a clear explanation. "
        "Proof every code string submitted by the user. "
        "Narrate each automated step before executing it. "
        "Show workflow algorithms and RAG sources alongside answers."
    ),
    Speed.FULL_AUTO: (
        "You are ConductorX in Full Automation mode. "
        "Plan, execute, validate, and recover autonomously. "
        "Run CI checks, licence checks, and build pipelines without waiting for prompts. "
        "Sign and deploy releases via GPG and app store pipelines. "
        "Rotate secrets, archive code, and update documentation automatically. "
        "Always confirm before irreversible hardware operations (firmware flash)."
    ),
}


class ModeController:
    """
    Manages the active 3SP speed for a session.

    The speed can be set:
    - Via environment variable (CONDUCTORX_SPEED=1|2|3)
    - Programmatically per session
    - Auto-detected from context signals
    """

    def __init__(self, initial_speed: Optional[Speed] = None) -> None:
        self._speed = initial_speed or self._load_from_env()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def speed(self) -> Speed:
        return self._speed

    def set_speed(self, speed: int | Speed) -> Speed:
        self._speed = Speed(int(speed))
        return self._speed

    def system_prompt(self) -> str:
        return SPEED_SYSTEM_PROMPTS[self._speed]

    def is_autonomous(self) -> bool:
        return self._speed == Speed.FULL_AUTO

    def is_tutorial(self) -> bool:
        return self._speed == Speed.OVERLAY

    def is_guidance(self) -> bool:
        return self._speed == Speed.GUIDANCE

    def auto_detect(self, user_message: str) -> Speed:
        """
        Heuristically detect appropriate speed from user message content.
        Updates internal speed and returns detected value.
        """
        msg = user_message.lower()
        auto_keywords = [
            "deploy", "release", "publish", "automate", "ci", "cd",
            "app store", "google play", "build", "flash all", "rotate secrets",
        ]
        tutorial_keywords = [
            "how do i", "explain", "show me", "tutorial", "step by step",
            "help me understand", "walk me through", "what is",
        ]
        if any(k in msg for k in auto_keywords):
            return self.set_speed(Speed.FULL_AUTO)
        if any(k in msg for k in tutorial_keywords):
            return self.set_speed(Speed.OVERLAY)
        return self.set_speed(Speed.GUIDANCE)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _load_from_env() -> Speed:
        raw = os.getenv(SPEED_ENV_VAR, "1")
        try:
            return Speed(int(raw))
        except (ValueError, KeyError):
            return Speed.GUIDANCE
