.PHONY: train evaluate lint test

DATA_PATH ?= data/raw/creditcard.csv

train:
	python src/train.py --data-path $(DATA_PATH)

evaluate:
	python src/evaluate.py --model-uri models:/fraud-detection/Production --data-path $(DATA_PATH)

lint:
	ruff check src/ tests/

test:
	pytest tests/ -v --tb=short
