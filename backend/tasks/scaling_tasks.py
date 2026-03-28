# backend/tasks/scaling_tasks.py

from core.celery_app import celery_app
from services.budget_scaler import AutoBudgetScaler
from core.database import SessionLocal, Workspace
from core.plugin_registry import plugin_registry

@celery_app.task
def auto_scale_all_workspaces():
    db = SessionLocal()
    scaler = AutoBudgetScaler()
    try:
        workspaces = db.query(Workspace).all()
        all_results = []
        for ws in workspaces:
            results = scaler.run_for_all_campaigns(str(ws.id))
            for r in results:
                if r.get("decision"):
                    plugin_registry.emit_hook("optimization_done", {
                        "campaign_name": r.get("campaign", {}).get("name"),
                        "action": r.get("decision", {}).get("action"),
                        "roi": r.get("metrics", {}).get("avg_roi"),
                        "reason": r.get("decision", {}).get("reason"),
                        "confidence": r.get("decision", {}).get("confidence")
                    })
            all_results.extend(results)
        return {"workspaces_processed": len(workspaces), "campaigns_scaled": len(all_results)}
    finally:
        db.close()

# Add to celery_app.py beat_schedule:
# "auto-scale-budgets-every-6h": {
#     "task": "tasks.scaling_tasks.auto_scale_all_workspaces",
#     "schedule": 21600.0,
# },