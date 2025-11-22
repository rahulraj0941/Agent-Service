from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatRequest, ChatResponse
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
        result = await current_agent.process_message(
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
