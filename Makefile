# Makefile for FlipperZero Custom Firmware Development
# Provides convenient shortcuts for common development tasks

.PHONY: help install install-dev clean lint format test security check setup pre-commit

# Default target
.DEFAULT_GOAL := help

# Python interpreter
PYTHON := python3
PIP := $(PYTHON) -m pip

# Directories
BUILD_DIR := build_configs
VENV_DIR := .venv

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Set up development environment (create venv and install dependencies)
	@echo "Setting up development environment..."
	@test -d $(VENV_DIR) || $(PYTHON) -m venv $(VENV_DIR)
	@echo "Activating virtual environment and installing dependencies..."
	@. $(VENV_DIR)/bin/activate && $(PIP) install --upgrade pip setuptools wheel
	@. $(VENV_DIR)/bin/activate && $(PIP) install -r requirements.txt
	@echo "✓ Setup complete! Activate with: source $(VENV_DIR)/bin/activate"

install: ## Install production dependencies
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt -r requirements-dev.txt

clean: ## Clean build artifacts and cache files
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.py,cover" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .eggs/ htmlcov/ .coverage .coverage.*
	rm -f pip-audit-report.json bandit-report.json dependency-tree.txt
	@echo "✓ Clean complete"

format: ## Format code with black and isort
	@echo "Formatting code..."
	black $(BUILD_DIR)/
	isort $(BUILD_DIR)/
	@echo "✓ Format complete"

lint: ## Run all linters (black, isort, flake8, mypy)
	@echo "Running linters..."
	@echo "→ Black..."
	black --check --diff $(BUILD_DIR)/
	@echo "→ isort..."
	isort --check-only --diff $(BUILD_DIR)/
	@echo "→ flake8..."
	flake8 $(BUILD_DIR)/ --max-line-length=100 --extend-ignore=E203,W503
	@echo "→ mypy..."
	mypy $(BUILD_DIR)/ --ignore-missing-imports
	@echo "✓ Lint complete"

test: ## Run tests with pytest
	@echo "Running tests..."
	pytest
	@echo "✓ Tests complete"

security: ## Run security checks (pip-audit, bandit)
	@echo "Running security scans..."
	@echo "→ pip-audit..."
	@pip-audit --requirement requirements.txt || echo "⚠ Security vulnerabilities found - review output above"
	@echo "→ bandit..."
	@bandit -r $(BUILD_DIR)/ || echo "⚠ Security issues found - review output above"
	@echo "✓ Security scan complete (check for warnings above)"

check: ## Run all checks (lint, test, security)
	@echo "Running all checks..."
	@$(MAKE) lint
	@$(MAKE) test
	@$(MAKE) security
	@echo "✓ All checks complete"

pre-commit: ## Install and set up pre-commit hooks
	@echo "Setting up pre-commit hooks..."
	$(PIP) install pre-commit
	pre-commit install
	pre-commit run --all-files || true
	@echo "✓ Pre-commit hooks installed"

deps-tree: ## Show dependency tree
	@echo "Dependency tree:"
	$(PIP) install pipdeptree
	pipdeptree

deps-outdated: ## Check for outdated dependencies
	@echo "Checking for outdated dependencies..."
	$(PIP) list --outdated

deps-update: ## Update all dependencies to latest versions (use with caution)
	@echo "Updating dependencies..."
	$(PIP) install --upgrade -r requirements.txt
	@echo "✓ Dependencies updated"

validate-syntax: ## Validate Python and shell script syntax
	@echo "Validating syntax..."
	@echo "→ Python files..."
	find . -name "*.py" -type f -exec $(PYTHON) -m py_compile {} \;
	@echo "→ Shell scripts..."
	find . -name "*.sh" -type f -exec bash -n {} \;
	@echo "✓ Syntax validation complete"

.PHONY: info
info: ## Display project information
	@echo "Project Information:"
	@echo "  Python version: $$($(PYTHON) --version)"
	@echo "  Virtual env: $(VENV_DIR)"
	@echo "  Build dir: $(BUILD_DIR)"
	@echo ""
	@echo "Installed packages:"
	@$(PIP) list | head -20
