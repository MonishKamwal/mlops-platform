.PHONY: train evaluate lint test

train:
	python src/train.py

evaluate:
	python src/evaluate.py --model-uri models:/sentiment-analysis/Production

lint:
	ruff check src/ tests/

test:
	pytest tests/ -v --tb=short
