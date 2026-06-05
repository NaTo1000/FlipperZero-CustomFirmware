"""
DebugAgent — error analysis, log triage, and auto-fix suggestions.

Parses Python tracebacks, Flipper serial logs, and agent error payloads.
In Speed 3: auto-submits fixes to CodeAgent and triggers recovery if needed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ErrorAnalysis:
    error_type: str
    message: str
    file: Optional[str]
    line: Optional[int]
    suggestions: list[str] = field(default_factory=list)
    auto_fixable: bool = False
    fix_description: Optional[str] = None


# Known error patterns → fix suggestions
ERROR_PATTERNS: list[tuple[str, str, str]] = [
    # (pattern, suggestion, fix_description)
    (
        r"ConnectionRefusedError",
        "Check that the Flipper Zero is connected and the correct port is selected.",
        "Verify USB connection and port in settings.",
    ),
    (
        r"serial\.serialutil\.SerialException",
        "Serial port unavailable — device may be disconnected or port in use.",
        "Disconnect and reconnect the device. Kill other serial monitor processes.",
    ),
    (
        r"asyncio\.TimeoutError",
        "Device did not respond within timeout — try increasing timeout or rebooting device.",
        "Increase CONDUCTORX_SERIAL_TIMEOUT env var or reboot Flipper.",
    ),
    (
        r"KeyError: '(.+)'",
        "Missing key in response payload.",
        "Check agent response schema against expected keys.",
    ),
    (
        r"jwt\.exceptions\.ExpiredSignatureError",
        "Session token expired — user needs to re-authenticate.",
        "Redirect to login and issue a new JWT.",
    ),
    (
        r"hvac\.exceptions\.Forbidden",
        "Vault access denied — check VAULT_TOKEN permissions.",
        "Verify VAULT_TOKEN has read access to the required secret path.",
    ),
    (
        r"qdrant_client\.http\.exceptions\.UnexpectedResponse",
        "Qdrant returned an unexpected response — collection may not exist.",
        "Run RAGIndexer._ensure_collection() to create the collection.",
    ),
    (
        r"psycopg.*OperationalError",
        "PostgreSQL connection failed — check POSTGRES_HOST and credentials.",
        "Verify database is running and POSTGRES_* env vars are set.",
    ),
]


def _parse_python_traceback(traceback: str) -> Optional[ErrorAnalysis]:
    """Extract structured info from a Python traceback string."""
    # Last line is the exception
    lines = [l.strip() for l in traceback.strip().splitlines() if l.strip()]
    if not lines:
        return None

    exception_line = lines[-1]
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception|Warning|Timeout))\s*:?\s*(.*)", exception_line)
    if not match:
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_.]*)\s*:?\s*(.*)", exception_line)

    error_type = match.group(1) if match else "UnknownError"
    message = match.group(2) if match else exception_line

    # Find file/line from traceback
    file_match = re.search(r'File "([^"]+)", line (\d+)', traceback)
    file_path = file_match.group(1) if file_match else None
    line_num = int(file_match.group(2)) if file_match else None

    return ErrorAnalysis(
        error_type=error_type,
        message=message,
        file=file_path,
        line=line_num,
    )


class DebugAgent:
    """
    Analyzes errors and provides actionable fix suggestions.
    """

    def analyze(self, error_text: str) -> ErrorAnalysis:
        """
        Analyze an error string (traceback, log line, or exception message).
        Returns structured analysis with suggestions.
        """
        analysis = _parse_python_traceback(error_text)
        if not analysis:
            analysis = ErrorAnalysis(
                error_type="UnknownError",
                message=error_text[:256],
                file=None,
                line=None,
            )

        # Match against known patterns
        for pattern, suggestion, fix_desc in ERROR_PATTERNS:
            if re.search(pattern, error_text):
                analysis.suggestions.append(suggestion)
                analysis.fix_description = fix_desc
                analysis.auto_fixable = True
                break

        if not analysis.suggestions:
            analysis.suggestions.append(
                "No known fix pattern matched. Check the audit ledger for recent agent actions "
                "that may have caused this error."
            )

        return analysis

    def analyze_flipper_log(self, log_output: str) -> list[ErrorAnalysis]:
        """Parse Flipper serial log output for errors."""
        errors = []
        error_line_pattern = re.compile(r"\[E\]\s+(.+)")
        for line in log_output.splitlines():
            m = error_line_pattern.search(line)
            if m:
                errors.append(
                    ErrorAnalysis(
                        error_type="FlipperError",
                        message=m.group(1),
                        file=None,
                        line=None,
                        suggestions=["Check Flipper firmware logs for the corresponding component."],
                    )
                )
        return errors

    def format_report(self, analysis: ErrorAnalysis) -> str:
        """Format a debug analysis as a markdown report."""
        lines = [
            f"## 🐛 Debug Report",
            f"**Error**: `{analysis.error_type}: {analysis.message}`",
        ]
        if analysis.file:
            lines.append(f"**Location**: `{analysis.file}:{analysis.line}`")
        lines.append("")
        lines.append("**Suggestions**:")
        for s in analysis.suggestions:
            lines.append(f"- {s}")
        if analysis.fix_description:
            lines.append(f"\n**Auto-fix**: {analysis.fix_description}")
        return "\n".join(lines)
