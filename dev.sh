#!/bin/bash

# Face recognition system development mode startup script

echo "=================================="
echo "Facial recognition system - development mode"
echo "=================================="

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "Virtual environment does not exist，Please run first ./start_uv.sh or ./start.sh"
    exit 1
fi

# Activate virtual environment
echo "Activate virtual environment..."
source .venv/bin/activate

# Start the development server (Hot reload)
echo "Start the development server (Hot reload mode)..."
python main.py --reload --log-level DEBUG