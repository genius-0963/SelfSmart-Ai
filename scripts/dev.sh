#!/bin/bash

# SmartShelf AI - Development Environment Script
# Starts all services in development mode

set -e

echo "🚀 Starting SmartShelf AI Development Environment..."

# Function to cleanup background processes
cleanup() {
    echo "🛑 Stopping all services..."
    jobs -p | xargs kill
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Run ./scripts/setup.sh first."
    exit 1
fi

# Start backend API
echo "🔧 Starting Backend API (port 8000)..."
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start Copilot service
echo "🤖 Starting AI Copilot (port 8001)..."
cd copilot_chatbot
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
COPILOT_PID=$!
cd ..

# Wait a moment for copilot to start
sleep 3

# Start frontend
echo "🎨 Starting Frontend (port 3000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "🎉 All services started successfully!"
echo ""
echo "🌐 Access points:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "- Copilot API: http://localhost:8001"
echo ""
echo "📝 Logs are being displayed in real-time."
echo "Press Ctrl+C to stop all services."

# Wait for all background jobs
wait
