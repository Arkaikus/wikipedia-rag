.PHONY: help install dev-install clean test lint format type-check docker-up docker-down docker-logs run

help:  ## Show this help message
	@echo "RAG Wikipedia Chatbot - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install project dependencies (production only)
	uv venv
	uv pip install -e .

dev-install:  ## Install project with dev dependencies
	uv venv
	uv pip install -e ".[dev]"

clean:  ## Remove virtual environment and cache files
	rm -rf .venv
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test:  ## Run tests with pytest
	pytest tests/ -v

test-cov:  ## Run tests with coverage report
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

lint:  ## Run ruff linter
	ruff check src/ tests/

format:  ## Format code with black and ruff
	black src/ tests/
	ruff check --fix src/ tests/

type-check:  ## Run mypy type checker
	mypy src/

quality:  ## Run all quality checks (format, lint, type-check, test)
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) test

docker-up:  ## Start Docker Compose services (Chroma)
	docker-compose up -d

docker-down:  ## Stop Docker Compose services
	docker-compose down

docker-logs:  ## Show Docker Compose logs
	docker-compose logs -f

docker-restart:  ## Restart Docker Compose services
	docker-compose restart

docker-clean:  ## Remove Docker volumes (⚠️  deletes all data)
	docker-compose down -v
	rm -rf chroma_data weaviate_data

run:  ## Run the chatbot application
	python main.py

setup:  ## Complete initial setup (install + docker + env)
	$(MAKE) dev-install
	cp -n .env.example .env || true
	$(MAKE) docker-up
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env with your configuration"
	@echo "  2. Start LMStudio and load a model"
	@echo "  3. Run: make run"
	@echo ""

# Development shortcuts
dev: dev-install docker-up  ## Quick dev setup

check: format lint type-check  ## Run code quality checks

