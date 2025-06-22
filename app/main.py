"""Main FastAPI application entry point."""

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.core import setup_api
from app.settings import settings
from app.log import get_logger

# API Routes
from app.api import health, camera, auth

logger = get_logger(__name__)
templates = Jinja2Templates(directory="templates")


def create_app():
  """Create and configure the FastAPI application."""
  
  # Setup API with custom configuration
  app = setup_api(prefix="", log_request=True)
  
  # Log current settings for debugging
  logger.info("=== PTT Home Configuration ===")
  logger.info("Camera Device ID: %s", settings.camera_device_id)
  logger.info("Camera Resolution: %sx%s", settings.camera_width, settings.camera_height)
  logger.info("Camera FPS: %s", settings.camera_fps)
  logger.info("=" * 30)
  
  # Include API routers
  app.include_router(health.router)
  app.include_router(camera.router)
  app.include_router(auth.router)
  
  # Add template route
  @app.get('/')
  async def index(request: Request):
    """Serve the main camera interface."""
    return templates.TemplateResponse("index.html", {"request": request})
  
  return app

# Create the FastAPI app instance
app = create_app()
