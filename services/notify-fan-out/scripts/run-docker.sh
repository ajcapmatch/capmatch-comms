#!/usr/bin/env bash
# Docker run script for notify-fan-out service
# Usage: ./scripts/run-docker.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SERVICE_ROOT/../.." && pwd)"

CONTAINER_NAME="capmatch-notify-fan-out"
IMAGE_NAME="capmatch-notify-fan-out:latest"

echo "=========================================="
echo "Notify Fan-Out Service - Docker"
echo "=========================================="

# Check if container is already running
if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo "Container $CONTAINER_NAME is already running."
    echo "Stop it first with: docker stop $CONTAINER_NAME"
    exit 1
fi

# Remove stopped container if exists
if docker ps -aq -f name="$CONTAINER_NAME" | grep -q .; then
    echo "Removing stopped container..."
    docker rm "$CONTAINER_NAME"
fi

# Build image from repo root
echo ""
echo "Building Docker image..."
docker build -f "$SERVICE_ROOT/Dockerfile" -t "$IMAGE_NAME" "$REPO_ROOT"

# Check for .env file
if [ ! -f "$SERVICE_ROOT/.env" ]; then
    echo ""
    echo "WARNING: .env file not found at $SERVICE_ROOT/.env"
    echo "Make sure environment variables are set before running."
fi

echo ""
echo "Starting container..."
docker run -d \
    --name "$CONTAINER_NAME" \
    --env-file "$SERVICE_ROOT/.env" \
    -p 8080:8080 \
    --restart unless-stopped \
    "$IMAGE_NAME"

echo ""
echo "=========================================="
echo "Container started successfully!"
echo "=========================================="
echo ""
echo "Service URL: http://localhost:8080"
echo "Webhook URL: http://localhost:8080/webhook"
echo ""
echo "View logs:   docker logs -f $CONTAINER_NAME"
echo "Stop:        docker stop $CONTAINER_NAME"
echo ""

