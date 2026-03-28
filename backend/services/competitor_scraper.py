# backend/services/competitor_scraper.py

import httpx
import asyncio
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from core.config import settings
from memory.vector_memory import VectorMemory

class CompetitorScraper:
    def __init__(self):
        self.llm = ChatOpenAI(model=settings.OPENAI_MODEL, openai_api_key=settings.OPENAI_API_KEY)
        self.vec = VectorMemory()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def scrape_url(self, url: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15, headers=self.headers) as client:
                res = await client.get(url, follow_redirects=True)
                res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            title = soup.find("title")
            meta_desc = soup.find("meta", {"name": "description"})
            h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
            h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")][:5]
            cta_buttons = [b.get_text(strip=True) for b in soup.find_all(["button", "a"])
                           if any(w in b.get_text().lower() for w in ["buy", "shop", "get", "try", "start", "order"])]
            body_text = soup.get_text(separator=" ", strip=True)[:3000]

            return {
                "url": url,
                "title": title.get_text(strip=True) if title else "",
                "description": meta_desc.get("content", "") if meta_desc else "",
                "headings": h1_tags + h2_tags,
                "cta_buttons": list(set(cta_buttons))[:8],
                "body_preview": body_text[:1000],
            }
        except Exception as e:
            return {"url": url, "error": str(e)}

    async def scrape_multiple(self, urls: list) -> list:
        tasks = [self.scrape_url(url) for url in urls]
        return await asyncio.gather(*tasks)

    def analyze_competitors(self, scraped_data: list, workspace_id: str) -> dict:
        content = "\n\n".join([
            f"URL: {d['url']}\nTitle: {d.get('title')}\nDesc: {d.get('description')}\n"
            f"Headings: {', '.join(d.get('headings', []))}\n"
            f"CTAs: {', '.join(d.get('cta_buttons', []))}\n"
            f"Content: {d.get('body_preview', '')[:500]}"
            for d in scraped_data if not d.get("error")
        ])

        prompt = f"""
        Analyze these competitor websites for an ad campaign strategist:

        {content}

        Return a detailed analysis:
        1. POSITIONING: How do competitors position themselves?
        2. MESSAGING: Key value propositions and angles used
        3. CTA PATTERNS: Most common calls to action
        4. PRICING SIGNALS: Any pricing or offer strategies visible
        5. GAPS: What are they NOT saying? (opportunities)
        6. AD ANGLES: 5 differentiated angles we can use to beat them
        7. KEYWORDS: Implied keywords they are targeting
        8. TONE: What tone/style do they use?
        """
        response = self.llm([
            SystemMessage(content="You are a competitive intelligence expert for digital advertising."),
            HumanMessage(content=prompt)
        ])

        analysis = response.content
        self.vec.store(workspace_id, f"Competitor analysis: {analysis[:500]}", {"type": "competitor_intel"})

        return {
            "raw_data": scraped_data,
            "analysis": analysis,
            "competitor_count": len([d for d in scraped_data if not d.get("error")])
        }

    def find_ad_keywords(self, analysis: str) -> list:
        prompt = f"""
        From this competitor analysis, extract the top 20 keywords they are targeting.
        Return as JSON array only: ["keyword1", "keyword2", ...]

        Analysis: {analysis[:2000]}
        """
        response = self.llm([
            SystemMessage(content="Return only a valid JSON array."),
            HumanMessage(content=prompt)
        ])
        try:
            import json
            return json.loads(response.content)
        except:
            return []