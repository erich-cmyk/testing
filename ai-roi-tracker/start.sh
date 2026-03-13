#!/bin/bash
set -e

echo "=== AI ROI Tracker ==="

# Backend
echo "[1/4] Installing backend dependencies..."
cd "$(dirname "$0")/backend"
pip install -r requirements.txt -q

echo "[2/4] Seeding demo data..."
python seed.py 2>/dev/null || true

echo "[3/4] Starting backend..."
uvicorn main:app --port 8000 &
BACKEND_PID=$!

# Frontend
echo "[4/4] Installing & starting frontend..."
cd ../frontend
npm install --silent
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✓ Running! Open http://localhost:5173 in your browser."
echo "  Press Ctrl+C to stop everything."
echo ""

# Stop both on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
