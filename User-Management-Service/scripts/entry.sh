#!/bin/bash
set -e
echo "Running migration script ->"

alembic upgrade head

echo "<- Migration completed"

echo "Initializing superuser ->"

python scripts/create_superuser.py

echo "<- Superuser initialized"

exec "$@"
