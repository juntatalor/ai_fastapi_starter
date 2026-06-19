#!/bin/sh
set -e
echo "Running alembic migrations..."
uv run alembic upgrade head
echo "Installing pgqueuer schema..."
uv run python /app/scripts/pgqueuer_install.py
echo "Migrate job finished."
