# backend/api/ws_agent.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.websocket_manager import ws_manager
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from agents.research_agent import ResearchAgent
from agents.strategy_agent import StrategyAgent
from agents.copywriting_agent import CopywritingAgent
from agents.validator_agent import ValidatorAgent
from memory.short_term import ShortTermMemory
from memory.vector_memory import VectorMemory
from core.config import settings
import json, asyncio

router = APIRouter()

@router.websocket("/ws/agent/{session_id}")
async def agent_websocket(websocket: WebSocket, session_id: str):
    await ws_manager.connect(session_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") == "run_agent":
                await run_streaming_agent(session_id, data)
            elif data.get("type") == "chat":
                await run_streaming_chat(session_id, data)
            elif data.get("type") == "ping":
                await ws_manager.send(session_id, {"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(session_id, websocket)

async def run_streaming_agent(session_id: str, payload: dict):
    state = {
        "user_input": payload["message"],
        "budget": payload.get("budget"),
        "platform": payload.get("platform", "google"),
        "goal": payload.get("goal", "conversions"),
        "tone": payload.get("tone", "professional"),
        "workspace_id": payload["workspace_id"],
        "session_id": session_id,
        "agent_log": []
    }

    agents = [
        ("Research Agent",     "🔍 Analyzing market trends and audience...",   ResearchAgent()),
        ("Strategy Agent",     "📋 Building campaign strategy...",              StrategyAgent()),
        ("Copywriting Agent",  "✍️  Writing ad copy and headlines...",          CopywritingAgent()),
        ("Validator Agent",    "✅ Validating output quality...",               ValidatorAgent()),
    ]

    try:
        for agent_name, message, agent in agents:
            await ws_manager.broadcast_agent_step(session_id, agent_name, "started", message)
            await asyncio.sleep(0.1)

            loop = asyncio.get_event_loop()
            state = await loop.run_in_executor(None, agent.run, state)

            await ws_manager.broadcast_agent_step(
                session_id, agent_name, "completed",
                f"{agent_name} finished",
                {"output": list(state.values())[-2] if state else ""}
            )

        await ws_manager.broadcast_done(session_id, {
            "research": state.get("research"),
            "strategy": state.get("strategy"),
            "ad_copy": state.get("ad_copy"),
            "validation": state.get("validation"),
            "agent_log": state.get("agent_log"),
        })

    except Exception as e:
        await ws_manager.broadcast_error(session_id, str(e))

async def run_streaming_chat(session_id: str, payload: dict):
    mem = ShortTermMemory()
    vec = VectorMemory()
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        streaming=True
    )

    await ws_manager.send(session_id, {"type": "chat_start"})

    history = mem.get_context(session_id)
    relevant = vec.search(payload["workspace_id"], payload["message"])
    context = "\n".join([r.get("text", "") for r in relevant])

    messages = [
        SystemMessage(content=f"You are an AI advertising consultant.\nContext:\n{context}"),
        *[HumanMessage(content=m["content"]) if m["role"] == "user"
          else SystemMessage(content=m["content"]) for m in history[-10:]],
        HumanMessage(content=payload["message"])
    ]

    full_response = ""
    async for chunk in llm.astream(messages):
        token = chunk.content
        full_response += token
        await ws_manager.send(session_id, {"type": "chat_token", "token": token})

    await ws_manager.send(session_id, {"type": "chat_end", "full": full_response})
    mem.add_context(session_id, {"role": "user", "content": payload["message"]})
    mem.add_context(session_id, {"role": "assistant", "content": full_response})

# Add to main.py:
# from api.ws_agent import router as ws_router
# app.include_router(ws_router, tags=["WebSocket"])