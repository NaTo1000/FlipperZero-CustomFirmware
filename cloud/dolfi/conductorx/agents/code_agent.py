"""
CodeAgent — code generation, proofing, rewriting, and workflow automation.

Speed 2: Annotates and proofs every code string.
Speed 3: Generates full CI pipelines, app manifests, and workflows autonomously.
"""
from __future__ import annotations

import ast
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CodeProofResult:
    original: str
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    is_safe: bool = True
    rewritten: Optional[str] = None


class CodeAgent:
    """
    Proofs, generates, and rewrites code for the Flipper ecosystem.
    """

    # ------------------------------------------------------------------
    # Proofing
    # ------------------------------------------------------------------

    def proof_python(self, code: str) -> CodeProofResult:
        """Static analysis of Python code before execution."""
        result = CodeProofResult(original=code)

        # Syntax check
        try:
            ast.parse(code)
        except SyntaxError as exc:
            result.issues.append(f"SyntaxError: {exc}")
            result.is_safe = False
            return result

        # Dangerous pattern checks
        dangerous = [
            (r"\bos\.system\b", "os.system() — use subprocess with shell=False"),
            (r"\beval\s*\(", "eval() — unsafe code execution"),
            (r"\bexec\s*\(", "exec() — unsafe code execution"),
            (r"\b__import__\s*\(", "__import__() — dynamic import risk"),
            (r"open\(['\"]\/etc", "Reading /etc files — potential sensitive data access"),
            (r"subprocess.*shell\s*=\s*True", "shell=True in subprocess — use list args"),
        ]
        for pattern, message in dangerous:
            if re.search(pattern, code):
                result.issues.append(f"WARNING: {message}")
                result.suggestions.append(f"Fix: avoid pattern matching '{pattern}'")

        # Suggest improvements
        if "print(" in code and "logging" not in code:
            result.suggestions.append("Consider using `logging` module instead of print().")
        if "except:" in code and "except Exception" not in code:
            result.suggestions.append("Bare `except:` catches all exceptions — be specific.")

        return result

    def proof_c(self, code: str) -> CodeProofResult:
        """Basic C code safety checks for Flipper app development."""
        result = CodeProofResult(original=code)

        dangerous_c = [
            (r"\bstrcpy\s*\(", "strcpy() — use strncpy() or strlcpy()"),
            (r"\bsprintf\s*\(", "sprintf() — use snprintf()"),
            (r"\bgets\s*\(", "gets() — always unsafe, use fgets()"),
            (r"\bstrcat\s*\(", "strcat() — use strncat()"),
        ]
        for pattern, message in dangerous_c:
            if re.search(pattern, code):
                result.issues.append(f"WARNING: {message}")
                result.is_safe = False

        return result

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate_fam_manifest(
        self,
        app_name: str,
        app_id: str,
        entry_point: str = "app_main",
        stack_size: int = 1024,
        fap_category: str = "Misc",
    ) -> str:
        """Generate a Flipper application manifest (.fam) file."""
        return f'''App(
    appid="{app_id}",
    name="{app_name}",
    apptype=FlipperAppType.EXTERNAL,
    entry_point="{entry_point}",
    stack_size={stack_size},
    fap_category="{fap_category}",
)
'''

    def generate_badusb_script(
        self,
        commands: list[str],
        delay_ms: int = 500,
    ) -> str:
        """Generate a BadUSB Ducky Script payload."""
        lines = [f"DELAY {delay_ms}"]
        for cmd in commands:
            lines.append(f"STRING {cmd}")
            lines.append(f"DELAY {delay_ms}")
            lines.append("ENTER")
        return "\n".join(lines)

    def generate_github_actions_workflow(
        self,
        python_version: str = "3.11",
        test_command: str = "pytest cloud/",
        lint_command: str = "ruff check cloud/",
    ) -> str:
        """Generate a GitHub Actions CI workflow YAML."""
        return f"""name: ConductorX CI

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python {python_version}
        uses: actions/setup-python@v5
        with:
          python-version: "{python_version}"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r cloud/requirements.txt
      - name: Lint
        run: {lint_command}
      - name: Test
        run: {test_command}
      - name: Licence check
        run: pip-licenses --order=license --fail-on="GPL-3.0-only"
"""

    # ------------------------------------------------------------------
    # Recovery rewrite
    # ------------------------------------------------------------------

    def safe_rewrite(self, code: str, language: str = "python") -> CodeProofResult:
        """Proof and auto-fix a code string, returning the safest possible version."""
        if language == "python":
            result = self.proof_python(code)
        elif language == "c":
            result = self.proof_c(code)
        else:
            result = CodeProofResult(original=code, issues=["Unknown language"])
            return result

        # Auto-fix known patterns
        rewritten = code
        rewritten = re.sub(r"\bstrcpy\s*\(", "strncpy(", rewritten)
        rewritten = re.sub(r"\bsprintf\s*\(", "snprintf(", rewritten)
        rewritten = re.sub(r"\bgets\s*\(", "fgets(", rewritten)
        result.rewritten = rewritten if rewritten != code else None
        return result
