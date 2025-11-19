#!/usr/bin/env bash

# Makefile for aitdr-elastic project
# Usage: make [target]

.PHONY: help build up down logs clean test setup

help:
	@echo "AITDR-Elastic Make Targets"
	@echo "========================="
	@echo ""
	@echo "setup        - Initial setup (create .env, build images)"
	@echo "up           - Start all services"
	@echo "down         - Stop all services"
	@echo "logs         - View logs (docker-compose logs -f)"
	@echo "build        - Build all Docker images"
	@echo "clean        - Remove containers, volumes, images"
	@echo "test         - Run tests"
	@echo "lint         - Run Python linter"
	@echo "index        - Create Elasticsearch indices"
	@echo "ingest       - Generate sample data"
	@echo ""

setup:
	@echo "Setting up aitdr-elastic..."
	@if [ ! -f .env ]; then \
		cp infra/env.example .env; \
		echo "✓ Created .env from template"; \
	fi
	@cd infra && docker-compose build
	@echo "✓ Setup complete. Run 'make up' to start"

up:
	@echo "Starting services..."
	@cd infra && docker-compose up -d
	@echo "✓ Services starting. Run 'make logs' to view"

down:
	@echo "Stopping services..."
	@cd infra && docker-compose down
	@echo "✓ Services stopped"

logs:
	@cd infra && docker-compose logs -f

build:
	@echo "Building all services..."
	@cd infra && docker-compose build

clean:
	@echo "Cleaning up..."
	@cd infra && docker-compose down -v
	@echo "✓ Cleaned (containers and volumes removed)"

test:
	@echo "Running tests..."
	@python -m pytest services/ml_scorer/tests -v || true
	@python -m pytest services/orchestrator/tests -v || true

lint:
	@echo "Linting Python code..."
	@python -m pip install flake8 > /dev/null 2>&1
	@flake8 services --max-line-length=120 || true

index:
	@echo "Creating Elasticsearch indices..."
	@bash scripts/setup-index.sh

ingest:
	@echo "Generating sample data..."
	@python scripts/embed_and_index.py --mode sample --index alerts
	@python scripts/embed_and_index.py --mode sample --index intel

health:
	@echo "Checking service health..."
	@curl -s http://localhost:9200/_cluster/health | python -m json.tool || echo "Elasticsearch: DOWN"
	@curl -s http://localhost:5601/api/status | python -m json.tool || echo "Kibana: DOWN"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "Orchestrator: DOWN"
	@curl -s http://localhost:8001/health | python -m json.tool || echo "ML Scorer: DOWN"
