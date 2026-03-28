# backend/api/budget_scaling.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from services.budget_scaler import AutoBudgetScaler

router = APIRouter()
scaler = AutoBudgetScaler()

class ScaleSingleRequest(BaseModel):
    campaign_id: str
    workspace_id: str

class ScaleAllRequest(BaseModel):
    workspace_id: str

@router.post("/scale-campaign")
def scale_single_campaign(data: ScaleSingleRequest):
    result = scaler.run_for_campaign(data.campaign_id, data.workspace_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.post("/scale-all")
def scale_all_campaigns(data: ScaleAllRequest, background: BackgroundTasks):
    background.add_task(scaler.run_for_all_campaigns, data.workspace_id)
    return {"status": "scaling_started", "message": "All campaigns are being analyzed in background"}

@router.post("/scale-all/sync")
def scale_all_sync(data: ScaleAllRequest):
    results = scaler.run_for_all_campaigns(data.workspace_id)
    summary = {
        "total": len(results),
        "scaled_up": sum(1 for r in results if "SCALE" in r.get("decision", {}).get("action", "")),
        "paused": sum(1 for r in results if r.get("decision", {}).get("action") == "PAUSE"),
        "reduced": sum(1 for r in results if r.get("decision", {}).get("action") == "REDUCE"),
        "held": sum(1 for r in results if r.get("decision", {}).get("action") == "HOLD"),
        "results": results
    }
    return summary

@router.get("/history/{campaign_id}")
def get_budget_history(campaign_id: str, days: int = 14):
    history = scaler.get_campaign_history(campaign_id, days)
    metrics = scaler.calculate_metrics(history)
    return {"campaign_id": campaign_id, "days": days, "metrics": metrics, "history": history}

# Add to main.py:
# from api.budget_scaling import router as budget_router
# app.include_router(budget_router, prefix="/budget", tags=["Budget Scaling"])