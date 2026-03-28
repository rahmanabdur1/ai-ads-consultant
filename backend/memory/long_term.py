# backend/memory/long_term.py

import json
from datetime import datetime
from sqlalchemy.orm import Session
from core.database import SessionLocal, MemoryLog
import uuid

class LongTermMemory:
    def __init__(self):
        pass

    def store_fact(self, workspace_id: str, data: dict, memory_type: str = "fact") -> str:
        db = SessionLocal()
        try:
            record = MemoryLog(
                id=uuid.uuid4(),
                workspace_id=workspace_id,
                memory_type=memory_type,
                content=json.dumps(data),
                roi_score=data.get("roi_score", 0.0)
            )
            db.add(record)
            db.commit()
            return str(record.id)
        finally:
            db.close()

    def get_workspace_facts(self, workspace_id: str, memory_type: str = None,
                             limit: int = 20) -> list:
        db = SessionLocal()
        try:
            query = db.query(MemoryLog).filter(MemoryLog.workspace_id == workspace_id)
            if memory_type:
                query = query.filter(MemoryLog.memory_type == memory_type)
            records = query.order_by(MemoryLog.created_at.desc()).limit(limit).all()
            results = []
            for r in records:
                try:
                    content = json.loads(r.content)
                except:
                    content = {"raw": r.content}
                results.append({
                    "id": str(r.id),
                    "type": r.memory_type,
                    "content": content,
                    "roi_score": r.roi_score,
                    "created_at": r.created_at.isoformat()
                })
            return results
        finally:
            db.close()

    def update_roi_score(self, memory_id: str, roi_score: float):
        db = SessionLocal()
        try:
            record = db.query(MemoryLog).filter(MemoryLog.id == memory_id).first()
            if record:
                record.roi_score = roi_score
                db.commit()
        finally:
            db.close()

    def get_top_performing(self, workspace_id: str, top_k: int = 5) -> list:
        db = SessionLocal()
        try:
            records = db.query(MemoryLog).filter(
                MemoryLog.workspace_id == workspace_id,
                MemoryLog.roi_score > 0
            ).order_by(MemoryLog.roi_score.desc()).limit(top_k).all()
            return [
                {"content": json.loads(r.content), "roi_score": r.roi_score}
                for r in records
            ]
        finally:
            db.close()

    def delete_old_memories(self, workspace_id: str, keep_days: int = 90):
        from datetime import timedelta
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=keep_days)
            db.query(MemoryLog).filter(
                MemoryLog.workspace_id == workspace_id,
                MemoryLog.created_at < cutoff,
                MemoryLog.roi_score < 10
            ).delete()
            db.commit()
        finally:
            db.close()

    def search_by_type(self, workspace_id: str, memory_types: list) -> list:
        db = SessionLocal()
        try:
            records = db.query(MemoryLog).filter(
                MemoryLog.workspace_id == workspace_id,
                MemoryLog.memory_type.in_(memory_types)
            ).order_by(MemoryLog.created_at.desc()).limit(30).all()
            return [
                {"type": r.memory_type, "content": json.loads(r.content), "roi_score": r.roi_score}
                for r in records
            ]
        finally:
            db.close()