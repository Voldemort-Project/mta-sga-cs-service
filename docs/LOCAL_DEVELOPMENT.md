# Local Development Guide

## 🚀 Quick Start

### 1. Setup Development Environment

```bash
make dev-setup
```

This will:
- Create `.env` file if it doesn't exist
- Install all dependencies using `uv`

### 2. Configure Database

Edit `.env` file and set your database URL:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cs_service
```

### 3. Run Database Migrations

```bash
make dev-migrate
```

### 4. Start Development Server

```bash
# Option 1: Run on port 8080 (recommended)
make dev-run

# Option 2: Run on port 8000
make dev-run-8000
```

Server will start with auto-reload enabled! 🔥

## 📋 Available Make Commands for Local Development

| Command | Description |
|---------|-------------|
| `make dev-setup` | Setup development environment (create .env + install deps) |
| `make dev-install` | Install/update dependencies with uv |
| `make dev-run` | Run server on port 8080 with auto-reload |
| `make dev-run-8000` | Run server on port 8000 with auto-reload |
| `make dev-migrate` | Run database migrations |
| `make dev-migrate-rollback` | Rollback last migration |
| `make dev-migrate-status` | Check current migration status |
| `make test-local` | Run tests locally |

## 🔧 Manual Commands (Without Make)

### Install Dependencies
```bash
uv sync
```

### Run Server
```bash
# Port 8080
uv run uvicorn app.main:app --reload --port 8080

# Port 8000
uv run uvicorn app.main:app --reload --port 8000
```

### Run Migrations
```bash
# Apply migrations
uv run alembic upgrade head

# Check status
uv run alembic current

# Rollback
uv run alembic downgrade -1
```

### Run Tests
```bash
uv run pytest
```

## 📦 Dependencies

All dependencies are managed in `pyproject.toml`:

```toml
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy>=2.0.25",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.26.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "email-validator>=2.1.0",  # Required for EmailStr validation
    "greenlet>=3.0.0",
    "psycopg2-binary>=2.9.9",
]
```

## 🌐 Access Points

Once the server is running:

- **API**: `http://localhost:8080` or `http://localhost:8000`
- **Interactive Docs (Swagger)**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`
- **OpenAPI JSON**: `http://localhost:8080/openapi.json`

## 🐛 Troubleshooting

### Error: `ModuleNotFoundError: No module named 'pydantic_settings'`

**Solution**: Install dependencies first
```bash
make dev-install
# or
uv sync
```

### Error: `ImportError: email-validator is not installed`

**Solution**: Already fixed in `pyproject.toml`. Just run:
```bash
make dev-install
# or
uv sync
```

### Error: `Address already in use`

**Solution**: Port is being used. Either:
1. Stop the other process using the port
2. Use different port:
```bash
uv run uvicorn app.main:app --reload --port 8081
```

### Error: Database connection failed

**Solution**: Check your `.env` file and ensure:
1. Database is running
2. DATABASE_URL is correct
3. Database exists

## 🔄 Development Workflow

### 1. Start New Feature
```bash
# Pull latest changes
git pull

# Install/update dependencies
make dev-install

# Apply any new migrations
make dev-migrate

# Start development server
make dev-run
```

### 2. Make Changes

- Edit code in `app/` directory
- Server auto-reloads on file changes
- Test in browser at `http://localhost:8080/docs`

### 3. Add New Database Changes

```bash
# Create migration
uv run alembic revision --autogenerate -m "description"

# Apply migration
make dev-migrate
```

### 4. Run Tests
```bash
make test-local
```

### 5. Commit Changes
```bash
git add .
git commit -m "Your message"
git push
```

## 📝 Environment Variables

Required environment variables in `.env`:

```bash
# Application
APP_NAME=sga-cs-service
APP_VERSION=0.1.0
ENV=development
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Database Pool Settings
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_ECHO=false
```

## 🎯 Testing Guest Registration

### Using curl:
```bash
curl -X POST http://localhost:8080/api/v1/guests/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "room_number": "101",
    "checkin_date": "2024-01-15",
    "email": "john@example.com",
    "phone_number": "+6281234567890"
  }'
```

### Using Interactive Docs:
1. Go to `http://localhost:8080/docs`
2. Find "Guests" section
3. Click "POST /api/v1/guests/register"
4. Click "Try it out"
5. Fill in the request body
6. Click "Execute"

## 🐳 Switch to Docker

If you prefer using Docker instead:

```bash
# Build and run with Docker
make build
make run

# Or use docker-compose
make up
```

See `docs/DOCKER.md` for more Docker commands.

## 📚 Related Documentation

- [Guest Registration API](./GUEST_REGISTRATION.md) - Full API documentation
- [Docker Guide](./DOCKER.md) - Docker setup and commands
- [Webhook Integration](./WEBHOOK_WAHA.md) - WhatsApp webhook setup
