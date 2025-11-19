import asyncio
import aiohttp
import json
import time
import logging
from typing import Optional, Dict, Any, Tuple
import cloudscraper

logger = logging.getLogger(__name__)

class CloudflareBypass:
    """Handle Cloudflare protection bypass using multiple methods"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.flaresolverr_url = config.get('flaresolverr_url', 'http://localhost:8191/v1')
        self.challenge_timeout = config.get('challenge_timeout', 60)
        self.cloudscraper_enabled = config.get('cloudscraper_enabled', True)

        # Session management
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_timeout = 3600  # 1 hour

    async def bypass_request(self, url: str, headers: Dict[str, str] = None,
                           proxy: str = None, timeout: int = 30) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Attempt to bypass Cloudflare protection for a URL

        Returns: (success, html_content, cookies_dict)
        """
        headers = headers or {}

        # Try cloudscraper first (fastest)
        if self.cloudscraper_enabled:
            logger.debug(f"Attempting cloudscraper bypass for {url}")
            success, content, cookies = await self._try_cloudscraper(url, headers, proxy, timeout)
            if success:
                return success, content, cookies

        # Fallback to FlareSolverr (slower but more reliable)
        logger.debug(f"Attempting FlareSolverr bypass for {url}")
        success, content, cookies = await self._try_flaresolverr(url, headers, proxy)
        if success:
            return success, content, cookies

        logger.warning(f"All Cloudflare bypass methods failed for {url}")
        return False, None, None

    async def _try_cloudscraper(self, url: str, headers: Dict[str, str],
                               proxy: str = None, timeout: int = 30) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Try cloudscraper bypass"""
        try:
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                },
                delay=random.uniform(1, 3)  # Add delay to avoid detection
            )

            # Set proxy if provided
            if proxy:
                scraper.proxies = {'http': proxy, 'https': proxy}

            # Set headers
            scraper.headers.update(headers)

            # Make request
            response = scraper.get(url, timeout=timeout)

            if response.status_code == 200:
                logger.info(f"Cloudscraper bypass successful for {url}")
                return True, response.text, dict(response.cookies)
            else:
                logger.debug(f"Cloudscraper failed with status {response.status_code} for {url}")
                return False, None, None

        except Exception as e:
            logger.debug(f"Cloudscraper error for {url}: {str(e)}")
            return False, None, None

    async def _try_flaresolverr(self, url: str, headers: Dict[str, str],
                               proxy: str = None) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Try FlareSolverr bypass"""
        try:
            # Prepare FlareSolverr request
            request_data = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": self.challenge_timeout * 1000,  # Convert to milliseconds
                "headers": headers
            }

            # Add proxy if provided
            if proxy:
                request_data["proxy"] = {
                    "url": proxy,
                    "type": "http"
                }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.flaresolverr_url,
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=self.challenge_timeout + 10)
                ) as response:

                    if response.status != 200:
                        logger.debug(f"FlareSolverr request failed with status {response.status} for {url}")
                        return False, None, None

                    result = await response.json()

                    if result.get("status") == "ok":
                        solution = result.get("solution", {})
                        html_content = solution.get("response")
                        cookies = solution.get("cookies", [])

                        # Convert cookies to dict
                        cookie_dict = {}
                        for cookie in cookies:
                            if isinstance(cookie, dict):
                                cookie_dict[cookie.get("name", "")] = cookie.get("value", "")
                            elif isinstance(cookie, str):
                                # Parse cookie string
                                try:
                                    name, value = cookie.split("=", 1)
                                    cookie_dict[name] = value.split(";")[0]
                                except:
                                    pass

                        logger.info(f"FlareSolverr bypass successful for {url}")
                        return True, html_content, cookie_dict
                    else:
                        logger.debug(f"FlareSolverr challenge failed for {url}: {result.get('message', 'Unknown error')}")
                        return False, None, None

        except asyncio.TimeoutError:
            logger.debug(f"FlareSolverr timeout for {url}")
            return False, None, None
        except Exception as e:
            logger.debug(f"FlareSolverr error for {url}: {str(e)}")
            return False, None, None

    async def create_session(self, domain: str) -> str:
        """Create a persistent session for a domain (with cookies)"""
        session_id = f"{domain}_{int(time.time())}"

        self._sessions[session_id] = {
            'domain': domain,
            'cookies': {},
            'created_at': time.time(),
            'last_used': time.time()
        }

        logger.debug(f"Created session {session_id} for {domain}")
        return session_id

    async def get_session_cookies(self, session_id: str) -> Dict[str, str]:
        """Get cookies for a session"""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session['last_used'] = time.time()
            return session['cookies']
        return {}

    async def update_session_cookies(self, session_id: str, cookies: Dict[str, str]):
        """Update cookies for a session"""
        if session_id in self._sessions:
            self._sessions[session_id]['cookies'].update(cookies)
            self._sessions[session_id]['last_used'] = time.time()
            logger.debug(f"Updated cookies for session {session_id}")

    async def cleanup_sessions(self):
        """Clean up expired sessions"""
        current_time = time.time()
        expired_sessions = []

        for session_id, session in self._sessions.items():
            if current_time - session['created_at'] > self._session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self._sessions[session_id]
            logger.debug(f"Cleaned up expired session {session_id}")

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    def detect_cloudflare_challenge(self, content: str, status_code: int) -> bool:
        """Detect if content contains Cloudflare challenge"""
        if status_code in [403, 503, 429]:
            return True

        challenge_indicators = [
            "checking your browser",
            "ddos protection by cloudflare",
            "cf-browser-verification",
            "cf-challenge-running",
            "__cf_chl_jschl_tk__",
            "cf-ray",
            "attention required!",
            "please complete the security check",
            "checking your browser before accessing"
        ]

        content_lower = content.lower()
        return any(indicator in content_lower for indicator in challenge_indicators)

    async def get_cf_clearance_token(self, url: str, proxy: str = None) -> Optional[str]:
        """Get cf_clearance cookie by solving challenge"""
        success, _, cookies = await self.bypass_request(url, proxy=proxy)
        if success and cookies:
            return cookies.get('cf_clearance')
        return None
