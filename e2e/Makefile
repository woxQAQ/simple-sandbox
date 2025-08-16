# E2E Test Makefile

.PHONY: help deps build test clean docker-build podman-build local-test docker-test

# Variables
GINKGO_FLAGS := --randomize-all --race
BUILD_DIR := ../tmp
SERVER_BIN := $(BUILD_DIR)/sandboxd
CONFIG_FILE := testdata/test_config.yaml

# Test configuration (overridable via environment variables)
PARALLEL_PROCS ?= 8
FOCUS ?= ""

help:
	@echo "Available targets:"
	@echo "  deps         - Install test dependencies"
	@echo "  build        - Build the sandbox server"
	@echo "  test         - Run tests with configuration from $(CONFIG_FILE)"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  test-focus   - Run focused tests (FOCUS=pattern)"
	@echo "  coverage     - Run tests with coverage report"
	@echo "  clean        - Clean up test artifacts"
	@echo "  docker-build - Build Docker images"
	@echo "  podman-build - Build Podman images"
	@echo "  local-test   - Build local images and run tests"
	@echo "  docker-test  - Build images and run tests"
	@echo ""
	@echo "Environment variables:"
	@echo "  SANDBOX_CONFIG     - Path to config file (default: $(CONFIG_FILE))"
	@echo "  PARALLEL_PROCS    - Number of parallel processes (default: $(PARALLEL_PROCS))"
	@echo "  FOCUS             - Test focus pattern (default: $(FOCUS))"

deps:
	go mod download
	@if command -v ginkgo >/dev/null 2>&1; then \
		echo "ginkgo is already installed"; \
	else \
		echo "Installing ginkgo..."; \
		go install github.com/onsi/ginkgo/v2/ginkgo@latest; \
	fi

build: deps
	mkdir -p $(BUILD_DIR)
	cd .. && go build -o tmp/sandboxd ./cmd/sandboxd

test: build
	SANDBOX_CONFIG=$(SANDBOX_CONFIG) ginkgo run $(GINKGO_FLAGS) --procs=$(PARALLEL_PROCS)

test-verbose: build
	SANDBOX_CONFIG=$(SANDBOX_CONFIG) ginkgo run $(GINKGO_FLAGS) --procs=$(PARALLEL_PROCS) --v

test-focus: build
	SANDBOX_CONFIG=$(SANDBOX_CONFIG) ginkgo run $(GINKGO_FLAGS) --procs=$(PARALLEL_PROCS) --focus="$(FOCUS)"

coverage: deps build
	SANDBOX_CONFIG=$(SANDBOX_CONFIG) ginkgo run $(GINKGO_FLAGS) --procs=$(PARALLEL_PROCS) --cover --coverprofile=coverage.out
	go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report: coverage.html"

docker-build:
	cd .. && docker build -f docker/runtimes/python/Dockerfile -t sandbox-python:latest .
	cd .. && docker build -f docker/runtimes/node/Dockerfile -t sandbox-node:latest .

podman-build:
	cd .. && podman build -f docker/runtimes/python/Dockerfile -t sandbox-python:latest .
	cd .. && podman build -f docker/runtimes/node/Dockerfile -t sandbox-node:latest .

local-test: podman-build test

docker-test: docker-build test

clean:
	rm -f $(SERVER_BIN)
	rm -f coverage.out coverage.html
	rm -f /tmp/test_sandbox_config*.yaml
	docker system prune -f --filter "label=sandbox-test" 2>/dev/null || true
	podman system prune -f 2>/dev/null || true
