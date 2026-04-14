#!/bin/bash
# Start ACE-Step UI (both frontend and backend)

set -e

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# ============= ACE-Step Configuration | ACE-Step 配置 =============
# Set ACE-Step installation path (parent directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACESTEP_PATH="${ACESTEP_PATH:-$(dirname "$SCRIPT_DIR")}"
# Set Python executable path (virtual environment)
if [ -z "$PYTHON_PATH" ]; then
    if [ -f "$ACESTEP_PATH/.venv/bin/python" ]; then
        PYTHON_PATH="$ACESTEP_PATH/.venv/bin/python"
    elif [ -f "$ACESTEP_PATH/venv/bin/python" ]; then
        PYTHON_PATH="$ACESTEP_PATH/venv/bin/python"
    fi
fi

if [ ! -d "$ACESTEP_PATH" ]; then
    echo "Error: ACE-Step not found at $ACESTEP_PATH"
    echo "Set ACESTEP_PATH or run ./setup.sh first."
    exit 1
fi

echo "Starting ACE-Step UI..."
echo "ACE-Step Path: $ACESTEP_PATH"
echo "Python Path:   ${PYTHON_PATH:-not found}"
echo ""

# Start backend in background
echo "Starting backend on port ${PORT:-3001}..."
cd server
npm run dev &
BACKEND_PID=$!
cd ..

# Wait for backend
sleep 3

# Start frontend
echo "Starting frontend on port ${FRONTEND_PORT:-3000}..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=================================="
echo "  ACE-Step UI Running"
echo "=================================="
echo ""
echo "  Frontend: http://localhost:${FRONTEND_PORT:-3000}"
echo "  Backend:  http://localhost:${PORT:-3001}"
echo ""
echo "Press Ctrl+C to stop..."

# Handle shutdown
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

# Wait for processes
wait
