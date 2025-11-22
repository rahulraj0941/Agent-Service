from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatRequest, ChatResponse
from backend.agent.scheduling_agent import SchedulingAgent

router = APIRouter(prefix="/api", tags=["chat"])

agent = SchedulingAgent()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await agent.process_message(
            user_message=request.message,
            conversation_history=request.conversation_history or []
        )
        
        return ChatResponse(
            response=result["response"],
            conversation_history=result["conversation_history"],
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
