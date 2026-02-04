#!/bin/bash
set -euo pipefail

# Build script for Voice of Engineering Blog Aggregator

echo "Starting blog aggregation and build process..."

# Step 1: Aggregate RSS feeds
echo "Step 1: Fetching RSS feeds..."
cd "$(dirname "$0")/../.." || exit 1

# Use venv Python if available, otherwise use system Python
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD scripts/aggregate_feeds/main.py

# Step 2: Build Hugo site
echo ""
echo "Step 2: Building Hugo site..."
hugo

echo ""
echo "✓ Build completed successfully!"
echo "  Site generated in ./public/"
