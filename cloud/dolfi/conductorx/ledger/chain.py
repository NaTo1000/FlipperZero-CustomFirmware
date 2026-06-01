"""
Append-only hash-chained audit ledger for ConductorX.

Every agent action is recorded as a row with:
  - prev_hash: SHA-256 of the previous row's canonical form
  - payload_hash: SHA-256 of the action payload
  - signature: Ed25519 signature by CryptoAgent

This creates a cryptographically verifiable chain — tampering with
any historical row breaks the hash chain and is detectable.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    PrivateFormat,
    NoEncryption,
)

GENESIS_HASH = "0" * 64  # Sentinel hash for the first row


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _canonical(row: dict[str, Any]) -> str:
    """Deterministic JSON serialization for hashing."""
    return json.dumps(row, sort_keys=True, separators=(",", ":"), default=str)


class AuditLedger:
    """
    In-memory ledger (swap the _storage list for a DB-backed version in prod).

    Prod usage: replace _append_to_storage / _last_hash with async Postgres calls.
    """

    def __init__(self, signing_key: Optional[Ed25519PrivateKey] = None) -> None:
        self._signing_key = signing_key or Ed25519PrivateKey.generate()
        self._storage: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append(
        self,
        agent: str,
        action: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Append an action to the ledger and return the full row.
        """
        prev_hash = self._last_hash()
        payload_hash = _sha256(_canonical(payload))
        timestamp = datetime.now(timezone.utc).isoformat()

        unsigned_row = {
            "prev_hash": prev_hash,
            "timestamp": timestamp,
            "agent": agent,
            "action": action,
            "payload_hash": payload_hash,
        }
        signature = self._sign(_canonical(unsigned_row))

        row = {**unsigned_row, "signature": signature}
        self._storage.append(row)
        return row

    def verify_chain(self) -> bool:
        """
        Walk the entire chain and verify hash integrity.
        Returns True if the chain is intact.
        """
        if not self._storage:
            return True
        expected_prev = GENESIS_HASH
        for row in self._storage:
            if row["prev_hash"] != expected_prev:
                return False
            # Recompute payload hash is not stored inline for simplicity;
            # full verification would re-fetch payloads from the payload store.
            unsigned = {k: v for k, v in row.items() if k != "signature"}
            expected_prev = _sha256(_canonical(unsigned))
        return True

    def to_list(self) -> list[dict[str, Any]]:
        return list(self._storage)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _last_hash(self) -> str:
        if not self._storage:
            return GENESIS_HASH
        last = self._storage[-1]
        unsigned = {k: v for k, v in last.items() if k != "signature"}
        return _sha256(_canonical(unsigned))

    def _sign(self, data: str) -> str:
        sig_bytes = self._signing_key.sign(data.encode())
        return sig_bytes.hex()


# ---------------------------------------------------------------------------
# SQLAlchemy schema for production PostgreSQL storage
# ---------------------------------------------------------------------------
LEDGER_DDL = """
CREATE TABLE IF NOT EXISTS conductorx_audit (
    id           BIGSERIAL PRIMARY KEY,
    prev_hash    CHAR(64)      NOT NULL,
    timestamp    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    agent        VARCHAR(64)   NOT NULL,
    action       VARCHAR(256)  NOT NULL,
    payload_hash CHAR(64)      NOT NULL,
    signature    TEXT          NOT NULL
);

-- Prevent any UPDATE or DELETE on audit rows (requires superuser to bypass)
CREATE RULE no_update_audit AS ON UPDATE TO conductorx_audit DO INSTEAD NOTHING;
CREATE RULE no_delete_audit AS ON DELETE TO conductorx_audit DO INSTEAD NOTHING;
"""
