# backend/services/meta_ads_service.py

import requests
from core.config import settings

class MetaAdsService:
    BASE = "https://graph.facebook.com/v19.0"

    def __init__(self):
        self.token = settings.META_ACCESS_TOKEN
        self.app_id = settings.META_APP_ID

    def _get(self, path, params={}):
        params["access_token"] = self.token
        res = requests.get(f"{self.BASE}/{path}", params=params)
        res.raise_for_status()
        return res.json()

    def _post(self, path, data={}):
        data["access_token"] = self.token
        res = requests.post(f"{self.BASE}/{path}", json=data)
        res.raise_for_status()
        return res.json()

    def create_campaign(self, ad_account_id: str, name: str, objective: str, budget: float):
        data = {
            "name": name,
            "objective": objective.upper(),  # CONVERSIONS, TRAFFIC, AWARENESS
            "status": "PAUSED",
            "special_ad_categories": [],
        }
        res = self._post(f"act_{ad_account_id}/campaigns", data)
        return res.get("id")

    def create_ad_set(self, ad_account_id: str, campaign_id: str, name: str,
                      budget: float, targeting: dict, optimization_goal: str = "CONVERSIONS"):
        data = {
            "name": name,
            "campaign_id": campaign_id,
            "daily_budget": int(budget * 100),  # cents
            "billing_event": "IMPRESSIONS",
            "optimization_goal": optimization_goal,
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "targeting": targeting,
            "status": "PAUSED",
            "start_time": "2024-01-01T00:00:00+0000",
        }
        res = self._post(f"act_{ad_account_id}/adsets", data)
        return res.get("id")

    def create_ad_creative(self, ad_account_id: str, name: str, page_id: str,
                            primary_text: str, headline: str, link: str, image_url: str):
        data = {
            "name": name,
            "object_story_spec": {
                "page_id": page_id,
                "link_data": {
                    "message": primary_text,
                    "name": headline,
                    "link": link,
                    "picture": image_url,
                    "call_to_action": {
                        "type": "LEARN_MORE",
                        "value": {"link": link}
                    }
                }
            }
        }
        res = self._post(f"act_{ad_account_id}/adcreatives", data)
        return res.get("id")

    def create_ad(self, ad_account_id: str, ad_set_id: str, creative_id: str, name: str):
        data = {
            "name": name,
            "adset_id": ad_set_id,
            "creative": {"creative_id": creative_id},
            "status": "PAUSED",
        }
        res = self._post(f"act_{ad_account_id}/ads", data)
        return res.get("id")

    def get_campaign_insights(self, campaign_id: str):
        res = self._get(f"{campaign_id}/insights", {
            "fields": "impressions,clicks,ctr,cpc,spend,actions,action_values",
            "date_preset": "last_30d"
        })
        data = res.get("data", [{}])[0]
        spend = float(data.get("spend", 0))
        revenue = sum(float(a.get("value", 0)) for a in data.get("action_values", []) if a.get("action_type") == "purchase")
        return {
            "impressions": int(data.get("impressions", 0)),
            "clicks": int(data.get("clicks", 0)),
            "ctr": round(float(data.get("ctr", 0)), 2),
            "cpc": round(float(data.get("cpc", 0)), 2),
            "spend": round(spend, 2),
            "revenue": round(revenue, 2),
            "roi": round((revenue - spend) / spend * 100, 2) if spend > 0 else 0
        }

    def build_targeting(self, age_min: int, age_max: int, countries: list,
                         interests: list, lookalike_audience_id: str = None):
        targeting = {
            "age_min": age_min,
            "age_max": age_max,
            "geo_locations": {"countries": countries},
        }
        if interests:
            targeting["flexible_spec"] = [{"interests": [{"id": i, "name": i} for i in interests]}]
        if lookalike_audience_id:
            targeting["custom_audiences"] = [{"id": lookalike_audience_id}]
        return targeting

    def pause_campaign(self, campaign_id: str):
        return self._post(f"{campaign_id}", {"status": "PAUSED"})

    def enable_campaign(self, campaign_id: str):
        return self._post(f"{campaign_id}", {"status": "ACTIVE"})

    def update_budget(self, ad_set_id: str, new_daily_budget: float):
        return self._post(f"{ad_set_id}", {"daily_budget": int(new_daily_budget * 100)})