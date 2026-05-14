"""Main API v1 router — aggregates all sub-routers."""

from fastapi import APIRouter

from app.api.v1 import auth, financial, properties, reference, scenarios

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(properties.router)
api_router.include_router(financial.router)
api_router.include_router(scenarios.router)
api_router.include_router(reference.router)
