import asyncio
import random
import time
import numpy as np
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)

class HumanBehaviorEngine:
    """Simulate human browsing behavior"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.min_delay = config.get('human_delays', {}).get('min_delay', 3.2)
        self.max_delay = config.get('human_delays', {}).get('max_delay', 9.7)
        self.homepage_visit_chance = config.get('human_delays', {}).get('homepage_visit_chance', 0.15)
        self.asset_fetch_chance = config.get('human_delays', {}).get('asset_fetch_chance', 0.10)

        # Track session state
        self.session_start_time = time.time()
        self.pages_visited = []
        self.last_request_time = 0

    async def pre_request_delay(self, url: str, is_first_request: bool = False) -> float:
        """Apply human-like delay before making request"""
        if is_first_request:
            # Shorter delay for first request
            delay = random.uniform(1.0, 3.0)
        else:
            # Normal distribution delay
            mean = (self.min_delay + self.max_delay) / 2
            std_dev = (self.max_delay - self.min_delay) / 6  # 99.7% within range
            delay = np.random.normal(mean, std_dev)
            delay = max(self.min_delay, min(self.max_delay, delay))

        # Add some jitter
        delay *= random.uniform(0.8, 1.2)

        logger.debug(f"Human delay: {delay:.2f}s for {url}")
        await asyncio.sleep(delay)

        self.last_request_time = time.time()
        return delay

    async def simulate_homepage_visit(self, base_url: str, target_url: str) -> Optional[str]:
        """Sometimes visit homepage first before going to article"""
        if random.random() < self.homepage_visit_chance:
            logger.info(f"Simulating homepage visit before {target_url}")

            # Visit homepage first
            await self.pre_request_delay(base_url, is_first_request=False)

            # Spend some time "reading" homepage
            reading_time = random.uniform(2.0, 8.0)
            await asyncio.sleep(reading_time)

            return base_url

        return None

    async def simulate_asset_requests(self, url: str, html_content: str) -> List[str]:
        """Simulate fetching CSS/JS assets like a real browser"""
        if random.random() >= self.asset_fetch_chance:
            return []

        # Extract asset URLs from HTML (simplified)
        asset_urls = []
        import re

        # Find CSS and JS links
        css_pattern = r'<link[^>]*href=["\']([^"\']*\.css[^"\']*)["\'][^>]*>'
        js_pattern = r'<script[^>]*src=["\']([^"\']*\.js[^"\']*)["\'][^>]*>'

        base_domain = urlparse(url).netloc

        for pattern in [css_pattern, js_pattern]:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if match.startswith('http'):
                    asset_url = match
                else:
                    asset_url = urljoin(url, match)

                # Only fetch assets from same domain (most common)
                if urlparse(asset_url).netloc == base_domain:
                    asset_urls.append(asset_url)

        # Limit to 2-5 assets to avoid being too aggressive
        if asset_urls:
            num_to_fetch = min(len(asset_urls), random.randint(2, 5))
            selected_assets = random.sample(asset_urls, num_to_fetch)

            logger.debug(f"Simulating asset fetches: {len(selected_assets)} from {url}")

            # Add small delays between asset requests
            for asset_url in selected_assets:
                await asyncio.sleep(random.uniform(0.1, 0.5))

            return selected_assets

        return []

    async def simulate_mouse_movements(self, driver) -> None:
        """Simulate human mouse movements (for Selenium mode)"""
        try:
            # Get viewport size
            viewport = driver.execute_script("""
                return {
                    width: window.innerWidth,
                    height: window.innerHeight
                };
            """)

            width, height = viewport['width'], viewport['height']

            # Generate natural mouse path
            points = self._generate_mouse_path(width, height, num_points=5)

            for x, y in points:
                # Add small delay between movements
                await asyncio.sleep(random.uniform(0.05, 0.15))

                # Use ActionChains for smooth movement
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(driver)
                actions.move_by_offset(x, y).perform()

        except Exception as e:
            logger.debug(f"Mouse movement simulation failed: {e}")

    async def simulate_scroll_behavior(self, driver) -> None:
        """Simulate human scrolling behavior"""
        try:
            # Get page height
            page_height = driver.execute_script("return document.body.scrollHeight;")
            viewport_height = driver.execute_script("return window.innerHeight;")

            if page_height > viewport_height:
                # Simulate reading by scrolling down gradually
                scroll_steps = random.randint(3, 8)
                max_scroll = min(page_height - viewport_height, viewport_height * 3)

                for i in range(scroll_steps):
                    scroll_amount = random.randint(100, 400)
                    current_scroll = driver.execute_script("return window.pageYOffset;")

                    if current_scroll + scroll_amount > max_scroll:
                        break

                    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")

                    # Pause to "read"
                    await asyncio.sleep(random.uniform(0.5, 2.0))

                # Sometimes scroll back up a bit (like re-reading)
                if random.random() < 0.3:
                    back_scroll = random.randint(50, 200)
                    driver.execute_script(f"window.scrollBy(0, -{back_scroll});")
                    await asyncio.sleep(random.uniform(0.3, 1.0))

        except Exception as e:
            logger.debug(f"Scroll behavior simulation failed: {e}")

    def _generate_mouse_path(self, width: int, height: int, num_points: int = 5) -> List[tuple]:
        """Generate natural-looking mouse movement path"""
        points = []

        for i in range(num_points):
            # Favor center-left area (common reading pattern)
            x = int(np.random.normal(width * 0.3, width * 0.2))
            y = int(np.random.normal(height * 0.5, height * 0.3))

            # Keep within bounds
            x = max(0, min(width, x))
            y = max(0, min(height, y))

            points.append((x, y))

        return points

    def should_follow_link(self, url: str, link_text: str, current_depth: int) -> bool:
        """Decide whether to follow a link based on human behavior patterns"""
        # Don't go too deep
        if current_depth > 3:
            return False

        # Skip certain types of links
        skip_patterns = [
            'login', 'signup', 'register', 'advertisement', 'popup',
            'cookie', 'privacy', 'terms', 'contact', 'about'
        ]

        link_lower = link_text.lower()
        if any(pattern in link_lower for pattern in skip_patterns):
            return False

        # Favor article-like links
        article_indicators = [
            'news', 'article', 'story', 'report', 'breaking', 'update',
            'politics', 'world', 'business', 'sports', 'entertainment'
        ]

        is_article_like = any(indicator in link_lower for indicator in article_indicators)

        # 70% chance to follow article-like links, 20% for others
        if is_article_like:
            return random.random() < 0.7
        else:
            return random.random() < 0.2

    def get_session_duration(self) -> float:
        """Get realistic session duration"""
        # Sessions typically last 5-30 minutes
        return random.uniform(300, 1800)

    def should_end_session(self) -> bool:
        """Decide if session should end based on duration and activity"""
        session_age = time.time() - self.session_start_time
        max_duration = self.get_session_duration()

        # 10% chance to end early, or if max duration reached
        if session_age > max_duration:
            return True

        return random.random() < 0.1
