#!/bin/bash
# EveCompiler IDE - Quick Start Script

echo "🔧 EveCompiler IDE — Setup & Start"
echo "===================================="
echo ""

cd "$(dirname "$0")" || exit

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found."
    exit 1
fi

# Setup virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q flask

echo ""
echo "✅ Setup complete!"
echo ""
echo "Choose an option:"
echo ""
echo "1) Run CLI compiler"
echo "2) Start Web UI (http://localhost:5000)"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "CLI Usage:"
        echo "  python cli.py <file.c> [--output output.asm] [--verbose]"
        echo ""
        echo "Examples:"
        echo "  python cli.py sample_programs/simple.c"
        echo "  python cli.py sample_programs/loop.c --verbose"
        echo "  python cli.py sample_programs/arithmetic.c --output out.asm"
        ;;
    2)
        echo ""
        echo "🚀 Starting Flask web server..."
        echo "📍 Open http://localhost:5000 in your browser"
        echo "⏹️  Press Ctrl+C to stop the server"
        echo ""
        python app.py
        ;;
    *)
        echo "Invalid choice"
        ;;
esac
