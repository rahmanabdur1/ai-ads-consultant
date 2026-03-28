# backend/memory/short_term.py

import redis
import json
from core.config import settings

class ShortTermMemory:
    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL)
        self.ttl = 3600  # 1 hour

    def set(self, key: str, value: dict):
        self.client.setex(key, self.ttl, json.dumps(value))

    def get(self, key: str) -> dict:
        data = self.client.get(key)
        return json.loads(data) if data else {}

    def delete(self, key: str):
        self.client.delete(key)

    def add_context(self, session_id: str, message: dict):
        key = f"context:{session_id}"
        history = self.get(key).get("messages", [])
        history.append(message)
        self.set(key, {"messages": history[-20:]})  # keep last 20

    def get_context(self, session_id: str) -> list:
        return self.get(f"context:{session_id}").get("messages", [])