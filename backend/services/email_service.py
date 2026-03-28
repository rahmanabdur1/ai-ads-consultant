# backend/services/email_service.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings

class EmailService:
    def __init__(self):
        self.host = getattr(settings, 'SMTP_HOST', 'smtp.gmail.com')
        self.port = getattr(settings, 'SMTP_PORT', 587)
        self.user = getattr(settings, 'SMTP_USER', '')
        self.password = getattr(settings, 'SMTP_PASSWORD', '')
        self.from_email = getattr(settings, 'FROM_EMAIL', self.user)

    def send(self, to_email: str, subject: str, html_body: str) -> bool:
        if not self.user or not self.password:
            print(f"[EMAIL STUB] To: {to_email} | Subject: {subject}")
            return True
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg.attach(MIMEText(html_body, "html"))
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            return True
        except Exception as e:
            print(f"Email failed: {e}")
            return False

    def send_campaign_launched(self, to_email: str, campaign_name: str,
                                platform: str, budget: float):
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
          <h2 style="color:#2563a8">🚀 Campaign Launched!</h2>
          <p>Your campaign <strong>{campaign_name}</strong> has been successfully launched.</p>
          <table style="border-collapse:collapse;width:100%">
            <tr><td style="padding:8px;border:1px solid #ddd">Platform</td>
                <td style="padding:8px;border:1px solid #ddd">{platform.capitalize()}</td></tr>
            <tr><td style="padding:8px;border:1px solid #ddd">Budget</td>
                <td style="padding:8px;border:1px solid #ddd">${budget}</td></tr>
          </table>
          <p style="color:#666;font-size:12px">AI Ads Consultant</p>
        </div>
        """
        return self.send(to_email, f"Campaign Launched: {campaign_name}", html)

    def send_optimization_alert(self, to_email: str, campaign_name: str,
                                 action: str, reason: str):
        color = {"SCALE_UP": "#1D9E75", "PAUSE": "#D85A30", "REDUCE": "#BA7517"}.get(action, "#2563a8")
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
          <h2 style="color:{color}">⚙️ Budget Optimization: {action}</h2>
          <p>Campaign: <strong>{campaign_name}</strong></p>
          <p>{reason}</p>
          <p style="color:#666;font-size:12px">AI Ads Consultant</p>
        </div>
        """
        return self.send(to_email, f"Campaign Optimization: {action}", html)

    def send_ab_winner(self, to_email: str, campaign_name: str,
                       winner: str, lift: float):
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
          <h2 style="color:#1D9E75">🏆 A/B Test Winner: Variant {winner}</h2>
          <p>Campaign: <strong>{campaign_name}</strong></p>
          <p>Winning variant achieved <strong>+{lift}% lift</strong> over the control.</p>
          <p style="color:#666;font-size:12px">AI Ads Consultant</p>
        </div>
        """
        return self.send(to_email, f"A/B Test Result: Variant {winner} Wins!", html)