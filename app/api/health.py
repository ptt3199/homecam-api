"""Health check API routes."""

from fastapi import APIRouter
from app.models.api.health import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check():
    """Simple health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="PTT Home Camera API is running"
    ) 