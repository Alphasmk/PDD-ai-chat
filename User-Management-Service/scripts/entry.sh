#!/bin/bash
set -e
echo "Running migration script ->"

alembic upgrade head

echo "<- Migration completed"

exec "$@"
