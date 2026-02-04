#!/bin/bash
# Build script for Voice of Engineering Blog Aggregator

echo "Starting blog aggregation and build process..."

# Step 1: Aggregate RSS feeds
echo "Step 1: Fetching RSS feeds..."
cd "$(dirname "$0")/../.." || exit 1
.venv/bin/python scripts/aggregate_feeds/main.py

if [ $? -ne 0 ]; then
    echo "Warning: Feed aggregation encountered errors, but continuing..."
fi

# Step 2: Build Hugo site
echo ""
echo "Step 2: Building Hugo site..."
hugo

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Build completed successfully!"
    echo "  Site generated in ./public/"
else
    echo "✗ Hugo build failed"
    exit 1
fi
