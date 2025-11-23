#!/usr/bin/env python3
"""
Simple single-file server that serves the app on port 5000
This bypasses any port configuration issues
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.api import chat, calendly_integration
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI(
    title="Medical Appointment Scheduling Agent",
    description="Intelligent conversational agent for scheduling medical appointments",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(chat.router)
app.include_router(calendly_integration.router)

# Serve static files
static_dir = Path(__file__).parent / "frontend" / "dist"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

@app.get("/")
async def root():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Medical Appointment Scheduling Agent API", "version": "1.0.0"}

if __name__ == "__main__":
    # Run on port 5000 as required by Replit webview
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
