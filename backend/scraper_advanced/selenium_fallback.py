import asyncio
import time
import random
import logging
from typing import Optional, Dict, Any, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

try:
    import undetected_chromedriver as uc
    from selenium_stealth import stealth
    UNDETECTED_AVAILABLE = True
except ImportError:
    UNDETECTED_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("undetected-chromedriver or selenium-stealth not available")

logger = logging.getLogger(__name__)

class UndetectedChromeFallback:
    """Fallback browser automation using undetected-chromedriver + selenium-stealth"""

    def __init__(self, config: Dict[str, Any], proxy_manager=None, fingerprint_spoofer=None,
                 human_behavior=None):
        self.config = config
        self.proxy_manager = proxy_manager
        self.fingerprint_spoofer = fingerprint_spoofer
        self.human_behavior = human_behavior

        self.timeout = config.get('timeout', 30)
        self.headless = True  # Run headless for server environment

        # Browser instance management
        self.driver = None
        self.current_proxy = None
        self.current_fingerprint = None

    async def get_page_content(self, url: str, wait_for_selector: Optional[str] = None,
                              proxy: Optional[Any] = None, fingerprint: Optional[Any] = None) -> Tuple[bool, Optional[str], Optional[Dict[str, str]]]:
        """
        Get page content using browser automation

        Returns: (success, html_content, cookies_dict)
        """
        try:
            # Initialize or reinitialize browser if needed
            await self._ensure_browser_ready(proxy, fingerprint)

            if not self.driver:
                logger.error("Failed to initialize browser")
                return False, None, None

            logger.info(f"Fetching {url} with browser automation")

            # Navigate to page
            self.driver.get(url)

            # Wait for page load
            await self._wait_for_page_load(wait_for_selector)

            # Simulate human behavior
            if self.human_behavior:
                await self.human_behavior.simulate_mouse_movements(self.driver)
                await self.human_behavior.simulate_scroll_behavior(self.driver)

                # Wait a bit for dynamic content
                await asyncio.sleep(random.uniform(1.0, 3.0))

            # Get page content
            html_content = self.driver.page_source

            # Get cookies
            cookies = {}
            for cookie in self.driver.get_cookies():
                cookies[cookie['name']] = cookie['value']

            logger.info(f"Successfully retrieved content from {url} ({len(html_content)} chars)")
            return True, html_content, cookies

        except Exception as e:
            logger.error(f"Browser automation failed for {url}: {str(e)}")

            # Mark proxy as failed if used
            if proxy and self.proxy_manager:
                await self.proxy_manager.mark_failure(proxy, f"Browser error: {str(e)}")

            return False, None, None

    async def _ensure_browser_ready(self, proxy: Optional[Any] = None, fingerprint: Optional[Any] = None):
        """Ensure browser is ready with correct configuration"""

        # Check if we need to restart browser (proxy or fingerprint change)
        needs_restart = (
            self.driver is None or
            self.current_proxy != proxy or
            self.current_fingerprint != fingerprint
        )

        if needs_restart:
            await self._close_browser()
            await self._start_browser(proxy, fingerprint)

    async def _start_browser(self, proxy: Optional[Any] = None, fingerprint: Optional[Any] = None):
        """Start undetected Chrome browser"""

        if not UNDETECTED_AVAILABLE:
            logger.error("undetected-chromedriver not available")
            return

        try:
            options = self._create_chrome_options(proxy, fingerprint)

            logger.info("Starting undetected Chrome browser...")

            # Use undetected-chromedriver
            self.driver = uc.Chrome(
                options=options,
                version_main=124,  # Use Chrome 124
                headless=self.headless
            )

            # Apply selenium-stealth
            stealth(self.driver,
                   languages=["en-US", "en"],
                   vendor="Google Inc.",
                   platform="Win32",
                   webgl_vendor="Intel Inc.",
                   renderer="Intel(R) Iris(TM) Graphics 6100",
                   fix_hairline=True,
                   )

            # Additional anti-detection measures
            self._apply_additional_stealth()

            self.current_proxy = proxy
            self.current_fingerprint = fingerprint

            logger.info("Browser started successfully")

        except Exception as e:
            logger.error(f"Failed to start browser: {str(e)}")
            self.driver = None

    def _create_chrome_options(self, proxy: Optional[Any] = None, fingerprint: Optional[Any] = None) -> Options:
        """Create Chrome options with anti-detection measures"""

        options = uc.ChromeOptions()

        # Basic options
        if self.headless:
            options.add_argument("--headless=new")  # Use new headless mode

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Speed up loading
        options.add_argument("--disable-javascript")  # Can be enabled if needed
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")

        # Window size (realistic)
        if fingerprint and hasattr(fingerprint, 'viewport_size'):
            width, height = fingerprint.viewport_size
            options.add_argument(f"--window-size={width},{height}")
        else:
            options.add_argument("--window-size=1366,768")

        # User agent
        if fingerprint and hasattr(fingerprint, 'user_agent'):
            options.add_argument(f"--user-agent={fingerprint.user_agent}")

        # Proxy
        if proxy:
            options.add_argument(f"--proxy-server={proxy.selenium_url}")

        # Disable automation indicators
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Language and locale
        if fingerprint and hasattr(fingerprint, 'language'):
            options.add_argument(f"--lang={fingerprint.language}")

        # Timezone (if available)
        if fingerprint and hasattr(fingerprint, 'timezone'):
            options.add_argument(f"--timezone={fingerprint.timezone}")

        # Additional anti-detection
        options.add_argument("--disable-features=VizDisplayCompositor")

        return options

    def _apply_additional_stealth(self):
        """Apply additional stealth measures via JavaScript"""

        if not self.driver:
            return

        try:
            # Remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Mock plugins and languages
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {name: 'Chrome PDF Plugin', description: 'Portable Document Format', filename: 'internal-pdf-viewer'},
                        {name: 'Chrome PDF Viewer', description: '', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                        {name: 'Native Client', description: '', filename: 'internal-nacl-plugin'}
                    ]
                });

                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)

            # Mock hardware concurrency
            if hasattr(self.current_fingerprint, 'hardware_concurrency'):
                self.driver.execute_script(f"""
                    Object.defineProperty(navigator, 'hardwareConcurrency', {{
                        get: () => {self.current_fingerprint.hardware_concurrency}
                    }});
                """)

            # Mock device memory
            if hasattr(self.current_fingerprint, 'device_memory'):
                self.driver.execute_script(f"""
                    Object.defineProperty(navigator, 'deviceMemory', {{
                        get: () => {self.current_fingerprint.device_memory}
                    }});
                """)

        except Exception as e:
            logger.debug(f"Additional stealth application failed: {str(e)}")

    async def _wait_for_page_load(self, wait_for_selector: Optional[str] = None, timeout: int = 10):
        """Wait for page to load"""

        if not self.driver:
            return

        try:
            # Wait for document ready
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )

            # Wait for specific selector if provided
            if wait_for_selector:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                )

            # Additional wait for dynamic content
            await asyncio.sleep(1.0)

        except TimeoutException:
            logger.warning("Page load timeout, continuing anyway")
        except Exception as e:
            logger.debug(f"Page load wait failed: {str(e)}")

    async def _close_browser(self):
        """Close browser instance"""

        if self.driver:
            try:
                self.driver.quit()
                logger.debug("Browser closed")
            except Exception as e:
                logger.debug(f"Browser close error: {str(e)}")
            finally:
                self.driver = None
                self.current_proxy = None
                self.current_fingerprint = None

    async def cleanup(self):
        """Cleanup resources"""
        await self._close_browser()

    def __del__(self):
        """Destructor cleanup"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass
