"""Base API models using Pydantic."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BaseResponse(BaseModel):
  """Base response model."""
  success: bool = True
  message: Optional[str] = None
  timestamp: datetime = datetime.now()


class ErrorResponse(BaseModel):
  """Error response model."""
  success: bool = False
  error: str
  error_type: str
  timestamp: datetime = datetime.now() 