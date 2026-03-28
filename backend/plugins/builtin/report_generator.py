# backend/plugins/builtin/report_generator.py

from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from core.config import settings
from core.database import SessionLocal, Campaign, Analytics
import json

class ReportGeneratorPlugin:
    def __init__(self, config: dict):
        self.email = config["email"]
        self.schedule = config.get("schedule", "weekly")
        self.sections = config.get("include_sections", ["summary", "campaigns", "recommendations"])
        self.llm = ChatOpenAI(model=settings.OPENAI_MODEL, openai_api_key=settings.OPENAI_API_KEY)

    def on_install(self):
        return {"status": "Report generator active", "schedule": self.schedule, "email": self.email}

    def generate_report(self, workspace_id: str) -> dict:
        db = SessionLocal()
        try:
            campaigns = db.query(Campaign).filter(Campaign.workspace_id == workspace_id).all()
            analytics = []
            for c in campaigns:
                records = db.query(Analytics).filter(Analytics.campaign_id == c.id).all()
                analytics.append({
                    "name": c.name,
                    "platform": c.platform,
                    "budget": c.budget,
                    "status": c.status,
                    "total_spend": sum(r.spend for r in records),
                    "avg_roi": sum(r.roi for r in records) / len(records) if records else 0,
                    "avg_ctr": sum(r.ctr for r in records) / len(records) if records else 0,
                })
        finally:
            db.close()

        prompt = f"""
        Generate a concise weekly performance report for an ad campaigns manager.

        Campaigns Data:
        {json.dumps(analytics, indent=2)}

        Include:
        1. Executive summary (2-3 sentences)
        2. Top performing campaign and why
        3. Campaigns needing attention
        4. Budget efficiency overview
        5. 3 actionable recommendations for next week
        6. Predicted ROI if recommendations are followed

        Use clear, professional language suitable for a business report.
        """
        response = self.llm([
            SystemMessage(content="You write concise, actionable ad performance reports."),
            HumanMessage(content=prompt)
        ])

        return {
            "report_text": response.content,
            "campaigns_count": len(campaigns),
            "generated_at": datetime.utcnow().isoformat(),
            "workspace_id": workspace_id
        }

    def on_optimization_done(self, data: dict):
        return {"logged": True, "event": "optimization_done"}