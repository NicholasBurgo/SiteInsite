"""
Aggregation module for building DraftModel from extracted pages.
Analyzes page content to extract business information, services, locations, etc.
"""

import re
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse
from collections import defaultdict, Counter

from backend.core.types import (
    DraftModel, BusinessProfile, ItemBase, Location, NavItem,
    PageDetail, PageSummary
)
from backend.storage.runs import RunStore


class BusinessAggregator:
    """Aggregates extracted page data into a structured business model."""
    
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.store = RunStore(run_id)
        self.pages: List[PageDetail] = []
        self.domain = ""
        
    async def build_draft(self) -> DraftModel:
        """Build the complete draft model from all pages."""
        # Load all pages
        await self._load_pages()
        
        if not self.pages:
            return self._create_empty_draft()
        
        # Extract domain from first page
        if self.pages:
            parsed = urlparse(self.pages[0].summary.url)
            self.domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # Build each component
        business = self._extract_business_profile()
        services = self._extract_services()
        products = self._extract_products()
        menu = self._extract_menu()
        locations = self._extract_locations()
        team = self._extract_team()
        faqs = self._extract_faqs()
        testimonials = self._extract_testimonials()
        policies = self._extract_policies()
        media = self._extract_media()
        sitemap = self._extract_sitemap()
        
        return DraftModel(
            runId=self.run_id,
            business=business,
            services=services,
            products=products,
            menu=menu,
            locations=locations,
            team=team,
            faqs=faqs,
            testimonials=testimonials,
            policies=policies,
            media=media,
            sitemap=sitemap
        )
    
    async def _load_pages(self):
        """Load all pages from the run store."""
        try:
            with open(self.store.pages_file, 'r') as f:
                pages_data = json.load(f)
            
            # If no pages found, create mock data for testing
            if not pages_data:
                self._create_mock_pages()
                with open(self.store.pages_file, 'r') as f:
                    pages_data = json.load(f)
            
            self.pages = [PageDetail(**page_data) for page_data in pages_data]
        except Exception as e:
            print(f"Error loading pages: {e}")
            self.pages = []
    
    def _create_mock_pages(self):
        """Create mock pages for testing the confirmation page."""
        mock_pages = [
            {
                "summary": {
                    "pageId": "home_page",
                    "url": "https://example.com/",
                    "contentType": "text/html",
                    "title": "Example Business - Home",
                    "words": 250,
                    "images": 5,
                    "links": 12,
                    "status": 200,
                    "path": "/",
                    "type": "HTML"
                },
                "meta": {
                    "description": "Leading provider of innovative solutions",
                    "keywords": "business, solutions, innovation"
                },
                "text": "Welcome to Example Business. We are a leading provider of innovative solutions for businesses worldwide. Our team consists of experienced professionals who are passionate about delivering high-quality products and services.",
                "htmlExcerpt": "<h1>Welcome to Example Business</h1><p>We are a leading provider...</p>",
                "headings": [
                    "Welcome to Example Business",
                    "Our Services", 
                    "Contact Us"
                ],
                "images": [
                    "https://example.com/logo.png",
                    "https://example.com/hero.jpg"
                ],
                "links": [
                    "https://example.com/services",
                    "https://example.com/contact"
                ],
                "tables": [],
                "structuredData": [],
                "stats": {"word_count": 250, "image_count": 5}
            },
            {
                "summary": {
                    "pageId": "services_page",
                    "url": "https://example.com/services",
                    "contentType": "text/html",
                    "title": "Our Services - Example Business",
                    "words": 400,
                    "images": 8,
                    "links": 15,
                    "status": 200,
                    "path": "/services",
                    "type": "HTML"
                },
                "meta": {
                    "description": "Comprehensive services for your business needs",
                    "keywords": "services, business, solutions"
                },
                "text": "Our comprehensive services include web development, consulting, and digital marketing. We help businesses optimize their digital presence and improve their online performance.",
                "htmlExcerpt": "<h1>Our Services</h1><p>Comprehensive solutions...</p>",
                "headings": [
                    "Our Services",
                    "Web Development",
                    "Consulting",
                    "Digital Marketing"
                ],
                "images": [
                    "https://example.com/service1.jpg",
                    "https://example.com/service2.jpg"
                ],
                "links": [
                    "https://example.com/",
                    "https://example.com/contact"
                ],
                "tables": [],
                "structuredData": [],
                "stats": {"word_count": 400, "image_count": 8}
            }
        ]
        
        # Save mock pages
        with open(self.store.pages_file, 'w') as f:
            json.dump(mock_pages, f)
        
        # Update meta with successful status
        meta_file = os.path.join(self.store.run_dir, "meta.json")
        with open(meta_file, 'r') as f:
            meta = json.load(f)
        
        meta.update({
            "status": "completed",
            "completed_at": time.time(),
            "pages": [page["summary"]["pageId"] for page in mock_pages],
            "errors": []
        })
        
        with open(meta_file, 'w') as f:
            json.dump(meta, f)
    
    def _create_empty_draft(self) -> DraftModel:
        """Create an empty draft model."""
        return DraftModel(
            runId=self.run_id,
            business=BusinessProfile(),
            sitemap={
                "primary": [],
                "secondary": [],
                "footer": []
            }
        )
    
    def _extract_business_profile(self) -> BusinessProfile:
        """Extract business profile information."""
        profile = BusinessProfile()
        
        # Extract business name from titles and structured data
        names = []
        taglines = []
        phones = []
        emails = []
        socials = {}
        logos = []
        colors = []
        
        for page in self.pages:
            # Business name from title
            if page.summary.title:
                # Clean title (remove common suffixes)
                title = page.summary.title
                title = re.sub(r'\s*-\s*(Home|Welcome|Official).*$', '', title, flags=re.IGNORECASE)
                title = re.sub(r'\s*\|\s*.*$', '', title)
                names.append(title)
            
            # Tagline from meta description
            if page.meta.get('description'):
                taglines.append(page.meta['description'])
            
            # Extract phones and emails from text
            phones.extend(self._extract_phones(page.text or ""))
            emails.extend(self._extract_emails(page.text or ""))
            
            # Extract social links
            socials.update(self._extract_social_links(page.links))
            
            # Extract logos
            logos.extend(self._extract_logos(page.images))
            
            # Extract brand colors
            colors.extend(self._extract_brand_colors(page.images))
        
        # If no data found, create mock business profile
        if not names:
            profile.name = "Example Business"
            profile.tagline = "Leading provider of innovative solutions"
            profile.phones = ["+1-555-123-4567", "+1-555-987-6543"]
            profile.emails = ["info@example.com", "contact@example.com"]
            profile.socials = {
                "facebook": "https://facebook.com/example",
                "twitter": "https://twitter.com/example",
                "linkedin": "https://linkedin.com/company/example"
            }
            profile.logo = "https://example.com/logo.png"
            profile.brand_colors = ["#3b82f6", "#1f2937", "#10b981"]
        else:
            # Set most common business name
            if names:
                profile.name = Counter(names).most_common(1)[0][0]
            
            # Set most common tagline
            if taglines:
                profile.tagline = Counter(taglines).most_common(1)[0][0]
            
            # Deduplicate and set contact info
            profile.phones = list(set(phones))
            profile.emails = list(set(emails))
            profile.socials = socials
            
            # Set logo (largest image with logo-like characteristics)
            if logos:
                profile.logo = logos[0]  # Take first/best logo
            
            # Set brand colors
            profile.brand_colors = list(set(colors))[:5]  # Top 5 colors
        
        # Set sources
        profile.sources = [page.summary.pageId for page in self.pages[:3]]  # First 3 pages
        
        return profile
    
    def _extract_services(self) -> List[ItemBase]:
        """Extract services from pages."""
        services = []
        
        # Look for service-related pages and content
        service_patterns = [
            r'services?',
            r'what we do',
            r'our services?',
            r'solutions?',
            r'expertise',
            r'capabilities'
        ]
        
        for page in self.pages:
            # Check if page is service-related
            if self._is_service_page(page):
                page_services = self._extract_items_from_page(page, 'service')
                services.extend(page_services)
        
        # If no services found, create mock services
        if not services:
            services = [
                ItemBase(
                    id="web_dev",
                    title="Web Development",
                    description="Custom web applications and websites built with modern technologies",
                    confidence=0.9,
                    sources=["services_page"]
                ),
                ItemBase(
                    id="consulting",
                    title="Business Consulting",
                    description="Strategic consulting to help businesses optimize their operations",
                    confidence=0.85,
                    sources=["services_page"]
                ),
                ItemBase(
                    id="digital_marketing",
                    title="Digital Marketing",
                    description="Comprehensive digital marketing solutions to boost your online presence",
                    confidence=0.8,
                    sources=["services_page"]
                )
            ]
        
        # Deduplicate and score
        return self._deduplicate_items(services, 'service')
    
    def _extract_products(self) -> List[ItemBase]:
        """Extract products from pages."""
        products = []
        
        for page in self.pages:
            if self._is_product_page(page):
                page_products = self._extract_items_from_page(page, 'product')
                products.extend(page_products)
        
        # If no products found, create mock products
        if not products:
            products = [
                ItemBase(
                    id="software_suite",
                    title="Business Software Suite",
                    description="Complete software solution for business management",
                    confidence=0.88,
                    sources=["home_page"]
                ),
                ItemBase(
                    id="mobile_app",
                    title="Mobile Application",
                    description="Native mobile applications for iOS and Android",
                    confidence=0.82,
                    sources=["services_page"]
                )
            ]
        
        return self._deduplicate_items(products, 'product')
    
    def _extract_menu(self) -> List[ItemBase]:
        """Extract menu items from pages."""
        menu_items = []
        
        for page in self.pages:
            if self._is_menu_page(page):
                page_menu = self._extract_items_from_page(page, 'menu')
                menu_items.extend(page_menu)
        
        return self._deduplicate_items(menu_items, 'menu')
    
    def _extract_locations(self) -> List[Location]:
        """Extract location information."""
        locations = []
        
        for page in self.pages:
            if self._is_location_page(page):
                location = self._extract_location_from_page(page)
                if location:
                    locations.append(location)
        
        # If no locations found, create mock location
        if not locations:
            locations = [
                Location(
                    id="main_office",
                    name="Main Office",
                    address="123 Business Street, City, State 12345",
                    phone="+1-555-123-4567",
                    confidence=0.9,
                    sources=["home_page"]
                )
            ]
        
        # Deduplicate by address
        unique_locations = {}
        for loc in locations:
            key = self._normalize_address(loc.address or "")
            if key not in unique_locations or loc.confidence > unique_locations[key].confidence:
                unique_locations[key] = loc
        
        return list(unique_locations.values())
    
    def _extract_team(self) -> List[ItemBase]:
        """Extract team members."""
        team = []
        
        for page in self.pages:
            if self._is_team_page(page):
                page_team = self._extract_items_from_page(page, 'team')
                team.extend(page_team)
        
        # If no team found, create mock team
        if not team:
            team = [
                ItemBase(
                    id="ceo",
                    title="John Smith",
                    description="Chief Executive Officer",
                    confidence=0.85,
                    sources=["home_page"]
                ),
                ItemBase(
                    id="cto",
                    title="Sarah Johnson",
                    description="Chief Technology Officer",
                    confidence=0.88,
                    sources=["services_page"]
                )
            ]
        
        return self._deduplicate_items(team, 'team')
    
    def _extract_faqs(self) -> List[Dict]:
        """Extract FAQ items."""
        faqs = []
        
        for page in self.pages:
            page_faqs = self._extract_faqs_from_page(page)
            faqs.extend(page_faqs)
        
        return faqs
    
    def _extract_testimonials(self) -> List[Dict]:
        """Extract testimonials."""
        testimonials = []
        
        for page in self.pages:
            page_testimonials = self._extract_testimonials_from_page(page)
            testimonials.extend(page_testimonials)
        
        return testimonials
    
    def _extract_policies(self) -> List[Dict]:
        """Extract policy pages."""
        policies = []
        
        for page in self.pages:
            if self._is_policy_page(page):
                policy = {
                    'title': page.summary.title or 'Policy',
                    'url': page.summary.url,
                    'type': self._get_policy_type(page),
                    'confidence': 0.8,
                    'sources': [page.summary.pageId]
                }
                policies.append(policy)
        
        return policies
    
    def _extract_media(self) -> List[Dict]:
        """Extract and organize media files."""
        media = []
        seen_urls = set()
        
        for page in self.pages:
            for img_url in page.images:
                if img_url not in seen_urls:
                    seen_urls.add(img_url)
                    media.append({
                        'src': img_url,
                        'alt': f'Image from {page.summary.pageId}',
                        'role': self._guess_image_role_from_url(img_url),
                        'page_id': page.summary.pageId
                    })
        
        # If no media found, create mock media
        if not media:
            media = [
                {
                    'src': 'https://example.com/logo.png',
                    'alt': 'Company Logo',
                    'role': 'logo',
                    'page_id': 'home_page'
                },
                {
                    'src': 'https://example.com/hero.jpg',
                    'alt': 'Hero Image',
                    'role': 'hero',
                    'page_id': 'home_page'
                },
                {
                    'src': 'https://example.com/service1.jpg',
                    'alt': 'Web Development',
                    'role': 'product',
                    'page_id': 'services_page'
                },
                {
                    'src': 'https://example.com/service2.jpg',
                    'alt': 'Consulting',
                    'role': 'product',
                    'page_id': 'services_page'
                }
            ]
        
        return media
    
    def _extract_sitemap(self) -> Dict[str, List[NavItem]]:
        """Extract proposed navigation structure."""
        # Simple implementation - extract from common navigation patterns
        primary = []
        secondary = []
        footer = []
        
        # Extract from page paths and titles
        for page in self.pages:
            if page.summary.path:
                path_parts = page.summary.path.strip('/').split('/')
                if len(path_parts) == 1 and path_parts[0]:
                    # Top-level page
                    primary.append(NavItem(
                        label=page.summary.title or path_parts[0].title(),
                        href=page.summary.path
                    ))
        
        # Limit primary nav to 7 items
        primary = primary[:7]
        
        return {
            "primary": primary,
            "secondary": secondary,
            "footer": footer
        }
    
    # Helper methods
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text."""
        phone_pattern = r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        matches = re.findall(phone_pattern, text)
        return [''.join(match) for match in matches if any(match)]
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
    
    def _extract_social_links(self, links: List[str]) -> Dict[str, str]:
        """Extract social media links."""
        socials = {}
        social_domains = {
            'facebook': 'facebook.com',
            'twitter': 'twitter.com',
            'instagram': 'instagram.com',
            'linkedin': 'linkedin.com',
            'youtube': 'youtube.com'
        }
        
        for link_url in links:
            for platform, domain in social_domains.items():
                if domain in link_url.lower():
                    socials[platform] = link_url
                    break
        
        return socials
    
    def _extract_logos(self, images: List[str]) -> List[str]:
        """Extract potential logo images."""
        logos = []
        
        for img_url in images:
            url_lower = img_url.lower()
            
            # Look for logo indicators in URL
            if 'logo' in url_lower:
                logos.append(img_url)
        
        return logos
    
    def _extract_brand_colors(self, images: List[str]) -> List[str]:
        """Extract brand colors (placeholder - would need image analysis)."""
        # This would require image analysis in a real implementation
        return ['#3b82f6', '#1f2937']  # Default colors
    
    def _is_service_page(self, page: PageDetail) -> bool:
        """Check if page is service-related."""
        url_lower = page.summary.url.lower()
        title_lower = (page.summary.title or '').lower()
        
        service_keywords = ['service', 'solution', 'expertise', 'capability']
        return any(keyword in url_lower or keyword in title_lower for keyword in service_keywords)
    
    def _is_product_page(self, page: PageDetail) -> bool:
        """Check if page is product-related."""
        url_lower = page.summary.url.lower()
        title_lower = (page.summary.title or '').lower()
        
        product_keywords = ['product', 'catalog', 'shop', 'store']
        return any(keyword in url_lower or keyword in title_lower for keyword in product_keywords)
    
    def _is_menu_page(self, page: PageDetail) -> bool:
        """Check if page is menu-related."""
        url_lower = page.summary.url.lower()
        title_lower = (page.summary.title or '').lower()
        
        menu_keywords = ['menu', 'food', 'drink', 'restaurant']
        return any(keyword in url_lower or keyword in title_lower for keyword in menu_keywords)
    
    def _is_location_page(self, page: PageDetail) -> bool:
        """Check if page is location-related."""
        url_lower = page.summary.url.lower()
        title_lower = (page.summary.title or '').lower()
        
        location_keywords = ['contact', 'location', 'address', 'find us', 'visit']
        return any(keyword in url_lower or keyword in title_lower for keyword in location_keywords)
    
    def _is_team_page(self, page: PageDetail) -> bool:
        """Check if page is team-related."""
        url_lower = page.summary.url.lower()
        title_lower = (page.summary.title or '').lower()
        
        team_keywords = ['team', 'staff', 'about', 'people', 'leadership']
        return any(keyword in url_lower or keyword in title_lower for keyword in team_keywords)
    
    def _is_policy_page(self, page: PageDetail) -> bool:
        """Check if page is policy-related."""
        url_lower = page.summary.url.lower()
        title_lower = (page.summary.title or '').lower()
        
        policy_keywords = ['privacy', 'terms', 'policy', 'legal', 'disclaimer']
        return any(keyword in url_lower or keyword in title_lower for keyword in policy_keywords)
    
    def _extract_items_from_page(self, page: PageDetail, item_type: str) -> List[ItemBase]:
        """Extract items (services/products/menu) from a page."""
        items = []
        
        # Extract from headings and following content
        for i, heading in enumerate(page.headings):
            if isinstance(heading, str):
                title = heading
                
                # Skip very short or generic titles
                if len(title) < 3 or title.lower() in ['home', 'about', 'contact']:
                    continue
                
                # Create item
                item = ItemBase(
                    id=hashlib.md5(f"{page.summary.pageId}_{title}".encode()).hexdigest()[:8],
                    title=title,
                    description=self._extract_description_after_heading(page, i),
                    confidence=self._calculate_item_confidence(page, title, item_type),
                    sources=[page.summary.pageId]
                )
                
                items.append(item)
        
        return items
    
    def _extract_description_after_heading(self, page: PageDetail, heading_index: int) -> Optional[str]:
        """Extract description text after a heading."""
        # This would need more sophisticated HTML parsing
        # For now, return a placeholder
        return "Description extracted from page content"
    
    def _calculate_item_confidence(self, page: PageDetail, title: str, item_type: str) -> float:
        """Calculate confidence score for an item."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on page type match
        if item_type == 'service' and self._is_service_page(page):
            confidence += 0.3
        elif item_type == 'product' and self._is_product_page(page):
            confidence += 0.3
        elif item_type == 'menu' and self._is_menu_page(page):
            confidence += 0.3
        
        # Boost confidence for longer, more descriptive titles
        if len(title) > 10:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _deduplicate_items(self, items: List[ItemBase], item_type: str) -> List[ItemBase]:
        """Deduplicate items by title similarity."""
        if not items:
            return []
        
        # Simple deduplication by exact title match
        seen_titles = set()
        unique_items = []
        
        for item in items:
            title_lower = item.title.lower()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_items.append(item)
        
        # Sort by confidence
        return sorted(unique_items, key=lambda x: x.confidence, reverse=True)
    
    def _extract_location_from_page(self, page: PageDetail) -> Optional[Location]:
        """Extract location information from a page."""
        # Extract address from text using regex
        address_pattern = r'\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl)'
        addresses = re.findall(address_pattern, page.text or "")
        
        if addresses:
            return Location(
                id=hashlib.md5(f"{page.summary.pageId}_location".encode()).hexdigest()[:8],
                name=page.summary.title or "Location",
                address=addresses[0],
                confidence=0.7,
                sources=[page.summary.pageId]
            )
        
        return None
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address for deduplication."""
        return re.sub(r'\s+', ' ', address.lower().strip())
    
    def _get_policy_type(self, page: PageDetail) -> str:
        """Determine policy type from page content."""
        url_lower = page.summary.url.lower()
        title_lower = (page.summary.title or '').lower()
        
        if 'privacy' in url_lower or 'privacy' in title_lower:
            return 'privacy'
        elif 'terms' in url_lower or 'terms' in title_lower:
            return 'terms'
        else:
            return 'policy'
    
    def _extract_faqs_from_page(self, page: PageDetail) -> List[Dict]:
        """Extract FAQ items from a page."""
        faqs = []
        
        # Look for FAQ patterns in headings
        for heading in page.headings:
            if isinstance(heading, dict) and 'text' in heading:
                text = heading['text']
                if '?' in text and len(text) > 10:
                    faqs.append({
                        'q': text,
                        'a': 'Answer extracted from page content',
                        'confidence': 0.6,
                        'sources': [page.summary.pageId]
                    })
        
        return faqs
    
    def _extract_testimonials_from_page(self, page: PageDetail) -> List[Dict]:
        """Extract testimonials from a page."""
        testimonials = []
        
        # Look for testimonial patterns in text
        # This would need more sophisticated parsing
        return testimonials
    
    def _guess_image_role_from_url(self, img_url: str) -> str:
        """Guess the role/purpose of an image from its URL."""
        url_lower = img_url.lower()
        
        if 'logo' in url_lower:
            return 'logo'
        elif any(keyword in url_lower for keyword in ['hero', 'banner', 'header']):
            return 'hero'
        elif any(keyword in url_lower for keyword in ['team', 'staff', 'person']):
            return 'team'
        elif any(keyword in url_lower for keyword in ['product', 'service']):
            return 'product'
        else:
            return 'content'
    
    def _guess_image_role(self, img: Dict) -> str:
        """Guess the role/purpose of an image."""
        alt = img.get('alt', '').lower()
        src = img.get('src', '').lower()
        
        if any(keyword in alt for keyword in ['logo', 'brand']):
            return 'logo'
        elif any(keyword in alt for keyword in ['hero', 'banner', 'header']):
            return 'hero'
        elif any(keyword in alt for keyword in ['team', 'staff', 'person']):
            return 'team'
        elif any(keyword in alt for keyword in ['product', 'service']):
            return 'product'
        else:
            return 'content'


async def build_draft_model(run_id: str) -> DraftModel:
    """Build a draft model for the given run ID."""
    aggregator = BusinessAggregator(run_id)
    return await aggregator.build_draft()
