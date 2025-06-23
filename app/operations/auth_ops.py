"""Authentication operations and JWT handling."""

from app.settings import settings   
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
from jose.backends import RSAKey
import httpx
import time
from fastapi import HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache
from typing import Dict, Any
from app.log import get_logger

# HTTP Bearer for token authentication
security = HTTPBearer()
logger = get_logger(__name__)

class ClerkJWTVerifier:
    """JWT verifier for Clerk authentication."""
    
    def __init__(self):
        self.jwks_cache = {}
        self.jwks_cache_time = 0
        self.jwks_cache_ttl = 3600  # 1 hour
    
    @lru_cache(maxsize=128)
    def get_jwks_from_url(self, jwks_url: str) -> Dict[str, Any]:
        """Get JWKS from URL with caching."""
        current_time = time.time()
        
        # Check cache
        if (jwks_url in self.jwks_cache and 
            current_time - self.jwks_cache_time < self.jwks_cache_ttl):
            return self.jwks_cache[jwks_url]
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(jwks_url)
                response.raise_for_status()
                jwks = response.json()
                
                # Cache the result
                self.jwks_cache[jwks_url] = jwks
                self.jwks_cache_time = current_time
                
                return jwks
                
        except Exception as e:
            logger.error("Failed to fetch JWKS from %s: %s", jwks_url, e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch signing keys"
            )
    
    def get_jwks_url_from_token(self, token: str) -> str:
        """Extract JWKS URL from token issuer."""
        try:
            # Decode without verification to get issuer
            payload = jwt.get_unverified_claims(token)
            issuer = payload.get('iss')
            
            if not issuer:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing issuer"
                )
            
            # Construct JWKS URL from issuer
            if issuer.endswith('/'):
                issuer = issuer[:-1]
            
            return f"{issuer}/.well-known/jwks.json"
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token format: {str(e)}"
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
            
            # Get JWKS from token issuer
            jwks_url = self.get_jwks_url_from_token(token)
            jwks = self.get_jwks_from_url(jwks_url)
            
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    # Convert JWK to RSA key
                    return RSAKey(key, algorithm='RS256').to_pem()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate signing key"
            )
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token format: {str(e)}"
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify Clerk JWT token."""
        try:
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
            
            logger.info("Token verification successful for user: %s", payload.get("sub"))
            return payload
            
        except ExpiredSignatureError:
            logger.warning("Expired token presented")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except JWTError as e:
            logger.warning("Invalid JWT token: %s", str(e))
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


# Global verifier instance
clerk_verifier = ClerkJWTVerifier()


def generate_streaming_token(user_id: str, expires_minutes: int = 5) -> str:
    """
    Generate a short-lived token specifically for streaming endpoints.
    This reduces security risks by having tokens expire quickly.
    """
    import time
    from jose import jwt
    
    payload = {
        "user_id": user_id,
        "token_type": "streaming",
        "exp": int(time.time()) + (expires_minutes * 60),
        "iat": int(time.time())
    }
    
    # Use a simple secret for streaming tokens (separate from Clerk)
    # In production, use a strong secret key
    streaming_secret = settings.streaming_token_secret
    return jwt.encode(payload, streaming_secret, algorithm="HS256")


def verify_streaming_token(token: str) -> Dict[str, Any]:
    """
    Verify a short-lived streaming token.
    """
    try:
        streaming_secret = settings.streaming_token_secret
        payload = jwt.decode(token, streaming_secret, algorithms=["HS256"])
        
        if payload.get("token_type") != "streaming":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
            
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Streaming token expired"
        )
    except jwt.JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid streaming token: {str(e)}"
        )


async def get_current_user_header(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current user from Authorization Bearer header.
    Use this for regular API endpoints (POST, PUT, DELETE, etc.)
    """
    try:
        token = credentials.credentials
        payload = clerk_verifier.verify_token(token)
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "username": payload.get("username", payload.get("email", "").split("@")[0]),
            "token_payload": payload,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Header auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def get_current_user_stream(token: str = Query(...)) -> Dict[str, Any]:
    """
    Get current user from query parameter token.
    Use this for streaming endpoints that need URL-based auth.
    
    Accepts both:
    1. Clerk JWT tokens (full auth)
    2. Short-lived streaming tokens (streaming-only access)
    """
    try:
        # Try Clerk JWT first
        try:
            payload = clerk_verifier.verify_token(token)
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "username": payload.get("username", payload.get("email", "").split("@")[0]),
                "token_payload": payload,
                "token_type": "clerk_jwt"
            }
        except Exception as e:
            logger.error(f"Clerk JWT verification error: {str(e)}")
            # If Clerk JWT fails, try streaming token
            payload = verify_streaming_token(token)
            return {
                "user_id": payload.get("user_id"),
                "token_payload": payload,
                "token_type": "streaming"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stream auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


# Keep the old function name for compatibility
get_current_user = get_current_user_header