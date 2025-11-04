#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Navigate to the auth service directory
# From: backend/scripts/services/auth/
# To: backend/services/auth_service/
cd "$SCRIPT_DIR/../../../services/auth_service" || exit 1

echo "Starting Auth Service on port 8001..."
echo "Working directory: $(pwd)"
echo "Adding shared modules to PYTHONPATH..."
echo ""

# Set PYTHONPATH to include shared modules
export PYTHONPATH="../../shared:$PYTHONPATH"

# Start the service
poetry run uvicorn app.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8001
