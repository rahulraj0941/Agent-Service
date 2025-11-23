#!/bin/bash

# Start the backend server on MULTIPLE ports simultaneously
# This works around the .replit duplicate port configuration issue
# by listening on ALL the ports that .replit has configured for external port 80

cd /home/runner/workspace

echo "Starting Medical Appointment Scheduling Agent on multiple ports..."
echo "This ensures the app is accessible regardless of Replit's routing choice"

# Start on port 5000 (primary)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 5000 --reload &
PID1=$!

# Start on port 41273 (the duplicate port that's causing issues)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 41273 &
PID2=$!

echo "Server started on ports 5000 (PID: $PID1) and 41273 (PID: $PID2)"
echo "App will be accessible on either port!"

# Wait for both processes
wait $PID1 $PID2
