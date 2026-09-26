# Stage 1 Service Execution

To build and run the Stage 1 service under clean-room zero network egress:

```bash
# Build static container
docker build -t pocketful:stage1 ./stage-1

# Run container with zero network egress
docker run --rm --network none -p 8080:8080 pocketful:stage1
```
