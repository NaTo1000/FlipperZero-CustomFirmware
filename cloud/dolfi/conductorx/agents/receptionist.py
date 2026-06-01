"""
ReceptionistAgent — intent classifier and router.

Routes incoming user messages to the appropriate ConductorX agent
based on intent classification. Uses the 3SP speed mode to determine
verbosity of routing explanation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AgentTarget = Literal[
    "conductor", "tutorial", "code", "recovery", "sql", "crypto", "debug", "receptionist"
]

INTENT_MAP: dict[str, AgentTarget] = {
    # Flipper device operations
    "flash": "conductor",
    "upload": "conductor",
    "download": "conductor",
    "reboot": "conductor",
    "connect": "conductor",
    "device": "conductor",
    "firmware": "conductor",
    "nfc": "conductor",
    "subghz": "conductor",
    "infrared": "conductor",
    "badusb": "conductor",
    "ibutton": "conductor",
    # Tutorial / learning
    "how do": "tutorial",
    "how to": "tutorial",
    "how i": "tutorial",
    "how can": "tutorial",
    "how would": "tutorial",
    "how is": "tutorial",
    "explain": "tutorial",
    "tutorial": "tutorial",
    "step": "tutorial",
    "guide": "tutorial",
    "walk": "tutorial",
    # Code generation / review
    "write": "code",
    "generate": "code",
    "code": "code",
    "script": "code",
    "build": "code",
    "compile": "code",
    "proof": "code",
    # Recovery
    "recover": "recovery",
    "rollback": "recovery",
    "broken": "recovery",
    "restore": "recovery",
    "backup": "recovery",
    # SQL / data
    "query": "sql",
    "database": "sql",
    "sql": "sql",
    "schema": "sql",
    "export": "sql",
    # Crypto / secrets
    "encrypt": "crypto",
    "decrypt": "crypto",
    "key": "crypto",
    "sign": "crypto",
    "gpg": "crypto",
    "secret": "crypto",
    "vault": "crypto",
    "rotate": "crypto",
    # Debug
    "error": "debug",
    "debug": "debug",
    "log": "debug",
    "fix": "debug",
    "crash": "debug",
    "traceback": "debug",
}


@dataclass
class RoutingDecision:
    target: AgentTarget
    confidence: float
    reason: str
    original_message: str


class ReceptionistAgent:
    """
    Classifies user intent and routes to the correct agent.
    """

    def route(self, message: str) -> RoutingDecision:
        msg_lower = message.lower()

        # Tutorial keywords take priority when they appear at the sentence start
        tutorial_starters = [
            "how do", "how to", "how i ", "how can", "how would", "how is",
            "explain", "tutorial", "step by step", "guide me", "walk me",
            "what is", "what are", "show me how",
        ]
        for starter in tutorial_starters:
            if msg_lower.startswith(starter) or f" {starter}" in msg_lower:
                return RoutingDecision(
                    target="tutorial",
                    confidence=0.9,
                    reason=f"Tutorial trigger phrase '{starter}' detected.",
                    original_message=message,
                )

        scores: dict[AgentTarget, int] = {}
        for keyword, target in INTENT_MAP.items():
            if keyword in msg_lower:
                scores[target] = scores.get(target, 0) + 1

        if not scores:
            return RoutingDecision(
                target="conductor",
                confidence=0.3,
                reason="No clear intent detected — defaulting to ConductorAgent.",
                original_message=message,
            )

        best_target = max(scores, key=lambda t: scores[t])
        total = sum(scores.values())
        confidence = scores[best_target] / total

        return RoutingDecision(
            target=best_target,
            confidence=round(confidence, 2),
            reason=f"Matched {scores[best_target]}/{total} intent signals for '{best_target}'.",
            original_message=message,
        )
