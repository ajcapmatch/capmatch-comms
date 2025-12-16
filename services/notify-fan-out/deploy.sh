#!/usr/bin/env bash
# Deployment script for Notify Fan-Out Service
# Use this to update the service after pulling new code
# Usage: ./deploy.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Notify Fan-Out Service - Deployment"
echo "=========================================="

# Find git root (where .git directory actually is)
GIT_ROOT="$SCRIPT_DIR"
while [ "$GIT_ROOT" != "/" ] && [ ! -d "$GIT_ROOT/.git" ]; do
    GIT_ROOT="$(dirname "$GIT_ROOT")"
done

# Check if we found a git repo and can pull
if [ -d "$GIT_ROOT/.git" ]; then
    echo ""
    echo "Step 1: Pulling latest code from $GIT_ROOT..."
    cd "$GIT_ROOT"
    git pull
    echo "✓ Code updated"
    cd "$SCRIPT_DIR"
else
    echo ""
    echo "⚠️  Not a git repository, skipping git pull"
fi

echo ""
echo "Step 2: Rebuilding Docker image..."
if [ -d "$GIT_ROOT/.git" ]; then
    # Building from repo root (preferred case)
    docker build -f "$GIT_ROOT/services/notify-fan-out/Dockerfile" -t capmatch-notify-fan-out:prod "$GIT_ROOT"
else
    # Fallback: build from this service directory only
    docker build -f "$SCRIPT_DIR/Dockerfile" -t capmatch-notify-fan-out:prod "$SCRIPT_DIR"
fi
echo "✓ Docker image rebuilt"

echo ""
echo "Step 3: Verifying .env file exists..."
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "   Make sure your environment variables are set before running the service."
else
    echo "✓ .env file found"
fi

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "To test the service:"
echo "  ./run-notify-fan-out.sh"
echo ""
echo "To view logs:"
echo "  tail -f /var/log/notify-fan-out.log"
echo ""

