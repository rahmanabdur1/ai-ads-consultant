# backend/api/trends.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.trend_detector import TrendDetector

router = APIRouter()
detector = TrendDetector()

class TrendRequest(BaseModel):
    keywords: List[str]
    industry: str
    workspace_id: str
    geo: Optional[str] = "US"

@router.post("/detect")
async def detect_trends(data: TrendRequest):
    if not data.keywords:
        raise HTTPException(status_code=400, detail="Provide at least one keyword")
    try:
        result = await detector.detect_trends(
            data.keywords, data.industry, data.workspace_id, data.geo
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/industries")
def list_industries():
    return {
        "industries": [
            "ecommerce", "saas", "fashion", "fitness",
            "food", "finance", "tech", "travel", "education", "health"
        ]
    }

# Add to main.py:
# from api.trends import router as trends_router
# app.include_router(trends_router, prefix="/trends", tags=["Trend Detection"])