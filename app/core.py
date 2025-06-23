"""Common API functions and FastAPI setup."""

import os
import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import (
    _AsyncGeneratorContextManager,  # type: ignore[reportPrivateUsage]
    asynccontextmanager,
)
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.exceptions.handlers import setup_error_handlers
from app.log import get_logger
from app.settings import settings
from app.operations.camera_ops import release_camera

logger = get_logger(__name__)


def custom_lifespan(
    ls: Callable[[FastAPI], Awaitable[None]] | None = None,
) -> Callable[[FastAPI], _AsyncGeneratorContextManager[None, None]]:
    """Create a custom lifespan for service defined lifespan."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        logger.info("Starting FastAPI application")
        logger.debug("Generic configuration")
        logger.debug(str(settings.model_dump_json(indent=2)))
        if ls:
            await ls(app)
        logger.info("Application path: %s", app.root_path)
        for route in app.routes:
            if isinstance(route, APIRoute):
                logger.debug("Route: %s%s -> %s", app.root_path, route.path, route.name)

        # Startup
        logger.info("Starting up PTT Home Camera API...")
        # Camera will be initialized on first use

        yield
        
        # Cleanup phase
        release_camera()
        logger.info("Stopping FastAPI application")

        # Shutdown
        logger.info("Shutting down PTT Home Camera API...")
        release_camera()

    return lifespan


def custom_generate_unique_id(route: APIRoute) -> str:
    """Generate unique ID for API routes."""
    return f"{route.tags[-1]}-{route.name}" if route.tags else route.name


def setup_api(
    prefix: str,
    service_lifespan: Callable[[FastAPI], Awaitable[None]] | None = None,
    *,
    log_request: bool = True,
) -> FastAPI:
    """Set up and configure a FastAPI application with custom settings.

    This function creates a new FastAPI instance, configures its root path,
    adds optional request logging middleware, sets up CORS, and applies
    error handlers.

    Args:
        prefix (str): The URL prefix for the API's root path.
        service_lifespan (Callable[[FastAPI], Awaitable[None]] | None, optional):
            An optional async function to be called during the application's lifespan.
            Defaults to None.
        log_request (boolean, optional): Flag to enable request logging middleware.
            Defaults to True.

    Returns:
        FastAPI: A configured FastAPI application instance.

    """
    app = FastAPI(
        root_path=f"/{prefix}",
        lifespan=custom_lifespan(service_lifespan),
        generate_unique_id_function=custom_generate_unique_id,
        title="PTT Home Camera API",
        description="Home camera streaming and control API with authentication",
        version="1.0.0",
        openapi_tags=[  
            {
                "name": "camera",
                "description": "Camera streaming and control"
            },
            {
                "name": "health",
                "description": "System health and status"
            }
        ]
    )
    
    if log_request:
        @app.middleware("http")
        async def log_requests(
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            start_time = time.perf_counter()
            rid = uuid4()
            logger.info(
                f"{rid} - beg - {request.method} {request.url} {request.query_params}",
            )
            response = await call_next(request)
            process_time = time.perf_counter() - start_time
            logger.info(
                f"{rid} - end - {response.status_code} - {process_time:.2f} seconds",
            )
            return response

    # Configure CORS
    origins = [
        "http://localhost",
        "http://localhost:3000",
        "https://localhost",
        "https://localhost:3000",
        "https://homecam.thanhpt.xyz",
        "https://homecam.thanhpt.xyz:3000",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    setup_error_handlers(app)

    # Configure static files and templates
    setup_static_files(app)
    setup_templates(app)

    logger.info("FastAPI application configured successfully")
    return app


def setup_static_files(app: FastAPI) -> None:
    """Configure static file serving."""
    if os.path.exists("templates"):
        app.mount("/static", StaticFiles(directory="templates"), name="static")


def setup_templates(app: FastAPI) -> None:
    """Configure template rendering."""
    if os.path.exists("templates"):
        templates = Jinja2Templates(directory="templates")
        
        @app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            """Serve the home page."""
            return templates.TemplateResponse("index.html", {"request": request}) 