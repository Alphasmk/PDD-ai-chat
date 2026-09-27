"""Run startup in independent processes against an explicitly isolated schema."""

import os
from pathlib import Path
import subprocess
import sys


def start_runner(
    database_url: str,
    schema: str,
    initial: dict[str, str],
    module: str = "scripts.initialize_service",
) -> subprocess.Popen[str]:
    if not schema.startswith("ums_test_") or not schema.replace("_", "").isalnum():
        raise ValueError("Startup harness requires a generated ums_test_ schema")
    environment = os.environ.copy()
    environment.update(initial)
    environment["UMS_INITIALIZE_DATABASE_URL"] = database_url
    environment["UMS_INITIALIZE_SCHEMA"] = schema
    return subprocess.Popen(
        [sys.executable, "-m", module],
        cwd=Path(__file__).resolve().parents[2],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
