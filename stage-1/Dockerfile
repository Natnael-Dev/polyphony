# Multi-stage zero-egress static Go build
# Stage 1: Build static Go binary with pure-Go SQLite
FROM golang:alpine AS builder

WORKDIR /build

# Pre-copy module manifests for optimal layer caching
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Compile fully static standalone binary (CGO_ENABLED=0, -p 1 to cap memory usage)
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -p 1 \
    -ldflags="-s -w -extldflags '-static'" \
    -tags "timetzdata" \
    -o /app/server .

# Stage 2: Minimal zero-egress runtime
FROM alpine:3.20

# Create non-root user and ensure /data is writable
RUN adduser -D -u 1000 appuser && \
    mkdir -p /data && \
    chown -R appuser:appuser /data

WORKDIR /app

# Copy static binary from builder stage
COPY --from=builder /app/server /app/server

# Service environment
ENV PORT=8080
ENV DATABASE_PATH=/data/app.db

USER appuser

EXPOSE 8080

ENTRYPOINT ["/app/server"]
