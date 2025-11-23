#!/bin/bash

# Use Replit's PORT environment variable (falls back to 5000 if not set)
# This ensures the server binds to whatever port Replit's routing expects
PORT=${PORT:-5000}

cd /home/runner/workspace
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT --reload
