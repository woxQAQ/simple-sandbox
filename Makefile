REGISTRY ?= docker.io
APISERVER_IMAGE ?= woxqaq/sandbox-apiserver
PYTHON_RUNTIME_IMAGE ?= woxqaq/sandbox-python
NODE_RUNTIME_IMAGE ?= woxqaq/sandbox-node
VERSION = latest
BUILDX_PLATFORM ?= linux/amd64,linux/arm64
BUILDX_ARGS ?= --sbom=false --provenance=false

.PHONY: setup-builder clean-builder
setup-builder:
	@if ! docker buildx inspect multi-platform >/dev/null 2>&1; then \
		docker buildx create --name multi-platform --use --driver docker-container --bootstrap; \
	else \
		docker buildx use multi-platform; \
	fi

clean-builder:
	@if docker buildx inspect multi-platform >/dev/null 2>&1; then \
		docker buildx rm multi-platform; \
	fi

build-apiserver: setup-builder
	docker buildx build -t $(REGISTRY)/$(APISERVER_IMAGE):$(VERSION) \
		--platform $(BUILDX_PLATFORM) $(BUILDX_ARGS) --push \
		-f ./docker/apiserver/Dockerfile .

build-python-runtime: setup-builder
	docker buildx build -t $(REGISTRY)/$(PYTHON_RUNTIME_IMAGE):$(VERSION) \
		--platform $(BUILDX_PLATFORM) $(BUILDX_ARGS) --push \
		-f ./docker/runtimes/python/Dockerfile .

build-node-runtime: setup-builder
	docker buildx build -t $(REGISTRY)/$(NODE_RUNTIME_IMAGE):$(VERSION) \
		--platform $(BUILDX_PLATFORM) $(BUILDX_ARGS) --push \
		-f ./docker/runtimes/node/Dockerfile .
