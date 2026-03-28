# backend/tasks/analytics_tasks.py

from core.celery_app import celery_app
from core.database import SessionLocal, Campaign, Analytics
from services.google_ads_service import GoogleAdsService
from services.meta_ads_service import MetaAdsService
from datetime import datetime

@celery_app.task
def sync_all_analytics():
    db = SessionLocal()
    google_svc = GoogleAdsService()
    meta_svc = MetaAdsService()

    try:
        campaigns = db.query(Campaign).filter(Campaign.status == "active").all()
        for campaign in campaigns:
            try:
                stats = {}
                if campaign.platform == "google" and campaign.google_campaign_resource:
                    stats = google_svc.get_campaign_stats(
                        campaign.google_customer_id,
                        campaign.google_campaign_resource
                    )
                elif campaign.platform == "meta" and campaign.meta_campaign_id:
                    stats = meta_svc.get_campaign_insights(campaign.meta_campaign_id)

                if stats and not stats.get("error"):
                    record = Analytics(
                        campaign_id=campaign.id,
                        impressions=stats.get("impressions", 0),
                        clicks=stats.get("clicks", 0),
                        ctr=stats.get("ctr", 0),
                        cpc=stats.get("avg_cpc") or stats.get("cpc", 0),
                        spend=stats.get("spend", 0),
                        roi=stats.get("roi", 0),
                        recorded_at=datetime.utcnow()
                    )
                    db.add(record)
            except Exception as e:
                print(f"Analytics sync failed for {campaign.id}: {e}")
        db.commit()
        return {"synced": len(campaigns)}
    finally:
        db.close()