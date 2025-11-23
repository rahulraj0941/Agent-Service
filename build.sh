#!/bin/bash

# Render Build Script for Medical Appointment Scheduling Agent
# This script builds the React frontend and installs Python dependencies

set -e  # Exit on error

echo "========================================="
echo "Starting Render Build Process"
echo "========================================="

# Build the React frontend
echo "Building React frontend..."
cd frontend
npm install
npm run build
cd ..

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "========================================="
echo "Build Complete!"
echo "========================================="
