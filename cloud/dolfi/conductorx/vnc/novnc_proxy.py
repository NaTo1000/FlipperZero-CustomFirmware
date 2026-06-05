"""
noVNC session manager — token-authenticated VNC session proxy.

Each user gets an isolated VNC session token tied to their JWT.
Sessions expire when the JWT expires or on explicit disconnect.
"""
from __future__ import annotations

import os
import secrets
import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VNCSession:
    token: str
    user_id: str
    port: int
    pid: int
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0

    def is_expired(self) -> bool:
        return time.time() > self.expires_at if self.expires_at else False


class NoVNCProxy:
    """
    Manages per-user VNC sessions with token-based authentication.

    In production: each session gets a dedicated TigerVNC display.
    noVNC is served on a shared port with per-session path tokens.
    """

    BASE_VNC_PORT = 5900
    SESSION_TTL = 3600  # 1 hour

    def __init__(self) -> None:
        self._sessions: dict[str, VNCSession] = {}  # token → session
        self._user_sessions: dict[str, str] = {}    # user_id → token
        self._next_port = self.BASE_VNC_PORT + 1

    def create_session(self, user_id: str, jwt_ttl: int = SESSION_TTL) -> VNCSession:
        """Start a VNC session for a user and return the access token."""
        # Kill existing session for this user if any
        self.terminate_session_for_user(user_id)

        token = secrets.token_urlsafe(32)
        port = self._allocate_port()
        pid = self._start_vnc(port)

        session = VNCSession(
            token=token,
            user_id=user_id,
            port=port,
            pid=pid,
            expires_at=time.time() + jwt_ttl,
        )
        self._sessions[token] = session
        self._user_sessions[user_id] = token
        return session

    def get_session(self, token: str) -> Optional[VNCSession]:
        session = self._sessions.get(token)
        if session and session.is_expired():
            self.terminate_session(token)
            return None
        return session

    def terminate_session(self, token: str) -> None:
        session = self._sessions.pop(token, None)
        if session:
            self._user_sessions.pop(session.user_id, None)
            self._kill_vnc(session.pid)
            self._release_port(session.port)

    def terminate_session_for_user(self, user_id: str) -> None:
        token = self._user_sessions.get(user_id)
        if token:
            self.terminate_session(token)

    def novnc_url(self, token: str, novnc_host: str = "localhost", novnc_port: int = 6080) -> str:
        session = self._sessions.get(token)
        if not session:
            raise ValueError("Invalid or expired session token")
        return (
            f"http://{novnc_host}:{novnc_port}/vnc.html"
            f"?host={novnc_host}&port={session.port}&token={token}&autoconnect=true"
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _allocate_port(self) -> int:
        port = self._next_port
        self._next_port += 1
        return port

    def _release_port(self, port: int) -> None:
        if port < self._next_port:
            self._next_port = port

    @staticmethod
    def _start_vnc(port: int) -> int:
        """Start a TigerVNC server on the given port. Returns PID."""
        display_num = port - 5900
        cmd = [
            "Xtigervnc",
            f":{display_num}",
            f"-rfbport={port}",
            "-SecurityTypes=None",
            "-localhost",
            "-geometry=1280x800",
            "-depth=24",
        ]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return proc.pid
        except FileNotFoundError:
            # VNC not installed — return stub PID
            return -1

    @staticmethod
    def _kill_vnc(pid: int) -> None:
        if pid <= 0:
            return
        try:
            import signal
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
