"""
Advanced Anti-Bot Web Scraper
Production-grade scraper for news sites with Cloudflare bypass
"""

__version__ = "1.0.0"

from .scraper import AdvancedNewsScraper
from .config_loader import config_loader
from .cli import ScraperCLI

__all__ = [
    'AdvancedNewsScraper',
    'config_loader',
    'ScraperCLI'
]
