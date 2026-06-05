"""Testcontainers helper — HashiCorp Vault (dev mode)."""
from __future__ import annotations

from typing import Tuple

from testcontainers.core.container import DockerContainer

VAULT_IMAGE = "hashicorp/vault:1.16"
VAULT_DEV_ROOT_TOKEN = "dolfi-dev-root-token"


def start_vault() -> Tuple[DockerContainer, str]:
    container = (
        DockerContainer(VAULT_IMAGE)
        .with_exposed_ports(8200)
        .with_env("VAULT_DEV_ROOT_TOKEN_ID", VAULT_DEV_ROOT_TOKEN)
        .with_env("VAULT_DEV_LISTEN_ADDRESS", "0.0.0.0:8200")
        .with_command("server -dev")
    )
    container.start()
    host = container.get_container_host_ip()
    port = int(container.get_exposed_port(8200))
    vault_addr = f"http://{host}:{port}"
    return container, vault_addr
