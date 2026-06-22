#!/bin/sh
set -e
echo "Running alembic migrations..."
uv run alembic upgrade head
echo "Installing pgqueuer schema..."
uv run pgq install --dsn "$PGQUEUER_DSN" || true
echo "Migrate job finished."
