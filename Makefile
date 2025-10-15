# bw-serve-client Makefile
# Convenience commands for common development tasks

.PHONY: help extract-routes test lint format clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

extract-routes: ## Extract API routes from swagger file
	python3 scripts/extract_routes.py docs/vault-management-api.json

extract-routes-text: ## Extract routes in text format
	python3 scripts/extract_routes.py -f text docs/vault-management-api.json

extract-routes-json: ## Extract routes in JSON format
	python3 scripts/extract_routes.py -f json docs/vault-management-api.json

test: ## Run tests
	python3 -m pytest tests/

lint: ## Run linting checks
	flake8 bw_serve_client/ tests/
	mypy bw_serve_client/

format: ## Format code
	yapf -i -r bw_serve_client/ tests/ scripts/

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
