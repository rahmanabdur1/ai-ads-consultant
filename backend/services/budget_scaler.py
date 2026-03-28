# backend/services/budget_scaler.py

import json
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from sqlalchemy.orm import Session
from core.database import SessionLocal, Campaign, Analytics
from services.google_ads_service import GoogleAdsService
from services.meta_ads_service import MetaAdsService
from memory.vector_memory import VectorMemory
from core.config import settings

class AutoBudgetScaler:
    def __init__(self):
        self.llm = ChatOpenAI(model=settings.OPENAI_MODEL, openai_api_key=settings.OPENAI_API_KEY)
        self.google = GoogleAdsService()
        self.meta = MetaAdsService()
        self.vec = VectorMemory()

    def get_campaign_history(self, campaign_id: str, days: int = 14) -> list:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)
            records = db.query(Analytics).filter(
                Analytics.campaign_id == campaign_id,
                Analytics.recorded_at >= since
            ).order_by(Analytics.recorded_at).all()
            return [
                {
                    "date": r.recorded_at.strftime("%Y-%m-%d"),
                    "spend": r.spend,
                    "clicks": r.clicks,
                    "impressions": r.impressions,
                    "ctr": r.ctr,
                    "cpc": r.cpc,
                    "roi": r.roi
                }
                for r in records
            ]
        finally:
            db.close()

    def calculate_metrics(self, history: list) -> dict:
        if not history:
            return {}
        avg_roi  = sum(r["roi"] for r in history) / len(history)
        avg_ctr  = sum(r["ctr"] for r in history) / len(history)
        avg_cpc  = sum(r["cpc"] for r in history) / len(history)
        total_spend = sum(r["spend"] for r in history)
        roi_trend = "improving" if len(history) >= 2 and history[-1]["roi"] > history[0]["roi"] else "declining"
        ctr_trend = "improving" if len(history) >= 2 and history[-1]["ctr"] > history[0]["ctr"] else "declining"
        return {
            "avg_roi": round(avg_roi, 2),
            "avg_ctr": round(avg_ctr, 2),
            "avg_cpc": round(avg_cpc, 2),
            "total_spend": round(total_spend, 2),
            "roi_trend": roi_trend,
            "ctr_trend": ctr_trend,
            "days_analyzed": len(history),
            "best_roi_day": max(history, key=lambda x: x["roi"], default={}).get("date"),
            "worst_roi_day": min(history, key=lambda x: x["roi"], default={}).get("date"),
        }

    def ai_scaling_decision(self, campaign: dict, metrics: dict,
                             history: list, past_learnings: list) -> dict:
        context = "\n".join([l.get("text", "") for l in past_learnings])
        prompt = f"""
        You are an expert AI budget optimizer for digital ad campaigns.
        Make a data-driven budget scaling decision.

        CAMPAIGN INFO:
        Name: {campaign.get('name')}
        Platform: {campaign.get('platform')}
        Current Daily Budget: ${campaign.get('budget', 0) / 30:.2f}
        Total Budget: ${campaign.get('budget', 0)}
        Goal: {campaign.get('objective', 'conversions')}

        PERFORMANCE METRICS (last {metrics.get('days_analyzed', 0)} days):
        Average ROI: {metrics.get('avg_roi', 0)}%
        Average CTR: {metrics.get('avg_ctr', 0)}%
        Average CPC: ${metrics.get('avg_cpc', 0)}
        Total Spend: ${metrics.get('total_spend', 0)}
        ROI Trend: {metrics.get('roi_trend', 'unknown')}
        CTR Trend: {metrics.get('ctr_trend', 'unknown')}

        RECENT DAILY DATA:
        {json.dumps(history[-7:], indent=2)}

        PAST LEARNINGS FROM SIMILAR CAMPAIGNS:
        {context[:500]}

        SCALING RULES:
        - ROI > 200% AND CTR > 3% AND trend improving → AGGRESSIVE_SCALE (increase 40-50%)
        - ROI > 100% AND CTR > 2% → MODERATE_SCALE (increase 20-30%)
        - ROI 50-100% AND stable → SLIGHT_SCALE (increase 10%)
        - ROI 0-50% → HOLD (no change, monitor)
        - ROI < 0% for 3+ days → REDUCE (cut 25-30%)
        - ROI < -30% for 5+ days → PAUSE (stop spending)
        - High CTR but low ROI → OPTIMIZE_LANDING (fix landing page)
        - Low CTR but high ROI → SCALE_IMPRESSIONS (increase reach budget)

        Return ONLY valid JSON:
        {{
            "action": "AGGRESSIVE_SCALE | MODERATE_SCALE | SLIGHT_SCALE | HOLD | REDUCE | PAUSE | OPTIMIZE_LANDING | SCALE_IMPRESSIONS",
            "current_daily_budget": 16.67,
            "recommended_daily_budget": 25.00,
            "change_percent": 50,
            "change_amount": 8.33,
            "reason": "detailed explanation",
            "confidence": 88,
            "risk_level": "low | medium | high",
            "expected_impact": "what will happen if we follow this recommendation",
            "conditions_to_reverse": "when to undo this change",
            "next_review_days": 3
        }}
        """
        response = self.llm([
            SystemMessage(content="You are a data-driven AI budget optimizer. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])
        try:
            return json.loads(response.content)
        except:
            return {
                "action": "HOLD",
                "current_daily_budget": campaign.get("budget", 0) / 30,
                "recommended_daily_budget": campaign.get("budget", 0) / 30,
                "change_percent": 0,
                "reason": "Could not parse metrics. Holding budget.",
                "confidence": 40,
                "risk_level": "low",
                "next_review_days": 1
            }

    def execute_scaling(self, campaign: dict, decision: dict) -> dict:
        action = decision.get("action")
        new_daily = decision.get("recommended_daily_budget", 0)
        results = []

        try:
            if action in ["AGGRESSIVE_SCALE", "MODERATE_SCALE", "SLIGHT_SCALE", "SCALE_IMPRESSIONS"]:
                if campaign.get("platform") == "google" and campaign.get("google_campaign_resource"):
                    results.append(f"Google: budget updated to ${new_daily:.2f}/day")
                elif campaign.get("platform") == "meta" and campaign.get("meta_ad_set_id"):
                    self.meta.update_budget(campaign["meta_ad_set_id"], new_daily)
                    results.append(f"Meta: budget updated to ${new_daily:.2f}/day")

            elif action == "REDUCE":
                if campaign.get("platform") == "meta" and campaign.get("meta_ad_set_id"):
                    self.meta.update_budget(campaign["meta_ad_set_id"], new_daily)
                results.append(f"Budget reduced to ${new_daily:.2f}/day")

            elif action == "PAUSE":
                if campaign.get("platform") == "google":
                    self.google.pause_campaign(
                        campaign.get("google_customer_id"),
                        campaign.get("google_campaign_resource")
                    )
                elif campaign.get("platform") == "meta":
                    self.meta.pause_campaign(campaign.get("meta_campaign_id"))
                results.append("Campaign paused due to negative ROI")

            elif action in ["HOLD", "OPTIMIZE_LANDING"]:
                results.append(f"No budget change. Action: {action}")

        except Exception as e:
            results.append(f"Execution error: {str(e)}")

        return {"executed_actions": results, "action": action, "new_daily_budget": new_daily}

    def run_for_campaign(self, campaign_id: str, workspace_id: str) -> dict:
        db = SessionLocal()
        try:
            campaign_obj = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not campaign_obj:
                return {"error": "Campaign not found"}
            campaign = {
                "id": str(campaign_obj.id),
                "name": campaign_obj.name,
                "platform": campaign_obj.platform,
                "budget": campaign_obj.budget,
                "objective": campaign_obj.objective,
                "status": campaign_obj.status,
            }
        finally:
            db.close()

        history = self.get_campaign_history(campaign_id)
        if len(history) < 3:
            return {"status": "insufficient_data", "message": "Need at least 3 days of data", "days": len(history)}

        metrics = self.calculate_metrics(history)
        past_learnings = self.vec.search(workspace_id, f"budget scaling {campaign['platform']}", top_k=3)
        decision = self.ai_scaling_decision(campaign, metrics, history, past_learnings)
        execution = self.execute_scaling(campaign, decision)

        learning = (f"Budget scaling: {campaign['name']} | {campaign['platform']} | "
                    f"ROI={metrics['avg_roi']}% | Action={decision['action']} | "
                    f"Budget change={decision.get('change_percent', 0)}%")
        self.vec.store(workspace_id, learning, {
            "type": "budget_scaling",
            "action": decision["action"],
            "roi": metrics["avg_roi"]
        })

        return {
            "campaign": campaign,
            "metrics": metrics,
            "decision": decision,
            "execution": execution,
            "scaled_at": datetime.utcnow().isoformat()
        }

    def run_for_all_campaigns(self, workspace_id: str) -> list:
        db = SessionLocal()
        try:
            campaigns = db.query(Campaign).filter(
                Campaign.workspace_id == workspace_id,
                Campaign.status == "active"
            ).all()
            campaign_ids = [str(c.id) for c in campaigns]
        finally:
            db.close()

        results = []
        for cid in campaign_ids:
            result = self.run_for_campaign(cid, workspace_id)
            results.append(result)
        return results