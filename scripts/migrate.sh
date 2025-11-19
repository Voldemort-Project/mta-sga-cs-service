#!/bin/bash
# Run database migrations

set -e

cd "$(dirname "$0")/.."

echo "Running database migrations..."
uv run alembic upgrade head

echo "✓ Migrations completed successfully"
