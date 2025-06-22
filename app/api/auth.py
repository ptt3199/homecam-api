"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.models.api.auth import LoginRequest, LoginResponse, LogoutResponse, AuthInfoResponse
from app.operations.auth_ops import login_user, get_current_user, require_auth
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse, summary="Login with credentials", 
  description="""
  Login with email/username and password to get access token.
  
  **SECURITY NOTICE:**
  Only one admin account is allowed for backend login.
  
  **Admin Account:**
  - Username: `admin` OR Email: `admin@ptt-home.local`
  - Password: Contact system administrator
  
  **For Regular Users:**
  - Use the frontend application with Clerk authentication
  - Backend login is restricted to admin only
  
  **OAuth2 Integration:**
  - Click the 🔒 "Authorize" button in docs
  - Enter admin credentials to test protected endpoints
  - All other credentials will be rejected
  """)
async def login_oauth2(form_data: OAuth2PasswordRequestForm = Depends()) -> LoginResponse:
  """OAuth2 compatible login endpoint for FastAPI docs integration.
  
  This endpoint supports both the OAuth2 password flow (for FastAPI docs)
  and direct API calls. Use username field for email or username.
  """
  try:
    # Login with Clerk
    result = await login_user(form_data.username, form_data.password)
    
    return LoginResponse(
      access_token=result["access_token"],
      token_type="bearer",
      expires_in=result.get("expires_in", 3600),
      user_id=result.get("user_id"),
      email=result.get("email"),
      username=result.get("username")
    )
    
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Login failed: {str(e)}"
    )


@router.post("/login/json", response_model=LoginResponse)
async def login_with_json(request: LoginRequest):
  """Alternative login endpoint that accepts JSON payload.
  
  Use this for programmatic access or when you prefer JSON over form data.
  """
  try:
    # Login with Clerk  
    result = await login_user(request.identifier, request.password)
    
    return LoginResponse(
      access_token=result["access_token"],
      token_type="bearer", 
      expires_in=result.get("expires_in", 3600),
      user_id=result.get("user_id"),
      email=result.get("email"),
      username=result.get("username")
    )
    
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Login failed: {str(e)}"
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(current_user: Dict[str, Any] = Depends(require_auth)):
  """Logout current user.
  
  Note: Since we're using JWT tokens, logout is handled client-side
  by discarding the token. This endpoint confirms the logout action.
  """
  return LogoutResponse(
    message="Successfully logged out",
    user_id=current_user.get("sub")
  )


@router.get("/info", response_model=AuthInfoResponse)
async def get_auth_info(current_user: Dict[str, Any] = Depends(get_current_user)):
  """Get current authentication status and user information.
  
  This endpoint shows information about the currently authenticated user.
  """
  return AuthInfoResponse(
    authenticated=True,
    user_id=current_user.get("sub"),
    email=current_user.get("email"),
    username=current_user.get("username"),
    token_valid=True
  ) 