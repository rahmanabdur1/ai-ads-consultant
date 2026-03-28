# backend/tasks/campaign_tasks.py

from core.celery_app import celery_app
from core.database import SessionLocal, Campaign, AgentTask
from core.orchestrator import Orchestrator
import asyncio, json

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def launch_campaign_task(self, campaign_id: str, user_input: str, workspace_id: str,
                          budget: float, platform: str, goal: str):
    db = SessionLocal()
    try:
        task_log = AgentTask(
            campaign_id=campaign_id,
            agent_name="orchestrator",
            status="running",
            input_data=json.dumps({"user_input": user_input, "budget": budget})
        )
        db.add(task_log)
        db.commit()

        orchestrator = Orchestrator()
        result = asyncio.run(orchestrator.run({
            "message": user_input,
            "workspace_id": workspace_id,
            "session_id": f"celery-{campaign_id}",
            "budget": budget,
            "platform": platform,
            "goal": goal,
        }))

        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if campaign:
            campaign.status = "active" if result.get("approved") else "failed"
            campaign.ad_copy = result.get("ad_copy", "")
        task_log.status = "completed"
        task_log.output_data = json.dumps({"approved": result.get("approved"), "log": result.get("agent_log")})
        db.commit()

        return {"status": "completed", "approved": result.get("approved")}
    except Exception as exc:
        if task_log:
            task_log.status = "failed"
            task_log.error = str(exc)
            db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()