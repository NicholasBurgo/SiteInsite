import asyncio
from typing import Optional, List
from playwright.async_api import async_playwright, Browser, Page
from backend.core.config import Settings

class RenderPool:
    """
    Playwright browser pool for JavaScript rendering.
    """
    
    def __init__(self, settings: Settings, pool_size: int = 3):
        self.settings = settings
        self.pool_size = pool_size
        self.browsers: List[Browser] = []
        self.pages: List[Page] = []
        self.playwright = None
        self._initialized = False
        
    async def initialize(self):
        """
        Initialize Playwright and browser pool.
        """
        if self._initialized:
            return
            
        self.playwright = await async_playwright().start()
        
        # Create browser instances
        for _ in range(self.pool_size):
            browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self.browsers.append(browser)
            
        # Create pages
        for browser in self.browsers:
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})
            self.pages.append(page)
            
        self._initialized = True
        
    async def render(self, url: str) -> Optional[str]:
        """
        Render URL with JavaScript and return HTML.
        """
        if not self._initialized:
            await self.initialize()
            
        if not self.pages:
            return None
            
        # Get available page
        page = self.pages.pop()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            content = await page.content()
            return content
        except Exception as e:
            print(f"Render error for {url}: {e}")
            return None
        finally:
            # Return page to pool
            self.pages.append(page)
            
    async def close(self):
        """
        Close all browsers and playwright.
        """
        for browser in self.browsers:
            await browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False
        
    async def __aenter__(self):
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

# Global render pool instance
_render_pool: Optional[RenderPool] = None

async def get_render_pool(settings: Settings) -> Optional[RenderPool]:
    """
    Get global render pool instance.
    """
    global _render_pool
    if not _render_pool and settings.RENDER_ENABLED:
        _render_pool = RenderPool(settings)
        await _render_pool.initialize()
    return _render_pool