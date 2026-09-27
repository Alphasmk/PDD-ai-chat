"""Serialize migrations and initial-only creation before starting HTTP."""

import asyncio
import os
import sys
from source.application.use_cases.bootstrap_use_case import InitializationError
from source.infrastructure.database.bootstrap import initialize_service
from source.settings.separated_configs.bootstrap_config import load_bootstrap_data
from source.settings.separated_configs.database_config import DatabaseConfig


async def main() -> int:
    try:
        schema = os.environ.get("UMS_INITIALIZE_SCHEMA")
        url = os.environ.get("UMS_INITIALIZE_DATABASE_URL") or str(
            DatabaseConfig().postgres_url
        )
        timeout = (
            float(os.environ.get("UMS_INITIALIZE_LOCK_TIMEOUT", "60"))
            if schema
            else 60.0
        )
        created = await initialize_service(url, load_bootstrap_data, schema, timeout)
    except InitializationError as error:
        print(str(error), file=sys.stderr)
        return 1
    except Exception:
        # External exceptions may contain connection details or credentials.
        print("database_unavailable", file=sys.stderr)
        return 1
    print(
        "superadmin_created"
        if created
        else "superadmin_exists: initial settings are not applied"
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
