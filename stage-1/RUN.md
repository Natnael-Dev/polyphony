# Stage 1: Pure-Go SQLite Zero-Egress Service

## Overview
Stage 1 provides a minimal HTTP service backed by a pure-Go SQLite engine (`modernc.org/sqlite`) engineered for zero runtime network dependencies.

## Build Instructions
Build the multi-stage static container image:
```bash
docker build -t factory-stage1 stage-1/
```

## Run Instructions (Zero Outbound Network)
Run the service inside a container with outbound networking completely disabled:
```bash
docker run --rm --network none -p 8080:8080 factory-stage1
```

## Health Verification
Verify endpoint health:
```bash
curl http://localhost:8080/health
```

Expected response:
```json
{"status":"ok","database":"connected"}
```
