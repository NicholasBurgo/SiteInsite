"""
Main FastAPI application entry point.

Configures the API server, CORS middleware, and registers all route handlers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.routers import runs, pages, review, confirm, insights, competitors

app = FastAPI(
    title="SiteInsite API",
    description=(
        "Website Intelligence Engine API for scanning websites, analyzing structure, SEO, performance, "
        "content, and layout. Generates comprehensive Website Insight Reports with actionable recommendations."
    ),
    version="1.0.0",
    contact={"name": "SiteInsite Team", "email": "contact@example.com"},
    license_info={"name": "MIT"},
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
app.include_router(pages.router, prefix="/api/pages", tags=["pages"])
app.include_router(review.router, prefix="/api/review", tags=["review"])
app.include_router(confirm.router, prefix="/api/confirm", tags=["confirm"])
app.include_router(insights.router, tags=["insights"])
app.include_router(competitors.router, tags=["competitors"])


@app.get("/health", tags=["meta"])
async def health():
    """
    Health check endpoint.
    
    Returns:
        dict: Simple health status response
    """
    return {"ok": True}