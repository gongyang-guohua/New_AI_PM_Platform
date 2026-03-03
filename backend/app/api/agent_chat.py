# backend/app/api/agent_chat.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from ai_agents.master_agent.router import MasterRouter

router = APIRouter()
# Instantiate the router (in production this would be handled by DI or dependency injection with memory layer)
agent_router = MasterRouter()

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    project_id: Optional[int] = None

class ChatResponse(BaseModel):
    reply: str
    thread_id: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Entrypoint for frontend to interact with the LangGraph Master Agent.
    """
    try:
        # Wrap message in LLM generic format
        messages = [{"role": "user", "content": request.message}]
        
        # Invoke LangGraph
        response_text = agent_router.process(messages)
        
        return ChatResponse(
            reply=response_text,
            thread_id=request.thread_id or "new_thread_123"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
