# backend/tasks/notification_tasks.py

from core.celery_app import celery_app
from services.email_service import EmailService
from core.plugin_registry import plugin_registry
from core.database import SessionLocal, User, Campaign

email_svc = EmailService()

@celery_app.task
def notify_campaign_launched(campaign_id: str, user_id: str):
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        if not campaign or not user:
            return

        # Email notification
        email_svc.send_campaign_launched(
            user.email,
            campaign.name,
            campaign.platform,
            campaign.budget
        )

        # Plugin hooks
        plugin_registry.emit_hook("campaign_launched", {
            "campaign_name": campaign.name,
            "platform": campaign.platform,
            "budget": campaign.budget,
            "status": campaign.status
        })
    finally:
        db.close()

@celery_app.task
def notify_optimization(campaign_id: str, action: str, reason: str):
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return
        ws = campaign.workspace
        if ws and ws.owner:
            email_svc.send_optimization_alert(
                ws.owner.email, campaign.name, action, reason
            )
        plugin_registry.emit_hook("optimization_done", {
            "campaign_name": campaign.name,
            "action": action,
            "reason": reason
        })
    finally:
        db.close()

@celery_app.task
def notify_ab_winner(test_id: str, winner: str, lift: float, campaign_id: str):
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return
        ws = campaign.workspace
        if ws and ws.owner:
            email_svc.send_ab_winner(ws.owner.email, campaign.name, winner, lift)
        plugin_registry.emit_hook("ab_winner", {
            "winner": winner,
            "lift_percent": lift,
            "campaign_name": campaign.name
        })
    finally:
        db.close()