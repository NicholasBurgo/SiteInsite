"""
Dependency injection utilities for FastAPI routes.
"""
from fastapi import Depends
from backend.core.config import settings


def get_settings():
    """
    Dependency function to inject settings into route handlers.
    
    Returns:
        Settings: Application settings instance
    """
    return settings

