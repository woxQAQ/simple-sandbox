FROM --platform=$BUILDPLATFORM golang:1.24-alpine AS build

# 添加构建参数以支持多目标构建
ARG TARGETOS
ARG TARGETARCH

WORKDIR /src

# 先复制 go.mod 和 go.sum 以利用 Docker 层缓存
COPY go.mod go.sum ./

# 使用缓存挂载优化依赖下载速度
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go mod download

# 复制源代码
COPY . .

# 使用缓存挂载优化构建速度
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=${TARGETOS:-linux} GOARCH=${TARGETARCH:-amd64} \
    go build -o /out/sandboxd -ldflags "-s -w" ./cmd/sandboxd/main.go

FROM gcr.io/distroless/static:nonroot
USER nonroot:nonroot
COPY --from=build /out/sandboxd /sandboxd
COPY --from=build /src/config/sandbox.example.yaml /sandbox.yaml
EXPOSE 8080
ENTRYPOINT ["/sandboxd","-addr",":8080"]