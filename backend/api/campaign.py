# backend/api/campaign.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from core.database import get_db, Campaign
from typing import Optional
import uuid

router = APIRouter()

class CampaignCreate(BaseModel):
    workspace_id: str
    name: str
    platform: str
    budget: float
    objective: str
    target_audience: Optional[str] = ""
    ad_copy: Optional[str] = ""

@router.post("/")
def create_campaign(data: CampaignCreate, db: Session = Depends(get_db)):
    campaign = Campaign(**data.dict())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return {"id": str(campaign.id), "name": campaign.name, "status": campaign.status}

@router.get("/")
def list_campaigns(workspace_id: str, db: Session = Depends(get_db)):
    campaigns = db.query(Campaign).filter(Campaign.workspace_id == workspace_id).all()
    return [{"id": str(c.id), "name": c.name, "platform": c.platform, "status": c.status, "budget": c.budget} for c in campaigns]

@router.get("/{campaign_id}")
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return c

@router.delete("/{campaign_id}")
def delete_campaign(campaign_id: str, db: Session = Depends(get_db)):
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(c)
    db.commit()
    return {"message": "Deleted"}