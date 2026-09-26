# Stage 1 Dockerfile - Zero-Egress Production Build
FROM golang:1.24-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /pocketful-stage1 .

FROM alpine:3.21
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /pocketful-stage1 .

EXPOSE 8080
CMD ["./pocketful-stage1"]
