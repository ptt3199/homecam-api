"""Camera API models for requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from app.models.api.base import BaseResponse


class ImageFormat(str, Enum):
  """Supported image formats."""
  JPEG = "jpeg"
  WEBP = "webp"
  PNG = "png"


class QualityLevel(str, Enum):
  """Quality levels for image compression."""
  LOW = "low"
  MEDIUM = "medium"
  HIGH = "high"


# Request Models
class CameraStreamRequest(BaseModel):
  """Request to start camera streaming."""
  camera_id: int = Field(default=0, ge=0, description="Camera device ID")
  format: ImageFormat = Field(default=ImageFormat.WEBP, description="Image format")
  quality: QualityLevel = Field(default=QualityLevel.MEDIUM, description="Image quality")


class SnapshotRequest(BaseModel):
  """Request for camera snapshot."""
  camera_id: int = Field(default=0, ge=0, description="Camera device ID")
  format: ImageFormat = Field(default=ImageFormat.WEBP, description="Image format")
  quality: QualityLevel = Field(default=QualityLevel.HIGH, description="Image quality")


class StreamControlRequest(BaseModel):
  """Request to control streaming."""
  action: str = Field(..., pattern="^(start|stop|pause|resume)$", description="Stream action")
  camera_id: Optional[int] = Field(default=None, ge=0, description="Camera device ID")


# Response Models
class CameraStatusResponse(BaseResponse):
  """Camera status response."""
  camera_id: int
  status: str  # "active", "inactive", "error"
  is_streaming: bool = False
  frame_rate: Optional[float] = None
  resolution: Optional[str] = None


class StreamStatusResponse(BaseResponse):
  """Streaming status response."""
  is_active: bool
  camera_id: Optional[int] = None
  start_time: Optional[datetime] = None
  frame_count: Optional[int] = None


class CameraFormatsResponse(BaseResponse):
  """Available camera formats response."""
  formats: List[str]
  default_format: str = "webp" 