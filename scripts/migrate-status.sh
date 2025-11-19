#!/bin/bash
# Show current migration status

cd "$(dirname "$0")/.."

echo "Current migration status:"
uv run alembic current

echo ""
echo "Migration history:"
uv run alembic history
