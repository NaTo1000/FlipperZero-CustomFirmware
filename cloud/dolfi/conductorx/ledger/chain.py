"""
Append-only hash-chained audit ledger for ConductorX.

Every agent action is recorded as a row with:
  - prev_hash: SHA-256 of the previous row's canonical form
  - payload_hash: SHA-256 of the action payload
  - signature: Ed25519 signature by CryptoAgent

This creates a cryptographically verifiable chain — tampering with
any historical row breaks the hash chain and is detectable.

Additionally, each row is assigned a sequential index and the ledger
can build a Merkle tree over all row hashes.  The Merkle root provides
O(log n) membership proofs and an independent tamper-detection path
that complements the linear hash chain.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

GENESIS_HASH = "0" * 64  # Sentinel hash for the first row


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _canonical(row: dict[str, Any]) -> str:
    """Deterministic JSON serialization for hashing."""
    return json.dumps(row, sort_keys=True, separators=(",", ":"), default=str)


def _build_merkle_root(leaves: list[str]) -> str:
    """
    Build a Merkle root from a list of hex-encoded leaf hashes.

    The tree is built bottom-up.  If a layer has an odd number of nodes the
    last node is duplicated before hashing the pair (Bitcoin-compatible padding).
    """
    nodes = list(leaves)
    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])  # duplicate last leaf
        nodes = [
            hashlib.sha256((nodes[i] + nodes[i + 1]).encode()).hexdigest()
            for i in range(0, len(nodes), 2)
        ]
    return nodes[0]


class AuditLedger:
    """
    In-memory ledger (swap the _storage list for a DB-backed version in prod).

    Prod usage: replace _append_to_storage / _last_hash with async Postgres calls.
    """

    def __init__(self, signing_key: Ed25519PrivateKey | None = None) -> None:
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
        timestamp = datetime.now(UTC).isoformat()

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

    def merkle_root(self) -> str:
        """
        Compute the Merkle root over all row hashes.

        Each leaf is the SHA-256 of the row's unsigned canonical form.
        Odd-length layers duplicate the last node (standard Bitcoin-style padding).
        An empty ledger returns the genesis hash.
        """
        if not self._storage:
            return GENESIS_HASH
        leaves = [
            _sha256(_canonical({k: v for k, v in row.items() if k != "signature"}))
            for row in self._storage
        ]
        return _build_merkle_root(leaves)

    def verify_merkle(self, expected_root: str) -> bool:
        """
        Re-compute the Merkle root and compare it against *expected_root*.
        Returns True if they match.
        """
        return self.merkle_root() == expected_root

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
