"""Health check API routes."""

from fastapi import APIRouter
from app.models.api.health import HealthResponse
import httpx
import asyncio
from app.log import get_logger

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger(__name__)


@router.get("", response_model=HealthResponse)
async def health_check():
    """Simple health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="PTT Home Camera API is running"
    )


@router.get("/network")
async def network_connectivity_check():
    """Test network connectivity for debugging Docker networking issues."""
    results = {}
    
    # Test basic internet connectivity
    test_urls = [
        "https://www.google.com",
        "https://httpbin.org/get",
        "https://clerk.com",  # Test Clerk domain connectivity
    ]
    
    for url in test_urls:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                results[url] = {
                    "status": "success",
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
        except httpx.ConnectError as e:
            results[url] = {
                "status": "connection_error",
                "error": str(e)
            }
        except httpx.TimeoutException as e:
            results[url] = {
                "status": "timeout",
                "error": str(e)
            }
        except Exception as e:
            results[url] = {
                "status": "error",
                "error": str(e)
            }
    
    # Test DNS resolution
    try:
        import socket
        clerk_ip = socket.gethostbyname("clerk.com")
        results["dns_test"] = {
            "status": "success",
            "clerk_ip": clerk_ip
        }
    except Exception as e:
        results["dns_test"] = {
            "status": "error",
            "error": str(e)
        }
    
    return {
        "status": "completed",
        "message": "Network connectivity test results",
        "results": results
    } 