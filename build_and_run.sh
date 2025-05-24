#!/usr/bin/env bash
set -euo pipefail

DOCKERFILE_PATH="server/Dockerfile"
IMAGE_NAME="zerclone"
CONTAINER_NAME="zerclone_dev"

echo "Building image ${IMAGE_NAME}…"
docker build -f "${DOCKERFILE_PATH}" -t "${IMAGE_NAME}" .

echo "Launching container '${CONTAINER_NAME}' in detached mode with GPU access…"
docker run --gpus all \
  -d \                         # detached mode
  --name "${CONTAINER_NAME}" \
  --rm \                       # remove on stop (optional)
  "${IMAGE_NAME}" \
  sleep infinity

echo
echo "✅ Container '${CONTAINER_NAME}' is up and running."
echo "   To get a shell in it, run:"
echo "     docker exec -it ${CONTAINER_NAME} bash"
