#!/bin/bash

# Start backend on port 5000 (required for Replit webview) - it now serves both API and frontend
cd /home/runner/workspace
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port 5000 --reload
