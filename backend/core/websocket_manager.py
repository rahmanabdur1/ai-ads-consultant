# backend/core/websocket_manager.py

from fastapi import WebSocket
from typing import Dict, List
import json

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.connections:
            self.connections[session_id] = []
        self.connections[session_id].append(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.connections:
            self.connections[session_id].remove(websocket)
            if not self.connections[session_id]:
                del self.connections[session_id]

    async def send(self, session_id: str, data: dict):
        if session_id in self.connections:
            dead = []
            for ws in self.connections[session_id]:
                try:
                    await ws.send_text(json.dumps(data))
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.connections[session_id].remove(ws)

    async def broadcast_agent_step(self, session_id: str, agent: str,
                                    status: str, message: str, data: dict = {}):
        await self.send(session_id, {
            "type": "agent_step",
            "agent": agent,
            "status": status,   # started / running / completed / failed
            "message": message,
            "data": data
        })

    async def broadcast_error(self, session_id: str, error: str):
        await self.send(session_id, {"type": "error", "message": error})

    async def broadcast_done(self, session_id: str, result: dict):
        await self.send(session_id, {"type": "done", "result": result})

ws_manager = WebSocketManager()