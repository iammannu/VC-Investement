.PHONY: help dev build down logs migrate seed test lint format

help:
	@echo "AI Investment Memo Generator — Dev Commands"
	@echo "============================================"
	@echo "make dev        - Start all services (dev mode)"
	@echo "make build      - Build Docker images"
	@echo "make down       - Stop all services"
	@echo "make logs       - Tail all logs"
	@echo "make migrate    - Run DB migrations"
	@echo "make seed       - Seed test data"
	@echo "make test       - Run backend tests"
	@echo "make lint       - Run linters"
	@echo "make format     - Format code"
	@echo "make shell      - Open backend shell"

dev:
	@cp -n .env.example .env 2>/dev/null || true
	docker compose up --build

build:
	docker compose build

down:
	docker compose down

down-v:
	docker compose down -v

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend worker

migrate:
	docker compose exec backend alembic upgrade head

migrate-create:
	docker compose exec backend alembic revision --autogenerate -m "$(name)"

migrate-down:
	docker compose exec backend alembic downgrade -1

seed:
	docker compose exec backend python -m app.utils.seed

test:
	docker compose exec backend pytest tests/ -v

lint:
	docker compose exec backend ruff check app/
	docker compose exec backend mypy app/

format:
	docker compose exec backend ruff format app/
	docker compose exec backend ruff check --fix app/

shell:
	docker compose exec backend python

minio-init:
	docker compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin123
	docker compose exec minio mc mb local/pitch-decks --ignore-existing

ps:
	docker compose ps

restart-backend:
	docker compose restart backend worker
