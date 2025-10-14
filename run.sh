#!/bin/bash
# Script for running OLX parser

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    /usr/local/bin/python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Copy env.example to .env and configure parameters:"
    echo "cp env.example .env"
    exit 1
fi

# Run parser
echo "🚀 Starting multi-site parser (OLX + Otodom)..."
python multi_parser.py

# Deactivate (if script completed)
deactivate

