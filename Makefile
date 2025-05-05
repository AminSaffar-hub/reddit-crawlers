#!/usr/bin/make

include .env

help:
	@echo "make"
	@echo "    install"
	@echo "        Install all packages of poetry project locally."
	@echo "    run-dev-build"
	@echo "        Run development docker compose and force build containers."
	@echo "    run-dev"
	@echo "        Run development docker compose."
	@echo "    stop-dev"
	@echo "        Stop development docker compose."
	@echo "    formatter"
	@echo "        Apply black formatting to code."
	@echo "    mypy"
	@echo "        Check typing."		
	@echo "    lint"
	@echo "        Lint code with ruff, and check if black formatter should be applied."
	@echo "    lint-watch"
	@echo "        Lint code with ruff in watch mode."
	@echo "    lint-fix"
	@echo "        Lint code with ruff and try to fix."	
	
install:
	poetry install

run-dev-build:
	docker compose -f docker-compose.yml up --build

run-dev:
	docker compose -f docker-compose.yml up

stop-dev:
	docker compose -f docker-compose.yml down

formatter:
	poetry run black . && poetry run isort .

mypy:
	poetry run mypy .

lint:
	poetry run ruff check . && poetry run black --check .

lint-watch:
	poetry run ruff check . --watch

lint-fix:
	poetry run ruff check . --fix

test:
	poetry run pytest
