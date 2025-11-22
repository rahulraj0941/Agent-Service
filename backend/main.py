from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import chat, calendly_integration
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Medical Appointment Scheduling Agent",
    description="Intelligent conversational agent for scheduling medical appointments",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(calendly_integration.router)


@app.get("/")
async def root():
    return {
        "message": "Medical Appointment Scheduling Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
