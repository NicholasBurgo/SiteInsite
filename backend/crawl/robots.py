import aiohttp
import asyncio
from urllib.parse import urljoin, urlparse
from typing import Optional, Set
from dataclasses import dataclass

@dataclass
class RobotsInfo:
    allowed: bool
    crawl_delay: Optional[float] = None
    sitemaps: Set[str] = None

class RobotsChecker:
    """
    Robots.txt parser and checker for crawl politeness.
    """
    
    def __init__(self):
        self._cache: dict = {}
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            
    async def can_fetch(self, url: str, user_agent: str = "*") -> RobotsInfo:
        """
        Check if URL can be fetched according to robots.txt.
        """
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        # Check cache first
        cache_key = f"{robots_url}:{user_agent}"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        try:
            if not self._session:
                await self.__aenter__()
                
            async with self._session.get(robots_url) as response:
                if response.status == 200:
                    content = await response.text()
                    robots_info = self._parse_robots(content, user_agent)
                else:
                    # No robots.txt, allow crawling
                    robots_info = RobotsInfo(allowed=True)
                    
        except Exception:
            # Error fetching robots.txt, allow crawling
            robots_info = RobotsInfo(allowed=True)
            
        # Cache result
        self._cache[cache_key] = robots_info
        return robots_info
        
    def _parse_robots(self, content: str, user_agent: str) -> RobotsInfo:
        """
        Parse robots.txt content.
        """
        lines = content.split('\n')
        current_ua = None
        allowed = True
        crawl_delay = None
        sitemaps = set()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('User-agent:'):
                current_ua = line.split(':', 1)[1].strip()
            elif line.startswith('Disallow:'):
                if current_ua == user_agent or current_ua == '*':
                    disallow_path = line.split(':', 1)[1].strip()
                    if disallow_path == '/':
                        allowed = False
            elif line.startswith('Allow:'):
                if current_ua == user_agent or current_ua == '*':
                    allow_path = line.split(':', 1)[1].strip()
                    if allow_path == '/':
                        allowed = True
            elif line.startswith('Crawl-delay:'):
                if current_ua == user_agent or current_ua == '*':
                    try:
                        crawl_delay = float(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
            elif line.startswith('Sitemap:'):
                sitemap_url = line.split(':', 1)[1].strip()
                sitemaps.add(sitemap_url)
                
        return RobotsInfo(
            allowed=allowed,
            crawl_delay=crawl_delay,
            sitemaps=sitemaps
        )