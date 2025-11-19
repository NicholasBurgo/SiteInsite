import asyncio
import json
import time
import random
import logging
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from urllib.parse import urlparse

try:
    import curl_cffi.requests as curl_requests
except ImportError:
    curl_requests = None

logger = logging.getLogger(__name__)

@dataclass
class HttpResponse:
    url: str
    status_code: int
    content: str
    headers: Dict[str, str]
    cookies: Dict[str, str]
    response_time: float
    proxy_used: Optional[str] = None
    fingerprint_used: Optional[str] = None
    error: Optional[str] = None

class AdvancedHttpClient:
    """Advanced HTTP client with TLS fingerprinting and anti-bot features"""

    def __init__(self, config: Dict[str, Any], proxy_manager=None, fingerprint_spoofer=None,
                 cf_bypass=None, human_behavior=None):
        self.config = config
        self.proxy_manager = proxy_manager
        self.fingerprint_spoofer = fingerprint_spoofer
        self.cf_bypass = cf_bypass
        self.human_behavior = human_behavior

        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delays = config.get('retry_delays', [2, 8, 30])

        # Session management
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_cookies: Dict[str, Dict[str, str]] = {}

        # Rate limiting
        self.last_request_time = 0
        self.request_interval = 1.0 / config.get('performance', {}).get('rate_limit_per_minute', 30)

    async def request(self, url: str, method: str = "GET", headers: Dict[str, str] = None,
                     proxy: Optional[Any] = None, session_id: Optional[str] = None,
                     fingerprint: Optional[Any] = None, is_first_request: bool = False) -> HttpResponse:
        """
        Make HTTP request with full anti-bot protection
        """

        # Apply human-like delay
        if self.human_behavior:
            await self.human_behavior.pre_request_delay(url, is_first_request)

        # Rate limiting
        await self._apply_rate_limit()

        # Get or create fingerprint
        if not fingerprint and self.fingerprint_spoofer:
            fingerprint = self.fingerprint_spoofer.generate_fingerprint()

        # Get proxy if not provided
        if not proxy and self.proxy_manager:
            proxy = await self.proxy_manager.get_proxy(urlparse(url).netloc)

        # Prepare headers
        request_headers = self._prepare_headers(url, headers, fingerprint, session_id)

        # Try request with retries
        for attempt in range(self.max_retries):
            try:
                response = await self._make_request(
                    url, method, request_headers, proxy, fingerprint, attempt
                )

                # Check for Cloudflare challenge
                if self._is_cloudflare_challenge(response):
                    if self.cf_bypass and attempt < self.max_retries - 1:
                        logger.info(f"Cloudflare challenge detected, attempting bypass for {url}")
                        cf_success, cf_content, cf_cookies = await self.cf_bypass.bypass_request(
                            url, request_headers, proxy.url if proxy else None
                        )

                        if cf_success:
                            response.content = cf_content
                            response.cookies.update(cf_cookies or {})
                            response.status_code = 200
                            break
                    else:
                        # Mark proxy as failed if we got Cloudflare
                        if proxy and self.proxy_manager:
                            await self.proxy_manager.mark_failure(proxy, "Cloudflare challenge")

                # Handle rate limiting
                if response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delays[attempt] * 2  # Extra delay for 429
                        logger.info(f"Rate limited (429), waiting {delay}s before retry")
                        await asyncio.sleep(delay)
                        continue

                # Update session cookies
                if session_id and response.cookies:
                    self._update_session_cookies(session_id, response.cookies)

                # Mark proxy as successful
                if proxy and self.proxy_manager and response.status_code < 400:
                    await self.proxy_manager.mark_success(proxy)

                return response

            except Exception as e:
                error_msg = str(e)
                logger.debug(f"Request attempt {attempt + 1} failed for {url}: {error_msg}")

                # Mark proxy as failed
                if proxy and self.proxy_manager:
                    await self.proxy_manager.mark_failure(proxy, error_msg)

                # Retry with different proxy if available
                if attempt < self.max_retries - 1:
                    proxy = await self.proxy_manager.get_proxy(urlparse(url).netloc) if self.proxy_manager else None
                    await asyncio.sleep(self.retry_delays[attempt])
                else:
                    return HttpResponse(
                        url=url,
                        status_code=0,
                        content="",
                        headers={},
                        cookies={},
                        response_time=0,
                        error=error_msg
                    )

        # Should not reach here, but just in case
        return HttpResponse(
            url=url,
            status_code=0,
            content="",
            headers={},
            cookies={},
            response_time=0,
            error="Max retries exceeded"
        )

    async def _make_request(self, url: str, method: str, headers: Dict[str, str],
                           proxy: Optional[Any], fingerprint: Optional[Any], attempt: int) -> HttpResponse:
        """Make the actual HTTP request using curl_cffi"""

        start_time = time.time()

        # Use curl_cffi if available, fallback to requests
        if curl_cffi:
            response = self._curl_cffi_request(url, method, headers, proxy, fingerprint)
        else:
            logger.warning("curl_cffi not available, using requests (less stealthy)")
            response = self._fallback_request(url, method, headers, proxy)

        response_time = time.time() - start_time

        return HttpResponse(
            url=url,
            status_code=response.status_code,
            content=response.text,
            headers=dict(response.headers),
            cookies=dict(response.cookies),
            response_time=response_time,
            proxy_used=proxy.url if proxy else None,
            fingerprint_used=fingerprint.user_agent if fingerprint else None
        )

    def _curl_cffi_request(self, url: str, method: str, headers: Dict[str, str],
                          proxy: Optional[Any], fingerprint: Optional[Any]) -> Any:
        """Make request with curl_cffi impersonation"""

        # Choose impersonation based on fingerprint or default to chrome124
        impersonate = "chrome124"
        if fingerprint and hasattr(fingerprint, 'user_agent'):
            if "126" in fingerprint.user_agent:
                impersonate = "chrome126"
            elif "120" in fingerprint.user_agent:
                impersonate = "chrome120"

        proxies = {"http": proxy.url, "https": proxy.url} if proxy else None

        response = curl_requests.request(
            method=method,
            url=url,
            headers=headers,
            proxies=proxies,
            timeout=self.timeout,
            impersonate=impersonate,
            verify=False  # Skip SSL verification for flexibility
        )

        return response

    def _fallback_request(self, url: str, method: str, headers: Dict[str, str],
                         proxy: Optional[Any]) -> Any:
        """Fallback request using requests library"""
        import requests

        proxies = {"http": proxy.url, "https": proxy.url} if proxy else None

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            proxies=proxies,
            timeout=self.timeout,
            verify=False
        )

        return response

    def _prepare_headers(self, url: str, custom_headers: Dict[str, str] = None,
                        fingerprint: Optional[Any] = None, session_id: Optional[str] = None) -> Dict[str, str]:
        """Prepare request headers"""

        headers = {}

        # Get base headers from fingerprint
        if fingerprint and self.fingerprint_spoofer:
            headers.update(self.fingerprint_spoofer.get_curl_cffi_headers(fingerprint))

        # Add custom headers
        if custom_headers:
            headers.update(custom_headers)

        # Add session cookies
        if session_id:
            session_cookies = self.session_cookies.get(session_id, {})
            if session_cookies:
                cookie_header = "; ".join([f"{k}={v}" for k, v in session_cookies.items()])
                headers["Cookie"] = cookie_header

        # Add some randomization to avoid detection
        headers["Accept"] = self._randomize_accept_header(headers.get("Accept", ""))
        headers["Accept-Encoding"] = self._randomize_accept_encoding(headers.get("Accept-Encoding", ""))

        return headers

    def _randomize_accept_header(self, accept: str) -> str:
        """Add slight randomization to Accept header"""
        if not accept:
            return "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"

        # Sometimes reorder or add/remove q-values
        if random.random() < 0.3:
            parts = accept.split(",")
            random.shuffle(parts)
            return ",".join(parts)

        return accept

    def _randomize_accept_encoding(self, encoding: str) -> str:
        """Randomize Accept-Encoding header"""
        encodings = ["gzip, deflate, br", "gzip, deflate", "deflate, gzip", "br, gzip, deflate"]

        if random.random() < 0.4:
            return random.choice(encodings)

        return encoding or "gzip, deflate, br"

    def _is_cloudflare_challenge(self, response: HttpResponse) -> bool:
        """Check if response indicates Cloudflare challenge"""
        if self.cf_bypass:
            return self.cf_bypass.detect_cloudflare_challenge(response.content, response.status_code)
        return False

    async def _apply_rate_limit(self):
        """Apply rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.request_interval:
            await asyncio.sleep(self.request_interval - time_since_last)

        self.last_request_time = time.time()

    def create_session(self, domain: str) -> str:
        """Create a new session for domain"""
        session_id = f"{domain}_{int(time.time())}_{random.randint(1000, 9999)}"
        self.sessions[session_id] = {
            'domain': domain,
            'created_at': time.time(),
            'last_used': time.time()
        }
        self.session_cookies[session_id] = {}
        return session_id

    def _update_session_cookies(self, session_id: str, cookies: Dict[str, str]):
        """Update cookies for session"""
        if session_id in self.session_cookies:
            self.session_cookies[session_id].update(cookies)
            self.sessions[session_id]['last_used'] = time.time()

    def get_session_cookies(self, session_id: str) -> Dict[str, str]:
        """Get cookies for session"""
        return self.session_cookies.get(session_id, {})

    def cleanup_sessions(self, max_age: int = 3600):
        """Clean up old sessions"""
        current_time = time.time()
        expired = []

        for session_id, session in self.sessions.items():
            if current_time - session['last_used'] > max_age:
                expired.append(session_id)

        for session_id in expired:
            del self.sessions[session_id]
            del self.session_cookies[session_id]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
