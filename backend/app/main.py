"""
FastAPI application entry point.

Startup sequence:
  1. Load settings from environment
  2. Configure CORS
  3. Mount API router
  4. Wire up database lifecycle

The financial engine is stateless — no startup initialization needed.
Database tables are created via Alembic migrations, not at startup.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown — nothing to clean up for now


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "NYC multifamily investment analysis API. "
        "Calculates NOI, DSCR, IRR, Monte Carlo risk distributions, "
        "and Investment Quality Scores for NYC rent-stabilized and free-market buildings."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS — allow the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes
app.include_router(api_router)


@app.get("/", tags=["health"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health():
    return JSONResponse({"status": "healthy"})
