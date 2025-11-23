#!/bin/bash

# Start backend in background
cd /home/runner/workspace
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Give backend time to start
sleep 2

# Start frontend in foreground (this keeps the script alive and allows Replit to detect the port)
cd /home/runner/workspace/frontend
exec npm run dev
