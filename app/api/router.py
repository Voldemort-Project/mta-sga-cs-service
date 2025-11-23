"""Main API router - combines all API versions"""
from fastapi import APIRouter

from app.api.v1 import health_router, webhook_router, guest_router, order_router, worker_router, protected_example

# API v1 router
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router.router)
api_v1_router.include_router(guest_router.router)
api_v1_router.include_router(order_router.router)
api_v1_router.include_router(worker_router.router)

# Main router - includes all versions
api_router = APIRouter()
api_router.include_router(api_v1_router)
api_router.include_router(webhook_router.router)
api_router.include_router(protected_example.router)
