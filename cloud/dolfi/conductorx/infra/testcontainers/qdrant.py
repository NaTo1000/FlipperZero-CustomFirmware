"""Testcontainers helper — Qdrant vector store."""
from __future__ import annotations

from typing import Tuple

from testcontainers.core.container import DockerContainer

from ..containers import ServiceConfig

QDRANT_IMAGE = "qdrant/qdrant:v1.9.2"


def start_qdrant() -> Tuple[DockerContainer, ServiceConfig]:
    container = (
        DockerContainer(QDRANT_IMAGE)
        .with_exposed_ports(6333)
    )
    container.start()
    host = container.get_container_host_ip()
    port = int(container.get_exposed_port(6333))
    cfg = ServiceConfig(host=host, port=port)
    return container, cfg
