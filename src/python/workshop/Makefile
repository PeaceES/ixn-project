# Makefile for Calendar Scheduler Agent Project
# This Makefile provides convenient commands for development, testing, and deployment

# Python interpreter
PYTHON := python3
PIP := pip3

# Project directories
PROJECT_DIR := $(shell pwd)
TESTS_DIR := $(PROJECT_DIR)/tests
SRC_DIR := $(PROJECT_DIR)

# Virtual environment
VENV_DIR := .venv
VENV_BIN := $(VENV_DIR)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

# Test and coverage settings
PYTEST_ARGS := --tb=short --strict-markers
COVERAGE_ARGS := --cov=services --cov=agent --cov=web_server
REPORTS_DIR := reports

# Test targets with comprehensive reporting
.PHONY: test-thesis test-unit test-integration test-all test-coverage test-performance clean-reports
COVERAGE_ARGS := --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=70

# Colors for terminal output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

# Help target
.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)Calendar Scheduler Agent - Development Commands$(NC)"
	@echo "=================================================="
	@echo ""
	@echo "$(GREEN)Environment Setup:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(venv|install|setup)' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(format|lint|type|check)' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(test|coverage)' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Utilities:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(clean|run|docs)' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

# Virtual environment setup
.PHONY: venv
venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "$(GREEN)Virtual environment created at $(VENV_DIR)$(NC)"
	@echo "$(YELLOW)To activate: source $(VENV_DIR)/bin/activate$(NC)"

# Installation targets
.PHONY: install
install: ## Install project dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependencies installed$(NC)"

.PHONY: install-dev
install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements-test.txt
	@echo "$(GREEN)Development dependencies installed$(NC)"

.PHONY: install-all
install-all: install install-dev ## Install all dependencies

.PHONY: setup
setup: venv install-all ## Complete project setup (venv + dependencies)
	@echo "$(GREEN)Project setup complete!$(NC)"

# Code quality and formatting
.PHONY: format
format: ## Format code with black and sort imports
	@echo "$(BLUE)Formatting code...$(NC)"
	$(PYTHON) -m black .
	$(PYTHON) -m isort .
	@echo "$(GREEN)Code formatted$(NC)"

.PHONY: format-check
format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	$(PYTHON) -m black --check .
	$(PYTHON) -m isort --check-only .

.PHONY: lint
lint: ## Run linting with ruff
	@echo "$(BLUE)Running linting...$(NC)"
	$(PYTHON) -m ruff check .
	@echo "$(GREEN)Linting complete$(NC)"

.PHONY: lint-fix
lint-fix: ## Run linting with automatic fixes
	@echo "$(BLUE)Running linting with fixes...$(NC)"
	$(PYTHON) -m ruff check --fix .
	@echo "$(GREEN)Linting with fixes complete$(NC)"

.PHONY: type-check
type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checking...$(NC)"
	$(PYTHON) -m mypy .
	@echo "$(GREEN)Type checking complete$(NC)"

.PHONY: check-all
check-all: format-check lint type-check ## Run all code quality checks

# Testing targets
.PHONY: test
test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	$(PYTHON) run_tests.py --all

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(PYTHON) run_tests.py --unit

.PHONY: test-integration
test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(PYTHON) run_tests.py --integration

.PHONY: test-smoke
test-smoke: ## Run smoke tests only
	@echo "$(BLUE)Running smoke tests...$(NC)"
	$(PYTHON) run_tests.py --smoke

.PHONY: test-verbose
test-verbose: ## Run all tests with verbose output
	@echo "$(BLUE)Running all tests (verbose)...$(NC)"
	$(PYTHON) run_tests.py --all --verbose

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTHON) -m pytest $(PYTEST_ARGS) $(COVERAGE_ARGS)
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

.PHONY: test-specific
test-specific: ## Run specific test (use TEST=path/to/test)
	@echo "$(BLUE)Running specific test: $(TEST)$(NC)"
	$(PYTHON) run_tests.py --test $(TEST)

.PHONY: test-marker
test-marker: ## Run tests with specific marker (use MARKER=marker_name)
	@echo "$(BLUE)Running tests with marker: $(MARKER)$(NC)"
	$(PYTHON) run_tests.py --marker $(MARKER)

.PHONY: test-full
test-full: ## Run complete test suite including all checks
	@echo "$(BLUE)Running complete test suite...$(NC)"
	$(PYTHON) run_tests.py --full-suite

# Thesis Testing Commands
# =======================

test-thesis: clean-reports install-test-deps
	@echo "🎓 Running comprehensive test suite for thesis documentation..."
	$(PYTHON) run_comprehensive_tests.py

test-unit:
	@echo "🧪 Running unit tests with reporting..."
	$(PYTHON) -m pytest tests/unit/ -v \
		--junitxml=$(REPORTS_DIR)/junit/unit_tests.xml \
		$(COVERAGE_ARGS) \
		--cov-report=html:$(REPORTS_DIR)/coverage_html_unit \
		--cov-report=xml:$(REPORTS_DIR)/coverage_unit.xml \
		--html=$(REPORTS_DIR)/unit_test_report.html \
		--self-contained-html \
		-m unit

test-integration:
	@echo "🔗 Running integration tests with reporting..."
	$(PYTHON) -m pytest tests/integration/ -v \
		--junitxml=$(REPORTS_DIR)/junit/integration_tests.xml \
		$(COVERAGE_ARGS) \
		--cov-report=html:$(REPORTS_DIR)/coverage_html_integration \
		--cov-report=xml:$(REPORTS_DIR)/coverage_integration.xml \
		--html=$(REPORTS_DIR)/integration_test_report.html \
		--self-contained-html \
		-m integration

test-all:
	@echo "🚀 Running complete test suite..."
	$(PYTHON) -m pytest -v \
		--junitxml=$(REPORTS_DIR)/junit/all_tests.xml \
		$(COVERAGE_ARGS) \
		--cov-report=term-missing \
		--cov-report=html:$(REPORTS_DIR)/coverage_html_combined \
		--cov-report=xml:$(REPORTS_DIR)/coverage_combined.xml \
		--cov-fail-under=75 \
		--html=$(REPORTS_DIR)/complete_test_report.html \
		--self-contained-html

test-coverage:
	@echo "📊 Generating detailed coverage report..."
	$(PYTHON) -m pytest \
		$(COVERAGE_ARGS) \
		--cov-report=html:$(REPORTS_DIR)/coverage_detailed \
		--cov-report=xml:$(REPORTS_DIR)/coverage_detailed.xml \
		--cov-report=term-missing \
		--cov-fail-under=85

test-performance:
	@echo "⏱️  Running performance tests..."
	$(PYTHON) -m pytest -v \
		--tb=short \
		--durations=0 \
		--durations-min=0.1 \
		-m "not slow"

install-test-deps:
	@echo "📦 Installing test dependencies..."
	$(PIP) install pytest-html pytest-cov pytest-xdist pytest-mock

clean-reports:
	@echo "🧹 Cleaning old reports..."
	rm -rf $(REPORTS_DIR)
	mkdir -p $(REPORTS_DIR)/junit
	mkdir -p $(REPORTS_DIR)/artifacts

# Individual test categories
test-fast:
	$(PYTHON) -m pytest -m "not slow" -v

test-slow:
	$(PYTHON) -m pytest -m slow -v

test-api:
	$(PYTHON) -m pytest tests/integration/test_web_server_integration.py -v

test-database:
	$(PYTHON) -m pytest tests/unit/test_sql_store.py tests/integration/test_calendar_integration.py -v

# Thesis-specific commands
thesis-data:
	@echo "📊 Collecting thesis data..."
	$(MAKE) test-thesis
	@echo "✅ Test data collected in $(REPORTS_DIR)/"
	@echo "Key files for thesis:"
	@echo "  - Complete test report: $(REPORTS_DIR)/complete_test_report.html"
	@echo "  - Coverage report: $(REPORTS_DIR)/coverage_html_combined/index.html"
	@echo "  - Test artifacts: $(REPORTS_DIR)/artifacts/"
	@echo "  - Performance data: Look for performance_*.json in artifacts/"

# Security and dependency checking
.PHONY: security
security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	$(PYTHON) run_tests.py --security

.PHONY: deps-check
deps-check: ## Check for dependency vulnerabilities
	@echo "$(BLUE)Checking dependencies...$(NC)"
	$(PIP) check
	@echo "$(GREEN)Dependency check complete$(NC)"

.PHONY: deps-update
deps-update: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	$(PIP) list --outdated
	@echo "$(YELLOW)To update: pip install --upgrade <package>$(NC)"

# Application running
.PHONY: run
run: ## Run the main application
	@echo "$(BLUE)Running Calendar Scheduler Agent...$(NC)"
	$(PYTHON) main.py

.PHONY: run-streamlit
run-streamlit: ## Run the Streamlit application
	@echo "$(BLUE)Running Streamlit application...$(NC)"
	$(PYTHON) -m streamlit run streamlit_app.py

.PHONY: run-debug
run-debug: ## Run application in debug mode
	@echo "$(BLUE)Running application in debug mode...$(NC)"
	DEBUG=1 $(PYTHON) main.py

# Cleaning targets
.PHONY: clean
clean: ## Clean up temporary files and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	$(PYTHON) run_tests.py --clean
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(NC)"

.PHONY: clean-venv
clean-venv: ## Remove virtual environment
	@echo "$(BLUE)Removing virtual environment...$(NC)"
	rm -rf $(VENV_DIR)
	@echo "$(GREEN)Virtual environment removed$(NC)"

.PHONY: clean-all
clean-all: clean clean-venv ## Clean everything including virtual environment

# Pre-commit hooks
.PHONY: pre-commit-install
pre-commit-install: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	$(PYTHON) -m pre_commit install
	@echo "$(GREEN)Pre-commit hooks installed$(NC)"

.PHONY: pre-commit-run
pre-commit-run: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	$(PYTHON) -m pre_commit run --all-files

# Documentation
.PHONY: docs
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@echo "$(YELLOW)Documentation generation not yet implemented$(NC)"

# Development workflow shortcuts
.PHONY: dev-setup
dev-setup: setup pre-commit-install ## Complete development setup

.PHONY: dev-check
dev-check: check-all test-unit ## Quick development checks

.PHONY: ci-check
ci-check: check-all test-full security ## Full CI/CD checks

.PHONY: quick-test
quick-test: test-unit ## Quick test run for development

.PHONY: full-check
full-check: format lint type-check test-coverage security ## Complete quality check

# Environment information
.PHONY: env-info
env-info: ## Show environment information
	@echo "$(BLUE)Environment Information:$(NC)"
	@echo "Project Directory: $(PROJECT_DIR)"
	@echo "Python Version: $(shell $(PYTHON) --version)"
	@echo "Pip Version: $(shell $(PIP) --version)"
	@echo "Virtual Environment: $(VENV_DIR)"
	@echo "Tests Directory: $(TESTS_DIR)"

# Dependency management
.PHONY: freeze
freeze: ## Freeze current dependencies
	@echo "$(BLUE)Freezing dependencies...$(NC)"
	$(PIP) freeze > requirements-frozen.txt
	@echo "$(GREEN)Dependencies frozen to requirements-frozen.txt$(NC)"

.PHONY: requirements
requirements: ## Generate requirements files
	@echo "$(BLUE)Generating requirements files...$(NC)"
	$(PIP) freeze | grep -v "^-e" > requirements-generated.txt
	@echo "$(GREEN)Requirements generated$(NC)"

# Profiling and performance
.PHONY: profile
profile: ## Profile application performance
	@echo "$(BLUE)Profiling application...$(NC)"
	$(PYTHON) -m cProfile -o profile_output.prof main.py
	@echo "$(GREEN)Profile saved to profile_output.prof$(NC)"

.PHONY: benchmark
benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running benchmarks...$(NC)"
	$(PYTHON) -m pytest -m benchmark --benchmark-only
	@echo "$(GREEN)Benchmarks complete$(NC)"

# Database and data management
.PHONY: db-setup
db-setup: ## Setup database (if applicable)
	@echo "$(BLUE)Setting up database...$(NC)"
	@echo "$(YELLOW)Database setup not yet implemented$(NC)"

.PHONY: db-migrate
db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	@echo "$(YELLOW)Database migrations not yet implemented$(NC)"

# Monitoring and logging
.PHONY: logs
logs: ## View application logs
	@echo "$(BLUE)Viewing logs...$(NC)"
	@if [ -f "app.log" ]; then tail -f app.log; else echo "$(YELLOW)No log file found$(NC)"; fi

.PHONY: monitor
monitor: ## Monitor application performance
	@echo "$(BLUE)Monitoring application...$(NC)"
	@echo "$(YELLOW)Application monitoring not yet implemented$(NC)"

# Build and deployment
.PHONY: build
build: ## Build the application
	@echo "$(BLUE)Building application...$(NC)"
	$(PYTHON) -m build
	@echo "$(GREEN)Build complete$(NC)"

.PHONY: package
package: ## Create distribution package
	@echo "$(BLUE)Creating package...$(NC)"
	$(PYTHON) setup.py sdist bdist_wheel
	@echo "$(GREEN)Package created$(NC)"

.PHONY: deploy
deploy: ## Deploy application
	@echo "$(BLUE)Deploying application...$(NC)"
	@echo "$(YELLOW)Deployment not yet implemented$(NC)"

# Utility targets
.PHONY: version
version: ## Show version information
	@echo "$(BLUE)Version Information:$(NC)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Project: Calendar Scheduler Agent"
	@echo "$(YELLOW)Version management not yet implemented$(NC)"

.PHONY: status
status: ## Show project status
	@echo "$(BLUE)Project Status:$(NC)"
	@echo "Directory: $(PROJECT_DIR)"
	@echo "Git Status:"
	@git status --porcelain || echo "Not a git repository"
	@echo "Virtual Environment: $(if $(wildcard $(VENV_DIR)),$(GREEN)Present$(NC),$(RED)Not found$(NC))"
	@echo "Dependencies: $(if $(wildcard requirements.txt),$(GREEN)Present$(NC),$(RED)Not found$(NC))"

# Make targets that don't create files
.PHONY: $(filter-out help, $(MAKECMDGOALS))
