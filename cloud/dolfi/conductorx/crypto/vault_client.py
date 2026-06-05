"""
Vault client — wraps HashiCorp Vault (hvac) for secrets management.

All secrets are fetched at runtime. Nothing is stored in application DB.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import hvac


@lru_cache(maxsize=1)
def _vault_client() -> hvac.Client:
    addr = os.environ.get("VAULT_ADDR", "http://localhost:8200")
    token = os.environ.get("VAULT_TOKEN", "")
    client = hvac.Client(url=addr, token=token)
    if not client.is_authenticated():
        raise RuntimeError(
            f"Vault authentication failed. Check VAULT_ADDR={addr} and VAULT_TOKEN."
        )
    return client


class VaultClient:
    """
    Thin wrapper around hvac for KV v2 secrets.

    All paths use the mount point 'secret/' by default.
    """

    def __init__(self, mount: str = "secret") -> None:
        self._mount = mount

    def get(self, path: str, key: str) -> str:
        """Fetch a single secret key from a KV v2 path."""
        client = _vault_client()
        response = client.secrets.kv.v2.read_secret_version(
            path=path, mount_point=self._mount
        )
        data: dict[str, Any] = response["data"]["data"]
        if key not in data:
            raise KeyError(f"Secret key '{key}' not found at path '{path}'")
        return str(data[key])

    def put(self, path: str, secrets: dict[str, str]) -> None:
        """Write secrets to a KV v2 path."""
        client = _vault_client()
        client.secrets.kv.v2.create_or_update_secret(
            path=path, secret=secrets, mount_point=self._mount
        )

    def delete(self, path: str) -> None:
        """Soft-delete all versions at a KV v2 path."""
        client = _vault_client()
        client.secrets.kv.v2.delete_metadata_and_all_versions(
            path=path, mount_point=self._mount
        )

    def rotate(self, path: str, key: str, new_value: str) -> None:
        """Rotate a single secret key by reading existing, updating, and writing back."""
        client = _vault_client()
        try:
            response = client.secrets.kv.v2.read_secret_version(
                path=path, mount_point=self._mount
            )
            existing: dict[str, str] = dict(response["data"]["data"])
        except Exception:
            existing = {}
        existing[key] = new_value
        self.put(path, existing)


# ---------------------------------------------------------------------------
# Known secret paths (constants — paths only, never values)
# ---------------------------------------------------------------------------
class SecretPaths:
    XAI_API = "dolfi/xai"                # key: api_key
    POSTGRES_CREDS = "dolfi/postgres"    # keys: user, password
    REDIS_CREDS = "dolfi/redis"          # key: password
    GPG_PASSPHRASE = "dolfi/gpg"         # key: passphrase
    JWT_SECRET = "dolfi/jwt"             # key: secret
    APPLE_CREDS = "dolfi/apple"          # keys: issuer_id, key_id, private_key
    GOOGLE_CREDS = "dolfi/google"        # key: service_account_json
