.PHONY: dev up down logs migrate seed test lint typecheck build smoke

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

migrate:
	docker compose run --rm api alembic -c services/api/alembic.ini upgrade head

seed:
	docker compose run --rm -e PYTHONPATH=/app api python scripts/seed_demo.py

test:
	python -m pytest

lint:
	ruff check services tests scripts

typecheck:
	mypy services/api/app

build:
	docker compose build

smoke:
	python scripts/smoke_test.py
