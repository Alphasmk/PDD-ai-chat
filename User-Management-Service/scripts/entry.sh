#!/bin/bash
set -e
python -m scripts.initialize_service

exec "$@"
