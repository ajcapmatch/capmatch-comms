#!/usr/bin/env bash
# Development run script for notify-fan-out service
# Usage: ./scripts/run-dev.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$SERVICE_ROOT"

echo "=========================================="
echo "Notify Fan-Out Service - Development Mode"
echo "=========================================="

# Load .env if present
if [ -f .env ]; then
    echo "Loading .env file..."
    set -a
    source .env
    set +a
fi

# Validate required environment variables
if [ -z "$SUPABASE_URL" ]; then
    echo "ERROR: SUPABASE_URL is not set"
    exit 1
fi

if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "ERROR: SUPABASE_SERVICE_ROLE_KEY is not set"
    exit 1
fi

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv sync
fi

echo ""
echo "Running notify-fan-out job (will process events and exit)..."
echo "=========================================="

uv run python main.py
