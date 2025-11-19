#!/bin/bash
# Rollback last migration

set -e

cd "$(dirname "$0")/.."

echo "Rolling back last migration..."
uv run alembic downgrade -1

echo "✓ Rollback completed successfully"
