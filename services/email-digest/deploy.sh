#!/usr/bin/env bash
# Deployment script for Email Digest Worker
# Use this to update the worker after pulling new code
# Usage: ./deploy.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Email Digest Worker - Deployment"
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
docker build -t capmatch-email-digest:prod .
echo "✓ Docker image rebuilt"

echo ""
echo "Step 3: Verifying .env file exists..."
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "   Make sure your environment variables are set before running the worker."
else
    echo "✓ .env file found"
fi

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "To test the worker:"
echo "  ./run-email-digest.sh"
echo ""
echo "To view logs:"
echo "  tail -f /var/log/email-digest.log"
echo ""

