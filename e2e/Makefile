# E2E Test Makefile

.PHONY: help deps build test clean docker-build podman-build local-test docker-test

# Variables
GINKGO_FLAGS := --randomize-all --race
BUILD_DIR := ../tmp
SERVER_BIN := $(BUILD_DIR)/sandboxd
CONFIG_FILE := testdata/test_config.yaml

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
	@echo "  podman-build - Build Podman images"
	@echo "  local-test   - Build local images and run tests"
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
	SANDBOX_CONFIG=$(CONFIG_FILE) ginkgo run $(GINKGO_FLAGS)

test-verbose: build
	SANDBOX_CONFIG=$(CONFIG_FILE) ginkgo run $(GINKGO_FLAGS) --v

test-focus: build
	SANDBOX_CONFIG=$(CONFIG_FILE) ginkgo run $(GINKGO_FLAGS) --focus="$(FOCUS)"

coverage: build
	SANDBOX_CONFIG=$(CONFIG_FILE) ginkgo run $(GINKGO_FLAGS) --cover --coverprofile=coverage.out
	go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report: coverage.html"

# =============================================================================
# Container Operations
# =============================================================================

docker-build:
	cd .. && docker build -f docker/runtimes/python/Dockerfile -t sandbox-python:latest .
	cd .. && docker build -f docker/runtimes/node/Dockerfile -t sandbox-node:latest .

podman-build:
	cd .. && podman build -f docker/runtimes/python/Dockerfile -t sandbox-python:latest .
	cd .. && podman build -f docker/runtimes/node/Dockerfile -t sandbox-node:latest .

local-test: podman-build test

docker-test: docker-build test

# =============================================================================
# Cleanup
# =============================================================================

clean:
	rm -f $(SERVER_BIN)
	rm -f coverage.out coverage.html
	rm -f /tmp/test_sandbox_config*.yaml
	# Clean up container images and system
	docker system prune -f --filter "label=sandbox-test" 2>/dev/null || true
	podman system prune -f 2>/dev/null || true