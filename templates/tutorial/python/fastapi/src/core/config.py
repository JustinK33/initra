"""Configuration settings for the application.

This module uses environment variables to make the app flexible:
- APP_ENV: controls whether you're in development, staging, or production
- DATABASE_URL: specifies where your database is located
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Settings class - frozen=True makes it immutable (read-only)."""
    # Get from environment, default to 'development' if not set
    env: str = os.getenv("APP_ENV", "development")
    db_url: str = os.getenv("DATABASE_URL", "sqlite:///data/app.db")


# Create a single instance that all modules can import
settings = Settings()