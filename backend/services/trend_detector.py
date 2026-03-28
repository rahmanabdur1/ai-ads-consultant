# backend/services/trend_detector.py

import httpx
import json
import asyncio
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from memory.vector_memory import VectorMemory
from core.config import settings

class TrendDetector:
    def __init__(self):
        self.llm = ChatOpenAI(model=settings.OPENAI_MODEL, openai_api_key=settings.OPENAI_API_KEY)
        self.vec = VectorMemory()
        self.headers = {"User-Agent": "Mozilla/5.0 (compatible; TrendBot/1.0)"}

    # ── 1. GOOGLE TRENDS (via SerpAPI or scraping) ──────
    async def fetch_google_trends(self, keywords: list, geo: str = "US") -> dict:
        try:
            encoded = "%2C".join([k.replace(" ", "+") for k in keywords[:5]])
            url = f"https://trends.google.com/trends/api/explore?hl=en-US&tz=-330&req=%7B%22comparisonItem%22%3A%5B%7B%22keyword%22%3A%22{encoded}%22%2C%22geo%22%3A%22{geo}%22%2C%22time%22%3A%22today+3-m%22%7D%5D%7D"
            async with httpx.AsyncClient(timeout=10, headers=self.headers) as client:
                res = await client.get(url)
            return {"raw": res.text[:2000], "keywords": keywords, "geo": geo, "fetched": True}
        except Exception as e:
            return {"keywords": keywords, "geo": geo, "fetched": False, "error": str(e)}

    # ── 2. REDDIT TRENDING ──────────────────────────────
    async def fetch_reddit_trends(self, subreddits: list) -> list:
        posts = []
        async with httpx.AsyncClient(timeout=10, headers=self.headers) as client:
            for sub in subreddits[:3]:
                try:
                    url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
                    res = await client.get(url, headers={"User-Agent": "TrendBot/1.0"})
                    data = res.json()
                    for post in data.get("data", {}).get("children", []):
                        p = post.get("data", {})
                        posts.append({
                            "title": p.get("title"),
                            "score": p.get("score"),
                            "comments": p.get("num_comments"),
                            "subreddit": sub,
                            "url": f"https://reddit.com{p.get('permalink')}"
                        })
                except Exception as e:
                    posts.append({"subreddit": sub, "error": str(e)})
        return sorted(posts, key=lambda x: x.get("score", 0), reverse=True)[:15]

    # ── 3. NEWS TRENDS ──────────────────────────────────
    async def fetch_news_trends(self, query: str, num: int = 10) -> list:
        try:
            url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
            async with httpx.AsyncClient(timeout=10, headers=self.headers) as client:
                res = await client.get(url)
            from xml.etree import ElementTree as ET
            root = ET.fromstring(res.text)
            items = []
            for item in root.findall(".//item")[:num]:
                items.append({
                    "title": item.findtext("title", ""),
                    "link": item.findtext("link", ""),
                    "published": item.findtext("pubDate", ""),
                    "source": item.findtext("source", "")
                })
            return items
        except Exception as e:
            return [{"error": str(e)}]

    # ── 4. TWITTER/X TRENDING (via scrape) ──────────────
    async def fetch_social_signals(self, keywords: list) -> dict:
        signals = {}
        for kw in keywords[:3]:
            try:
                url = f"https://www.google.com/search?q={kw.replace(' ', '+')}+site:twitter.com&num=5"
                async with httpx.AsyncClient(timeout=8, headers=self.headers) as client:
                    res = await client.get(url)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(res.text, "html.parser")
                snippets = [s.get_text()[:100] for s in soup.find_all("span", limit=10)]
                signals[kw] = snippets[:5]
            except Exception as e:
                signals[kw] = []
        return signals

    # ── 5. MAIN ANALYSIS ────────────────────────────────
    async def detect_trends(self, keywords: list, industry: str,
                             workspace_id: str, geo: str = "US") -> dict:
        subreddits_map = {
            "ecommerce":   ["entrepreneur", "ecommerce", "shopify"],
            "saas":        ["saas", "entrepreneur", "startups"],
            "fashion":     ["fashion", "femalefashionadvice", "streetwear"],
            "fitness":     ["fitness", "loseit", "bodybuilding"],
            "food":        ["food", "foodhacks", "mealprep"],
            "finance":     ["personalfinance", "investing", "financialindependence"],
            "tech":        ["technology", "gadgets", "hardware"],
            "travel":      ["travel", "solotravel", "digitalnomad"],
        }
        subreddits = subreddits_map.get(industry.lower(), ["entrepreneur", "marketing"])

        google_task  = self.fetch_google_trends(keywords, geo)
        reddit_task  = self.fetch_reddit_trends(subreddits)
        news_task    = self.fetch_news_trends(f"{industry} trends advertising")
        signals_task = self.fetch_social_signals(keywords[:2])

        google_data, reddit_data, news_data, social_data = await asyncio.gather(
            google_task, reddit_task, news_task, signals_task
        )

        analysis = self._analyze_all_trends(
            keywords, industry, google_data, reddit_data, news_data, social_data
        )
        self.vec.store(workspace_id, f"Trend analysis {industry}: {analysis['summary'][:300]}",
                       {"type": "trend_intel", "industry": industry})

        return {
            "keywords": keywords,
            "industry": industry,
            "geo": geo,
            "analysis": analysis,
            "reddit_hot": reddit_data[:5],
            "news": news_data[:5],
            "social_signals": social_data,
            "generated_at": datetime.utcnow().isoformat()
        }

    def _analyze_all_trends(self, keywords, industry, google, reddit, news, social) -> dict:
        reddit_titles = "\n".join([f"- {p.get('title', '')} ({p.get('score', 0)} upvotes)"
                                    for p in reddit[:10] if not p.get("error")])
        news_titles   = "\n".join([f"- {n.get('title', '')}" for n in news[:8]])
        social_summary = "\n".join([f"{kw}: {', '.join(sigs[:2])}" for kw, sigs in social.items()])

        prompt = f"""
        You are a trend analyst for digital advertising.

        Industry: {industry}
        Keywords being tracked: {', '.join(keywords)}

        REDDIT HOT POSTS:
        {reddit_titles}

        NEWS HEADLINES:
        {news_titles}

        SOCIAL SIGNALS:
        {social_summary}

        Analyze all this data and return JSON:
        {{
            "summary": "2-3 sentence overview of current trends",
            "hot_topics": ["topic1", "topic2", "topic3"],
            "trending_angles": ["angle to use in ads 1", "angle 2", "angle 3"],
            "seasonal_factors": ["any seasonal trends relevant now"],
            "urgency_score": 1-10,
            "recommended_keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],
            "ad_copy_suggestions": ["suggestion 1", "suggestion 2"],
            "avoid_topics": ["topics to avoid in ads right now"],
            "opportunity_window": "brief/medium/long",
            "confidence": 1-100
        }}
        """
        response = self.llm([
            SystemMessage(content="You analyze trends for digital advertising strategy. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])
        try:
            return json.loads(response.content)
        except:
            return {
                "summary": "Trend analysis complete.",
                "hot_topics": keywords,
                "trending_angles": [],
                "urgency_score": 5,
                "recommended_keywords": keywords,
                "ad_copy_suggestions": [],
                "avoid_topics": [],
                "opportunity_window": "medium",
                "confidence": 60
            }