"""
Storage utilities for confirmation and seed data.
Handles site-level data (nav, footer) and page-level structured content.
"""
import os
import json
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from backend.extract.nav_footer import extract_navigation, extract_footer
from backend.storage.async_io import get_async_writer


class ConfirmationStore:
    """
    File-based storage for confirmation data.
    Manages site.json, pages_index.json, and individual page files.
    """
    
    def __init__(self, run_id: str, data_dir: str = "runs"):
        self.run_id = run_id
        self.data_dir = data_dir
        self.run_dir = os.path.join(data_dir, run_id)
        self.site_file = os.path.join(self.run_dir, "site.json")
        self.pages_index_file = os.path.join(self.run_dir, "pages_index.json")
        self.pages_dir = os.path.join(self.run_dir, "pages")
        
        # Ensure directories exist
        os.makedirs(self.run_dir, exist_ok=True)
        os.makedirs(self.pages_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize site.json and pages_index.json if they don't exist."""
        if not os.path.exists(self.site_file):
            with open(self.site_file, 'w') as f:
                json.dump({
                    "baseUrl": "",
                    "nav": [],
                    "footer": {
                        "columns": [],
                        "socials": [],
                        "contact": {}
                    },
                    "brand": None
                }, f)
        
        if not os.path.exists(self.pages_index_file):
            with open(self.pages_index_file, 'w') as f:
                json.dump([], f)
    
    def extract_site_data(self, html_content: str, base_url: str):
        """Extract and save site-level navigation and footer data."""
        from bs4 import BeautifulSoup
        import aiohttp
        import asyncio
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract navigation
        nav = extract_navigation(soup, base_url)
        
        # Extract footer
        footer = extract_footer(soup, base_url)
        
        # Detect robots.txt and sitemap
        robots_present, sitemap_present = self._detect_robots_and_sitemap(base_url)
        
        # Update site.json
        site_data = {
            "baseUrl": base_url,
            "nav": nav,
            "footer": footer,
            "brand": self._extract_brand_info(soup, base_url),
            "robots_present": robots_present,
            "sitemap_present": sitemap_present
        }
        
        with open(self.site_file, 'w') as f:
            json.dump(site_data, f, indent=2)
    
    def _detect_robots_and_sitemap(self, base_url: str) -> tuple[bool, bool]:
        """Detect if robots.txt and sitemap exist for the site."""
        import urllib.request
        import urllib.error
        from urllib.parse import urlparse
        
        robots_present = False
        sitemap_present = False
        
        try:
            parsed = urlparse(base_url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"
            
            # Check robots.txt
            try:
                req = urllib.request.Request(robots_url)
                req.add_header('User-Agent', 'SiteInsite/1.0')
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        robots_present = True
                        # Parse robots.txt for sitemap references
                        content = resp.read().decode('utf-8', errors='ignore')
                        for line in content.split('\n'):
                            line = line.strip()
                            if line.startswith('Sitemap:'):
                                sitemap_present = True
                                break
            except (urllib.error.URLError, urllib.error.HTTPError, Exception):
                pass
            
            # Check sitemap.xml directly if not found in robots.txt
            if not sitemap_present:
                try:
                    req = urllib.request.Request(sitemap_url)
                    req.add_header('User-Agent', 'SiteInsite/1.0')
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        if resp.status == 200:
                            sitemap_present = True
                except (urllib.error.URLError, urllib.error.HTTPError, Exception):
                    pass
                    
        except Exception:
            pass
        
        return robots_present, sitemap_present
    
    async def add_page_to_index(self, page_data: Dict[str, Any]):
        """Add page to pages_index.json asynchronously."""
        writer = get_async_writer()
        
        def update_index(new_page_data, existing_index):
            """Update function to add or update page in index."""
            if existing_index is None:
                existing_index = []
            
            page_id = new_page_data.get("pageId")
            existing_page = next((p for p in existing_index if p.get("pageId") == page_id), None)
            
            if existing_page:
                # Update existing page
                existing_page.update({
                    "titleGuess": new_page_data.get("title"),
                    "path": new_page_data.get("path", "/"),
                    "url": new_page_data.get("url"),
                    "status": new_page_data.get("status"),
                    "status_code": new_page_data.get("status_code"),
                    "words": new_page_data.get("words", 0),
                    "mediaCount": new_page_data.get("mediaCount", 0),
                    "loadTimeMs": new_page_data.get("loadTimeMs"),
                    "contentLengthBytes": new_page_data.get("contentLengthBytes"),
                    "page_type": new_page_data.get("page_type")
                })
            else:
                # Add new page
                existing_index.append({
                    "pageId": page_id,
                    "titleGuess": new_page_data.get("title"),
                    "path": new_page_data.get("path", "/"),
                    "url": new_page_data.get("url"),
                    "status": new_page_data.get("status"),
                    "status_code": new_page_data.get("status_code"),
                    "words": new_page_data.get("words", 0),
                    "mediaCount": new_page_data.get("mediaCount", 0),
                    "loadTimeMs": new_page_data.get("loadTimeMs"),
                    "contentLengthBytes": new_page_data.get("contentLengthBytes"),
                    "page_type": new_page_data.get("page_type", "generic")
                })
            
            return existing_index
        
        await writer.write_json(self.pages_index_file, page_data, update_func=update_index)
    
    def get_site_data(self) -> Dict[str, Any]:
        """Get site-level data (nav, footer, brand)."""
        try:
            with open(self.site_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading site data: {e}")
            return {
                "baseUrl": "",
                "nav": [],
                "footer": {"columns": [], "socials": [], "contact": {}},
                "brand": None
            }
    
    def update_navigation(self, nav: List[Dict[str, Any]]):
        """Update navigation in site.json."""
        try:
            site_data = self.get_site_data()
            site_data["nav"] = nav
            
            with open(self.site_file, 'w') as f:
                json.dump(site_data, f, indent=2)
                
        except Exception as e:
            print(f"Error updating navigation: {e}")
    
    def update_footer(self, footer: Dict[str, Any]):
        """Update footer in site.json."""
        try:
            site_data = self.get_site_data()
            site_data["footer"] = footer
            
            with open(self.site_file, 'w') as f:
                json.dump(site_data, f, indent=2)
                
        except Exception as e:
            print(f"Error updating footer: {e}")
    
    def get_pages_index(self) -> List[Dict[str, Any]]:
        """Get pages index."""
        try:
            with open(self.pages_index_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading pages index: {e}")
            return []
    
    def get_page_content(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get structured content for a specific page."""
        try:
            page_file = os.path.join(self.pages_dir, f"{page_id}.json")
            if os.path.exists(page_file):
                with open(page_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error reading page content: {e}")
        return None
    
    async def update_page_content(self, page_id: str, content: Dict[str, Any]):
        """Update structured content for a specific page asynchronously."""
        page_file = os.path.join(self.pages_dir, f"{page_id}.json")
        writer = get_async_writer()
        await writer.write_json(page_file, content)
    
    def _extract_brand_info(self, soup, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract basic brand information."""
        brand = {}
        
        # Try to find logo
        logo_selectors = [
            'img[alt*="logo" i]',
            'img[class*="logo" i]',
            'img[id*="logo" i]',
            '.logo img',
            '#logo img'
        ]
        
        for selector in logo_selectors:
            logo_img = soup.select_one(selector)
            if logo_img and logo_img.get('src'):
                brand["logo"] = logo_img['src']
                break
        
        # Try to extract brand name from title or h1
        title = soup.find('title')
        if title and title.get_text():
            brand["name"] = title.get_text().strip()
        
        return brand if brand else None
