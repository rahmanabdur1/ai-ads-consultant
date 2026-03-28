# backend/plugins/builtin/audience_expander.py

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from core.config import settings
import json

class AudienceExpanderPlugin:
    def __init__(self, config: dict):
        self.min_size = config.get("min_audience_size", 10000)
        self.factor = config.get("expansion_factor", 1.5)
        self.platforms = config.get("platforms", ["meta", "google"])
        self.llm = ChatOpenAI(model=settings.OPENAI_MODEL, openai_api_key=settings.OPENAI_API_KEY)

    def on_install(self):
        return {"status": "Audience Expander active", "min_size": self.min_size}

    def on_campaign_launched(self, data: dict) -> dict:
        suggestions = self.suggest_audiences(
            data.get("campaign_name", ""),
            data.get("platform", "meta"),
            data.get("target_audience", "")
        )
        return {"audience_suggestions": suggestions}

    def suggest_audiences(self, campaign_name: str, platform: str,
                          current_audience: str) -> dict:
        prompt = f"""
        You are a digital advertising audience expert.
        Suggest expanded audiences for this campaign.

        Campaign: {campaign_name}
        Platform: {platform}
        Current Targeting: {current_audience}
        Min Audience Size: {self.min_size:,}

        Return JSON:
        {{
            "lookalike_suggestions": [
                {{"description": "...", "estimated_size": 50000, "similarity_score": 0.85}}
            ],
            "interest_expansions": [
                {{"interest": "...", "relevance_score": 0.9, "estimated_reach": 120000}}
            ],
            "demographic_expansions": [
                {{"segment": "age 35-44", "reason": "...", "estimated_lift": 0.15}}
            ],
            "keyword_expansions": ["kw1", "kw2", "kw3"],
            "negative_audiences": ["audience to exclude 1", "audience to exclude 2"],
            "total_expanded_reach": 500000
        }}
        """
        response = self.llm([
            SystemMessage(content="You are a digital audience targeting expert. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])
        try:
            return json.loads(response.content)
        except:
            return {"error": "Could not generate suggestions"}