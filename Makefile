.PHONY: dev down logs ps lint test build

dev:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f

ps:
	docker compose ps

lint:
	ruff check .
	mypy . --ignore-missing-imports

test:
	pytest models/ serving/ -v --tb=short -q

build:
	docker compose build
