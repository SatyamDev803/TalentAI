#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$SCRIPT_DIR/../../../services/matching_engine_service" || exit 1

echo "Starting Matching Engine Service on port 8004..."
echo "Working directory: $(pwd)"
echo "Adding shared modules to PYTHONPATH..."
echo ""

# Set PYTHONPATH to include shared modules
export PYTHONPATH="../../shared:$PYTHONPATH"

# Start the service
poetry run uvicorn app.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8004
