"""Exception handlers for FastAPI application."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.exceptions.base import HomeCamException
from app.log import get_logger

logger = get_logger(__name__)


async def homecam_exception_handler(request: Request, exc: HomeCamException) -> JSONResponse:
    """Handle HomeCam custom exceptions."""
    logger.error("HomeCam exception: %s", exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "type": exc.__class__.__name__}
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error("Unhandled exception: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "type": "InternalServerError"}
    )


def setup_error_handlers(app: FastAPI) -> None:
    """Set up error handlers for the FastAPI application."""
    app.add_exception_handler(HomeCamException, homecam_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler) 