"""Health check API models."""

from app.models.api.base import BaseResponse
from typing import Optional


class HealthResponse(BaseResponse):
  """Health check response."""
  status: str = "healthy"
  version: Optional[str] = None 