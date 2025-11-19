import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from urllib.parse import urljoin, urlparse
import aiofiles

from .config_loader import config_loader
from .proxy_manager import ProxyManager
from .fingerprint_spoofer import FingerprintSpoofer
from .human_behavior import HumanBehaviorEngine
from .cloudflare_bypass import CloudflareBypass
from .http_client import AdvancedHttpClient
from .selenium_fallback import UndetectedChromeFallback
from .article_extractor import ArticleExtractor

logger = logging.getLogger(__name__)

class AdvancedNewsScraper:
    """Production-grade news scraper with advanced anti-bot evasion"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = config_loader.load()
        if config_path:
            # Override config path if specified
            from .config_loader import ConfigLoader
            loader = ConfigLoader(config_path)
            self.config = loader.load()

        # Initialize components
        self.proxy_manager = ProxyManager(self.config.get('scraper', {}).get('proxies', {}))
        self.fingerprint_spoofer = FingerprintSpoofer(self.config.get('scraper', {}).get('fingerprinting', {}))
        self.human_behavior = HumanBehaviorEngine(self.config.get('scraper', {}).get('human_delays', {}))
        self.cf_bypass = CloudflareBypass(self.config.get('scraper', {}).get('cloudflare', {}))
        self.http_client = AdvancedHttpClient(
            self.config.get('scraper', {}),
            proxy_manager=self.proxy_manager,
            fingerprint_spoofer=self.fingerprint_spoofer,
            cf_bypass=self.cf_bypass,
            human_behavior=self.human_behavior
        )
        self.selenium_fallback = UndetectedChromeFallback(
            self.config.get('scraper', {}),
            proxy_manager=self.proxy_manager,
            fingerprint_spoofer=self.fingerprint_spoofer,
            human_behavior=self.human_behavior
        )
        self.article_extractor = ArticleExtractor(self.config.get('scraper', {}).get('output', {}))

        # Session management
        self.sessions: Dict[str, str] = {}  # domain -> session_id

        # Output
        self.output_dir = Path(self.config.get('scraper', {}).get('output', {}).get('output_dir', './output'))
        self.output_dir.mkdir(exist_ok=True)

        # Stats
        self.stats = {
            'requests_made': 0,
            'successful_extractions': 0,
            'failed_requests': 0,
            'proxy_failures': 0,
            'cloudflare_challenges': 0,
            'start_time': time.time()
        }

    async def scrape_article(self, url: str, site_name: str = None) -> Dict[str, Any]:
        """
        Scrape a single article URL

        Returns structured article data
        """

        self.stats['requests_made'] += 1

        try:
            # Determine site name if not provided
            if not site_name:
                domain = urlparse(url).netloc.lower()
                site_name = self._guess_site_name(domain)

            logger.info(f"Scraping article: {url} (site: {site_name})")

            # Get or create session for domain
            session_id = self._get_session_for_domain(urlparse(url).netloc)

            # Generate fingerprint for this request
            fingerprint = self.fingerprint_spoofer.generate_fingerprint()

            # Check if we should visit homepage first
            homepage_url = await self._maybe_visit_homepage(url, site_name, session_id, fingerprint)

            # Make the main request
            response = await self.http_client.request(
                url, session_id=session_id, fingerprint=fingerprint
            )

            if response.status_code != 200 or not response.content:
                logger.warning(f"HTTP request failed for {url}: {response.status_code}")

                # Try browser fallback
                logger.info(f"Attempting browser fallback for {url}")
                browser_success, browser_content, browser_cookies = await self.selenium_fallback.get_page_content(
                    url, proxy=await self.proxy_manager.get_proxy(urlparse(url).netloc), fingerprint=fingerprint
                )

                if browser_success and browser_content:
                    response.content = browser_content
                    response.cookies.update(browser_cookies or {})
                    response.status_code = 200
                else:
                    self.stats['failed_requests'] += 1
                    return self._create_error_result(url, "All request methods failed")

            # Extract article content
            article_data = self.article_extractor.extract_article(response.content, url, site_name)

            if article_data.get('success'):
                self.stats['successful_extractions'] += 1
                await self._save_article(article_data)
            else:
                self.stats['failed_requests'] += 1

            return article_data

        except Exception as e:
            logger.error(f"Scraping failed for {url}: {str(e)}")
            self.stats['failed_requests'] += 1
            return self._create_error_result(url, str(e))

    async def scrape_site_articles(self, site_name: str, urls: List[str], max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """
        Scrape multiple articles from a site with concurrency control
        """

        logger.info(f"Scraping {len(urls)} articles from {site_name} (max_concurrent: {max_concurrent})")

        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def scrape_with_semaphore(url: str):
            async with semaphore:
                result = await self.scrape_article(url, site_name)
                results.append(result)

        # Scrape concurrently
        tasks = [scrape_with_semaphore(url) for url in urls]
        await asyncio.gather(*tasks, return_exceptions=True)

        successful = sum(1 for r in results if r.get('success', False))
        logger.info(f"Completed scraping {site_name}: {successful}/{len(urls)} successful")

        return results

    async def _maybe_visit_homepage(self, article_url: str, site_name: str, session_id: str, fingerprint) -> Optional[str]:
        """Visit homepage first based on human behavior patterns"""

        if not self.human_behavior:
            return None

        homepage_url = await self.human_behavior.simulate_homepage_visit(
            self._get_homepage_url(article_url, site_name), article_url
        )

        if homepage_url:
            logger.debug(f"Visiting homepage first: {homepage_url}")

            # Make homepage request
            response = await self.http_client.request(
                homepage_url, session_id=session_id, fingerprint=fingerprint, is_first_request=True
            )

            if response.status_code == 200:
                # Simulate asset requests
                await self.human_behavior.simulate_asset_requests(homepage_url, response.content)

        return homepage_url

    def _get_homepage_url(self, article_url: str, site_name: str) -> str:
        """Get homepage URL for a site"""

        parsed = urlparse(article_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Check config for custom homepage
        site_config = self.config.get('scraper', {}).get('targets', {}).get(site_name, {})
        if 'base_url' in site_config:
            return site_config['base_url']

        return base_url

    def _guess_site_name(self, domain: str) -> str:
        """Guess site name from domain"""

        domain = domain.lower().replace('www.', '')

        site_mappings = {
            'newsmax.com': 'newsmax',
            'breitbart.com': 'breitbart',
            'oann.com': 'oann'
        }

        return site_mappings.get(domain, domain.split('.')[0])

    def _get_session_for_domain(self, domain: str) -> str:
        """Get or create session for domain"""

        if domain not in self.sessions:
            self.sessions[domain] = self.http_client.create_session(domain)
            logger.debug(f"Created session for domain: {domain}")

        return self.sessions[domain]

    async def _save_article(self, article_data: Dict[str, Any]):
        """Save extracted article to output"""

        output_config = self.config.get('scraper', {}).get('output', {})
        format_type = output_config.get('format', 'jsonl')

        if format_type == 'jsonl':
            await self._save_as_jsonl(article_data)
        elif format_type == 'json':
            await self._save_as_json(article_data)
        else:
            logger.warning(f"Unknown output format: {format_type}")

    async def _save_as_jsonl(self, article_data: Dict[str, Any]):
        """Save article as JSONL line"""

        output_file = self.output_dir / 'articles.jsonl'

        # Add metadata
        enriched_data = {
            **article_data,
            'scraper_metadata': {
                'timestamp': time.time(),
                'version': '1.0.0'
            }
        }

        async with aiofiles.open(output_file, 'a', encoding='utf-8') as f:
            await f.write(json.dumps(enriched_data, ensure_ascii=False) + '\n')

    async def _save_as_json(self, article_data: Dict[str, Any]):
        """Save article as individual JSON file"""

        # Use URL hash as filename
        import hashlib
        url_hash = hashlib.md5(article_data['url'].encode()).hexdigest()[:8]
        filename = f"{article_data.get('site_name', 'unknown')}_{url_hash}.json"

        output_file = self.output_dir / filename

        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(article_data, indent=2, ensure_ascii=False))

    def _create_error_result(self, url: str, error: str) -> Dict[str, Any]:
        """Create error result for failed scraping"""

        return {
            'url': url,
            'success': False,
            'error': error,
            'site_name': self._guess_site_name(urlparse(url).netloc),
            'extracted_at': time.time(),
            'extraction_method': 'error'
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Get scraper statistics"""

        # Update proxy stats
        proxy_stats = await self.proxy_manager.get_stats() if self.proxy_manager else {}

        return {
            **self.stats,
            'runtime_seconds': time.time() - self.stats['start_time'],
            'success_rate': (self.stats['successful_extractions'] / max(1, self.stats['requests_made'])) * 100,
            'proxy_stats': proxy_stats
        }

    async def cleanup(self):
        """Cleanup resources"""

        logger.info("Cleaning up scraper resources...")

        # Close HTTP client sessions
        self.http_client.cleanup_sessions()

        # Close browser if running
        await self.selenium_fallback.cleanup()

        # Cleanup Cloudflare sessions
        await self.cf_bypass.cleanup_sessions()

        logger.info("Cleanup completed")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of all components"""

        health = {
            'overall': 'healthy',
            'components': {}
        }

        # Check proxy manager
        if self.proxy_manager:
            proxy_stats = await self.proxy_manager.get_stats()
            health['components']['proxy_manager'] = {
                'status': 'healthy' if proxy_stats['healthy_proxies'] > 0 else 'degraded',
                'stats': proxy_stats
            }

        # Check HTTP client
        health['components']['http_client'] = {
            'status': 'healthy',
            'sessions_active': len(self.http_client.sessions)
        }

        # Check browser fallback
        health['components']['browser_fallback'] = {
            'status': 'healthy' if self.selenium_fallback else 'unavailable'
        }

        # Check Cloudflare bypass
        health['components']['cloudflare_bypass'] = {
            'status': 'healthy'
        }

        # Overall health
        unhealthy_components = [k for k, v in health['components'].items() if v['status'] != 'healthy']
        if unhealthy_components:
            health['overall'] = 'degraded'
            health['issues'] = unhealthy_components

        return health
