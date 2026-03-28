# backend/agents/execution_agent.py

from services.google_ads_service import GoogleAdsService
from services.meta_ads_service import MetaAdsService
from core.config import settings
import json

class ExecutionAgent:
    def __init__(self):
        self.google = GoogleAdsService()
        self.meta = MetaAdsService()

    def run(self, state: dict) -> dict:
        platform = state.get("platform", "google").lower()
        ad_copy = state.get("ad_copy", "")
        budget = state.get("budget", 100)
        workspace = state.get("workspace_id")

        try:
            if platform == "google":
                result = self._launch_google(state, ad_copy, budget)
            elif platform == "meta":
                result = self._launch_meta(state, ad_copy, budget)
            else:
                result = self._launch_google(state, ad_copy, budget)
                result.update(self._launch_meta(state, ad_copy, budget))

            state["execution_result"] = result
            state["agent_log"].append("Execution Agent: Campaign launched successfully")
        except Exception as e:
            state["execution_result"] = {"error": str(e)}
            state["agent_log"].append(f"Execution Agent: Failed — {str(e)}")

        return state

    def _launch_google(self, state, ad_copy, budget):
        customer_id = state.get("google_customer_id", "")
        headlines = self._extract_headlines(ad_copy)
        descriptions = self._extract_descriptions(ad_copy)
        keywords = self._extract_keywords(state.get("research", ""))
        final_url = state.get("landing_url", "https://example.com")

        campaign_resource = self.google.create_campaign(
            customer_id, state["user_input"][:30], budget, state.get("goal", "conversions")
        )
        ad_group_resource = self.google.create_ad_group(
            customer_id, campaign_resource, f"{state['user_input'][:20]} Ad Group"
        )
        self.google.create_responsive_search_ad(
            customer_id, ad_group_resource, headlines, descriptions, final_url
        )
        self.google.add_keywords(customer_id, ad_group_resource, keywords)

        return {"google_campaign": campaign_resource, "status": "launched"}

    def _launch_meta(self, state, ad_copy, budget):
        ad_account_id = state.get("meta_ad_account_id", "")
        page_id = state.get("meta_page_id", "")
        primary_text = self._extract_meta_text(ad_copy)
        headline = self._extract_meta_headline(ad_copy)

        targeting = self.meta.build_targeting(
            age_min=state.get("age_min", 25),
            age_max=state.get("age_max", 55),
            countries=state.get("countries", ["US"]),
            interests=state.get("interests", [])
        )
        campaign_id = self.meta.create_campaign(
            ad_account_id, state["user_input"][:40], state.get("goal", "CONVERSIONS"), budget
        )
        ad_set_id = self.meta.create_ad_set(
            ad_account_id, campaign_id, "Main Ad Set", budget / 30, targeting
        )
        creative_id = self.meta.create_ad_creative(
            ad_account_id, "Main Creative", page_id,
            primary_text, headline, state.get("landing_url", "https://example.com"),
            state.get("image_url", "")
        )
        self.meta.create_ad(ad_account_id, ad_set_id, creative_id, "Main Ad")

        return {"meta_campaign": campaign_id, "meta_ad_set": ad_set_id}

    def _extract_headlines(self, text):
        lines = [l.strip() for l in text.split("\n") if "headline" in l.lower() or l.startswith("-")]
        return [l.replace("-", "").strip()[:30] for l in lines[:3]] or ["Buy Now", "Best Deal", "Shop Today"]

    def _extract_descriptions(self, text):
        lines = [l.strip() for l in text.split("\n") if "description" in l.lower()]
        return [l.replace("-", "").strip()[:90] for l in lines[:2]] or ["Get the best deals today.", "Shop now and save big."]

    def _extract_meta_text(self, text):
        for line in text.split("\n"):
            if "primary" in line.lower():
                return line.split(":")[-1].strip()[:125]
        return text[:125]

    def _extract_meta_headline(self, text):
        for line in text.split("\n"):
            if "meta" in line.lower() and "headline" in line.lower():
                return line.split(":")[-1].strip()[:40]
        return text[:40]

    def _extract_keywords(self, research_text):
        keywords = []
        for line in research_text.split("\n"):
            if "keyword" in line.lower():
                words = line.split(":")[-1].strip().split(",")
                keywords.extend([w.strip() for w in words])
        return keywords[:10] or ["buy online", "best price", "shop now"]