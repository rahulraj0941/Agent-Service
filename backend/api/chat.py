from fastapi import APIRouter, HTTPException
from typing import List, Dict
from backend.models.schemas import ChatRequest, ChatResponse, ChatMessage
from backend.agent.scheduling_agent import SchedulingAgent

router = APIRouter(prefix="/api", tags=["chat"])

agent = None


def get_agent():
    global agent
    if agent is None:
        agent = SchedulingAgent()
    return agent


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        current_agent = get_agent()
        history: List[Dict[str, str]] = [
            {"role": msg.role, "content": msg.content} 
            for msg in (request.conversation_history or [])
        ]
        result = await current_agent.process_message(
            user_message=request.message,
            conversation_history=history
        )
        
        conversation_history = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in result["conversation_history"]
        ]
        
        return ChatResponse(
            response=result["response"],
            conversation_history=conversation_history,
            metadata=result.get("metadata")
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Medical Appointment Scheduling Agent",
        "version": "1.0.0"
    }
