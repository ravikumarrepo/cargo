#!/bin/bash
# Cargo - Quick Start Script for macOS/Linux

echo ""
echo "========================================"
echo "  Cargo - Bulk Content Generator"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if dependencies are installed
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    echo ""
fi

# Start the application
echo "Starting Cargo..."
echo ""
echo "Open your browser and navigate to:"
echo "  http://localhost:5000"
echo ""
echo "Press CTRL+C to stop the server"
echo ""
python3 run.py
