.PHONY: lint fix

lint:
	ruff check . --fix
	ruff check . --fix --select I

format:
	ruff format
