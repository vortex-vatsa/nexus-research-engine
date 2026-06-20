"""FastAPI application entry point for Nexus Research Engine."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import NexusBaseError


# Initialize logger
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown event handler."""
    # Startup
    settings = get_settings()
    logger.info("Starting Nexus Research Engine...")

    # Initialize LLM router on startup
    from app.providers.llm_router import llm_router
    await llm_router.initialize()

    # Database initialization and job healing will be added in Task 1.7

    logger.info("Startup complete")
    yield
    # Shutdown
    logger.info("Shutting down Nexus Research Engine...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Nexus Research Engine",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add SessionMiddleware for OAuth session management
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
        https_only=False,  # Set to True in production
        same_site="lax",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register global exception handlers
    @app.exception_handler(NexusBaseError)
    async def nexus_error_handler(request, exc: NexusBaseError):
        """Handle custom Nexus exceptions."""
        return JSONResponse(
            status_code=400,
            content={
                "error": str(exc),
                "context": exc.context,
                "type": type(exc).__name__,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request, exc: Exception):
        """Handle unhandled exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "type": type(exc).__name__,
            },
        )

    # Mount routers (stubs for now, will be implemented in later tasks)
    from app.routers import auth, research, workspaces, notebook

    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(research.router, prefix="/research", tags=["research"])
    app.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
    app.include_router(notebook.router, prefix="/notebook", tags=["notebook"])

    # Health check endpoint
    @app.get("/health")
    async def health():
        """Health check endpoint. Full implementation in Task 1.7."""
        return {
            "status": "ok",
            "version": "1.0.0",
            "services": {
                "llm": "ok",
                "tavily": "ok",
                "database": "ok",
                "storage": "ok",
            },
        }

    return app


app = create_app()
