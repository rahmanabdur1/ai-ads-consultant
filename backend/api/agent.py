# backend/api/agent.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from core.orchestrator import Orchestrator
from typing import Optional
import json

router = APIRouter()
orchestrator = Orchestrator()

class AgentRunRequest(BaseModel):
    message: str
    workspace_id: str
    session_id: str
    budget: Optional[float] = None
    platform: Optional[str] = "google"
    goal: Optional[str] = "conversions"
    tone: Optional[str] = "professional"

class ChatRequest(BaseModel):
    message: str
    session_id: str
    workspace_id: str

@router.post("/run")
async def run_agent(data: AgentRunRequest):
    try:
        result = await orchestrator.run(data.dict())
        return {
            "status": "success",
            "research": result.get("research"),
            "strategy": result.get("strategy"),
            "ad_copy": result.get("ad_copy"),
            "validation": result.get("validation"),
            "agent_log": result.get("agent_log"),
            "approved": result.get("approved")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat(data: ChatRequest):
    from memory.short_term import ShortTermMemory
    from memory.vector_memory import VectorMemory
    from langchain_openai import ChatOpenAI
    from langchain.schema import SystemMessage, HumanMessage
    from core.config import settings

    mem = ShortTermMemory()
    vec = VectorMemory()
    llm = ChatOpenAI(model=settings.OPENAI_MODEL, openai_api_key=settings.OPENAI_API_KEY)

    history = mem.get_context(data.session_id)
    relevant = vec.search(data.workspace_id, data.message)
    context = "\n".join([r.get("text", "") for r in relevant])

    messages = [
        SystemMessage(content=f"You are an AI advertising consultant. Context from past campaigns:\n{context}"),
        *[HumanMessage(content=m["content"]) if m["role"] == "user" else SystemMessage(content=m["content"]) for m in history[-10:]],
        HumanMessage(content=data.message)
    ]

    response = llm(messages)
    mem.add_context(data.session_id, {"role": "user", "content": data.message})
    mem.add_context(data.session_id, {"role": "assistant", "content": response.content})
    return {"reply": response.content}