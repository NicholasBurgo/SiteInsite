#!/usr/bin/env python3
"""
Example usage of the Advanced News Scraper
"""

import asyncio
import logging
from scraper_advanced.scraper import AdvancedNewsScraper

# Setup logging
logging.basicConfig(level=logging.INFO)

async def main():
    """Example scraping session"""

    # Initialize scraper
    scraper = AdvancedNewsScraper()

    try:
        # Example 1: Scrape single article
        print("=== Scraping Single Article ===")
        url = "https://www.newsmax.com/newsfront/breaking-news/2024/01/15/id/1146800/"  # Replace with real URL
        result = await scraper.scrape_article(url, "newsmax")

        print(f"Success: {result.get('success', False)}")
        print(f"Title: {result.get('title', 'N/A')[:100]}...")
        print(f"Content Length: {len(result.get('content', ''))}")
        print(f"Author: {result.get('author', 'N/A')}")
        print()

        # Example 2: Scrape multiple articles
        print("=== Scraping Multiple Articles ===")
        urls = [
            # Add real article URLs here
            # "https://www.newsmax.com/article1",
            # "https://www.newsmax.com/article2",
        ]

        if urls:
            results = await scraper.scrape_site_articles("newsmax", urls, max_concurrent=2)

            successful = sum(1 for r in results if r.get('success', False))
            print(f"Completed: {successful}/{len(urls)} successful extractions")

        # Example 3: Health check
        print("=== Health Check ===")
        health = await scraper.health_check()
        print(f"Overall Status: {health['overall']}")

        for component, status in health['components'].items():
            print(f"  {component}: {status['status']}")

        # Example 4: Statistics
        print("=== Statistics ===")
        stats = await scraper.get_stats()
        print(f"Requests Made: {stats['requests_made']}")
        print(f"Success Rate: {stats['success_rate']:.1f}%")

        if 'proxy_stats' in stats:
            proxy = stats['proxy_stats']
            print(f"Healthy Proxies: {proxy['healthy_proxies']}/{proxy['total_proxies']}")

    finally:
        # Cleanup
        await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
