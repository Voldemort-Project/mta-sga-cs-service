"""Health check router"""
from fastapi import APIRouter

from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the service is running and healthy"
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint

    Returns:
        HealthResponse: Service health status
    """
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version
    )
