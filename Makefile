.PHONY: install dev test lint run

install:
	python -m pip install -e .

dev:
	python -m pip install -e '.[dev]'

test:
	pytest

lint:
	ruff check .

run:
	uvicorn main:app --reload --host 127.0.0.1 --port 8000
