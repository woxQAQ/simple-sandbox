.PHONY: fmt
fmt:
	@echo "Formatting code..."
	@ruff check . --fix
	@black .