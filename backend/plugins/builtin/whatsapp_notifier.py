# backend/plugins/builtin/whatsapp_notifier.py

import httpx

class WhatsAppPlugin:
    BASE = "https://graph.facebook.com/v19.0"

    def __init__(self, config: dict):
        self.phone_number_id = config["phone_number_id"]
        self.access_token = config["access_token"]
        self.recipient = config["recipient"]

    def on_install(self):
        return self._send_text("✅ AI Ads Consultant connected to WhatsApp!")

    def on_campaign_launched(self, data: dict):
        msg = (
            f"🚀 *Campaign Launched*\n"
            f"Name: {data.get('campaign_name')}\n"
            f"Platform: {data.get('platform')}\n"
            f"Budget: ${data.get('budget')}"
        )
        return self._send_text(msg)

    def on_optimization_done(self, data: dict):
        action = data.get('action', 'HOLD')
        icon = {"SCALE_UP": "📈", "PAUSE": "🛑", "REDUCE": "📉"}.get(action, "⚙️")
        msg = (
            f"{icon} *Budget Optimization: {action}*\n"
            f"ROI: {data.get('roi', 0)}%\n"
            f"Reason: {data.get('reason', 'N/A')}"
        )
        return self._send_text(msg)

    def on_ab_winner(self, data: dict):
        msg = (
            f"🏆 *A/B Test Winner: Variant {data.get('winner')}*\n"
            f"Lift: +{data.get('lift_percent', 0)}%\n"
            f"Campaign: {data.get('campaign_name')}"
        )
        return self._send_text(msg)

    def _send_text(self, text: str) -> dict:
        url = f"{self.BASE}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": self.recipient,
            "type": "text",
            "text": {"body": text}
        }
        try:
            res = httpx.post(url, json=payload, headers=headers, timeout=10)
            return {"sent": True, "message_id": res.json().get("messages", [{}])[0].get("id")}
        except Exception as e:
            return {"sent": False, "error": str(e)}