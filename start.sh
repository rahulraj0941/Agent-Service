#!/bin/bash

cd /home/runner/workspace/frontend && npm run dev &
FRONTEND_PID=$!

sleep 5

cd /home/runner/workspace && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

wait $FRONTEND_PID $BACKEND_PID
