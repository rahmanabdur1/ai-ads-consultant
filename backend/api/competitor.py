# backend/api/competitor.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from services.competitor_scraper import CompetitorScraper

router = APIRouter()
scraper = CompetitorScraper()

class ScrapeRequest(BaseModel):
    urls: List[str]
    workspace_id: str

@router.post("/analyze")
async def analyze_competitors(data: ScrapeRequest):
    scraped = await scraper.scrape_multiple(data.urls)
    analysis = scraper.analyze_competitors(scraped, data.workspace_id)
    keywords = scraper.find_ad_keywords(analysis["analysis"])
    return {
        "competitors_analyzed": analysis["competitor_count"],
        "analysis": analysis["analysis"],
        "suggested_keywords": keywords,
        "raw_data": [{"url": d["url"], "title": d.get("title"), "ctas": d.get("cta_buttons")}
                     for d in scraped]
    }

# Add to main.py:
# from api.competitor import router as competitor_router
# app.include_router(competitor_router, prefix="/competitor", tags=["Competitor"])