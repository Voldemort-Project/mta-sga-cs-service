# Docker Deployment Guide

Dokumentasi lengkap untuk deployment menggunakan Docker.

## 📋 Daftar Isi

- [Fitur Dockerfile](#fitur-dockerfile)
- [Quick Start](#quick-start)
- [Build Image](#build-image)
- [Run Container](#run-container)
- [Docker Compose](#docker-compose)
- [Environment Variables](#environment-variables)
- [Migration Management](#migration-management)
- [Troubleshooting](#troubleshooting)

## 🚀 Fitur Dockerfile

Dockerfile yang telah dibuat mengimplementasikan best practices untuk production:

### ✨ Optimasi
- **Multi-stage build**: Memisahkan builder dan runtime untuk image size lebih kecil
- **Layer caching**: Optimasi caching untuk build yang lebih cepat
- **uv package manager**: Instalasi dependencies 10-100x lebih cepat dari pip
- **Bytecode compilation**: Pre-compile Python untuk performa lebih baik

### 🔒 Security
- **Non-root user**: Aplikasi berjalan sebagai user non-root
- **Minimal base image**: Menggunakan python:3.11-slim
- **Readonly filesystem**: Dapat dikonfigurasi dengan read-only root filesystem

### 🏥 Health & Monitoring
- **Health check**: Built-in health check endpoint
- **Proper logging**: Structured logging dengan stdout/stderr
- **Graceful shutdown**: Handle SIGTERM dengan baik

### 🔄 Database Migrations
- **Auto-migration**: Otomatis run migrations saat container start
- **Database wait**: Wait for database ready sebelum migration
- **Migration status**: Tampilkan status migration sebelum dan sesudah
- **Error handling**: Proper error handling untuk migration failures

## 🏃 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+ (optional)
- Database PostgreSQL (Neon atau local)

### 1. Setup Environment Variables

Buat file `.env` di root directory:

```bash
# Application
APP_NAME=sga-cs-service
ENV=production
DEBUG=false

# Database (ganti dengan database URL Anda)
DATABASE_URL=postgresql+asyncpg://user:password@host/database
```

### 2. Build & Run

```bash
# Build image
docker build -t sga-cs-service:latest .

# Run container
docker run -d \
  --name sga-cs-service \
  --env-file .env \
  -p 8000:8000 \
  sga-cs-service:latest
```

### 3. Check Status

```bash
# Check logs
docker logs -f sga-cs-service

# Check health
curl http://localhost:8000/api/v1/health
```

## 🔨 Build Image

### Basic Build

```bash
docker build -t sga-cs-service:latest .
```

### Build dengan Tag Spesifik

```bash
# Development
docker build -t sga-cs-service:dev .

# Production dengan version
docker build -t sga-cs-service:1.0.0 .
docker build -t sga-cs-service:latest .
```

### Build dengan BuildKit (Recommended)

```bash
# Enable BuildKit untuk caching yang lebih baik
DOCKER_BUILDKIT=1 docker build -t sga-cs-service:latest .
```

### Build Tanpa Cache

```bash
docker build --no-cache -t sga-cs-service:latest .
```

## 🏃‍♂️ Run Container

### Basic Run

```bash
docker run -d \
  --name sga-cs-service \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host/db" \
  sga-cs-service:latest
```

### Run dengan Environment File

```bash
docker run -d \
  --name sga-cs-service \
  --env-file .env \
  -p 8000:8000 \
  sga-cs-service:latest
```

### Run dengan Custom Port

```bash
docker run -d \
  --name sga-cs-service \
  -p 3000:8000 \
  -e PORT=8000 \
  -e DATABASE_URL="your-db-url" \
  sga-cs-service:latest
```

### Run dengan Resource Limits

```bash
docker run -d \
  --name sga-cs-service \
  --memory="512m" \
  --cpus="0.5" \
  -p 8000:8000 \
  -e DATABASE_URL="your-db-url" \
  sga-cs-service:latest
```

### Run dengan Restart Policy

```bash
docker run -d \
  --name sga-cs-service \
  --restart unless-stopped \
  -p 8000:8000 \
  -e DATABASE_URL="your-db-url" \
  sga-cs-service:latest
```

## 🐳 Docker Compose

### Basic Usage

1. **Edit docker-compose.yml**: Sesuaikan environment variables
2. **Start services**:
   ```bash
   docker-compose up -d
   ```
3. **View logs**:
   ```bash
   docker-compose logs -f
   ```
4. **Stop services**:
   ```bash
   docker-compose down
   ```

### Development dengan Local Database

Uncomment bagian PostgreSQL di `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=cs_user
      - POSTGRES_PASSWORD=cs_password
      - POSTGRES_DB=cs_service
    ports:
      - "5432:5432"
```

Lalu update DATABASE_URL:
```bash
DATABASE_URL=postgresql+asyncpg://cs_user:cs_password@postgres:5432/cs_service
```

Run dengan:
```bash
docker-compose up -d
```

### Useful Docker Compose Commands

```bash
# Start services
docker-compose up -d

# Start with rebuild
docker-compose up -d --build

# View logs
docker-compose logs -f app

# Restart specific service
docker-compose restart app

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove with volumes
docker-compose down -v

# Scale services (if needed)
docker-compose up -d --scale app=3
```

## 🌍 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host/db` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | `sga-cs-service` |
| `APP_VERSION` | Application version | `0.1.0` |
| `ENV` | Environment (dev/staging/production) | `production` |
| `DEBUG` | Debug mode | `false` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DB_POOL_SIZE` | Connection pool size | `5` |
| `DB_MAX_OVERFLOW` | Max pool overflow | `10` |
| `DB_POOL_TIMEOUT` | Pool timeout (seconds) | `30` |
| `DB_POOL_RECYCLE` | Recycle connections (seconds) | `3600` |
| `DB_ECHO` | Echo SQL queries | `false` |

### Environment File Example

Buat file `.env`:

```bash
# Application
APP_NAME=sga-cs-service
APP_VERSION=0.1.0
ENV=production
DEBUG=false

# Server
HOST=0.0.0.0
PORT=8000

# Database (Neon)
DATABASE_URL=postgresql+asyncpg://user:password@ep-xxx.neon.tech/cs_service?sslmode=require

# Database Pool
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600
```

## 🔄 Migration Management

### Automatic Migrations

Migrations berjalan otomatis saat container start melalui `docker-entrypoint.sh`:

1. ✅ Wait for database ready
2. ✅ Show current migration status
3. ✅ Run migrations (`alembic upgrade head`)
4. ✅ Show final migration status
5. ✅ Start application

### Manual Migration Commands

```bash
# View migration logs saat container start
docker logs sga-cs-service

# Run migration manually (jika perlu)
docker exec sga-cs-service alembic upgrade head

# Check migration status
docker exec sga-cs-service alembic current

# Show migration history
docker exec sga-cs-service alembic history

# Rollback one revision
docker exec sga-cs-service alembic downgrade -1

# Rollback to specific revision
docker exec sga-cs-service alembic downgrade <revision>
```

### Skip Migrations (Development Only)

Jika ingin skip auto-migration, override entrypoint:

```bash
docker run -d \
  --name sga-cs-service \
  --entrypoint uvicorn \
  -p 8000:8000 \
  -e DATABASE_URL="your-db-url" \
  sga-cs-service:latest \
  app.main:app --host 0.0.0.0 --port 8000
```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs sga-cs-service

# Check if port is already in use
lsof -i :8000

# Check container status
docker ps -a

# Inspect container
docker inspect sga-cs-service
```

### Database Connection Issues

```bash
# Test database connectivity
docker exec sga-cs-service alembic current

# Check environment variables
docker exec sga-cs-service env | grep DATABASE

# Check database URL format
# Should be: postgresql+asyncpg://user:pass@host/db
```

### Migration Failures

```bash
# View detailed migration logs
docker logs sga-cs-service

# Check migration history
docker exec sga-cs-service alembic history

# Check current revision
docker exec sga-cs-service alembic current

# Try manual migration
docker exec -it sga-cs-service alembic upgrade head
```

### Permission Issues

```bash
# Check if running as non-root
docker exec sga-cs-service whoami
# Should output: appuser

# If you need root access for debugging
docker exec -u root -it sga-cs-service bash
```

### High Memory Usage

```bash
# Check container stats
docker stats sga-cs-service

# Set memory limit
docker update --memory="512m" sga-cs-service

# Or when running:
docker run --memory="512m" ...
```

### View Application Logs

```bash
# Follow logs
docker logs -f sga-cs-service

# Last 100 lines
docker logs --tail 100 sga-cs-service

# With timestamps
docker logs -t sga-cs-service

# Since specific time
docker logs --since 1h sga-cs-service
```

## 📊 Monitoring

### Health Check

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' sga-cs-service

# Check health history
docker inspect --format='{{json .State.Health}}' sga-cs-service | jq
```

### Resource Usage

```bash
# Real-time stats
docker stats sga-cs-service

# One-time stats
docker stats --no-stream sga-cs-service
```

### Process List

```bash
# List processes
docker top sga-cs-service
```

## 🚀 Deployment

### Production Deployment

1. **Build production image**:
   ```bash
   docker build -t your-registry/sga-cs-service:1.0.0 .
   ```

2. **Push to registry**:
   ```bash
   docker push your-registry/sga-cs-service:1.0.0
   ```

3. **Deploy to server**:
   ```bash
   docker pull your-registry/sga-cs-service:1.0.0
   docker run -d \
     --name sga-cs-service \
     --restart unless-stopped \
     --memory="512m" \
     --cpus="1" \
     -p 8000:8000 \
     -e DATABASE_URL="${DATABASE_URL}" \
     your-registry/sga-cs-service:1.0.0
   ```

### CI/CD Pipeline Example (GitHub Actions)

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t sga-cs-service:${{ github.sha }} .

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push sga-cs-service:${{ github.sha }}
```

## 📝 Best Practices

1. ✅ Selalu gunakan specific version tags, hindari `latest` di production
2. ✅ Set resource limits (memory, CPU)
3. ✅ Gunakan health checks
4. ✅ Configure restart policy (`unless-stopped` atau `always`)
5. ✅ Simpan logs dengan log driver yang tepat
6. ✅ Gunakan secrets management untuk sensitive data
7. ✅ Regular update base image untuk security patches
8. ✅ Monitor resource usage dan logs
9. ✅ Backup database secara regular
10. ✅ Test migrations di staging sebelum production

## 🔗 Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

---

**Support**: Jika ada pertanyaan atau issue, silakan buat issue di repository.
