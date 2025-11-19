import re
import hashlib
import os
import json
from bs4 import BeautifulSoup
from readability import Document
import trafilatura
from backend.crawl.fetch import FetchResponse
from backend.extract.nav_footer import extract_navigation, extract_footer
from backend.extract.files_words_links import extract_structured_content
from backend.insights.page_type import infer_page_type, extract_page_features, PageFeatures

async def extract_html(resp: FetchResponse, run_id: str = None) -> dict:
    """
    Extract content from HTML response using readability and trafilatura.
    Enhanced with structured content extraction for confirmation UI.
    """
    try:
        html_content = resp.content.decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title = _extract_title(soup, resp.url)
        
        # Extract text using readability
        doc = Document(html_content)
        readable_html = doc.summary()
        readable_text = trafilatura.extract(readable_html) or ""
        
        # Extract metadata
        meta = _extract_meta(soup)
        
        # Extract links
        links = _extract_links(soup, resp.url)
        
        # Extract images
        images = _extract_images(soup, resp.url)
        
        # Extract headings
        headings = _extract_headings(soup)
        
        # Extract tables
        tables = _extract_tables(soup)
        
        # Extract structured data
        structured_data = _extract_structured_data(soup)
        
        # Count words
        word_count = len(readable_text.split()) if readable_text else 0
        
        # Generate unique pageId from URL
        page_id = hashlib.md5(resp.url.encode()).hexdigest()[:12]
        
        # Extract structured content for confirmation UI
        structured_content = extract_structured_content(soup, resp.url, resp.url)
        structured_content["status"] = resp.status
        
        # Infer page type
        # Build page data dict for feature extraction
        page_data_for_features = {
            "words": {"wordCount": word_count, "paragraphs": [], "headings": headings},
            "links": {"internal": [l for l in links if resp.url.split('/')[2] in l.get("url", "")]},
            "media": {"images": images}
        }
        # Count paragraphs from readable text
        paragraphs = [p.strip() for p in readable_text.split('\n\n') if p.strip() and len(p.strip()) > 20]
        page_data_for_features["words"]["paragraphs"] = paragraphs
        
        features = extract_page_features(page_data_for_features)
        detected_page_type = infer_page_type(resp.url, features)
        
        # Save structured content if run_id provided
        if run_id:
            _save_structured_content(run_id, page_id, structured_content)
        
        return {
            "summary": {
                "pageId": page_id,
                "url": resp.url,
                "contentType": resp.content_type,
                "title": title,
                "words": word_count,
                "images": len(images),
                "links": len(links),
                "status": resp.status,
                "status_code": resp.status,
                "path": resp.path,
                "type": "HTML",
                "load_time_ms": resp.load_time_ms,
                "content_length_bytes": resp.content_length_bytes,
                "page_type": detected_page_type
            },
            "meta": meta,
            "text": readable_text,
            "htmlExcerpt": readable_html[:1000] if readable_html else None,
            "headings": headings,
            "images": images,
            "links": links,
            "tables": tables,
            "structuredData": structured_data,
            "stats": {
                "word_count": word_count,
                "image_count": len(images),
                "link_count": len(links),
                "heading_count": len(headings),
                "table_count": len(tables),
                "page_type": detected_page_type
            },
            "structuredContent": structured_content
        }
    except Exception as e:
        print(f"HTML extraction error: {e}")
        return _create_error_response(resp, "HTML")

def _extract_title(soup: BeautifulSoup, url: str = None) -> str:
    """Extract page title using improved heuristics."""
    import re
    from urllib.parse import urlparse
    
    # Check if this is the homepage
    is_homepage = False
    if url:
        parsed_url = urlparse(url)
        path = parsed_url.path.strip('/')
        is_homepage = not path or path in ['', 'index', 'index.html', 'home']
    
    # Try Open Graph title first
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        title = og_title['content'].strip()
        if _is_good_title(title):
            return title
    
    # Try regular title tag
    title_tag = soup.find('title')
    if title_tag and title_tag.get_text():
        title = title_tag.get_text().strip()
        if _is_good_title(title):
            return title
    
    # Try first h1 as fallback
    h1 = soup.find('h1')
    if h1 and h1.get_text():
        title = h1.get_text().strip()
        if _is_good_title(title):
            # If this is the homepage and the title looks like a company name, use "Home"
            if is_homepage and _looks_like_company_name(title):
                return "Home"
            return title
    
    # Try h2 tags if h1 is not good
    for h2 in soup.find_all('h2'):
        title = h2.get_text().strip()
        if _is_good_title(title):
            # If this is the homepage and the title looks like a company name, use "Home"
            if is_homepage and _looks_like_company_name(title):
                return "Home"
            return title
    
    # Try h3 tags as last resort
    for h3 in soup.find_all('h3'):
        title = h3.get_text().strip()
        if _is_good_title(title):
            # If this is the homepage and the title looks like a company name, use "Home"
            if is_homepage and _looks_like_company_name(title):
                return "Home"
            return title
    
    # If this is the homepage and we couldn't find a good title, default to "Home"
    if is_homepage:
        return "Home"
    
    return ""


def _looks_like_company_name(title: str) -> bool:
    """Check if a title looks like a company name rather than a page title."""
    if not title:
        return False
    
    # Company name patterns
    company_patterns = [
        r'\b(inc|llc|ltd|corp|corporation|company|co\.|group|solutions|services|systems|technologies|tech)\b',
        r'\b(exterior|interior|construction|building|roofing|siding|landscaping|maintenance|upkeep)\b',
        r'\b(northshore|north shore|southshore|south shore|eastside|westside)\b'
    ]
    
    title_lower = title.lower()
    for pattern in company_patterns:
        if re.search(pattern, title_lower):
            return True
    
    # Check if it's very long (company names tend to be longer)
    if len(title) > 30:
        return True
    
    # Check if it contains multiple words that could be a company name
    words = title.split()
    if len(words) >= 3:
        return True
    
    return False


def _is_good_title(title: str) -> bool:
    """Check if a title is good (not phone numbers, CTAs, etc.)."""
    if not title or len(title.strip()) < 3:
        return False
    
    # Filter out phone numbers
    phone_pattern = r'\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4}|\d{3}\.\d{3}\.\d{4}'
    if re.search(phone_pattern, title):
        return False
    
    # Filter out common CTAs
    cta_patterns = [
        r'call us at',
        r'contact us',
        r'get a quote',
        r'free estimate',
        r'click here',
        r'learn more',
        r'read more',
        r'view more',
        r'shop now',
        r'buy now',
        r'sign up',
        r'subscribe',
        r'follow us',
        r'like us',
        r'share',
        r'download',
        r'free',
        r'sale',
        r'special offer'
    ]
    
    title_lower = title.lower()
    for pattern in cta_patterns:
        if re.search(pattern, title_lower):
            return False
    
    # Filter out very short titles
    if len(title) < 5:
        return False
    
    # Filter out titles that are mostly numbers or symbols
    if len(re.sub(r'[^a-zA-Z]', '', title)) < 3:
        return False
    
    return True

def _extract_meta(soup: BeautifulSoup) -> dict:
    """Extract meta information."""
    meta = {}
    
    # Meta tags
    for tag in soup.find_all('meta'):
        name = tag.get('name') or tag.get('property')
        content = tag.get('content')
        if name and content:
            meta[name] = content
    
    # Open Graph
    og_tags = soup.find_all('meta', property=re.compile(r'^og:'))
    for tag in og_tags:
        prop = tag.get('property')
        content = tag.get('content')
        if prop and content:
            meta[prop] = content
    
    return meta

def _extract_links(soup: BeautifulSoup, base_url: str) -> list:
    """Extract all links."""
    from urllib.parse import urljoin
    links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        text = link.get_text().strip()
        if href and text:
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            links.append({
                "url": absolute_url,
                "text": text
            })
    return links

def _extract_images(soup: BeautifulSoup, base_url: str) -> list:
    """Extract all images."""
    images = []
    for img in soup.find_all('img', src=True):
        src = img['src']
        alt = img.get('alt', '')
        title = img.get('title', '')
        images.append({
            "src": src,
            "alt": alt,
            "title": title
        })
    return images

def _extract_headings(soup: BeautifulSoup) -> list:
    """Extract all headings."""
    headings = []
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = tag.get_text().strip()
        if text:
            headings.append({
                "level": int(tag.name[1]),
                "text": text
            })
    return headings

def _extract_tables(soup: BeautifulSoup) -> list:
    """Extract table data."""
    tables = []
    for table in soup.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            cells = []
            for td in tr.find_all(['td', 'th']):
                cells.append(td.get_text().strip())
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables

def _extract_structured_data(soup: BeautifulSoup) -> list:
    """Extract structured data (JSON-LD, microdata)."""
    structured = []
    
    # JSON-LD
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            import json
            data = json.loads(script.string)
            structured.append({
                "type": "json-ld",
                "data": data
            })
        except:
            pass
    
    return structured

def _save_structured_content(run_id: str, page_id: str, content: dict):
    """Save structured content to run directory."""
    try:
        run_dir = os.path.join("runs", run_id)
        pages_dir = os.path.join(run_dir, "pages")
        
        # Ensure directories exist
        os.makedirs(pages_dir, exist_ok=True)
        
        # Save page content
        page_file = os.path.join(pages_dir, f"{page_id}.json")
        with open(page_file, 'w') as f:
            json.dump(content, f, indent=2)
            
    except Exception as e:
        print(f"Error saving structured content: {e}")


def _create_error_response(resp: FetchResponse, content_type: str) -> dict:
    """Create error response."""
    page_id = hashlib.md5(resp.url.encode()).hexdigest()[:12]
    return {
        "summary": {
            "pageId": page_id,
            "url": resp.url,
            "contentType": resp.content_type,
            "title": None,
            "words": 0,
            "images": 0,
            "links": 0,
            "status": resp.status,
            "status_code": resp.status,
            "path": resp.path,
            "type": content_type,
            "load_time_ms": resp.load_time_ms,
            "content_length_bytes": resp.content_length_bytes,
            "page_type": "generic"  # Default for error pages
        },
        "meta": {},
        "text": None,
        "htmlExcerpt": None,
        "headings": [],
        "images": [],
        "links": [],
        "tables": [],
        "structuredData": [],
        "stats": {}
    }