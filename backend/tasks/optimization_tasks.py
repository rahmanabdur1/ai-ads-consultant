# backend/tasks/optimization_tasks.py

from core.celery_app import celery_app
from core.database import SessionLocal, Campaign
from agents.optimization_agent import OptimizationAgent

@celery_app.task
def run_optimization_all():
    db = SessionLocal()
    optimizer = OptimizationAgent()
    try:
        campaigns = db.query(Campaign).filter(Campaign.status == "active").all()
        results = []
        for campaign in campaigns:
            state = {
                "workspace_id": str(campaign.workspace_id),
                "platform": campaign.platform,
                "budget": campaign.budget,
                "goal": campaign.objective,
                "google_customer_id": getattr(campaign, "google_customer_id", None),
                "google_campaign_resource": getattr(campaign, "google_campaign_resource", None),
                "meta_campaign_id": getattr(campaign, "meta_campaign_id", None),
                "meta_ad_set_id": getattr(campaign, "meta_ad_set_id", None),
                "agent_log": []
            }
            result = optimizer.run(state)
            results.append({
                "campaign": str(campaign.id),
                "action": result.get("optimization_result", {}).get("decision", {}).get("action"),
                "stats": result.get("optimization_result", {}).get("stats")
            })
        return results
    finally:
        db.close()