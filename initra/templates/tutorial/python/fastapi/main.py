"""Main application entry point for FastAPI.

FastAPI is a modern Python web framework that's fast, easy to use, and production-ready.
It automatically generates API documentation (OpenAPI/Swagger) and handles request validation.
"""
from fastapi import FastAPI

# Import route handlers (these define your API endpoints)
from src.api.routes.health import router as health_router
from src.api.routes.users import router as users_router

# Create the FastAPI application instance
# FastAPI is the web framework - it handles HTTP requests and responses
app = FastAPI(title="{{project_name}}")

# Register route handlers with the application
# Each router contains related endpoints grouped together
app.include_router(health_router)
app.include_router(users_router)


@app.get("/readyz")
def ready() -> dict[str, str]:
    """Health check endpoint - returns basic status info."""
    return {"status": "ready", "project": "{{project_name}}"}