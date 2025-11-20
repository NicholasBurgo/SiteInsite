from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal

# SiteInsite version
SITEINSITE_VERSION = "1.0.0"

# Performance measurement modes
PerfMode = Literal["controlled", "realistic", "stress"]

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
    PERF_MODE: PerfMode = Field("controlled", description="Performance measurement mode: controlled, realistic, or stress")
    PERF_SAMPLES_PER_URL: int = Field(3, description="Number of performance samples to take per URL in controlled mode")
    PERF_BANDWIDTH_MBPS: float = Field(5.0, description="Simulated bandwidth in Mbps for throttling calculation")
    USE_MULTIPROCESSING: bool = Field(True, description="Use multiprocessing for CPU-bound extraction tasks (auto-detects CPU cores)")
    EXTRACTION_WORKERS: int | None = Field(12, description="Number of extraction worker processes (12 by default, None = auto-detect: CPU cores - 1)")

settings = Settings()