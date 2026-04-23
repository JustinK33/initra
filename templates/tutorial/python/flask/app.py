"""Main application entry point for Flask.

Flask is a lightweight Python web framework that's easy to learn and flexible.
It's great for small to medium-sized projects and prototyping.
"""
from flask import Flask

# Import blueprint (a blueprint groups related routes together)
from src.routes import health_bp


def create_app() -> Flask:
    """Application factory pattern - creates and configures the Flask app."""
    app = Flask(__name__)

    # Register the blueprint to add its routes to the app
    app.register_blueprint(health_bp)

    return app


# Create the app instance - this is what uvicorn/gunicorn will run
app = create_app()


if __name__ == "__main__":
    # This runs the development server when you execute `python src/app.py`
    app.run(debug=True)