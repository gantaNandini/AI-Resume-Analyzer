.PHONY: up down test build logs ps clean frontend-dev frontend-build lint format help

# Default target
.DEFAULT_GOAL := help

# Variables
COMPOSE_FILE := docker-compose.yml
SERVICE ?=

##@ General

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Docker Compose

up: ## Start all services (docker compose up -d)
	docker compose -f $(COMPOSE_FILE) up -d --build

down: ## Stop all services (docker compose down)
	docker compose -f $(COMPOSE_FILE) down

build: ## Build all Docker images
	docker compose -f $(COMPOSE_FILE) build

logs: ## Tail logs for all services (or SERVICE=<name> for one)
	@if [ -n "$(SERVICE)" ]; then \
		docker compose -f $(COMPOSE_FILE) logs -f $(SERVICE); \
	else \
		docker compose -f $(COMPOSE_FILE) logs -f; \
	fi

ps: ## Show running containers
	docker compose -f $(COMPOSE_FILE) ps

clean: ## Remove containers, volumes, and images
	docker compose -f $(COMPOSE_FILE) down -v --rmi local

restart: ## Restart all services (or SERVICE=<name> for one)
	@if [ -n "$(SERVICE)" ]; then \
		docker compose -f $(COMPOSE_FILE) restart $(SERVICE); \
	else \
		docker compose -f $(COMPOSE_FILE) restart; \
	fi

##@ Testing

test: ## Run all tests (frontend + all backend services)
	@echo "Running frontend tests..."
	cd frontend && npm run test -- --run
	@echo "Running auth_service tests..."
	cd services/auth_service && python -m pytest tests/ -v
	@echo "Running file_processor tests..."
	cd services/file_processor && python -m pytest tests/ -v
	@echo "Running nlp_pipeline tests..."
	cd services/nlp_pipeline && python -m pytest tests/ -v
	@echo "Running scoring_engine tests..."
	cd services/scoring_engine && python -m pytest tests/ -v
	@echo "Running llm_service tests..."
	cd services/llm_service && python -m pytest tests/ -v

test-frontend: ## Run frontend tests only
	cd frontend && npm run test -- --run

test-backend: ## Run all backend service tests
	@for svc in auth_service file_processor nlp_pipeline scoring_engine llm_service; do \
		echo "Testing $$svc..."; \
		cd services/$$svc && python -m pytest tests/ -v && cd ../..; \
	done

test-service: ## Run tests for a specific service (SERVICE=auth_service)
	cd services/$(SERVICE) && python -m pytest tests/ -v

##@ Frontend

frontend-dev: ## Start frontend dev server
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	cd frontend && npm run build

frontend-install: ## Install frontend dependencies
	cd frontend && npm install

##@ Code Quality

lint: ## Run linters (ruff for Python, eslint for TypeScript)
	@echo "Linting Python services..."
	@for svc in auth_service file_processor nlp_pipeline scoring_engine llm_service celery_worker; do \
		if [ -d "services/$$svc" ]; then \
			echo "  Linting $$svc..."; \
			cd services/$$svc && ruff check . && cd ../..; \
		fi \
	done
	@echo "Linting frontend..."
	cd frontend && npm run lint

format: ## Format code (black for Python, prettier for TypeScript)
	@echo "Formatting Python services..."
	@for svc in auth_service file_processor nlp_pipeline scoring_engine llm_service celery_worker; do \
		if [ -d "services/$$svc" ]; then \
			echo "  Formatting $$svc..."; \
			cd services/$$svc && black . && cd ../..; \
		fi \
	done
	@echo "Formatting frontend..."
	cd frontend && npm run format

type-check: ## Run TypeScript type checking
	cd frontend && npm run type-check

##@ Database

db-migrate: ## Run Alembic migrations for all services
	@for svc in auth_service file_processor; do \
		if [ -d "services/$$svc/alembic" ]; then \
			echo "Migrating $$svc..."; \
			cd services/$$svc && alembic upgrade head && cd ../..; \
		fi \
	done

db-rollback: ## Rollback last migration (SERVICE=auth_service)
	cd services/$(SERVICE) && alembic downgrade -1

##@ Utilities

install-all: ## Install all dependencies (frontend + all backend services)
	cd frontend && npm install
	@for svc in auth_service file_processor nlp_pipeline scoring_engine llm_service celery_worker; do \
		if [ -d "services/$$svc" ] && [ -f "services/$$svc/requirements.txt" ]; then \
			echo "Installing $$svc dependencies..."; \
			cd services/$$svc && pip install -r requirements.txt && cd ../..; \
		fi \
	done

env-setup: ## Copy all .env.example files to .env (won't overwrite existing)
	@for svc in auth_service file_processor nlp_pipeline scoring_engine llm_service celery_worker; do \
		if [ -f "services/$$svc/.env.example" ] && [ ! -f "services/$$svc/.env" ]; then \
			cp services/$$svc/.env.example services/$$svc/.env; \
			echo "Created services/$$svc/.env"; \
		fi \
	done
