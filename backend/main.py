

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from core.database import Base, engine
from core.error_handler import (app_error_handler, http_error_handler,
                                 validation_error_handler, global_error_handler, AppError)
from core.middleware import RequestLoggingMiddleware

from api import auth, campaign, agent, analytics
from api.ws_agent       import router as ws_router
from api.competitor     import router as competitor_router
from api.voice          import router as voice_router
from api.ab_test        import router as ab_router
from api.plugins        import router as plugin_router
from api.trends         import router as trends_router
from api.budget_scaling import router as budget_router
from api.workspace      import router as workspace_router
from api.users          import router as users_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Ads Consultant API",
    version="3.0.0",
    description="Full Multi-Agent AI SaaS for Google & Meta Ads"
)

# Middleware
app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RequestLoggingMiddleware)

# Error handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, global_error_handler)

# Routes
app.include_router(auth.router,           prefix="/auth",       tags=["Auth"])
app.include_router(users_router,          prefix="/users",      tags=["Users"])
app.include_router(workspace_router,      prefix="/workspace",  tags=["Workspace"])
app.include_router(campaign.router,       prefix="/campaign",   tags=["Campaign"])
app.include_router(agent.router,          prefix="/agent",      tags=["Agent"])
app.include_router(analytics.router,      prefix="/analytics",  tags=["Analytics"])
app.include_router(ws_router,                                   tags=["WebSocket"])
app.include_router(competitor_router,     prefix="/competitor", tags=["Competitor"])
app.include_router(voice_router,          prefix="/voice",      tags=["Voice"])
app.include_router(ab_router,             prefix="/ab",         tags=["A/B Testing"])
app.include_router(plugin_router,         prefix="/plugins",    tags=["Plugins"])
app.include_router(trends_router,         prefix="/trends",     tags=["Trends"])
app.include_router(budget_router,         prefix="/budget",     tags=["Budget"])

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "3.0.0",
        "routes": len(app.routes),
        "features": [
            "multi-agent", "websocket-streaming", "voice",
            "ab-testing", "competitor-intel", "plugins",
            "trend-detection", "auto-budget-scaling",
            "user-management", "workspace-management"
        ]
    }