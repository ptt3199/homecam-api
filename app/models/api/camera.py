"""Camera API models for requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.api.base import BaseResponse


# Response Models
class CameraStatusResponse(BaseResponse):
  """Camera status response."""
  camera_id: int
  status: str  # "active", "inactive", "error"
  is_streaming: bool = False
  frame_rate: Optional[float] = None
  resolution: Optional[str] = None


class CameraFormatsResponse(BaseResponse):
  """Available camera formats response."""
  formats: List[str]
  default_format: str = "webp" 