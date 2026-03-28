# backend/agents/optimization_agent.py

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from services.google_ads_service import GoogleAdsService
from services.meta_ads_service import MetaAdsService
from core.config import settings
from memory.vector_memory import VectorMemory
import json

class OptimizationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model=settings.OPENAI_MODEL, openai_api_key=settings.OPENAI_API_KEY)
        self.google = GoogleAdsService()
        self.meta = MetaAdsService()
        self.vector_mem = VectorMemory()

    def run(self, state: dict) -> dict:
        platform = state.get("platform", "google")
        stats = self._get_stats(state, platform)
        past_learnings = self.vector_mem.search(
            state["workspace_id"], f"optimization {platform}", top_k=3
        )

        decision = self._analyze_and_decide(stats, past_learnings, state)
        actions = self._execute_actions(decision, state)

        # Store learning in memory
        summary = f"Optimization: {platform} | Stats: CTR={stats.get('ctr')}% ROI={stats.get('roi')}% | Action: {decision.get('action')}"
        self.vector_mem.store(state["workspace_id"], summary, {"type": "optimization", "roi": stats.get("roi", 0)})

        state["optimization_result"] = {"stats": stats, "decision": decision, "actions": actions}
        state["agent_log"].append("Optimization Agent: Complete")
        return state

    def _get_stats(self, state, platform):
        try:
            if platform == "google":
                return self.google.get_campaign_stats(
                    state.get("google_customer_id"), state.get("google_campaign_resource")
                )
            else:
                return self.meta.get_campaign_insights(state.get("meta_campaign_id"))
        except Exception as e:
            return {"error": str(e), "impressions": 0, "clicks": 0, "ctr": 0, "spend": 0, "roi": 0}

    def _analyze_and_decide(self, stats, past_learnings, state):
        context = "\n".join([l.get("text", "") for l in past_learnings])
        prompt = f"""
        You are an AI ads optimization expert.

        Current Stats:
        {json.dumps(stats, indent=2)}

        Past Campaign Learnings:
        {context}

        Budget: ${state.get('budget', 100)}
        Goal: {state.get('goal', 'conversions')}

        Based on the stats, decide ONE action:
        - SCALE_UP: ROI > 150% and CTR > 3% → increase budget by 20%
        - SCALE_DOWN: ROI < 0% or spend > budget * 1.1 → reduce budget by 30%
        - PAUSE: ROI < -50% for 7 days → pause campaign
        - AB_TEST: CTR < 1% → test new ad copy
        - OPTIMIZE_BID: CPC too high → lower bid ceiling
        - HOLD: Stats look normal → keep running

        Return JSON only:
        {{"action": "SCALE_UP", "reason": "...", "new_budget": 120, "confidence": 85}}
        """
        response = self.llm([
            SystemMessage(content="You are a data-driven ads optimization AI. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])
        try:
            return json.loads(response.content)
        except:
            return {"action": "HOLD", "reason": "Could not parse stats", "confidence": 50}

    def _execute_actions(self, decision, state):
        action = decision.get("action")
        results = []

        try:
            if action == "SCALE_UP":
                new_budget = decision.get("new_budget", state.get("budget", 100) * 1.2)
                if state.get("platform") == "meta" and state.get("meta_ad_set_id"):
                    self.meta.update_budget(state["meta_ad_set_id"], new_budget / 30)
                results.append(f"Budget scaled up to ${new_budget:.2f}")

            elif action == "SCALE_DOWN":
                new_budget = state.get("budget", 100) * 0.7
                if state.get("platform") == "meta" and state.get("meta_ad_set_id"):
                    self.meta.update_budget(state["meta_ad_set_id"], new_budget / 30)
                results.append(f"Budget reduced to ${new_budget:.2f}")

            elif action == "PAUSE":
                if state.get("platform") == "google":
                    self.google.pause_campaign(state.get("google_customer_id"), state.get("google_campaign_resource"))
                elif state.get("platform") == "meta":
                    self.meta.pause_campaign(state.get("meta_campaign_id"))
                results.append("Campaign paused due to poor ROI")

            elif action == "AB_TEST":
                results.append("A/B test triggered — Copywriting Agent will generate new variants")

            elif action == "HOLD":
                results.append("No action needed — campaign performing normally")

        except Exception as e:
            results.append(f"Action failed: {str(e)}")

        return results