# syntax=docker/dockerfile:1
FROM golang:1.24-alpine AS build
WORKDIR /src
COPY . .
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/sandboxd -ldflags "-s -w" ./cmd/sandboxd

FROM gcr.io/distroless/static:nonroot
USER nonroot:nonroot
COPY --from=build /out/sandboxd /sandboxd
EXPOSE 8080
ENTRYPOINT ["/sandboxd","-addr",":8080"] 