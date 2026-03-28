# backend/agents/creative_agent.py

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from core.config import settings
import json

class CreativeAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )

    def run(self, state: dict) -> dict:
        prompt = f"""
        You are a creative director for digital advertising.
        Based on the strategy and ad copy below, generate detailed creative briefs.

        Strategy: {state.get('strategy', '')}
        Ad Copy: {state.get('ad_copy', '')}
        Platform: {state.get('platform', 'google')}
        Tone: {state.get('tone', 'professional')}
        Target Audience: {state.get('target_audience', 'general')}

        Generate a complete creative brief including:

        1. IMAGE CONCEPTS (3 options):
           - Visual style (photorealistic / illustration / minimal)
           - Scene description
           - Color palette
           - Mood and emotion
           - DALL-E prompt ready for generation

        2. VIDEO CONCEPT (15-second script):
           - Scene 1 (0-5s): hook
           - Scene 2 (5-10s): value proposition
           - Scene 3 (10-15s): CTA
           - Voiceover text
           - Music mood

        3. DESIGN GUIDELINES:
           - Primary color (hex)
           - Secondary color (hex)
           - Font style recommendation
           - Logo placement
           - CTA button style

        4. AD SIZES NEEDED:
           - Facebook/Instagram: 1080x1080, 1080x1920, 1200x628
           - Google Display: 300x250, 728x90, 160x600
           - YouTube thumbnail: 1280x720

        Return as structured text with clear sections.
        """

        response = self.llm([
            SystemMessage(content="You are an award-winning creative director for performance marketing."),
            HumanMessage(content=prompt)
        ])

        state['creative_brief'] = response.content
        state['agent_log'] = state.get('agent_log', []) + ["Creative Agent: Brief generated"]
        return state

    def generate_dall_e_prompts(self, state: dict) -> list:
        prompt = f"""
        Based on this creative brief, extract exactly 3 DALL-E image generation prompts.
        Each prompt must be ready to send directly to DALL-E 3.
        Include: subject, style, lighting, composition, mood.
        Max 200 words each.

        Brief: {state.get('creative_brief', '')[:1000]}

        Return JSON only:
        [
            {{"id": 1, "prompt": "...", "size": "1024x1024", "use_case": "social_feed"}},
            {{"id": 2, "prompt": "...", "size": "1792x1024", "use_case": "banner"}},
            {{"id": 3, "prompt": "...", "size": "1024x1792", "use_case": "story"}}
        ]
        """
        response = self.llm([
            SystemMessage(content="You generate precise DALL-E prompts. Return only valid JSON array."),
            HumanMessage(content=prompt)
        ])
        try:
            return json.loads(response.content)
        except:
            return []