.PHONY: help install install-dev test test-unit test-integration test-e2e test-clean lint format clean build run-dev run-prod docker-build docker-run

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run all tests"
	@echo "  test-unit    - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-e2e     - Run end-to-end tests only"
	@echo "  test-clean   - Run integration tests with separate output directory"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code with black and isort"
	@echo "  clean        - Clean up temporary files"
	@echo "  build        - Build the package"
	@echo "  run-dev      - Run development server"
	@echo "  run-prod     - Run production server"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,test]"

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

test-e2e:
	pytest tests/e2e/ -v -m e2e

test-coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term

test-clean:
	python run_tests_with_separate_output.py

# Code quality
lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

format-check:
	black --check src/ tests/
	isort --check-only src/ tests/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/

# Build
build: clean
	python -m build

# Development server
run-dev:
	uvicorn src.api.v1.api:app --reload --host 0.0.0.0 --port 8000

run-case-management:
	uvicorn src.api.v1.case_management_api:app --reload --host 0.0.0.0 --port 8001

# Production server
run-prod:
	uvicorn src.api.v1.api:app --host 0.0.0.0 --port 8000 --workers 4

# Docker
docker-build:
	docker build -t ocr-api:latest -f deployment/docker/Dockerfile .

docker-run:
	docker run -p 8000:8000 ocr-api:latest

# Database migrations (if using Alembic)
migrations-init:
	alembic init alembic

migrations-generate:
	alembic revision --autogenerate -m "$(msg)"

migrations-upgrade:
	alembic upgrade head

migrations-downgrade:
	alembic downgrade -1

# Environment setup
setup-env:
	python -m venv venv
	@echo "Activate virtual environment with: source venv/bin/activate"

setup-pre-commit:
	pre-commit install
	pre-commit run --all-files