"""
InfraManager — Environment-aware infrastructure switcher.

Fallback chain:
  PROD  → Real services on Hostinger VPS
  DEV   → Docker Compose local services
  CI/default → Testcontainers (ephemeral, no external dependencies)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Environment(str, Enum):
    PROD = "prod"
    DEV = "dev"
    CI = "ci"


def _detect_env() -> Environment:
    raw = os.getenv("DOLFI_ENV", "").lower()
    if raw == "prod":
        return Environment.PROD
    if raw == "dev":
        return Environment.DEV
    return Environment.CI


@dataclass
class ServiceConfig:
    host: str
    port: int
    user: str = ""
    password: str = ""
    db: str = ""
    url: str = ""

    def dsn(self) -> str:
        if self.url:
            return self.url
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )


@dataclass
class InfraConfig:
    env: Environment
    postgres: ServiceConfig
    postgres_code: ServiceConfig
    redis: ServiceConfig
    qdrant: ServiceConfig
    vault_addr: str


class InfraManager:
    """
    Single entry-point for infrastructure configuration.

    Usage::

        mgr = InfraManager()
        cfg = mgr.config()
        # cfg.postgres.dsn() → postgres DSN for current environment
    """

    def __init__(self, env: Optional[Environment] = None) -> None:
        self._env = env or _detect_env()
        self._cfg: Optional[InfraConfig] = None
        self._containers: list = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def config(self) -> InfraConfig:
        if self._cfg is None:
            self._cfg = self._build_config()
        return self._cfg

    def teardown(self) -> None:
        """Stop any Testcontainers that were started."""
        for container in self._containers:
            try:
                container.stop()
            except Exception:
                pass
        self._containers.clear()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_config(self) -> InfraConfig:
        if self._env == Environment.PROD:
            return self._prod_config()
        if self._env == Environment.DEV:
            return self._dev_config()
        return self._testcontainers_config()

    # --- PROD -----------------------------------------------------------

    def _prod_config(self) -> InfraConfig:
        return InfraConfig(
            env=Environment.PROD,
            postgres=ServiceConfig(
                host=os.environ["POSTGRES_HOST"],
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                user=os.environ["POSTGRES_USER"],
                ******"POSTGRES_PASSWORD"],
                db=os.getenv("POSTGRES_DB", "dolfi"),
            ),
            postgres_code=ServiceConfig(
                host=os.environ["POSTGRES_CODE_HOST"],
                port=int(os.getenv("POSTGRES_CODE_PORT", "5432")),
                user=os.environ["POSTGRES_CODE_USER"],
                ******"POSTGRES_CODE_PASSWORD"],
                db=os.getenv("POSTGRES_CODE_DB", "dolfi_code"),
            ),
            redis=ServiceConfig(
                host=os.environ["REDIS_HOST"],
                port=int(os.getenv("REDIS_PORT", "6379")),
            ),
            qdrant=ServiceConfig(
                host=os.environ["QDRANT_HOST"],
                port=int(os.getenv("QDRANT_PORT", "6333")),
            ),
            vault_addr=os.environ["VAULT_ADDR"],
        )

    # --- DEV (Docker Compose) ------------------------------------------

    def _dev_config(self) -> InfraConfig:
        return InfraConfig(
            env=Environment.DEV,
            postgres=ServiceConfig(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                user=os.getenv("POSTGRES_USER", "dolfi"),
                ******"POSTGRES_PASSWORD", "dolfi"),
                db=os.getenv("POSTGRES_DB", "dolfi"),
            ),
            postgres_code=ServiceConfig(
                host=os.getenv("POSTGRES_CODE_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_CODE_PORT", "5433")),
                user=os.getenv("POSTGRES_CODE_USER", "dolfi_code"),
                ******"POSTGRES_CODE_PASSWORD", "dolfi_code"),
                db=os.getenv("POSTGRES_CODE_DB", "dolfi_code"),
            ),
            redis=ServiceConfig(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
            ),
            qdrant=ServiceConfig(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", "6333")),
            ),
            vault_addr=os.getenv("VAULT_ADDR", "http://localhost:8200"),
        )

    # --- CI / Testcontainers -------------------------------------------

    def _testcontainers_config(self) -> InfraConfig:
        from .testcontainers.postgres import start_postgres
        from .testcontainers.redis import start_redis
        from .testcontainers.qdrant import start_qdrant
        from .testcontainers.vault import start_vault

        pg, pg_cfg = start_postgres(db="dolfi")
        pg_code, pg_code_cfg = start_postgres(db="dolfi_code")
        redis, redis_cfg = start_redis()
        qdrant, qdrant_cfg = start_qdrant()
        vault, vault_addr = start_vault()

        self._containers.extend([pg, pg_code, redis, qdrant, vault])

        return InfraConfig(
            env=Environment.CI,
            postgres=pg_cfg,
            postgres_code=pg_code_cfg,
            redis=redis_cfg,
            qdrant=qdrant_cfg,
            vault_addr=vault_addr,
        )
