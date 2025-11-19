# SGA CS Service

Customer Service Backend API built with FastAPI, SQLAlchemy 2.0, and PostgreSQL.

## Tech Stack

-   **Python 3.11+**
-   **FastAPI** - Modern async web framework
-   **SQLAlchemy 2.0** - Async ORM
-   **Neon PostgreSQL** - Serverless PostgreSQL database
-   **uv** - Fast Python package manager
-   **Alembic** - Database migrations
-   **Pydantic v2** - Data validation

## Project Structure

```
app/
  core/
    config.py       # Application configuration
    database.py     # Database setup and session management
  models/           # SQLAlchemy models
  schemas/          # Pydantic schemas
  repositories/     # Data access layer
  services/         # Business logic layer
  api/
    v1/             # API v1 endpoints
    router.py       # Main API router
  integrations/     # External integrations (H2H)
  main.py           # FastAPI application
alembic/            # Database migrations
tests/              # Test files
```

## 🐳 Quick Start with Docker (Recommended for Production)

The fastest way to get started:

```bash
# 1. Create .env file with your database URL
echo "DATABASE_URL=postgresql+asyncpg://user:pass@host/db" > .env

# 2. Build and run with Docker Compose
docker-compose up -d

# 3. View logs
docker-compose logs -f
```

Or using Makefile:

```bash
make build    # Build Docker image
make run      # Run container
make logs     # View logs
```

📖 **Full Docker documentation**: See [docs/DOCKER.md](docs/DOCKER.md) for comprehensive Docker deployment guide.

---

## Setup (Local Development)

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Create virtual environment and install dependencies

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### 3. Setup Neon Database

1. Create a Neon project at [neon.tech](https://neon.tech)
2. Copy your connection string (use the **pooled** connection string for production)

### 4. Configure environment variables

Create `.env` file:

```bash
cat > .env << 'EOF'
# Application
APP_NAME=sga-cs-service
APP_VERSION=0.1.0
ENV=development
DEBUG=True

# Server
HOST=0.0.0.0
PORT=8000

# Database - Neon PostgreSQL
# Format: postgresql+asyncpg://user:password@host/database?sslmode=require
DATABASE_URL=postgresql+asyncpg://[user]:[password]@[neon-host]/[database]?sslmode=require

# Database Pool Settings (optimized for Neon)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_ECHO=False
EOF
```

**Note**: Replace `[user]`, `[password]`, `[neon-host]`, and `[database]` with your actual Neon credentials.

### 5. Run the application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or using the settings from .env:

```bash
python -m uvicorn app.main:app --reload
```

## API Documentation

Once the server is running, visit:

-   **Swagger UI**: http://localhost:8000/docs
-   **ReDoc**: http://localhost:8000/redoc
-   **OpenAPI JSON**: http://localhost:8000/openapi.json

## Available Endpoints

### Health Check

```
GET /api/v1/health
```

Response:

```json
{
	"status": "healthy",
	"service": "sga-cs-service",
	"version": "0.1.0"
}
```

## Development

### Install development dependencies

```bash
uv pip install -e ".[dev]"
```

### Run tests

```bash
pytest
```

### Database Migrations with Neon

Create `.alembic.ini` if not exists:

```bash
alembic init alembic
```

Update `alembic/env.py` to use async engine and your DATABASE_URL from .env

Create migration:

```bash
alembic revision --autogenerate -m "Initial migration"
```

Apply migrations to Neon:

```bash
alembic upgrade head
```

**Neon Tips**:

-   Use the **pooled connection** for application runtime
-   Use the **direct connection** for migrations and admin tasks
-   Neon automatically scales to zero when idle
-   Connection pooling is handled by Neon's proxy

## Environment Variables

| Variable          | Description                       | Default                            |
| ----------------- | --------------------------------- | ---------------------------------- |
| `APP_NAME`        | Application name                  | `sga-cs-service`                   |
| `APP_VERSION`     | Application version               | `0.1.0`                            |
| `ENV`             | Environment                       | `development`                      |
| `DEBUG`           | Debug mode                        | `True`                             |
| `HOST`            | Server host                       | `0.0.0.0`                          |
| `PORT`            | Server port                       | `8000`                             |
| `DATABASE_URL`    | Neon PostgreSQL connection string | Required - get from Neon dashboard |
| `DB_POOL_SIZE`    | Database connection pool size     | `5`                                |
| `DB_MAX_OVERFLOW` | Max overflow connections          | `10`                               |
| `DB_POOL_TIMEOUT` | Connection timeout (seconds)      | `30`                               |
| `DB_POOL_RECYCLE` | Connection recycle time (seconds) | `3600`                             |
| `DB_ECHO`         | Echo SQL queries (debug)          | `False`                            |

## ✨ Features

### Application Features
-   ✅ FastAPI dengan async/await
-   ✅ Pydantic v2 untuk validation
-   ✅ SQLAlchemy 2.0 async dengan Neon PostgreSQL
-   ✅ Connection pooling optimized untuk Neon
-   ✅ SSL/TLS support untuk database
-   ✅ Repository & Service pattern
-   ✅ Error handling structure
-   ✅ CORS middleware
-   ✅ OpenAPI documentation
-   ✅ Graceful shutdown dengan connection cleanup
-   ✅ Modular dan scalable

### Docker & Deployment Features
-   ✅ Production-ready Dockerfile dengan multi-stage build
-   ✅ Automatic database migrations pada startup
-   ✅ Health checks dan monitoring
-   ✅ Non-root user untuk security
-   ✅ Optimized image size
-   ✅ Docker Compose untuk easy deployment
-   ✅ Makefile untuk command shortcuts

## 🗄️ Neon Database Features

-   **Serverless** - Auto-scales to zero when idle
-   **Branching** - Create database branches for development
-   **Point-in-time recovery** - Restore to any point in time
-   **Connection pooling** - Built-in PgBouncer
-   **Global availability** - Deploy in multiple regions

## License

Proprietary - MTA
