"""Health check routes for FastAPI application.

FastAPI route handlers are defined with decorators like @app.get().
The decorator specifies the HTTP method (GET, POST, etc.) and URL path.
"""
from fastapi import APIRouter, HTTPException

from src.core.config import settings


# APIRouter groups related routes - think of it like a chapter for API endpoints
router = APIRouter(tags=["health"])


@router.get("/")
def health() -> dict[str, str]:
    """Health check endpoint - returns status and current environment.

    Returns:
        dict: A dictionary that FastAPI automatically converts to JSON
    """
    return {"status": "ok", "env": settings.env}


@router.get("/readyz")
def ready() -> dict[str, str]:
    """Readiness check - used by load balancers to know if the app is ready."""
    return {"status": "ready", "project": "{{project_name}}"}