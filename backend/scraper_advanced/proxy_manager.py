import asyncio
import aiohttp
import time
import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

@dataclass
class Proxy:
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    failures: int = 0
    last_used: float = 0
    last_health_check: float = 0
    is_healthy: bool = True

    @property
    def url(self) -> str:
        """Get proxy URL for HTTP clients"""
        if self.username and self.password:
            return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"http://{self.host}:{self.port}"

    @property
    def selenium_url(self) -> str:
        """Get proxy URL for Selenium"""
        if self.username and self.password:
            return f"{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.host}:{self.port}"

@dataclass
class ProxyHealthMetrics:
    response_time: float
    success_rate: float
    last_check: float
    total_requests: int
    successful_requests: int

class ProxyManager:
    """Manages residential proxy rotation and health checking"""

    def __init__(self, config: Dict[str, any]):
        self.config = config
        self.proxies: List[Proxy] = []
        self.health_metrics: Dict[str, ProxyHealthMetrics] = {}
        self.rotation_strategy = config.get('rotation_strategy', 'round_robin')
        self.health_check_interval = config.get('health_check_interval', 300)
        self.max_failures = config.get('max_failures_before_ban', 3)
        self.geo_target = config.get('geo_target', 'US')
        self._current_index = 0
        self._lock = asyncio.Lock()

        # Load residential proxies from config
        self._load_proxies()

    def _load_proxies(self):
        """Load proxy configurations from config"""
        residential_proxies = self.config.get('residential', [])

        for proxy_config in residential_proxies:
            proxy = Proxy(
                host=proxy_config['host'],
                port=proxy_config['port'],
                username=proxy_config.get('username'),
                password=proxy_config.get('password'),
                country=proxy_config.get('country', 'US')
            )
            self.proxies.append(proxy)

        if not self.proxies:
            logger.warning("No proxies configured, running without proxy support")

    async def get_proxy(self, domain: Optional[str] = None) -> Optional[Proxy]:
        """Get next healthy proxy based on rotation strategy"""
        if not self.proxies:
            return None

        async with self._lock:
            healthy_proxies = [p for p in self.proxies if p.is_healthy and p.failures < self.max_failures]

            if not healthy_proxies:
                logger.warning("No healthy proxies available")
                return None

            # Filter by geo target if specified
            if self.geo_target:
                geo_proxies = [p for p in healthy_proxies if p.country == self.geo_target]
                if geo_proxies:
                    healthy_proxies = geo_proxies

            if self.rotation_strategy == 'round_robin':
                proxy = self._round_robin_select(healthy_proxies)
            elif self.rotation_strategy == 'random':
                proxy = random.choice(healthy_proxies)
            elif self.rotation_strategy == 'geo_targeted':
                proxy = self._geo_targeted_select(healthy_proxies, domain)
            else:
                proxy = self._round_robin_select(healthy_proxies)

            if proxy:
                proxy.last_used = time.time()
                logger.debug(f"Selected proxy: {proxy.host}:{proxy.port}")

            return proxy

    def _round_robin_select(self, proxies: List[Proxy]) -> Proxy:
        """Round-robin proxy selection"""
        if self._current_index >= len(proxies):
            self._current_index = 0

        proxy = proxies[self._current_index]
        self._current_index += 1
        return proxy

    def _geo_targeted_select(self, proxies: List[Proxy], domain: Optional[str]) -> Proxy:
        """Select proxy based on domain and geographic targeting"""
        # For now, just use round-robin, but could be enhanced with domain-specific logic
        return self._round_robin_select(proxies)

    async def mark_failure(self, proxy: Proxy, error: str):
        """Mark proxy as failed"""
        async with self._lock:
            proxy.failures += 1
            proxy.last_used = time.time()

            if proxy.failures >= self.max_failures:
                proxy.is_healthy = False
                logger.warning(f"Proxy {proxy.host}:{proxy.port} banned after {proxy.failures} failures")

            logger.debug(f"Proxy failure: {proxy.host}:{proxy.port} - {error}")

    async def mark_success(self, proxy: Proxy):
        """Mark proxy as successful"""
        async with self._lock:
            proxy.failures = max(0, proxy.failures - 1)  # Gradually reduce failure count
            proxy.is_healthy = True

    async def health_check_all(self):
        """Perform health check on all proxies"""
        if not self.proxies:
            return

        logger.info("Starting proxy health check...")

        tasks = []
        for proxy in self.proxies:
            if time.time() - proxy.last_health_check > self.health_check_interval:
                tasks.append(self._check_proxy_health(proxy))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        healthy_count = sum(1 for p in self.proxies if p.is_healthy)
        logger.info(f"Health check complete: {healthy_count}/{len(self.proxies)} proxies healthy")

    async def _check_proxy_health(self, proxy: Proxy) -> bool:
        """Check if proxy is working"""
        proxy.last_health_check = time.time()

        try:
            # Simple connectivity test
            connector = aiohttp.TCPConnector(limit=1, limit_per_host=1)
            timeout = aiohttp.ClientTimeout(total=10)

            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                start_time = time.time()

                # Test with a reliable endpoint
                test_url = "http://httpbin.org/ip"
                proxy_url = proxy.url

                async with session.get(test_url, proxy=proxy_url) as response:
                    response_time = time.time() - start_time

                    if response.status == 200:
                        proxy.is_healthy = True
                        proxy.failures = 0
                        logger.debug(f"Proxy {proxy.host}:{proxy.port} is healthy ({response_time:.2f}s)")
                        return True
                    else:
                        proxy.is_healthy = False
                        logger.debug(f"Proxy {proxy.host}:{proxy.port} returned status {response.status}")
                        return False

        except Exception as e:
            proxy.is_healthy = False
            logger.debug(f"Proxy {proxy.host}:{proxy.port} health check failed: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, any]:
        """Get proxy statistics"""
        total = len(self.proxies)
        healthy = sum(1 for p in self.proxies if p.is_healthy)
        banned = sum(1 for p in self.proxies if not p.is_healthy and p.failures >= self.max_failures)

        return {
            'total_proxies': total,
            'healthy_proxies': healthy,
            'banned_proxies': banned,
            'available_proxies': healthy,
            'rotation_strategy': self.rotation_strategy,
            'geo_target': self.geo_target
        }
