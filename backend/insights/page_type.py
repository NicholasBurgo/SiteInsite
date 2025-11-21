"""
Page type detection heuristics.
Infers page_type from URL patterns and content features.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PageFeatures:
    """Content features used for page type inference."""
    word_count: int = 0
    paragraph_count: int = 0
    heading_count: int = 0
    internal_link_count: int = 0
    product_card_count: int = 0  # Estimated from repeated blocks with price/button patterns


def infer_page_type(url: str, features: PageFeatures) -> str:
    """
    Infer page type from URL and content features.
    
    Supported page types:
    - "article" – blog/news/article content
    - "landing" – marketing/hero pages, few key sections
    - "catalog" – category/product listing pages
    - "product" – single product/detail page
    - "media_gallery" – image/video/gallery-style pages
    - "contact" – contact/locations pages
    - "utility" – login, account, auth, legal, etc.
    - "generic" – default fallback
    
    Args:
        url: Page URL
        features: PageFeatures object with content metrics
        
    Returns:
        page_type string
    """
    path = url.lower()
    
    # Utility / legal / auth pages
    utility_keywords = ["login", "signin", "sign-in", "account", "checkout", "privacy", "terms", 
                       "legal", "cookie", "auth", "register", "signup", "sign-up", "dashboard"]
    if any(keyword in path for keyword in utility_keywords):
        return "utility"
    
    # Contact
    contact_keywords = ["contact", "locations", "find-us", "findus", "location", "about-us", "aboutus"]
    if any(keyword in path for keyword in contact_keywords):
        return "contact"
    
    # Catalog-like (product listing pages)
    catalog_keywords = ["shop", "category", "catalog", "products", "listings", "collection", 
                       "browse", "store", "all-products"]
    if any(keyword in path for keyword in catalog_keywords):
        # Check if it looks like a catalog: many product cards, few paragraphs
        if features.product_card_count >= 8 and features.paragraph_count <= 3:
            return "catalog"
        # Also check if it has catalog-like URL structure but fewer products
        if features.product_card_count >= 4 and features.paragraph_count <= 2:
            return "catalog"
    
    # Product detail page
    product_keywords = ["/product/", "/item/", "/p/", "/products/", "/shop/"]
    if any(keyword in path for keyword in product_keywords):
        # Product pages typically have some content but not many product cards
        if features.word_count >= 50 and features.product_card_count <= 4:
            return "product"
    
    # Article / blog
    article_keywords = ["blog", "news", "article", "post", "/blog/", "/news/", "/articles/", 
                       "/posts/", "/story/", "/stories/"]
    if any(keyword in path for keyword in article_keywords):
        if features.word_count > 600 and features.paragraph_count > 5:
            return "article"
        # Also accept shorter articles if they have good structure
        if features.word_count > 300 and features.paragraph_count > 3 and features.heading_count >= 2:
            return "article"
    
    # Media gallery
    gallery_keywords = ["gallery", "gallery/", "photos", "images", "media", "portfolio", 
                       "video", "videos", "/gallery/", "/photos/"]
    if any(keyword in path for keyword in gallery_keywords):
        # Gallery pages typically have many images/media but few words
        if features.word_count < 200 and features.paragraph_count <= 2:
            return "media_gallery"
    
    # Landing page (shorter copy but important, typically homepage or marketing pages)
    # Homepage is often a landing page
    is_homepage = path.strip('/').endswith(('', 'index', 'index.html', 'home'))
    if is_homepage:
        if features.word_count < 400 and features.paragraph_count <= 6 and features.heading_count >= 2:
            return "landing"
    
    # Other landing page indicators
    if features.word_count < 250 and features.paragraph_count <= 4 and features.heading_count >= 2:
        # Could be a landing page, but check if it's not a utility page
        if not any(keyword in path for keyword in utility_keywords):
            return "landing"
    
    return "generic"


def extract_page_features(page_data: Dict[str, Any]) -> PageFeatures:
    """
    Extract PageFeatures from page data structure.
    
    Args:
        page_data: Page data dict (from pages/{page_id}.json or structured content)
        
    Returns:
        PageFeatures object
    """
    # Extract word count
    words_data = page_data.get("words", {})
    if isinstance(words_data, dict):
        word_count = words_data.get("wordCount", 0)
        paragraphs = words_data.get("paragraphs", [])
        headings = words_data.get("headings", [])
    else:
        word_count = page_data.get("word_count", 0) or page_data.get("words", 0)
        paragraphs = []
        headings = []
    
    # Count paragraphs
    if isinstance(paragraphs, list):
        paragraph_count = len(paragraphs)
    else:
        paragraph_count = 0
    
    # Count headings
    if isinstance(headings, list):
        heading_count = len(headings)
    else:
        heading_count = 0
    
    # Count internal links
    links_data = page_data.get("links", {})
    if isinstance(links_data, dict):
        internal_links = links_data.get("internal", [])
        internal_link_count = len(internal_links) if isinstance(internal_links, list) else 0
    else:
        internal_link_count = 0
    
    # Estimate product card count
    # Look for patterns that suggest product cards:
    # - Multiple images with similar structure
    # - Links that might be product links
    # - Price patterns in text
    product_card_count = 0
    
    # Simple heuristic: if there are many images and internal links, might be product cards
    images_data = page_data.get("media", {})
    if isinstance(images_data, dict):
        images = images_data.get("images", [])
        image_count = len(images) if isinstance(images, list) else 0
    else:
        image_count = page_data.get("images", 0) or 0
    
    # If there are many images (8+) and many internal links, likely product cards
    if image_count >= 8 and internal_link_count >= 8:
        # Estimate: roughly one product card per 2-3 images
        product_card_count = min(image_count // 2, internal_link_count // 2)
    elif image_count >= 4 and internal_link_count >= 4:
        product_card_count = min(image_count // 3, internal_link_count // 3)
    
    return PageFeatures(
        word_count=word_count,
        paragraph_count=paragraph_count,
        heading_count=heading_count,
        internal_link_count=internal_link_count,
        product_card_count=product_card_count
    )


