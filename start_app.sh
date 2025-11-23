#!/bin/bash

# Medical Appointment Scheduling Agent Start Script
echo "Starting Medical Appointment Scheduling Agent..."

# Build the frontend first if dist doesn't exist
if [ ! -d "frontend/dist" ]; then
    echo "Building frontend..."
    cd frontend && npm run build && cd ..
fi

# Start the backend server on port 5000 (Replit webview port)
echo "Starting backend server on port 5000..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 5000 --reload
