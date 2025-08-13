# E2E Test Makefile

.PHONY: help deps build test clean docker-build docker-test

# Variables
GINKGO_FLAGS := --randomize-all --race
BUILD_DIR := ../tmp
SERVER_BIN := $(BUILD_DIR)/sandboxd

# =============================================================================
# Help and Setup
# =============================================================================

help:
	@echo "Available targets:"
	@echo "  deps         - Install test dependencies"
	@echo "  build        - Build the sandbox server"
	@echo "  test         - Run all e2e tests"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  test-focus   - Run focused tests (use FOCUS=pattern)"
	@echo "  coverage     - Run tests with coverage report"
	@echo "  clean        - Clean up test artifacts"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-test  - Build images and run tests"

deps:
	go mod download
	go install github.com/onsi/ginkgo/v2/ginkgo@latest

# =============================================================================
# Build
# =============================================================================

build:
	mkdir -p $(BUILD_DIR)
	cd .. && go build -o tmp/sandboxd ./cmd/sandboxd

# =============================================================================
# Testing
# =============================================================================

test: build
	ginkgo run $(GINKGO_FLAGS)

test-verbose: build
	ginkgo run $(GINKGO_FLAGS) --v

test-focus: build
	ginkgo run $(GINKGO_FLAGS) --focus="$(FOCUS)"

coverage: build
	ginkgo run $(GINKGO_FLAGS) --cover --coverprofile=coverage.out
	go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report: coverage.html"

# =============================================================================
# Docker Operations
# =============================================================================

docker-build:
	cd .. && docker build -f docker/runtimes/python/Dockerfile -t sandbox-python:latest docker/runtimes/python/
	cd .. && docker build -f docker/runtimes/node/Dockerfile -t sandbox-node:latest docker/runtimes/node/
	cd .. && docker build -f docker/apiserver/Dockerfile -t sandbox-api:latest .

docker-test: docker-build test

# =============================================================================
# Cleanup
# =============================================================================

clean:
	rm -f $(SERVER_BIN)
	rm -f coverage.out coverage.html
	rm -f /tmp/test_sandbox_config*.yaml
	docker system prune -f --filter "label=sandbox-test" 2>/dev/null || true