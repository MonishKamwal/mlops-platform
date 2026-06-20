.PHONY: train evaluate lint test

DATA_PATH ?= data/raw/demand.csv

train:
	python src/train.py --data-path $(DATA_PATH)

evaluate:
	python src/evaluate.py --model-uri models:/demand-forecasting/Production --data-path $(DATA_PATH)

lint:
	ruff check src/ tests/

test:
	pytest tests/ -v --tb=short
