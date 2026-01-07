#!/bin/bash
# Quick start script for Polymarket BTC Monitor

echo "🚀 Starting Polymarket BTC Monitor..."
echo ""

# Check if Python 3.12+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    exit 1
fi

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.12"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "⚠️  Warning: Python $required_version+ recommended (you have $python_version)"
fi

# Check if dependencies are installed
if ! python3 -c "import polymarket_apis" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "ℹ️  Edit .env to configure alerts and notifications"
fi

# Run the monitor
echo "✅ Launching monitor..."
echo ""
python3 main.py
