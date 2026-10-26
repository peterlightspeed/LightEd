.PHONY: help install dev up down test lint format clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (web + api + ai)
	cd apps/web && npm install
	cd apps/api && pip install -r requirements.txt
	cd ai && pip install -r requirements.txt

up: ## Start full stack with Docker
	docker compose -f infra/docker-compose.yml up --build

down: ## Stop the stack
	docker compose -f infra/docker-compose.yml down

dev-web: ## Run frontend dev server
	cd apps/web && npm run dev

dev-api: ## Run backend dev server
	cd apps/api && uvicorn app.main:app --reload --port 8000

test: ## Run all tests
	cd apps/api && pytest
	cd ai && pytest

lint: ## Lint everything
	cd apps/web && npm run lint
	cd apps/api && ruff check .
	cd ai && ruff check .

format: ## Auto-format backend + ai
	cd apps/api && ruff format .
	cd ai && ruff format .

clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf apps/web/.next apps/web/node_modules
