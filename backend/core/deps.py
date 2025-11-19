from fastapi import Depends
from backend.core.config import settings

def get_settings():
    return settings

