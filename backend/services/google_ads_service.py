# backend/services/google_ads_service.py

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from core.config import settings
import yaml, os

class GoogleAdsService:
    def __init__(self):
        config = {
            "developer_token": settings.GOOGLE_ADS_DEVELOPER_TOKEN,
            "client_id": settings.GOOGLE_ADS_CLIENT_ID,
            "client_secret": settings.GOOGLE_ADS_CLIENT_SECRET,
            "refresh_token": settings.GOOGLE_ADS_REFRESH_TOKEN,
            "use_proto_plus": True,
        }
        self.client = GoogleAdsClient.load_from_dict(config)

    def create_campaign(self, customer_id: str, name: str, budget: float, goal: str):
        campaign_service = self.client.get_service("CampaignService")
        campaign_budget_service = self.client.get_service("CampaignBudgetService")
        ga_service = self.client.get_service("GoogleAdsService")

        # Step 1: Create budget
        budget_op = self.client.get_type("CampaignBudgetOperation")
        budget_obj = budget_op.create
        budget_obj.name = f"{name} Budget"
        budget_obj.amount_micros = int(budget * 1_000_000)
        budget_obj.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD

        budget_res = campaign_budget_service.mutate_campaign_budgets(
            customer_id=customer_id, operations=[budget_op]
        )
        budget_resource = budget_res.results[0].resource_name

        # Step 2: Create campaign
        campaign_op = self.client.get_type("CampaignOperation")
        campaign = campaign_op.create
        campaign.name = name
        campaign.status = self.client.enums.CampaignStatusEnum.PAUSED
        campaign.advertising_channel_type = self.client.enums.AdvertisingChannelTypeEnum.SEARCH
        campaign.campaign_budget = budget_resource
        campaign.target_spend.cpc_bid_ceiling_micros = 2_000_000  # $2 max CPC

        response = campaign_service.mutate_campaigns(
            customer_id=customer_id, operations=[campaign_op]
        )
        return response.results[0].resource_name

    def create_ad_group(self, customer_id: str, campaign_resource: str, name: str):
        ad_group_service = self.client.get_service("AdGroupService")
        op = self.client.get_type("AdGroupOperation")
        ad_group = op.create
        ad_group.name = name
        ad_group.campaign = campaign_resource
        ad_group.status = self.client.enums.AdGroupStatusEnum.ENABLED
        ad_group.type_ = self.client.enums.AdGroupTypeEnum.SEARCH_STANDARD
        ad_group.cpc_bid_micros = 1_000_000  # $1 CPC default

        res = ad_group_service.mutate_ad_groups(
            customer_id=customer_id, operations=[op]
        )
        return res.results[0].resource_name

    def create_responsive_search_ad(self, customer_id: str, ad_group_resource: str,
                                     headlines: list, descriptions: list, final_url: str):
        ad_group_ad_service = self.client.get_service("AdGroupAdService")
        op = self.client.get_type("AdGroupAdOperation")
        ad = op.create
        ad.ad_group = ad_group_resource
        ad.status = self.client.enums.AdGroupAdStatusEnum.PAUSED

        rsa = ad.ad.responsive_search_ad
        for h in headlines[:15]:
            asset = self.client.get_type("AdTextAsset")
            asset.text = h[:30]
            rsa.headlines.append(asset)
        for d in descriptions[:4]:
            asset = self.client.get_type("AdTextAsset")
            asset.text = d[:90]
            rsa.descriptions.append(asset)

        ad.ad.final_urls.append(final_url)

        res = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=customer_id, operations=[op]
        )
        return res.results[0].resource_name

    def add_keywords(self, customer_id: str, ad_group_resource: str, keywords: list):
        kw_service = self.client.get_service("AdGroupCriterionService")
        operations = []
        for kw in keywords:
            op = self.client.get_type("AdGroupCriterionOperation")
            criterion = op.create
            criterion.ad_group = ad_group_resource
            criterion.status = self.client.enums.AdGroupCriterionStatusEnum.ENABLED
            criterion.keyword.text = kw
            criterion.keyword.match_type = self.client.enums.KeywordMatchTypeEnum.PHRASE
            operations.append(op)

        res = kw_service.mutate_ad_group_criteria(
            customer_id=customer_id, operations=operations
        )
        return [r.resource_name for r in res.results]

    def get_campaign_stats(self, customer_id: str, campaign_resource: str):
        query = f"""
            SELECT
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_micros,
                metrics.conversions,
                metrics.all_conversions_value
            FROM campaign
            WHERE campaign.resource_name = '{campaign_resource}'
            AND segments.date DURING LAST_30_DAYS
        """
        ga_service = self.client.get_service("GoogleAdsService")
        response = ga_service.search(customer_id=customer_id, query=query)
        for row in response:
            m = row.metrics
            return {
                "impressions": m.impressions,
                "clicks": m.clicks,
                "ctr": round(m.ctr * 100, 2),
                "avg_cpc": round(m.average_cpc / 1_000_000, 2),
                "spend": round(m.cost_micros / 1_000_000, 2),
                "conversions": m.conversions,
                "revenue": m.all_conversions_value,
                "roi": round((m.all_conversions_value - m.cost_micros / 1_000_000) / (m.cost_micros / 1_000_000) * 100, 2) if m.cost_micros > 0 else 0
            }
        return {}

    def pause_campaign(self, customer_id: str, campaign_resource: str):
        campaign_service = self.client.get_service("CampaignService")
        op = self.client.get_type("CampaignOperation")
        campaign = op.update
        campaign.resource_name = campaign_resource
        campaign.status = self.client.enums.CampaignStatusEnum.PAUSED
        field_mask = self.client.get_type("FieldMask")
        field_mask.paths.append("status")
        op.update_mask.CopyFrom(field_mask)
        campaign_service.mutate_campaigns(customer_id=customer_id, operations=[op])
        return {"status": "paused"}

    def enable_campaign(self, customer_id: str, campaign_resource: str):
        campaign_service = self.client.get_service("CampaignService")
        op = self.client.get_type("CampaignOperation")
        campaign = op.update
        campaign.resource_name = campaign_resource
        campaign.status = self.client.enums.CampaignStatusEnum.ENABLED
        field_mask = self.client.get_type("FieldMask")
        field_mask.paths.append("status")
        op.update_mask.CopyFrom(field_mask)
        campaign_service.mutate_campaigns(customer_id=customer_id, operations=[op])
        return {"status": "enabled"}