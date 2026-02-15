#!/bin/bash
# Single script to run the whole SmartShelf project - one command does everything

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# 1. Create and activate Python virtualenv
if [ ! -d "venv" ]; then
  echo "📦 Creating Python virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate

# 2. Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -q -r requirements.txt

# 3. Install frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
  echo "📦 Installing frontend dependencies..."
  (cd frontend && npm install)
fi

# 4. Free port 8002 if in use (e.g. from previous run)
if lsof -i :8002 >/dev/null 2>&1; then
  echo "⚠️  Port 8002 in use, freeing it..."
  lsof -ti :8002 | xargs kill -9 2>/dev/null || true
  sleep 2
fi

# 5. Start backend (port 8002) in background
echo "🚀 Starting backend on http://localhost:8002..."
python3 -m uvicorn copilot_chatbot.main:app --host 0.0.0.0 --port 8002 &
BACKEND_PID=$!

# Give backend time to start
sleep 3

# 6. Start frontend (port 3000)
echo "🚀 Starting frontend on http://localhost:3000..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

# Trap Ctrl+C to kill both processes
cleanup() {
  echo ""
  echo "Shutting down..."
  kill $BACKEND_PID 2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

# Wait for either process to exit
wait
