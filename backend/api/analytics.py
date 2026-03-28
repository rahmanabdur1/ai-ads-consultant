# backend/api/analytics.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db, Analytics, Campaign
from sqlalchemy import func

router = APIRouter()

@router.get("/")
def get_analytics(workspace_id: str, db: Session = Depends(get_db)):
    campaigns = db.query(Campaign).filter(Campaign.workspace_id == workspace_id).all()
    campaign_ids = [c.id for c in campaigns]

    records = db.query(Analytics).filter(Analytics.campaign_id.in_(campaign_ids)).all()

    total_spend = sum(r.spend for r in records)
    total_clicks = sum(r.clicks for r in records)
    total_impressions = sum(r.impressions for r in records)
    avg_roi = sum(r.roi for r in records) / len(records) if records else 0

    return {
        "summary": {
            "total_spend": round(total_spend, 2),
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "avg_ctr": round(total_clicks / total_impressions * 100, 2) if total_impressions else 0,
            "avg_roi": round(avg_roi, 2),
        },
        "by_campaign": [
            {
                "campaign_id": str(r.campaign_id),
                "spend": r.spend,
                "clicks": r.clicks,
                "ctr": r.ctr,
                "cpc": r.cpc,
                "roi": r.roi,
                "recorded_at": r.recorded_at.isoformat(),
            }
            for r in sorted(records, key=lambda x: x.recorded_at, reverse=True)[:50]
        ]
    }