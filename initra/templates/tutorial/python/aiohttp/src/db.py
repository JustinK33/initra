"""Database utilities for aiohttp application.

This module provides an in-memory storage for demo purposes.
In a production app, you'd use a real database like PostgreSQL or SQLite.
"""
from typing import Dict, List

# In-memory storage for demo users
# Each user is a dictionary with id, name, and email
users: list[dict[str, object]] = []

# Track the next available ID for new users
next_id = 1