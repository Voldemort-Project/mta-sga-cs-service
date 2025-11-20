.PHONY: help build run stop restart logs shell test clean

# Docker image name and tag
IMAGE_NAME := sga-cs-service
IMAGE_TAG := latest
CONTAINER_NAME := sga-cs-service
PORT := 8000

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(CYAN)SGA CS Service - Docker Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(CYAN)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(CYAN)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Docker Build

build: ## Build Docker image
	@echo "$(CYAN)Building Docker image...$(NC)"
	DOCKER_BUILDKIT=1 docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "$(GREEN)✓ Build completed!$(NC)"

build-no-cache: ## Build Docker image without cache
	@echo "$(CYAN)Building Docker image (no cache)...$(NC)"
	DOCKER_BUILDKIT=1 docker build --no-cache -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "$(GREEN)✓ Build completed!$(NC)"

##@ Docker Run

run: ## Run container
	@echo "$(CYAN)Starting container...$(NC)"
	docker run -d \
		--name $(CONTAINER_NAME) \
		--restart unless-stopped \
		--env-file .env \
		-p $(PORT):8000 \
		$(IMAGE_NAME):$(IMAGE_TAG)
	@echo "$(GREEN)✓ Container started!$(NC)"
	@echo "Access at: http://localhost:$(PORT)"

run-dev: ## Run container in development mode with auto-reload
	@echo "$(CYAN)Starting container in development mode...$(NC)"
	docker run -d \
		--name $(CONTAINER_NAME) \
		--env-file .env \
		-p $(PORT):8000 \
		-v $(PWD)/app:/app/app \
		$(IMAGE_NAME):$(IMAGE_TAG) \
		uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
	@echo "$(GREEN)✓ Container started in dev mode!$(NC)"

##@ Docker Control

stop: ## Stop container
	@echo "$(CYAN)Stopping container...$(NC)"
	docker stop $(CONTAINER_NAME) || true
	@echo "$(GREEN)✓ Container stopped!$(NC)"

start: ## Start stopped container
	@echo "$(CYAN)Starting container...$(NC)"
	docker start $(CONTAINER_NAME)
	@echo "$(GREEN)✓ Container started!$(NC)"

restart: ## Restart container
	@echo "$(CYAN)Restarting container...$(NC)"
	docker restart $(CONTAINER_NAME)
	@echo "$(GREEN)✓ Container restarted!$(NC)"

rm: stop ## Remove container
	@echo "$(CYAN)Removing container...$(NC)"
	docker rm $(CONTAINER_NAME) || true
	@echo "$(GREEN)✓ Container removed!$(NC)"

##@ Docker Compose

up: ## Start services with docker-compose
	@echo "$(CYAN)Starting services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Services started!$(NC)"

down: ## Stop services with docker-compose
	@echo "$(CYAN)Stopping services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Services stopped!$(NC)"

compose-logs: ## View docker-compose logs
	docker-compose logs -f

compose-restart: ## Restart docker-compose services
	docker-compose restart

##@ Logs & Monitoring

logs: ## View container logs (follow)
	docker logs -f $(CONTAINER_NAME)

logs-tail: ## View last 100 lines of logs
	docker logs --tail 100 $(CONTAINER_NAME)

stats: ## View container resource usage
	docker stats $(CONTAINER_NAME)

health: ## Check container health
	@docker inspect --format='{{.State.Health.Status}}' $(CONTAINER_NAME) || echo "No health check configured"

ps: ## List running containers
	docker ps -a | grep $(CONTAINER_NAME) || echo "Container not found"

##@ Database & Migrations

migrate: ## Run database migrations inside container
	@echo "$(CYAN)Running migrations...$(NC)"
	docker exec $(CONTAINER_NAME) alembic upgrade head
	@echo "$(GREEN)✓ Migrations completed!$(NC)"

migrate-status: ## Check migration status
	docker exec $(CONTAINER_NAME) alembic current

migrate-history: ## Show migration history
	docker exec $(CONTAINER_NAME) alembic history

migrate-rollback: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	docker exec $(CONTAINER_NAME) alembic downgrade -1
	@echo "$(GREEN)✓ Rollback completed!$(NC)"

##@ Shell & Debug

shell: ## Access container shell
	docker exec -it $(CONTAINER_NAME) bash

shell-root: ## Access container shell as root
	docker exec -u root -it $(CONTAINER_NAME) bash

exec: ## Execute command in container (usage: make exec cmd="your command")
	docker exec $(CONTAINER_NAME) $(cmd)

inspect: ## Inspect container
	docker inspect $(CONTAINER_NAME)

##@ Testing

test: ## Run tests inside container
	docker exec $(CONTAINER_NAME) pytest

test-local: ## Run tests locally (requires python env)
	uv run pytest

##@ Cleanup

clean: rm ## Remove container and image
	@echo "$(CYAN)Removing image...$(NC)"
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) || true
	@echo "$(GREEN)✓ Cleanup completed!$(NC)"

clean-all: ## Remove all unused Docker resources
	@echo "$(YELLOW)Cleaning up Docker resources...$(NC)"
	docker system prune -f
	@echo "$(GREEN)✓ Cleanup completed!$(NC)"

clean-volumes: ## Remove all unused volumes (DANGEROUS!)
	@echo "$(YELLOW)⚠️  This will remove all unused volumes!$(NC)"
	docker volume prune -f

##@ Development

dev-setup: ## Setup development environment
	@echo "$(CYAN)Setting up development environment...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env file...$(NC)"; \
		echo "DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cs_service" > .env; \
	fi
	uv sync
	@echo "$(GREEN)✓ Development environment ready!$(NC)"
	@echo "$(YELLOW)Don't forget to update .env with your actual database URL$(NC)"

dev-install: ## Install dependencies locally with uv
	@echo "$(CYAN)Installing dependencies...$(NC)"
	uv sync
	@echo "$(GREEN)✓ Dependencies installed!$(NC)"

dev-run: ## Run server locally with auto-reload (port 8080)
	@echo "$(CYAN)Starting development server on http://localhost:8080$(NC)"
	uv run uvicorn app.main:app --reload --port 8080

dev-run-8000: ## Run server locally on port 8000
	@echo "$(CYAN)Starting development server on http://localhost:8000$(NC)"
	uv run uvicorn app.main:app --reload --port 8000

dev-migrate: ## Run migrations locally
	@echo "$(CYAN)Running database migrations...$(NC)"
	uv run alembic upgrade head
	@echo "$(GREEN)✓ Migrations completed!$(NC)"

dev-migrate-rollback: ## Rollback last migration locally
	@echo "$(CYAN)Rolling back last migration...$(NC)"
	uv run alembic downgrade -1
	@echo "$(GREEN)✓ Rollback completed!$(NC)"

dev-migrate-status: ## Check migration status locally
	@echo "$(CYAN)Checking migration status...$(NC)"
	uv run alembic current

rebuild: clean build run ## Clean, build, and run container

redeploy: stop rm build run logs ## Stop, remove, build, and run with logs

##@ CI/CD

ci-build: ## Build for CI/CD (with version tag)
	@echo "$(CYAN)Building for CI/CD...$(NC)"
	@if [ -z "$(VERSION)" ]; then \
		echo "$(YELLOW)⚠️  VERSION not set, using 'latest'$(NC)"; \
		VERSION=latest; \
	fi
	docker build -t $(IMAGE_NAME):$(VERSION) .
	docker tag $(IMAGE_NAME):$(VERSION) $(IMAGE_NAME):latest
	@echo "$(GREEN)✓ CI build completed!$(NC)"

ci-test: ## Run tests in CI/CD
	@echo "$(CYAN)Running tests...$(NC)"
	docker run --rm $(IMAGE_NAME):$(IMAGE_TAG) pytest
	@echo "$(GREEN)✓ Tests completed!$(NC)"

##@ Production

prod-deploy: ## Deploy to production (requires PROD_SERVER env var)
	@if [ -z "$(PROD_SERVER)" ]; then \
		echo "$(YELLOW)⚠️  PROD_SERVER not set!$(NC)"; \
		echo "Usage: make prod-deploy PROD_SERVER=user@server"; \
		exit 1; \
	fi
	@echo "$(CYAN)Deploying to production...$(NC)"
	docker save $(IMAGE_NAME):$(IMAGE_TAG) | ssh $(PROD_SERVER) 'docker load'
	ssh $(PROD_SERVER) 'docker stop $(CONTAINER_NAME) || true'
	ssh $(PROD_SERVER) 'docker rm $(CONTAINER_NAME) || true'
	ssh $(PROD_SERVER) 'docker run -d --name $(CONTAINER_NAME) --restart unless-stopped --env-file .env -p $(PORT):8000 $(IMAGE_NAME):$(IMAGE_TAG)'
	@echo "$(GREEN)✓ Production deployment completed!$(NC)"

##@ Info

version: ## Show version info
	@echo "Image: $(IMAGE_NAME):$(IMAGE_TAG)"
	@echo "Container: $(CONTAINER_NAME)"
	@echo "Port: $(PORT)"

size: ## Show Docker image size
	@docker images $(IMAGE_NAME):$(IMAGE_TAG) --format "Size: {{.Size}}"

info: ## Show container info
	@echo "$(CYAN)Container Information:$(NC)"
	@docker inspect --format='Name: {{.Name}}' $(CONTAINER_NAME) || echo "Container not found"
	@docker inspect --format='Status: {{.State.Status}}' $(CONTAINER_NAME) 2>/dev/null || true
	@docker inspect --format='Health: {{.State.Health.Status}}' $(CONTAINER_NAME) 2>/dev/null || true
	@docker inspect --format='IP Address: {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(CONTAINER_NAME) 2>/dev/null || true
