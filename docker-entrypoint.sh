#!/bin/bash
# Docker entrypoint script for SGA CS Service
# Runs database migrations before starting the application

set -e

echo "================================================"
echo "🚀 SGA CS Service - Starting..."
echo "================================================"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if database is ready
wait_for_db() {
    echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"

    max_attempts=30
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if alembic current &> /dev/null; then
            echo -e "${GREEN}✓ Database is ready!${NC}"
            return 0
        fi

        attempt=$((attempt + 1))
        echo "   Attempt $attempt/$max_attempts - Waiting for database..."
        sleep 2
    done

    echo -e "${RED}✗ Database is not ready after $max_attempts attempts${NC}"
    return 1
}

# Function to run migrations
run_migrations() {
    echo ""
    echo -e "${YELLOW}🔄 Running database migrations...${NC}"

    if alembic upgrade head; then
        echo -e "${GREEN}✓ Migrations completed successfully!${NC}"
        return 0
    else
        echo -e "${RED}✗ Migration failed!${NC}"
        return 1
    fi
}

# Function to show current migration status
show_migration_status() {
    echo ""
    echo -e "${YELLOW}📊 Current migration status:${NC}"
    alembic current || echo "No migrations applied yet"
    echo ""
}

# Main execution flow
main() {
    # Wait for database to be ready
    if ! wait_for_db; then
        echo -e "${RED}Exiting due to database connection failure${NC}"
        exit 1
    fi

    # Show current migration status
    show_migration_status

    # Run migrations
    if ! run_migrations; then
        echo -e "${RED}Exiting due to migration failure${NC}"
        exit 1
    fi

    # Show final status
    show_migration_status

    echo "================================================"
    echo -e "${GREEN}✓ Initialization complete!${NC}"
    echo -e "${GREEN}🎯 Starting application...${NC}"
    echo "================================================"
    echo ""

    # Execute the main command (uvicorn server)
    exec "$@"
}

# Run main function with all script arguments
main "$@"
