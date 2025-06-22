"""Authentication API models for requests and responses."""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, Any, Union
from app.models.api.base import BaseResponse


# Request Models
class LoginRequest(BaseModel):
  """Login request with email/username and password."""
  identifier: str = Field(..., description="Email address or username")
  password: str = Field(..., description="User password")
  
  @validator('identifier')
  def validate_identifier(cls, v):
    """Validate that identifier is not empty."""
    if not v or not v.strip():
      raise ValueError('Email or username is required')
    return v.strip()


class TokenRefreshRequest(BaseModel):
  """Token refresh request."""
  refresh_token: str = Field(..., description="Refresh token")


# Response Models
class AuthInfoResponse(BaseModel):
  """Authentication status and user information."""
  authenticated: bool = Field(..., description="Whether user is authenticated")
  user_id: Optional[str] = Field(None, description="User ID if authenticated")
  email: Optional[str] = Field(None, description="User email if authenticated")
  username: Optional[str] = Field(None, description="Username if authenticated")
  token_valid: Optional[bool] = Field(None, description="Whether token is valid")


class LoginResponse(BaseModel):
  """OAuth2 compatible login response."""
  access_token: str = Field(..., description="JWT access token")
  token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
  expires_in: Optional[int] = Field(None, description="Token expiration time in seconds")
  user_id: Optional[str] = Field(None, description="User ID")
  email: Optional[str] = Field(None, description="User email")
  username: Optional[str] = Field(None, description="Username")


class LogoutResponse(BaseResponse):
  """Logout response."""
  user_id: Optional[str] = Field(None, description="Logged out user ID")
  message: str = Field(default="Successfully logged out", description="Logout message") 