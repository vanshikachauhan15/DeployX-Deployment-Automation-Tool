#!/bin/bash

# Deployment Automation Tool Setup Script

echo "🚀 Deployment Automation Tool - Setup"
echo "======================================"
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [ -z "$python_version" ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi
echo "✅ Python version: $python_version"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please edit .env file and add your GitHub credentials!"
else
    echo "✅ .env file already exists"
fi
echo ""

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p deployments
mkdir -p logs
echo "✅ Directories created"
echo ""

echo "✨ Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your GitHub credentials"
echo "2. Edit core/default.env with your database/API credentials"
echo "3. Run: python app/routes.py"
echo "4. Open http://localhost:5000 in your browser"
echo ""

