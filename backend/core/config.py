from pydantic_settings import BaseSettings
from pydantic import Field

# SiteInsite version
SITEINSITE_VERSION = "1.0.0"

class Settings(BaseSettings):
    BASE_USER_AGENT: str = Field("SiteInsite/1.0 (+contact@example.com)")
    GLOBAL_CONCURRENCY: int = 12
    PER_HOST_LIMIT: int = 6
    REQUEST_TIMEOUT_SEC: int = 20
    MAX_PAGES_DEFAULT: int = 400
    RENDER_ENABLED: bool = False
    RENDER_BUDGET: float = 0.10
    DATA_DIR: str = "runs"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "*"]

settings = Settings()