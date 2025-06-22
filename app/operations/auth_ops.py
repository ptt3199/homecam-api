"""Authentication operations and JWT handling."""

from jose import jwt
import httpx
import time
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, HTTPAuthorizationCredentials, HTTPBearer
from functools import lru_cache
import time
from typing import Optional, Dict, Any
from app.settings import settings
from app.log import get_logger

# OAuth2 scheme for FastAPI docs integration
oauth2_scheme = OAuth2PasswordBearer(
  tokenUrl="/auth/login",
  description="Login with email/username and password to get access token"
)

# HTTP Bearer for manual token usage
security = HTTPBearer()
logger = get_logger(__name__)

class ClerkJWTVerifier:
    """JWT verifier for Clerk authentication."""
    
    def __init__(self):
        self.jwks_cache = {}
        self.jwks_cache_time = 0
        self.jwks_cache_ttl = 3600  # 1 hour
        
    @lru_cache(maxsize=1)
    def get_clerk_jwks_url(self) -> str:
        """Get Clerk JWKS URL from publishable key."""
        if not settings.clerk_publishable_key:
            raise ValueError("CLERK_PUBLISHABLE_KEY not configured")
        
        # Extract domain from publishable key (format: pk_test_xxx or pk_live_xxx)
        key_parts = settings.clerk_publishable_key.split('_')
        if len(key_parts) < 3:
            raise ValueError("Invalid Clerk publishable key format")
        
        # For most cases, use the standard Clerk API domain
        return "https://api.clerk.com/v1/jwks"
    
    def get_jwks(self) -> Dict[str, Any]:
        """Get JWKS from Clerk with caching."""
        current_time = time.time()
        
        # Return cached JWKS if still valid
        if (self.jwks_cache and 
            current_time - self.jwks_cache_time < self.jwks_cache_ttl):
            return self.jwks_cache
        
        try:
            jwks_url = self.get_clerk_jwks_url()
            with httpx.Client(timeout=10.0) as client:
                response = client.get(jwks_url)
                response.raise_for_status()
                
                self.jwks_cache = response.json()
                self.jwks_cache_time = current_time
                
                return self.jwks_cache
            
        except Exception as e:
            logger.error("Failed to fetch JWKS: %s", str(e))
            # Return cached JWKS if available, even if expired
            if self.jwks_cache:
                return self.jwks_cache
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
    
    def get_signing_key(self, token: str) -> str:
        """Get the signing key for token verification."""
        try:
            # Decode header without verification to get kid
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
            
            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing key ID"
                )
            
            # Get JWKS and find matching key
            jwks = self.get_jwks()
            
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    # Convert JWK to PEM format
                    return jwt.algorithms.RSAAlgorithm.from_jwk(key)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate signing key"
            )
            
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token format: {str(e)}"
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify Clerk JWT token."""
        try:
            # Handle admin token
            if token == "admin-jwt-token-ptt-home":
                logger.info("Admin token verification successful")
                return {
                    "sub": "admin-user",
                    "email": settings.admin_email,
                    "username": settings.admin_username,
                    "iat": int(time.time()),
                    "exp": int(time.time()) + 3600
                }
            
            # Handle old development/mock tokens for backward compatibility
            if token == "mock-jwt-token-for-development" or token.startswith("clerk-mock-"):
                logger.warning("Using deprecated mock token")
                if token.startswith("clerk-mock-"):
                    user_id = token.replace("clerk-mock-", "")
                else:
                    user_id = "dev-user-123"
                
                return {
                    "sub": user_id,
                    "email": "dev@example.com",
                    "username": "dev-user",
                    "iat": int(time.time()),
                    "exp": int(time.time()) + 3600
                }
            
            # Get signing key
            signing_key = self.get_signing_key(token)
            
            # Verify and decode token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": False,  # Clerk doesn't always include aud
                }
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            logger.error("Token verification error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )


class ClerkAuthenticator:
    """Handle Clerk authentication operations."""
    
    def __init__(self):
        self.base_url = "https://api.clerk.com/v1"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Clerk API requests."""
        if not settings.clerk_secret_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Clerk secret key not configured"
            )
        
        return {
            "Authorization": f"Bearer {settings.clerk_secret_key}",
            "Content-Type": "application/json"
        }
    
    async def login_with_credentials(self, identifier: str, password: str) -> Dict[str, Any]:
        """Login user with email/username and password using Clerk API."""
        try:
            # Get admin credentials from settings
            ADMIN_USERNAME = settings.admin_username
            ADMIN_EMAIL = settings.admin_email  
            ADMIN_PASSWORD = settings.admin_password
            
            # Check if this is the admin account
            is_admin_login = (
              (identifier == ADMIN_USERNAME or identifier == ADMIN_EMAIL) and 
              password == ADMIN_PASSWORD
            )
            
            if is_admin_login:
              logger.info("Admin login successful for: %s", identifier)
              return {
                "access_token": "admin-jwt-token-ptt-home",
                "user_id": "admin-user",
                "email": ADMIN_EMAIL,
                "username": ADMIN_USERNAME,
                "expires_in": 3600
              }
            
            # For development mode, still allow the admin only
            if settings.development_mode:
              logger.warning("Development mode: Invalid credentials for %s", identifier)
              raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Only admin account is allowed."
              )
            
            # Real Clerk authentication (for production)
            logger.info("Attempting Clerk user lookup for: %s", identifier)
            
            # Try using Clerk's Backend API to verify user exists
            async with httpx.AsyncClient(timeout=30.0) as client:
              # Use Clerk Backend API to find the user
              backend_url = f"{self.base_url}/users"
              
              # Get headers for Clerk API
              headers = self._get_headers()
              
              # Search for user by email or username
              search_params = {}
              if "@" in identifier:
                search_params["email_address"] = [identifier]
              else:
                search_params["username"] = [identifier]
              
              logger.info("Searching for user in Clerk with params: %s", search_params)
              
              user_response = await client.get(
                backend_url,
                headers=headers,
                params=search_params
              )
              
              logger.info("Clerk API response status: %s", user_response.status_code)
              
              if user_response.status_code != 200:
                logger.error("Failed to find user in Clerk: %s - %s", user_response.status_code, user_response.text)
                raise HTTPException(
                  status_code=status.HTTP_401_UNAUTHORIZED,
                  detail="Invalid credentials"
                )
              
              users = user_response.json()
              if not users:
                logger.error("User not found in Clerk database")
                raise HTTPException(
                  status_code=status.HTTP_401_UNAUTHORIZED,
                  detail="Invalid credentials"
                )
              
              user = users[0]
              user_id = user["id"]
              
              logger.info("Found user in Clerk: %s", user_id)
              
              # For production, we still need to implement real password verification
              # For now, reject all non-admin logins in production too
              logger.warning("Production Clerk login not implemented, rejecting user: %s", user_id)
              raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Clerk password verification not implemented. Use frontend authentication."
              )
              
        except HTTPException:
            raise
        except httpx.RequestError as e:
            logger.error("Authentication service error: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
        except Exception as e:
            logger.error("Login error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login failed"
            )
    
    def _get_frontend_api_domain(self) -> str:
        """Extract frontend API domain from publishable key."""
        if not settings.clerk_publishable_key:
            raise ValueError("Clerk publishable key not configured")
        
        # Extract instance ID from publishable key
        # Format: pk_test_<instance>.<domain> or pk_live_<instance>.<domain>
        key_parts = settings.clerk_publishable_key.split('_')
        if len(key_parts) >= 3:
            instance_part = '_'.join(key_parts[2:])  # Everything after pk_test_ or pk_live_
            if '.' in instance_part:
                return instance_part
        
        # Fallback to default
        return "clerk.accounts.dev"


# Global instances
clerk_verifier = ClerkJWTVerifier()
clerk_authenticator = ClerkAuthenticator()


async def login_user(identifier: str, password: str) -> Dict[str, Any]:
    """Login user with email/username and password."""
    return await clerk_authenticator.login_with_credentials(identifier, password)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Dependency to get current authenticated user from JWT token.
    
    This uses OAuth2PasswordBearer which integrates with FastAPI docs.
    Users can click the lock icon and enter credentials to get a token.
    """
    # Skip authentication in development mode
    if settings.development_mode:
        return {"sub": "dev-user", "email": "dev@localhost"}
    
    # Skip authentication if Clerk verification is disabled
    if not settings.clerk_jwt_verification:
        return {"sub": "anonymous", "email": "anonymous@localhost"}
    
    # Verify token
    user_payload = clerk_verifier.verify_token(token)
    return user_payload


async def get_current_user_bearer(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Alternative dependency for manual Bearer token usage."""
    # Skip authentication in development mode
    if settings.development_mode:
        return {"sub": "dev-user", "email": "dev@localhost"}
    
    # Skip authentication if Clerk verification is disabled
    if not settings.clerk_jwt_verification:
        return {"sub": "anonymous", "email": "anonymous@localhost"}
    
    # Verify token
    token = credentials.credentials
    user_payload = clerk_verifier.verify_token(token)
    return user_payload


async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[Dict[str, Any]]:
    """Optional authentication - returns user if authenticated, None if not."""
    if not token:
        return None
    
    try:
        return await get_current_user(token)
    except HTTPException:
        return None


def require_auth(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Simple dependency that requires authentication.
    
    Use this for protected endpoints. Integrates with FastAPI docs OAuth2.
    """
    return user 