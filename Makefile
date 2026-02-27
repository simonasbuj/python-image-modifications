ifneq (,$(wildcard .env.example))
    include .env.example
    export $(shell sed 's/=.*//' .env.example)
endif

ifneq (,$(wildcard .env))
    include .env
    export $(shell sed 's/=.*//' .env)
endif


run-api:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

run-api-watch:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-validator:
	python -m app.services.background_validator

test:
	pytest

pre-commit:
	pre-commit run --all-files
