# backend/plugins/builtin/slack_notifier.py

import httpx
from datetime import datetime

class SlackNotifierPlugin:
    def __init__(self, config: dict):
        self.webhook_url = config["webhook_url"]
        self.channel = config.get("channel", "#ads-alerts")
        self.notify_on = config.get("notify_on", ["campaign_launched", "optimization_done", "ab_winner"])

    def on_install(self):
        self._send(":white_check_mark: AI Ads Consultant plugin connected successfully!")

    def on_uninstall(self):
        self._send(":wave: AI Ads Consultant plugin disconnected.")

    def on_campaign_launched(self, data: dict):
        if "campaign_launched" not in self.notify_on:
            return
        msg = (
            f":rocket: *Campaign Launched*\n"
            f"Name: {data.get('campaign_name', 'N/A')}\n"
            f"Platform: {data.get('platform', 'N/A')}\n"
            f"Budget: ${data.get('budget', 0)}\n"
            f"Status: {data.get('status', 'launched')}\n"
            f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )
        return self._send(msg)

    def on_optimization_done(self, data: dict):
        if "optimization_done" not in self.notify_on:
            return
        action = data.get("action", "HOLD")
        roi = data.get("roi", 0)
        emoji = ":chart_with_upwards_trend:" if action == "SCALE_UP" else ":warning:" if action == "PAUSE" else ":bar_chart:"
        msg = (
            f"{emoji} *Optimization Complete*\n"
            f"Action: {action}\n"
            f"ROI: {roi}%\n"
            f"Reason: {data.get('reason', 'N/A')}\n"
            f"Confidence: {data.get('confidence', 0)}%"
        )
        return self._send(msg)

    def on_ab_winner(self, data: dict):
        if "ab_winner" not in self.notify_on:
            return
        msg = (
            f":trophy: *A/B Test Winner: Variant {data.get('winner')}*\n"
            f"CTR Lift: +{data.get('lift_percent', 0)}%\n"
            f"Total Impressions: {data.get('total_impressions', 0)}\n"
            f"AI Recommendation: {data.get('ai_explanation', '')[:200]}"
        )
        return self._send(msg)

    def _send(self, text: str):
        try:
            httpx.post(self.webhook_url, json={"text": text, "channel": self.channel}, timeout=5)
            return {"sent": True}
        except Exception as e:
            return {"sent": False, "error": str(e)}