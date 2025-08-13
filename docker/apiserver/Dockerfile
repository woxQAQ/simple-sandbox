FROM golang:1.24-alpine AS build

# 添加构建参数以支持多目标构建
ARG TARGETOS
ARG TARGETARCH

WORKDIR /src
COPY . .
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=${TARGETOS:-linux} GOARCH=${TARGETARCH:-amd64} go build -o /out/sandboxd -ldflags "-s -w" ./cmd/sandboxd

FROM gcr.io/distroless/static:nonroot
USER nonroot:nonroot
COPY --from=build /out/sandboxd /sandboxd
COPY --from=build /src/config/sandbox.yaml.example /sandbox.yaml
EXPOSE 8080
ENTRYPOINT ["/sandboxd","-addr",":8080"]