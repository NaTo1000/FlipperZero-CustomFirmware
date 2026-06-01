"""
SQLAgent — parameterized SQL generation, execution, and schema management.

All queries are parameterized — no raw string interpolation.
Supports: query generation, schema migration assistance, explain-plan analysis.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class QueryResult:
    sql: str
    params: dict[str, Any]
    rows: list[dict[str, Any]] = field(default_factory=list)
    rowcount: int = 0
    error: Optional[str] = None
    explain: Optional[str] = None


class SQLAgent:
    """
    Generates and validates SQL for the Dolfi.AI platform.

    Production usage: inject an async SQLAlchemy session via set_session().
    CI/stub mode: returns stub results.
    """

    def __init__(self, session=None) -> None:
        self._session = session

    def set_session(self, session) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Query builders
    # ------------------------------------------------------------------

    def select_devices(self, user_id: str) -> QueryResult:
        sql = """
            SELECT d.id, d.serial_hash, d.firmware_version, d.last_seen
            FROM devices d
            WHERE d.user_id = :user_id
            ORDER BY d.last_seen DESC
        """
        return QueryResult(sql=sql.strip(), params={"user_id": user_id})

    def upsert_device(
        self,
        user_id: str,
        serial_hash: str,
        firmware_version: str,
    ) -> QueryResult:
        sql = """
            INSERT INTO devices (user_id, serial_hash, firmware_version, last_seen)
            VALUES (:user_id, :serial_hash, :firmware_version, NOW())
            ON CONFLICT (serial_hash)
            DO UPDATE SET firmware_version = EXCLUDED.firmware_version,
                          last_seen = NOW()
            RETURNING id
        """
        return QueryResult(
            sql=sql.strip(),
            params={
                "user_id": user_id,
                "serial_hash": serial_hash,
                "firmware_version": firmware_version,
            },
        )

    def select_audit_range(self, start: str, end: str) -> QueryResult:
        sql = """
            SELECT id, timestamp, agent, action, payload_hash, prev_hash
            FROM conductorx_audit
            WHERE timestamp BETWEEN :start AND :end
            ORDER BY id ASC
        """
        return QueryResult(sql=sql.strip(), params={"start": start, "end": end})

    def select_rag_sessions(self, user_id: str, limit: int = 50) -> QueryResult:
        sql = """
            SELECT s.id, s.started_at, s.speed, s.domain, s.turn_count
            FROM rag_sessions s
            WHERE s.user_id = :user_id
            ORDER BY s.started_at DESC
            LIMIT :limit
        """
        return QueryResult(
            sql=sql.strip(), params={"user_id": user_id, "limit": limit}
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_no_injection(sql: str) -> bool:
        """
        Basic guard — ensure no raw string concatenation patterns.
        Real parameterization is enforced at the driver level.
        """
        dangerous = [
            r"'.*OR.*'.*=.*'",
            r";\s*DROP\s+TABLE",
            r";\s*DELETE\s+FROM",
            r"UNION\s+SELECT",
            r"--\s*$",
        ]
        for pattern in dangerous:
            if re.search(pattern, sql, re.IGNORECASE):
                return False
        return True

    # ------------------------------------------------------------------
    # Schema DDL
    # ------------------------------------------------------------------

    SCHEMA_DDL = """
-- Devices registry
CREATE TABLE IF NOT EXISTS devices (
    id               BIGSERIAL PRIMARY KEY,
    user_id          UUID NOT NULL,
    serial_hash      CHAR(64) UNIQUE NOT NULL,
    firmware_version VARCHAR(64),
    last_seen        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RAG sessions
CREATE TABLE IF NOT EXISTS rag_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    speed       SMALLINT NOT NULL DEFAULT 1,
    domain      VARCHAR(32),
    turn_count  INT NOT NULL DEFAULT 0
);

-- RAG turns (training data)
CREATE TABLE IF NOT EXISTS rag_turns (
    id          BIGSERIAL PRIMARY KEY,
    session_id  UUID NOT NULL REFERENCES rag_sessions(id),
    role        VARCHAR(16) NOT NULL,  -- 'user' | 'assistant'
    content     TEXT NOT NULL,
    feedback    SMALLINT,              -- 1=thumbs_up, -1=thumbs_down, NULL=none
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_devices_user ON devices(user_id);
CREATE INDEX IF NOT EXISTS idx_rag_sessions_user ON rag_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_rag_turns_session ON rag_turns(session_id);
"""
