.PHONY: dev down lint test build

dev:
	docker compose up --build

down:
	docker compose down -v

lint:
	ruff check .
	mypy . --ignore-missing-imports

test:
	pytest models/ serving/ -v --tb=short -q

build:
	docker compose build
