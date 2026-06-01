"""Testcontainers helper — PostgreSQL."""
from __future__ import annotations

from typing import Tuple

from testcontainers.postgres import PostgresContainer

from ..containers import ServiceConfig


def start_postgres(
    db: str = "dolfi",
    user: str = "dolfi",
    password: str = "dolfi_test",
    image: str = "postgres:16-alpine",
) -> Tuple[PostgresContainer, ServiceConfig]:
    container = PostgresContainer(
        image=image,
        dbname=db,
        username=user,
        ******
    )
    container.start()
    host = container.get_container_host_ip()
    port = int(container.get_exposed_port(5432))
    cfg = ServiceConfig(host=host, port=port, user=user, ****** db=db)
    return container, cfg
