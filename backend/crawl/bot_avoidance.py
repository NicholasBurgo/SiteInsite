import asyncio
import random
import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Deque
from urllib.parse import urlparse


DEFAULT_BLOCK_KEYWORDS = [
    "robot or human",
    "are you a robot",
    "bot detection",
    "captcha",
    "unusual traffic",
    "verify you are human",
]

DEFAULT_BROWSER_PROFILES = [
    {
        "name": "chrome_windows_desktop",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.84 Safari/537.36",
        "sec_ch_ua": '"Not/A)Brand";v="8", "Chromium";v="128", "Google Chrome";v="128"',
        "sec_ch_ua_mobile": "?0",
        "sec_ch_ua_platform": '"Windows"',
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept_encoding": "gzip, deflate, br",
        "accept_languages": [
            "en-US,en;q=0.9",
            "en-US,en;q=0.8,en-GB;q=0.7",
            "en-US,en;q=0.9,en;q=0.6",
        ],
        "device_width_range": (1280, 1920),
    },
    {
        "name": "chrome_linux_desktop",
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.126 Safari/537.36",
        "sec_ch_ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec_ch_ua_mobile": "?0",
        "sec_ch_ua_platform": '"Linux"',
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept_encoding": "gzip, deflate, br",
        "accept_languages": [
            "en-US,en;q=0.9",
            "en-GB,en;q=0.8",
            "en-CA,en;q=0.75,en;q=0.65",
        ],
        "device_width_range": (1200, 2048),
    },
    {
        "name": "safari_mac",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
        "sec_ch_ua": None,
        "sec_ch_ua_mobile": None,
        "sec_ch_ua_platform": None,
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "accept_encoding": "gzip, deflate, br",
        "accept_languages": [
            "en-US,en;q=0.9",
            "en-GB,en;q=0.8",
        ],
        "device_width_range": (1280, 1720),
    },
    {
        "name": "safari_ios",
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
        "sec_ch_ua": None,
        "sec_ch_ua_mobile": None,
        "sec_ch_ua_platform": '"iOS"',
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "accept_encoding": "gzip, deflate, br",
        "accept_languages": [
            "en-US,en;q=0.9",
            "en-US,en;q=0.8,en;q=0.7",
        ],
        "device_width_range": (375, 430),
    },
]


@dataclass
class BotBlockEvent:
    url: str
    reason: str
    status: Optional[int]
    timestamp: float = field(default_factory=lambda: time.time())


class BotAvoidanceStrategy:
    """
    Simple heuristics for slowing down and detecting bot walls/captcha pages.
    """

    def __init__(
        self,
        *,
        min_delay: float = 0.6,
        max_delay: float = 2.4,
        per_host_interval: float = 1.2,
        block_keywords: Optional[List[str]] = None,
        status_blocklist: Optional[List[int]] = None,
        sample_bytes: int = 4096,
        user_agents: Optional[List[str]] = None,
        accept_languages: Optional[List[str]] = None,
        browser_profiles: Optional[List[Dict[str, object]]] = None,
        profile_ttl: float = 900.0,
    ) -> None:
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.per_host_interval = per_host_interval
        self.keywords = [kw.lower() for kw in (block_keywords or DEFAULT_BLOCK_KEYWORDS)]
        self.status_blocklist = set(status_blocklist or [403, 409, 423, 429, 503])
        self.sample_bytes = sample_bytes
        self.browser_profiles = list(browser_profiles or DEFAULT_BROWSER_PROFILES)
        if user_agents:
            fallback_profiles = []
            for agent in user_agents:
                fallback_profiles.append(
                    {
                        "name": f"custom_{hash(agent) & 0xffff}",
                        "user_agent": agent,
                        "sec_ch_ua": None,
                        "sec_ch_ua_mobile": None,
                        "sec_ch_ua_platform": None,
                        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        "accept_encoding": "gzip, deflate, br",
                        "accept_languages": accept_languages or ["en-US,en;q=0.9"],
                        "device_width_range": (1200, 1920),
                    }
                )
            self.browser_profiles = fallback_profiles
        self.user_agents = [profile["user_agent"] for profile in self.browser_profiles]
        self.accept_languages = accept_languages or [
            language for profile in self.browser_profiles for language in profile.get("accept_languages", [])  # type: ignore[arg-type]
        ]
        self.profile_ttl = profile_ttl
        self._last_host_request: Dict[str, float] = {}
        self._blocked_events: List[BotBlockEvent] = []
        self._host_profiles: Dict[str, Dict[str, object]] = {}
        self._last_host_url: Dict[str, str] = {}
        shuffled_profiles = list(self.browser_profiles)
        random.shuffle(shuffled_profiles)
        self._profile_queue: Deque[Dict[str, object]] = deque(shuffled_profiles)

    async def before_request(self, url: str) -> None:
        """
        Apply randomized delays and simple per-host pacing.
        """
        host = urlparse(url).netloc.lower()
        now = time.monotonic()
        wait_time = random.uniform(self.min_delay, self.max_delay)
        last = self._last_host_request.get(host)
        if last is not None:
            gap = self.per_host_interval - (now - last)
            if gap > 0:
                wait_time += gap
        if wait_time > 0:
            await asyncio.sleep(wait_time)

    def after_request(self, url: str, status: Optional[int]) -> None:
        """
        Record request timestamp so future requests can pace.
        """
        host = urlparse(url).netloc.lower()
        self._last_host_request[host] = time.monotonic()
        self._last_host_url[host] = url

    def prepare_request_kwargs(self, url: str) -> Dict[str, Dict[str, str]]:
        """
        Randomize a few headers to reduce fingerprinting.
        """
        host = urlparse(url).netloc.lower()
        profile_state = self._select_host_profile(host)
        profile = profile_state["template"]

        headers: Dict[str, str] = {
            "User-Agent": profile["user_agent"],
            "Accept": profile.get("accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"),
            "Accept-Language": profile_state["accept_language"],
            "Accept-Encoding": profile.get("accept_encoding", "gzip, deflate, br"),
            "Connection": "keep-alive",
            "sec-ch-ua": profile.get("sec_ch_ua"),
            "sec-ch-ua-mobile": profile.get("sec_ch_ua_mobile"),
            "sec-ch-ua-platform": profile.get("sec_ch_ua_platform"),
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": profile_state.get("sec_fetch_site", "none"),
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Viewport-Width": str(profile_state["viewport_width"]) if profile_state.get("viewport_width") else None,
        }
        if profile_state.get("send_cache_control"):
            headers["Cache-Control"] = "max-age=0"
        if profile_state.get("send_pragma"):
            headers["Pragma"] = "no-cache"
        if profile_state.get("dnt"):
            headers["DNT"] = profile_state["dnt"]  # type: ignore[assignment]
        if profile_state.get("sec_ch_ua_platform_version"):
            headers["sec-ch-ua-platform-version"] = profile_state["sec_ch_ua_platform_version"]  # type: ignore[index]
        referer = self._last_host_url.get(host)
        if referer and referer != url:
            headers["Referer"] = referer
            headers["Sec-Fetch-Site"] = "same-origin"
        headers = {k: v for k, v in headers.items() if v is not None}
        return {"headers": headers}

    def detect_block(self, url: str, status: Optional[int], headers: Dict[str, str], content: bytes) -> Optional[str]:
        """
        Inspect status codes and content for common bot wall patterns.
        """
        reason: Optional[str] = None
        if status and status in self.status_blocklist:
            reason = f"http_status_{status}"
        else:
            snippet = content[: self.sample_bytes].decode("utf-8", errors="ignore").lower()
            if any(keyword in snippet for keyword in self.keywords):
                reason = "captcha_content"
        if reason:
            self.record_block(url, reason, status)
        return reason

    def record_block(self, url: str, reason: str, status: Optional[int]) -> None:
        """
        Store a rolling history of block events for diagnostics.
        """
        self._blocked_events.append(BotBlockEvent(url=url, reason=reason, status=status))
        # keep last 100 events to bound memory
        if len(self._blocked_events) > 100:
            self._blocked_events = self._blocked_events[-100:]

    def recent_blocks(self, limit: int = 10) -> List[BotBlockEvent]:
        return self._blocked_events[-limit:]

    def _select_host_profile(self, host: str) -> Dict[str, object]:
        now = time.monotonic()
        cached = self._host_profiles.get(host)
        if cached and now - cached["created_at"] < self.profile_ttl:  # type: ignore[operator]
            cached["last_seen"] = now  # type: ignore[index]
            cached["request_count"] = cached.get("request_count", 0) + 1  # type: ignore[call-arg]
            if cached["request_count"] > 1:  # type: ignore[index]
                cached["sec_fetch_site"] = "same-origin"
            return cached

        template = self._next_profile_template()
        accept_language = self._choose_accept_language(template)
        viewport_width = self._choose_viewport_width(template)
        send_pragma = random.random() < 0.35
        send_cache_control = random.random() < 0.65
        dnt = "1" if random.random() < 0.25 else None
        sec_ch_ua_platform_version = template.get("sec_ch_ua_platform_version")

        state: Dict[str, object] = {
            "template": template,
            "created_at": now,
            "last_seen": now,
            "request_count": 1,
            "accept_language": accept_language,
            "viewport_width": viewport_width,
            "send_pragma": send_pragma,
            "send_cache_control": send_cache_control,
            "dnt": dnt,
            "sec_fetch_site": "none",
            "sec_ch_ua_platform_version": sec_ch_ua_platform_version,
        }
        self._host_profiles[host] = state
        return state

    def _choose_accept_language(self, template: Dict[str, object]) -> str:
        languages: List[str] = template.get("accept_languages") or self.accept_languages  # type: ignore[assignment]
        choice = random.choice(languages)
        # interleave subtle q-value noise to better resemble browsers
        if "," in choice and random.random() < 0.4:
            parts = choice.split(",")
            bumped = []
            for part in parts:
                if ";q=" in part:
                    lang, q = part.split(";q=")
                    jitter = random.uniform(-0.05, 0.05)
                    q_val = max(0.1, min(1.0, float(q) + jitter))
                    bumped.append(f"{lang};q={q_val:.2f}")
                else:
                    bumped.append(part)
            return ",".join(bumped)
        return choice

    def _choose_viewport_width(self, template: Dict[str, object]) -> Optional[int]:
        window_range = template.get("device_width_range")
        if not window_range or not isinstance(window_range, tuple):
            return None
        low, high = window_range
        if not isinstance(low, int) or not isinstance(high, int):
            return None
        return random.randint(low, high)

    def _next_profile_template(self) -> Dict[str, object]:
        if not self._profile_queue:
            shuffled = list(self.browser_profiles)
            random.shuffle(shuffled)
            self._profile_queue = deque(shuffled)
        template = self._profile_queue[0]
        self._profile_queue.rotate(-1)
        return template

