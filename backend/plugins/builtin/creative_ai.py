# backend/plugins/builtin/creative_ai.py

import openai
from core.config import settings

class CreativeAIPlugin:
    def __init__(self, config: dict):
        self.style = config.get("style", "photorealistic")
        self.aspect_ratio = config.get("aspect_ratio", "1:1")
        self.brand_colors = config.get("brand_colors", [])
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def on_install(self):
        return {"status": "Creative AI ready", "style": self.style}

    def generate_image_prompt(self, ad_copy: str, product: str, audience: str) -> str:
        from langchain_openai import ChatOpenAI
        from langchain.schema import SystemMessage, HumanMessage
        llm = ChatOpenAI(model=settings.OPENAI_MODEL, openai_api_key=settings.OPENAI_API_KEY)
        response = llm([
            SystemMessage(content="You write detailed DALL-E image generation prompts for digital ads."),
            HumanMessage(content=f"""
                Create a DALL-E prompt for an ad image.
                Product: {product}
                Target Audience: {audience}
                Ad Copy: {ad_copy[:200]}
                Style: {self.style}
                Aspect Ratio: {self.aspect_ratio}
                Brand Colors: {', '.join(self.brand_colors) if self.brand_colors else 'any'}
                Make it visually compelling, high quality, suitable for digital advertising.
            """)
        ])
        return response.content

    def generate_image(self, prompt: str) -> dict:
        size_map = {"1:1": "1024x1024", "16:9": "1792x1024", "9:16": "1024x1792"}
        size = size_map.get(self.aspect_ratio, "1024x1024")
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt[:1000],
                size=size,
                quality="standard",
                n=1
            )
            return {"url": response.data[0].url, "revised_prompt": response.data[0].revised_prompt}
        except Exception as e:
            return {"error": str(e)}

    def on_campaign_launched(self, data: dict):
        prompt = self.generate_image_prompt(
            data.get("ad_copy", ""),
            data.get("campaign_name", "product"),
            data.get("target_audience", "general audience")
        )
        return {"image_prompt": prompt, "status": "prompt_generated"}