import aiohttp
import asyncio
from typing import Optional
from dataclasses import dataclass
from time import perf_counter
from backend.core.config import Settings
from backend.crawl.bot_avoidance import BotAvoidanceStrategy

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

class Fetcher:
    """
    Async HTTP fetcher with rate limiting and retry logic.
    """
    
    def __init__(self, settings: Settings, bot_strategy: BotAvoidanceStrategy | None = None):
        self.settings = settings
        self.session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(settings.GLOBAL_CONCURRENCY)
        self.bot_strategy = bot_strategy
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=self.settings.REQUEST_TIMEOUT_SEC)
        headers = {"User-Agent": self.settings.BASE_USER_AGENT}
        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def fetch(self, url: str) -> Optional[FetchResponse]:
        """
        Fetch URL with rate limiting and error handling.
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
                content_length_bytes: Optional[int] = None

                start_time = perf_counter()
                async with self.session.get(url, **request_kwargs) as response:
                    content = await response.read()
                    end_time = perf_counter()
                    load_time_ms = int((end_time - start_time) * 1000)
                    content_length_bytes = len(content)
                    content_type = response.headers.get('content-type', 'text/html')
                    status = response.status
                    blocked_reason = None
                    if self.bot_strategy:
                        blocked_reason = self.bot_strategy.detect_block(url, status, dict(response.headers), content)
                    
                    return FetchResponse(
                        url=str(response.url),
                        content=content,
                        content_type=content_type,
                        status=response.status,
                        headers=dict(response.headers),
                        path=url,
                        blocked_reason=blocked_reason,
                        load_time_ms=load_time_ms,
                        content_length_bytes=content_length_bytes
                    )
            except Exception as e:
                print(f"Fetch error for {url}: {e}")
                return None
            finally:
                if self.bot_strategy:
                    self.bot_strategy.after_request(url, status)
                
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