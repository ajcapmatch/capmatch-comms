#!/usr/bin/env bash
# Deployment script for Invite Email Worker
# Use this to update the worker after pulling new code
# Usage: ./scripts/deploy.sh

set -e

# Get the directory where this script is located (scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the service root directory (parent of scripts/)
SERVICE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "Invite Email Worker - Deployment"
echo "=========================================="

# Find git root (where .git directory actually is)
GIT_ROOT="$SERVICE_ROOT"
while [ "$GIT_ROOT" != "/" ] && [ ! -d "$GIT_ROOT/.git" ]; do
    GIT_ROOT="$(dirname "$GIT_ROOT")"
done

# Check if we found a git repo and can pull
if [ -d "$GIT_ROOT/.git" ]; then
    echo ""
    echo "Step 1: Pulling latest code from $GIT_ROOT..."
    cd "$GIT_ROOT"
    # Try to pull, but continue if upstream isn't configured
    if git pull 2>/dev/null; then
        echo "✓ Code updated"
    else
        echo "⚠️  Could not pull (no upstream branch configured or network issue)"
        echo "   Continuing with local code..."
    fi
    cd "$SERVICE_ROOT"
else
    echo ""
    echo "⚠️  Not a git repository, skipping git pull"
fi

echo ""
echo "Step 2: Rebuilding Docker image..."
if [ -d "$GIT_ROOT/.git" ]; then
    # Building from repo root (preferred case)
    docker build -f "$GIT_ROOT/services/invite-email/Dockerfile" -t capmatch-invite-email:prod "$GIT_ROOT"
else
    # Fallback: build from this service directory only
    docker build -f "$SERVICE_ROOT/Dockerfile" -t capmatch-invite-email:prod "$SERVICE_ROOT"
fi
echo "✓ Docker image rebuilt"

echo ""
echo "Step 3: Verifying .env file exists..."
if [ ! -f "$SERVICE_ROOT/.env" ]; then
    echo "⚠️  WARNING: .env file not found in $SERVICE_ROOT!"
    echo "   Make sure your environment variables are set before running the worker."
else
    echo "✓ .env file found"
fi

echo ""
echo "Step 4: Checking if daemon is running..."
CONTAINER_NAME="capmatch-invite-email"
DOCKER_BIN="$(command -v docker || true)"
if [ -n "$DOCKER_BIN" ] && "$DOCKER_BIN" ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo "⚠️  Daemon container is currently running."
    echo "   To restart with new image:"
    echo "     docker stop $CONTAINER_NAME"
    echo "     ./scripts/run-invite-email.sh"
else
    echo "✓ Daemon is not running (will start fresh on next run)"
fi

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "To start the daemon:"
echo "  ./scripts/run-invite-email.sh"
echo ""
echo "To view logs:"
echo "  docker logs -f capmatch-invite-email"
echo ""
echo "To stop the daemon:"
echo "  docker stop capmatch-invite-email"
echo ""

