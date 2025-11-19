import aiohttp
import asyncio
from typing import Optional, Literal, List, Dict, Any
from dataclasses import dataclass
from time import perf_counter
from backend.core.config import Settings
from backend.crawl.bot_avoidance import BotAvoidanceStrategy
from backend.crawl.performance import simulate_bandwidth_throttling

@dataclass
class FetchResponse:
    url: str
    content: bytes
    content_type: str
    status: int
    headers: dict
    path: str
    blocked_reason: str | None = None
    load_time_ms: Optional[int] = None
    content_length_bytes: Optional[int] = None
    ttfb_ms: Optional[int] = None  # Time to First Byte
    render_mode: Literal["raw", "js"] = "raw"  # Whether JS rendering was used
    effective_load_ms: Optional[float] = None  # Load time with bandwidth throttling simulation

class Fetcher:
    """
    Async HTTP fetcher with rate limiting and retry logic.
    """
    
    def __init__(self, settings: Settings, bot_strategy: BotAvoidanceStrategy | None = None, perf_mode: Literal["controlled", "realistic", "stress"] = "controlled"):
        self.settings = settings
        self.session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(settings.GLOBAL_CONCURRENCY)
        self.bot_strategy = bot_strategy
        self.perf_mode = perf_mode
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=self.settings.REQUEST_TIMEOUT_SEC)
        
        # Controlled mode: static headers for consistent measurement
        if self.perf_mode == "controlled":
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.84 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "no-store",
                "Connection": "keep-alive"
            }
        else:
            headers = {"User-Agent": self.settings.BASE_USER_AGENT}
        
        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def fetch(self, url: str, render_mode: Literal["raw", "js"] = "raw") -> Optional[FetchResponse]:
        """
        Fetch URL with rate limiting and error handling.
        
        Args:
            url: URL to fetch
            render_mode: Whether this is a JS-rendered request or raw fetch
        """
        if not self.session:
            await self.__aenter__()
            
        async with self._semaphore:
            try:
                if self.bot_strategy:
                    await self.bot_strategy.before_request(url)
                    request_kwargs = self.bot_strategy.prepare_request_kwargs(url)
                else:
                    request_kwargs = {}

                status: int | None = None
                load_time_ms: Optional[int] = None
                ttfb_ms: Optional[int] = None
                content_length_bytes: Optional[int] = None

                start_time = perf_counter()
                async with self.session.get(url, **request_kwargs) as response:
                    # Measure TTFB (Time to First Byte)
                    ttfb_time = perf_counter()
                    ttfb_ms = int((ttfb_time - start_time) * 1000)
                    
                    content = await response.read()
                    end_time = perf_counter()
                    load_time_ms = int((end_time - start_time) * 1000)
                    content_length_bytes = len(content)
                    content_type = response.headers.get('content-type', 'text/html')
                    status = response.status
                    blocked_reason = None
                    if self.bot_strategy:
                        blocked_reason = self.bot_strategy.detect_block(url, status, dict(response.headers), content)
                    
                    # Apply bandwidth throttling simulation in controlled mode
                    effective_load_ms = None
                    if self.perf_mode == "controlled" and content_length_bytes > 0:
                        effective_load_ms = simulate_bandwidth_throttling(
                            load_time_ms,
                            content_length_bytes,
                            self.settings.PERF_BANDWIDTH_MBPS
                        )
                    
                    return FetchResponse(
                        url=str(response.url),
                        content=content,
                        content_type=content_type,
                        status=response.status,
                        headers=dict(response.headers),
                        path=url,
                        blocked_reason=blocked_reason,
                        load_time_ms=load_time_ms,
                        content_length_bytes=content_length_bytes,
                        ttfb_ms=ttfb_ms,
                        render_mode=render_mode,
                        effective_load_ms=effective_load_ms
                    )
            except Exception as e:
                print(f"Fetch error for {url}: {e}")
                return None
            finally:
                if self.bot_strategy:
                    self.bot_strategy.after_request(url, status)
    
    async def fetch_samples(
        self,
        url: str,
        num_samples: int = 3,
        render_mode: Literal["raw", "js"] = "raw"
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple samples of a URL for performance measurement.
        
        Args:
            url: URL to sample
            num_samples: Number of samples to take
            render_mode: Whether this is JS-rendered or raw fetch
        
        Returns:
            List of sample dictionaries with performance metrics
        """
        samples: List[Dict[str, Any]] = []
        
        for i in range(num_samples):
            resp = await self.fetch(url, render_mode=render_mode)
            if resp and resp.status == 200:
                # Use effective_load_ms if available (controlled mode), otherwise load_time_ms
                load_ms = resp.effective_load_ms if resp.effective_load_ms is not None else resp.load_time_ms
                
                sample = {
                    "load_ms": round(load_ms, 2) if load_ms else None,
                    "ttfb_ms": resp.ttfb_ms,
                    "render_mode": resp.render_mode,
                    "status": resp.status,
                    "content_length_bytes": resp.content_length_bytes,
                    "raw_load_ms": resp.load_time_ms  # Keep raw time for debugging
                }
                samples.append(sample)
            else:
                # Still record failed samples
                if resp:
                    sample = {
                        "load_ms": None,
                        "ttfb_ms": None,
                        "render_mode": render_mode,
                        "status": resp.status,
                        "content_length_bytes": None,
                        "raw_load_ms": None
                    }
                    samples.append(sample)
        
        return samples
                
    async def fetch_text(self, url: str) -> Optional[str]:
        """
        Fetch URL and return text content.
        """
        resp = await self.fetch(url)
        if resp and resp.status == 200:
            try:
                return resp.content.decode('utf-8')
            except UnicodeDecodeError:
                return resp.content.decode('utf-8', errors='ignore')
        return None