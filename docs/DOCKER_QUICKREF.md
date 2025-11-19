# Docker Quick Reference

Quick commands untuk operasi Docker sehari-hari.

## 🚀 Quick Start

```bash
# Build image
docker build -t sga-cs-service:latest .

# Run container
docker run -d --name sga-cs-service -p 8000:8000 \
  -e DATABASE_URL="your-db-url" \
  sga-cs-service:latest

# View logs
docker logs -f sga-cs-service

# Stop container
docker stop sga-cs-service
```

## 📦 Using Docker Compose

```bash
docker-compose up -d      # Start services
docker-compose down       # Stop services
docker-compose logs -f    # View logs
docker-compose restart    # Restart services
```

## 🛠️ Using Makefile (Recommended)

```bash
make build       # Build image
make run         # Run container
make logs        # View logs
make stop        # Stop container
make restart     # Restart container
make shell       # Access shell
make migrate     # Run migrations
make clean       # Remove container and image
make help        # Show all commands
```

## 🔄 Common Operations

### Build & Deploy
```bash
# Build
make build

# Run
make run

# Or rebuild and run
make rebuild
```

### View Logs
```bash
# Follow logs
make logs

# Last 100 lines
make logs-tail

# Docker compose logs
make compose-logs
```

### Database Migrations
```bash
# Run migrations
make migrate

# Check status
make migrate-status

# View history
make migrate-history

# Rollback
make migrate-rollback
```

### Container Management
```bash
# Start/Stop
make start
make stop
make restart

# Remove
make rm

# Redeploy (stop, remove, build, run)
make redeploy
```

### Access Container
```bash
# Shell access
make shell

# Root shell
make shell-root

# Execute command
make exec cmd="alembic current"
```

### Monitoring
```bash
# Resource usage
make stats

# Health check
make health

# Container info
make info
```

## 🐛 Troubleshooting

### Container won't start
```bash
# Check logs
docker logs sga-cs-service

# Inspect container
docker inspect sga-cs-service

# Check if port is in use
lsof -i :8000
```

### Database issues
```bash
# Test database connection
docker exec sga-cs-service alembic current

# Check environment
docker exec sga-cs-service env | grep DATABASE
```

### Migration issues
```bash
# View migration status
docker exec sga-cs-service alembic current

# Try manual migration
docker exec sga-cs-service alembic upgrade head

# View migration history
docker exec sga-cs-service alembic history
```

## 🧹 Cleanup

```bash
# Remove container
make rm

# Remove container and image
make clean

# Clean all unused Docker resources
make clean-all

# Clean volumes (DANGEROUS!)
make clean-volumes
```

## 📊 Useful Commands

### Check if container is running
```bash
docker ps | grep sga-cs-service
# or
make ps
```

### View resource usage
```bash
docker stats sga-cs-service
# or
make stats
```

### Access application
```bash
# Health check
curl http://localhost:8000/api/v1/health

# API docs
open http://localhost:8000/docs
```

### Environment variables
```bash
# View all env vars in container
docker exec sga-cs-service env

# View specific env var
docker exec sga-cs-service env | grep DATABASE_URL
```

## 🚀 Production Deployment

### Using Makefile
```bash
# Deploy to production server
make prod-deploy PROD_SERVER=user@server
```

### Manual deployment
```bash
# 1. Build image
docker build -t sga-cs-service:1.0.0 .

# 2. Save image
docker save sga-cs-service:1.0.0 | gzip > sga-cs-service.tar.gz

# 3. Copy to server
scp sga-cs-service.tar.gz user@server:/tmp/

# 4. Load on server
ssh user@server 'docker load < /tmp/sga-cs-service.tar.gz'

# 5. Run on server
ssh user@server 'docker run -d --name sga-cs-service \
  --restart unless-stopped \
  -p 8000:8000 \
  -e DATABASE_URL="your-db-url" \
  sga-cs-service:1.0.0'
```

## 📝 Best Practices Checklist

- [ ] Use specific version tags instead of `latest` in production
- [ ] Set resource limits (memory, CPU)
- [ ] Configure restart policy
- [ ] Use health checks
- [ ] Set up proper logging
- [ ] Use secrets for sensitive data
- [ ] Regular security updates
- [ ] Monitor resource usage
- [ ] Backup database regularly
- [ ] Test in staging first

## 🔗 More Information

- **Full documentation**: [DOCKER.md](DOCKER.md)
- **Project README**: [../README.md](../README.md)
- **Docker docs**: https://docs.docker.com/
- **FastAPI deployment**: https://fastapi.tiangolo.com/deployment/

## 💡 Tips

1. **Use Makefile** for common operations - it's faster and easier
2. **Always check logs** if something goes wrong
3. **Test locally** before deploying to production
4. **Use Docker Compose** for development with local database
5. **Monitor resource usage** regularly with `make stats`
6. **Keep your base image updated** for security patches
7. **Use `.dockerignore`** to reduce build context size
8. **Tag your images** with version numbers for production
