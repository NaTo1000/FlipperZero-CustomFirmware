"""Testcontainers helper — Redis."""
from __future__ import annotations

from typing import Tuple

from testcontainers.redis import RedisContainer

from ..containers import ServiceConfig


def start_redis(image: str = "redis:7-alpine") -> Tuple[RedisContainer, ServiceConfig]:
    container = RedisContainer(image=image)
    container.start()
    host = container.get_container_host_ip()
    port = int(container.get_exposed_port(6379))
    cfg = ServiceConfig(host=host, port=port)
    return container, cfg
