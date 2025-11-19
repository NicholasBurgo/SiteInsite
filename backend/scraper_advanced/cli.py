#!/usr/bin/env python3
"""
Advanced News Scraper CLI
Production-grade scraper for news sites with anti-bot evasion
"""

import asyncio
import argparse
import sys
import logging
import json
from typing import List, Optional
from pathlib import Path

from .scraper import AdvancedNewsScraper
from .config_loader import config_loader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScraperCLI:
    """Command-line interface for the advanced scraper"""

    def __init__(self):
        self.scraper: Optional[AdvancedNewsScraper] = None

    async def run(self, args: argparse.Namespace):
        """Run the CLI with parsed arguments"""

        try:
            # Initialize scraper
            config_path = args.config if hasattr(args, 'config') else None
            self.scraper = AdvancedNewsScraper(config_path)

            logger.info("Advanced News Scraper initialized")

            # Execute command
            if args.command == 'scrape':
                await self._cmd_scrape(args)
            elif args.command == 'scrape-site':
                await self._cmd_scrape_site(args)
            elif args.command == 'health':
                await self._cmd_health()
            elif args.command == 'stats':
                await self._cmd_stats()
            elif args.command == 'test':
                await self._cmd_test(args)
            else:
                logger.error(f"Unknown command: {args.command}")

        except Exception as e:
            logger.error(f"CLI execution failed: {str(e)}")
            sys.exit(1)

        finally:
            if self.scraper:
                await self.scraper.cleanup()

    async def _cmd_scrape(self, args: argparse.Namespace):
        """Scrape single article"""

        if not args.url:
            logger.error("URL required for scrape command")
            sys.exit(1)

        logger.info(f"Scraping article: {args.url}")

        result = await self.scraper.scrape_article(args.url, args.site)

        if args.output:
            # Save to file
            output_file = Path(args.output)
            output_file.parent.mkdir(exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            logger.info(f"Result saved to {output_file}")
        else:
            # Print to stdout
            print(json.dumps(result, indent=2, ensure_ascii=False))

    async def _cmd_scrape_site(self, args: argparse.Namespace):
        """Scrape multiple articles from a site"""

        if not args.site:
            logger.error("Site name required for scrape-site command")
            sys.exit(1)

        if not args.urls and not args.url_file:
            logger.error("URLs or URL file required")
            sys.exit(1)

        # Get URLs
        urls = []
        if args.urls:
            urls = args.urls
        elif args.url_file:
            with open(args.url_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]

        if not urls:
            logger.error("No URLs to scrape")
            sys.exit(1)

        logger.info(f"Scraping {len(urls)} articles from {args.site}")

        results = await self.scraper.scrape_site_articles(
            args.site, urls, max_concurrent=args.concurrency
        )

        # Save results
        if args.output:
            output_file = Path(args.output)
            output_file.parent.mkdir(exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"Results saved to {output_file}")
        else:
            print(json.dumps(results, indent=2, ensure_ascii=False))

        # Print summary
        successful = sum(1 for r in results if r.get('success', False))
        logger.info(f"Completed: {successful}/{len(urls)} successful extractions")

    async def _cmd_health(self):
        """Show health status"""

        if not self.scraper:
            logger.error("Scraper not initialized")
            return

        health = await self.scraper.health_check()

        print("=== Scraper Health Check ===")
        print(f"Overall Status: {health['overall']}")

        print("\nComponent Status:")
        for component, status in health['components'].items():
            print(f"  {component}: {status['status']}")

        if health.get('issues'):
            print(f"\nIssues: {', '.join(health['issues'])}")

        print("\nDetailed Status:")
        print(json.dumps(health, indent=2))

    async def _cmd_stats(self):
        """Show scraper statistics"""

        if not self.scraper:
            logger.error("Scraper not initialized")
            return

        stats = await self.scraper.get_stats()

        print("=== Scraper Statistics ===")
        print(f"Runtime: {stats['runtime_seconds']:.1f} seconds")
        print(f"Requests Made: {stats['requests_made']}")
        print(f"Successful Extractions: {stats['successful_extractions']}")
        print(f"Failed Requests: {stats['failed_requests']}")
        print(f"Success Rate: {stats['success_rate']:.1f}%")

        if 'proxy_stats' in stats:
            proxy = stats['proxy_stats']
            print(f"\nProxy Stats:")
            print(f"  Total Proxies: {proxy['total_proxies']}")
            print(f"  Healthy Proxies: {proxy['healthy_proxies']}")
            print(f"  Banned Proxies: {proxy['banned_proxies']}")

    async def _cmd_test(self, args: argparse.Namespace):
        """Run test scraping"""

        test_urls = {
            'newsmax': 'https://www.newsmax.com/newsfront/breaking-news/2024/01/15/id/1146800/',
            'breitbart': 'https://www.breitbart.com/politics/2024/01/15/example-article/',
            'oann': 'https://www.oann.com/newsroom/example-article/'
        }

        site = args.site or 'newsmax'
        url = test_urls.get(site)

        if not url:
            logger.error(f"No test URL for site: {site}")
            sys.exit(1)

        logger.info(f"Running test scrape on {site}: {url}")

        result = await self.scraper.scrape_article(url, site)

        print("=== Test Result ===")
        print(f"Success: {result.get('success', False)}")
        print(f"Title: {result.get('title', 'N/A')[:100]}...")
        print(f"Content Length: {len(result.get('content', ''))}")
        print(f"Author: {result.get('author', 'N/A')}")
        print(f"Date: {result.get('publish_date', 'N/A')}")

        if result.get('error'):
            print(f"Error: {result['error']}")

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""

    parser = argparse.ArgumentParser(
        description="Advanced News Scraper - Production-grade scraper with anti-bot evasion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape single article
  python -m scraper_advanced.cli scrape https://www.newsmax.com/article

  # Scrape multiple articles from site
  python -m scraper_advanced.cli scrape-site newsmax --urls url1 url2 url3

  # Scrape from URL file
  python -m scraper_advanced.cli scrape-site newsmax --url-file urls.txt

  # Health check
  python -m scraper_advanced.cli health

  # Test scrape
  python -m scraper_advanced.cli test --site newsmax
        """
    )

    parser.add_argument('--config', help='Path to config file (default: config.yaml)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Scrape single article
    scrape_parser = subparsers.add_parser('scrape', help='Scrape single article')
    scrape_parser.add_argument('url', help='Article URL to scrape')
    scrape_parser.add_argument('--site', help='Site name (auto-detected if not provided)')
    scrape_parser.add_argument('--output', '-o', help='Output file path')

    # Scrape site articles
    site_parser = subparsers.add_parser('scrape-site', help='Scrape multiple articles from site')
    site_parser.add_argument('site', help='Site name (newsmax, breitbart, oann)')
    site_parser.add_argument('--urls', nargs='+', help='Article URLs to scrape')
    site_parser.add_argument('--url-file', help='File containing URLs (one per line)')
    site_parser.add_argument('--concurrency', type=int, default=3, help='Max concurrent requests')
    site_parser.add_argument('--output', '-o', help='Output file path')

    # Health check
    subparsers.add_parser('health', help='Show scraper health status')

    # Statistics
    subparsers.add_parser('stats', help='Show scraper statistics')

    # Test
    test_parser = subparsers.add_parser('test', help='Run test scrape')
    test_parser.add_argument('--site', choices=['newsmax', 'breitbart', 'oann'],
                           default='newsmax', help='Site to test')

    return parser

def main():
    """Main CLI entry point"""

    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Run CLI
    cli = ScraperCLI()
    asyncio.run(cli.run(args))

if __name__ == '__main__':
    main()
