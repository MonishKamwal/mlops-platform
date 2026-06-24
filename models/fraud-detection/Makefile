.PHONY: train evaluate lint test

DATA_PATH ?= data/raw/creditcard.csv

featurize:
	python -m src.features --input data/raw/creditcard.csv --output data/processed/features.parquet

train:
	python -m src.train --data-path data/processed/features.parquet

evaluate:
	python -m src.evaluate --model-path model/model.json --scaler-path model/scaler.pkl --data-path data/processed/features.parquet

lint:
	ruff check src/ tests/

test:
	pytest tests/ -v --tb=short
