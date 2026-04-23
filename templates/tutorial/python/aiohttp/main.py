"""Main application entry point for aiohttp.

aiohttp is an asynchronous HTTP client/server framework for Python.
It uses async/await syntax and can handle many concurrent connections efficiently.
"""
from aiohttp import web

# Import route registration function
from src.routes import register_routes


def create_app() -> web.Application:
    """Creates and configures the aiohttp application.

    The Application class is the main entry point for aiohttp.
    All configuration (routes, middlewares, signals) is done here.
    """
    app = web.Application()

    # Register all routes with the application
    register_routes(app)

    return app


def main() -> None:
    """Runs the application.

    web.run_app() is a convenience function that:
    1. Creates an event loop
    2. Starts the server
    3. Handles graceful shutdown
    """
    web.run_app(create_app(), port=8000)


if __name__ == "__main__":
    main()