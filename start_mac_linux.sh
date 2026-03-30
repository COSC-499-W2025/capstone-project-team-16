#!/bin/bash

# --- Cleanup function to be called on exit ---
cleanup() {
    echo "Shutting down..."
    if [ -n "$API_PID" ]; then
        kill $API_PID
    fi
}

# --- Trap signals to ensure cleanup runs ---
trap cleanup EXIT INT TERM

# Check for python3
if ! command -v python3 &> /dev/null
then
    echo "[ERROR] python3 could not be found."
    echo "Please install Python 3 and make sure 'python3' is in your PATH."
    exit 1
fi

# Check for npm
if ! command -v npm &> /dev/null; then
    echo "[ERROR] Node.js/npm could not be found."
    echo "Please install Node.js (which includes npm) and try again."
    exit 1
fi

echo "=========================================="
echo "Starting Skill Scope (Mac/Linux)"
echo "=========================================="

echo "[1/3] Installing Python dependencies..."
python3 -m pip install -r requirements.txt

echo "[2/3] Starting Backend API in the background on port 8000..."
export PORT=8000
export SKILLSCOPE_API_URL=http://127.0.0.1:8000
python3 src/api.py &
API_PID=$!

echo "[3/3] Starting Frontend UI..."
cd src/ui
export VITE_API_BASE_URL=http://127.0.0.1:8000
export REACT_APP_API_URL=http://127.0.0.1:8000
npm install
npm run dev