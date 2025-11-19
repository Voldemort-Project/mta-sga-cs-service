"""Health check schemas"""
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str = Field(..., description="Health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "service": "sga-cs-service",
                    "version": "0.1.0"
                }
            ]
        }
    }
