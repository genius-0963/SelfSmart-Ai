#!/bin/bash

# Quick Start Script for SmartShelf AI (No Docker Required)
echo "🚀 SmartShelf AI - Quick Start Setup"
echo "===================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3.11+"
    echo "   Visit: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required. Please install Node.js 18+"
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"

# Create virtual environment
echo ""
echo "📦 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.minimal.txt

# Install frontend dependencies
echo "🎨 Installing frontend packages..."
cd frontend
npm install
cd ..

# Create directories
echo "📁 Creating directories..."
mkdir -p logs data/vector_store

# Create environment file
echo "🔧 Creating environment file..."
cat > .env << EOF
# SmartShelf AI Configuration
DATABASE_URL=sqlite:///./smartshelf.db

# API Keys (get these from the respective services)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here

# Security
SECRET_KEY=change-this-secret-key-in-production
ENVIRONMENT=development

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/smartshelf.log
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next Steps:"
echo "1. Edit .env file and add your actual API keys"
echo "2. Start backend: ./start_backend.sh"
echo "3. Start frontend: ./start_frontend.sh"
echo "4. Open browser to: http://localhost:3000"
echo ""
echo "📖 API Documentation: http://localhost:8001/docs"
echo ""
echo "⚠️  Note: This is a minimal setup. For full features (Redis, monitoring, etc.),"
echo "   install Docker Desktop and use: docker-compose -f docker-compose.enhanced.yml up"
