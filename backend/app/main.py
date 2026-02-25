"""
LancasterLink Backend – FastAPI Application Entry Point.

This is the module loaded by uvicorn (see Dockerfile CMD and docker-compose
backend service command):

    uvicorn app.main:app --host 0.0.0.0 --port 8000

Responsibilities:
    • Create the FastAPI application instance.
    • Configure CORS middleware (NFR-UA-01 mobile access).
    • Register API routers from app.api.routes (Section 6 of Design Doc).
    • Expose /api/health for Docker healthchecks.
    • Set up the database engine and session on startup; tear down on shutdown.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.management.data_access import engine, sessionmanager

# Import route modules
from app.api.routes import departures, journey, live, map as map_routes


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan handler.

    Startup  – verify DB connectivity, create tables if missing.
    Shutdown – dispose of the SQLAlchemy engine / connection pool.
    """
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    logger = logging.getLogger("lancasterlink")

    # Startup
    logger.info("Starting LancasterLink backend v%s", settings.app_version)
    sessionmanager.init(settings.database_url)
    logger.info("Database engine initialised")

    yield  # ← application runs here

    # Shutdown
    logger.info("Shutting down – disposing DB engine")
    sessionmanager.close()


# ── Application factory ─────────────────────────────────────────────────────

settings = get_settings()

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Required for the frontend (served from Nginx on a different origin during
# local development) to call the API.  In production the Nginx reverse proxy
# makes this same-origin, but we keep it for flexibility.

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ─────────────────────────────────────────────────────────────
# Used by docker-compose healthcheck and the frontend to confirm the API
# is reachable.  Intentionally lightweight.

@app.get("/api/health", tags=["system"])
async def health_check():
    """Return a simple health status (used by Docker healthchecks)."""
    return {"status": "ok", "version": settings.app_version}


# ── Register API routers ────────────────────────────────────────────────────
# Endpoint grouping follows Design Doc §6.2:
#   /api/journey      – Journey planning
#   /api/departures   – Stop-level departure boards
#   /api/live         – Live vehicle positions
#   /api/map          – Combined map state

app.include_router(journey.router,    prefix="/api/journey",    tags=["journey"])
app.include_router(departures.router, prefix="/api/departures", tags=["departures"])
app.include_router(live.router,       prefix="/api/live",       tags=["live"])
app.include_router(map_routes.router, prefix="/api/map",        tags=["map"])

