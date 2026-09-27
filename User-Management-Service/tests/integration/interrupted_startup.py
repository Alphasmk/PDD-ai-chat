"""Crash a separate test process after INSERT but before bootstrap commit."""

import asyncio
from collections.abc import Callable
import os
from source.application.use_cases.bootstrap_use_case import (
    BootstrapData,
    BootstrapSuperadmin,
)
from unittest.mock import patch
from scripts.initialize_service import main


class InterruptedBootstrap(BootstrapSuperadmin):
    async def execute(self, initial: Callable[[], BootstrapData]) -> bool:
        await super().execute(initial)
        print("before_bootstrap_commit", flush=True)
        os._exit(17)


if __name__ == "__main__":
    with patch(
        "source.infrastructure.database.bootstrap.BootstrapSuperadmin",
        InterruptedBootstrap,
    ):
        asyncio.run(main())
