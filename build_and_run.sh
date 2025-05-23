#!/usr/bin/env bash
set -euo pipefail

# Path to your Dockerfile (relative or absolute)
DOCKERFILE_PATH="server/Dockerfile"

# Name:tag for your image
IMAGE_NAME="zerclone"

echo "Building image ${IMAGE_NAME} using Dockerfile at ${DOCKERFILE_PATH}…"
docker build \
  -f "${DOCKERFILE_PATH}" \
  -t "${IMAGE_NAME}" \
  .

echo "Launching container with GPU access…"
docker run --gpus all -it --rm \
  "${IMAGE_NAME}" \
  bash
