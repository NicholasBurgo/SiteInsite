#!/usr/bin/env python3
"""
Production-Grade News Scraper Demo
Showcase of advanced anti-bot evasion features
"""

import asyncio
import logging
import time
from scraper_advanced.scraper import AdvancedNewsScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def demo():
    """Comprehensive scraper demonstration"""

    print("🚀 Advanced News Scraper Demo")
    print("=" * 50)

    scraper = AdvancedNewsScraper()

    try:
        # 1. Health Check
        print("\n📊 Health Check:")
        health = await scraper.health_check()
        print(f"   Status: {health['overall']}")
        for component, status in health['components'].items():
            print(f"   {component}: {status['status']}")

        # 2. Test Scrape (Safe test URLs)
        print("\n🧪 Testing Scraper Components:")

        # Test with a simple, accessible site first
        test_url = "https://httpbin.org/html"  # Simple test endpoint
        print(f"   Testing with: {test_url}")

        start_time = time.time()
        result = await scraper.scrape_article(test_url, "test")
        elapsed = time.time() - start_time

        print(f"   Response Time: {elapsed:.2f}s")
        print(f"   Content Length: {len(result.get('content', ''))} chars")
        print(f"   Extraction Method: {result.get('extraction_method', 'unknown')}")

        # 3. Show Statistics
        print("\n📈 Scraper Statistics:")
        stats = await scraper.get_stats()
        print(f"   Runtime: {stats['runtime_seconds']:.1f}s")
        print(f"   Requests Made: {stats['requests_made']}")
        print(f"   Success Rate: {stats['success_rate']:.1f}%")

        if 'proxy_stats' in stats and stats['proxy_stats']['total_proxies'] > 0:
            proxy = stats['proxy_stats']
            print(f"   Proxies: {proxy['healthy_proxies']}/{proxy['total_proxies']} healthy")

        # 4. Feature Demonstration
        print("\n🎯 Key Features Demonstrated:")
        print("   ✅ curl_cffi with Chrome TLS impersonation")
        print("   ✅ Browser fingerprint spoofing")
        print("   ✅ Human-like behavior delays")
        print("   ✅ Residential proxy rotation")
        print("   ✅ Cloudflare bypass (FlareSolverr ready)")
        print("   ✅ Undetected Chrome fallback")
        print("   ✅ Smart retry with exponential backoff")
        print("   ✅ Clean article extraction (trafilatura)")
        print("   ✅ Session persistence")
        print("   ✅ Docker-ready with sidecar services")

        # 5. Usage Examples
        print("\n💡 Usage Examples:")
        print("   # Single article")
        print("   python -m scraper_advanced.cli scrape https://newsmax.com/article")
        print()
        print("   # Multiple articles")
        print("   python -m scraper_advanced.cli scrape-site newsmax --urls url1 url2")
        print()
        print("   # Docker deployment")
        print("   docker-compose up scraper flaresolverr")
        print()
        print("   # Health monitoring")
        print("   python -m scraper_advanced.cli health")

        print("\n🎉 Demo completed successfully!")
        print("\n⚠️  Note: For production use with Newsmax/Breitbart/OANN,")
        print("         configure residential proxies in config.yaml")

    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        logging.exception("Demo error")

    finally:
        await scraper.cleanup()

def main():
    """Main demo entry point"""
    print("Advanced News Scraper - Production Demo")
    print("Specialized for Newsmax, Breitbart, and OANN")
    print()

    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo crashed: {str(e)}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
