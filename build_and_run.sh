#!/usr/bin/env bash
set -euo pipefail

DOCKERFILE_PATH="server/Dockerfile"
IMAGE_NAME="zerclone"
CONTAINER_NAME="zerclone_dev"

echo "Building ${IMAGE_NAME}…"
docker build -f "$DOCKERFILE_PATH" -t "$IMAGE_NAME" .

echo "Starting container ${CONTAINER_NAME} in detached mode…"
docker run --gpus all \
  -d \
  --name "$CONTAINER_NAME" \
  --rm \
  "$IMAGE_NAME" \
  sleep infinity

echo
echo "✅  Container is up. Attach a shell with:"
echo "    docker exec -it $CONTAINER_NAME bash"
