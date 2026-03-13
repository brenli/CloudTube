.PHONY: help install install-dev test test-unit test-property test-integration lint format typecheck clean run

help:
	@echo "YouTube WebDAV Bot - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install production dependencies"
	@echo "  make install-dev   Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test          Run all tests"
	@echo "  make test-unit     Run unit tests only"
	@echo "  make test-property Run property-based tests only"
	@echo "  make test-integration Run integration tests only"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          Run flake8 linter"
	@echo "  make format        Format code with black"
	@echo "  make typecheck     Run mypy type checker"
	@echo ""
	@echo "Running:"
	@echo "  make run           Run the bot"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove generated files"

install:
	pip install -r requirements.txt

install-dev:
	pip install -e ".[dev]"

test:
	pytest

test-unit:
	pytest -m unit

test-property:
	pytest -m property

test-integration:
	pytest -m integration

lint:
	flake8 bot/ tests/

format:
	black bot/ tests/

typecheck:
	mypy bot/

clean:
	rm -rf __pycache__ .pytest_cache .hypothesis .mypy_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run:
	python -m bot.main
