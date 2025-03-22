.PHONY: build up down logs ps shell clean help

# Docker Compose commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

ps:
	docker-compose ps

shell:
	docker-compose exec backend bash

# Development commands
dev:
	uvicorn app.main:app --reload

# Clean commands
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Help command
help:
	@echo "Available commands:"
	@echo "  make build      Build Docker images"
	@echo "  make up         Start Docker containers in background"
	@echo "  make down       Stop Docker containers"
	@echo "  make logs       View Docker container logs"
	@echo "  make ps         List Docker containers"
	@echo "  make shell      Start a shell in the backend container"
	@echo "  make dev        Start development server locally (not in Docker)"
	@echo "  make clean      Clean Docker volumes, containers, and cache files" 