"""
ReceptionistAgent — intent classifier and router.

Routes incoming user messages to the appropriate ConductorX agent
based on intent classification.  Uses adaptive weighted scoring:

  • Each keyword carries a per-category *weight* (higher = stronger signal).
  • Category score = Σ(weight_i) for all matched keywords in that category.
  • Confidence = best_score / total_score (i.e. normalised dominance).
  • Tutorial-starter phrases retain priority override (speed-matching).

This replaces the previous equal-weight keyword count and provides
more reliable routing when messages contain cross-category terms.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AgentTarget = Literal[
    "conductor", "tutorial", "code", "recovery", "sql", "crypto", "debug", "receptionist"
]

# (keyword, target, weight)
# Weight ∈ [0.5, 3.0]; higher = stronger signal for that category
WEIGHTED_INTENT_MAP: list[tuple[str, AgentTarget, float]] = [
    # --- Flipper device operations ---
    ("flash", "conductor", 2.0),
    ("upload", "conductor", 1.0),
    ("download", "conductor", 1.0),
    ("reboot", "conductor", 2.0),
    ("connect", "conductor", 1.0),
    ("device", "conductor", 0.8),
    ("firmware", "conductor", 2.5),
    ("nfc", "conductor", 2.0),
    ("subghz", "conductor", 2.5),
    ("infrared", "conductor", 2.0),
    ("badusb", "conductor", 2.5),
    ("ibutton", "conductor", 2.5),
    ("serial", "conductor", 1.5),
    ("dfu", "conductor", 2.5),
    # --- Tutorial / learning ---
    ("how do", "tutorial", 2.0),
    ("how to", "tutorial", 2.0),
    ("how i ", "tutorial", 1.5),
    ("how can", "tutorial", 1.5),
    ("how would", "tutorial", 1.5),
    ("how is", "tutorial", 1.0),
    ("explain", "tutorial", 2.0),
    ("tutorial", "tutorial", 3.0),
    ("step", "tutorial", 1.0),
    ("guide", "tutorial", 1.5),
    ("walk", "tutorial", 1.0),
    ("what is", "tutorial", 1.5),
    ("what are", "tutorial", 1.5),
    ("overview", "tutorial", 1.5),
    ("introduction", "tutorial", 1.5),
    # --- Code generation / review ---
    ("write", "code", 1.5),
    ("generate", "code", 1.5),
    ("code", "code", 1.0),
    ("script", "code", 2.0),
    ("build", "code", 1.0),
    ("compile", "code", 1.5),
    ("proof", "code", 2.0),
    ("review", "code", 1.5),
    ("refactor", "code", 2.0),
    ("manifest", "code", 2.0),
    ("fam", "code", 2.5),
    # --- Recovery ---
    ("recover", "recovery", 3.0),
    ("rollback", "recovery", 3.0),
    ("broken", "recovery", 1.5),
    ("restore", "recovery", 2.5),
    ("backup", "recovery", 2.0),
    ("snapshot", "recovery", 2.5),
    ("reset", "recovery", 1.5),
    # --- SQL / data ---
    ("query", "sql", 2.0),
    ("database", "sql", 2.0),
    ("sql", "sql", 3.0),
    ("schema", "sql", 2.5),
    ("export", "sql", 1.0),
    ("table", "sql", 1.5),
    ("insert", "sql", 2.0),
    ("select", "sql", 2.5),
    # --- Crypto / secrets ---
    ("encrypt", "crypto", 3.0),
    ("decrypt", "crypto", 3.0),
    ("key", "crypto", 1.5),
    ("sign", "crypto", 2.0),
    ("gpg", "crypto", 3.0),
    ("secret", "crypto", 1.5),
    ("vault", "crypto", 2.5),
    ("rotate", "crypto", 2.0),
    ("aes", "crypto", 3.0),
    ("ed25519", "crypto", 3.0),
    # --- Debug ---
    ("error", "debug", 2.0),
    ("debug", "debug", 2.5),
    ("log", "debug", 1.5),
    ("fix", "debug", 1.0),
    ("crash", "debug", 2.5),
    ("traceback", "debug", 3.0),
    ("exception", "debug", 2.5),
    ("timeout", "debug", 1.5),
]


@dataclass
class RoutingDecision:
    target: AgentTarget
    confidence: float
    reason: str
    original_message: str


class ReceptionistAgent:
    """
    Classifies user intent and routes to the correct agent using
    adaptive weighted scoring.
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

        scores: dict[AgentTarget, float] = {}
        matched: dict[AgentTarget, int] = {}
        for keyword, target, weight in WEIGHTED_INTENT_MAP:
            if keyword in msg_lower:
                scores[target] = scores.get(target, 0.0) + weight
                matched[target] = matched.get(target, 0) + 1

        if not scores:
            return RoutingDecision(
                target="conductor",
                confidence=0.3,
                reason="No clear intent detected — defaulting to ConductorAgent.",
                original_message=message,
            )

        best_target = max(scores, key=lambda t: scores[t])
        total_score = sum(scores.values())
        confidence = scores[best_target] / total_score

        return RoutingDecision(
            target=best_target,
            confidence=round(confidence, 2),
            reason=(
                f"Weighted score {scores[best_target]:.1f}/{total_score:.1f} "
                f"({matched[best_target]} keyword(s)) for '{best_target}'."
            ),
            original_message=message,
        )
