"""Main API router - combines all API versions"""
from fastapi import APIRouter

from app.api.v1 import health_router

# API v1 router
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router.router)

# Main router - includes all versions
api_router = APIRouter()
api_router.include_router(api_v1_router)
