"""
Enhanced content extraction for files, words, and links.
Provides structured data for confirmation UI.
"""
import re
import hashlib
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Tuple
import requests
import time


def extract_structured_content(soup: BeautifulSoup, url: str, base_url: str) -> Dict[str, Any]:
    """
    Extract structured content with media, files, words, and links.
    Returns data in the format expected by confirmation UI.
    """
    return {
        "url": url,
        "path": urlparse(url).path or "/",
        "status": 200,  # Will be updated by caller
        "title": _extract_title(soup, url),
        "description": _extract_description(soup),
        "canonical": _extract_canonical(soup, url),
        "media": _extract_media(soup, base_url),
        "files": _extract_files(soup, base_url),
        "words": _extract_words(soup),
        "links": _extract_links_structured(soup, base_url),
        "extractedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


def _extract_title(soup: BeautifulSoup, url: str = None) -> Optional[str]:
    """Extract title using heuristics: og:title → <title> → first h1."""
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
    
    return None


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


def _extract_description(soup: BeautifulSoup) -> Optional[str]:
    """Extract description using heuristics: meta description → og:description → first paragraph."""
    # Try meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        return meta_desc['content'].strip()
    
    # Try Open Graph description
    og_desc = soup.find('meta', property='og:description')
    if og_desc and og_desc.get('content'):
        return og_desc['content'].strip()
    
    # Try first body paragraph as fallback
    body = soup.find('body')
    if body:
        first_p = body.find('p')
        if first_p and first_p.get_text():
            text = first_p.get_text().strip()
            if len(text) > 20:  # Only use if substantial
                return text[:200] + "..." if len(text) > 200 else text
    
    return None


def _extract_canonical(soup: BeautifulSoup, url: str) -> str:
    """Extract canonical URL."""
    canonical = soup.find('link', rel='canonical')
    if canonical and canonical.get('href'):
        return urljoin(url, canonical['href'])
    return url


def _extract_media(soup: BeautifulSoup, base_url: str) -> Dict[str, List[Dict[str, Any]]]:
    """Extract images, videos, and GIFs with metadata."""
    media = {
        "images": [],
        "videos": [],
        "gifs": []
    }
    
    # Track seen URLs to avoid duplicates
    seen_urls = set()
    
    # Extract images
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src')
        if not src:
            continue
        
        src = urljoin(base_url, src)
        
        # Skip duplicates
        if src in seen_urls:
            continue
        seen_urls.add(src)
        
        alt = img.get('alt', '')
        width = _parse_dimension(img.get('width'))
        height = _parse_dimension(img.get('height'))
        
        # Try to get dimensions from srcset if not available
        if not width or not height:
            srcset_dims = _parse_srcset_dimensions(img.get('srcset', ''))
            if srcset_dims:
                width, height = srcset_dims
        
        # Check if it's a GIF
        if src.lower().endswith('.gif'):
            media["gifs"].append({"url": src})
        else:
            media["images"].append({
                "url": src,
                "alt": alt,
                "width": width,
                "height": height
            })
    
    # Extract videos
    seen_video_urls = set()
    for video in soup.find_all(['video', 'iframe']):
        src = None
        video_type = None
        
        if video.name == 'video':
            src = video.get('src')
            if not src:
                source = video.find('source')
                if source:
                    src = source.get('src')
            video_type = 'mp4'
        elif video.name == 'iframe':
            src = video.get('src')
            video_type = 'embed'
        
        if src:
            src = urljoin(base_url, src)
            
            # Skip duplicate videos
            if src in seen_video_urls:
                continue
            seen_video_urls.add(src)
            
            media["videos"].append({
                "url": src,
                "type": video_type
            })
    
    return media


def _extract_files(soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
    """Extract downloadable files (PDF, DOC, CSV, etc.)."""
    files = []
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not href:
            continue
        
        href = urljoin(base_url, href)
        
        # Check if it's a downloadable file
        file_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.txt', '.zip', '.rar']
        if any(href.lower().endswith(ext) for ext in file_extensions):
            file_type = href.split('.')[-1].lower()
            label = link.get_text().strip() or f"Download {file_type.upper()}"
            
            files.append({
                "url": href,
                "type": file_type,
                "label": label,
                "bytes": None  # Could be fetched with HEAD request
            })
    
    return files


def _extract_words(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract headings and paragraphs with word count."""
    words_data = {
        "headings": [],
        "paragraphs": [],
        "wordCount": 0
    }
    
    # Extract headings
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = heading.get_text().strip()
        if text:
            words_data["headings"].append({
                "tag": heading.name,
                "text": text
            })
    
    # Extract paragraphs
    all_text = ""
    for p in soup.find_all('p'):
        text = p.get_text().strip()
        if text and len(text) > 20:  # Only substantial paragraphs
            words_data["paragraphs"].append(text)
            all_text += text + " "
    
    # Count words
    words_data["wordCount"] = len(all_text.split()) if all_text else 0
    
    return words_data


def _extract_links_structured(soup: BeautifulSoup, base_url: str) -> Dict[str, List[Dict[str, Any]]]:
    """Extract links classified as internal, external, or broken."""
    links = {
        "internal": [],
        "external": [],
        "broken": []
    }
    
    base_hostname = urlparse(base_url).hostname
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not href or href.startswith('#'):
            continue
        
        href = urljoin(base_url, href)
        label = link.get_text().strip()
        
        link_data = {
            "label": label,
            "href": href
        }
        
        # Classify as internal or external
        link_hostname = urlparse(href).hostname
        if link_hostname == base_hostname:
            links["internal"].append(link_data)
        else:
            links["external"].append(link_data)
    
    return links


def _parse_dimension(value: Any) -> Optional[int]:
    """Parse dimension value to integer."""
    if not value:
        return None
    
    try:
        # Remove non-numeric characters except decimal point
        cleaned = re.sub(r'[^\d.]', '', str(value))
        return int(float(cleaned)) if cleaned else None
    except (ValueError, TypeError):
        return None


def _parse_srcset_dimensions(srcset: str) -> Optional[Tuple[int, int]]:
    """Parse dimensions from srcset attribute."""
    if not srcset:
        return None
    
    # Look for the largest image in srcset
    largest_width = 0
    largest_url = None
    
    for entry in srcset.split(','):
        entry = entry.strip()
        if ' ' in entry:
            url, descriptor = entry.rsplit(' ', 1)
            if descriptor.endswith('w'):
                try:
                    width = int(descriptor[:-1])
                    if width > largest_width and width <= 2000:  # Cap at 2000px
                        largest_width = width
                        largest_url = url.strip()
                except ValueError:
                    continue
    
    # For now, return None as we'd need to fetch the image to get dimensions
    # In a real implementation, you might want to fetch the largest image
    return None


def check_broken_links(links: List[Dict[str, Any]], rate_limit: float = 0.1) -> List[Dict[str, Any]]:
    """
    Check for broken links with rate limiting.
    Returns list of broken links with status codes.
    """
    broken = []
    
    for link in links:
        try:
            response = requests.head(link['href'], timeout=5, allow_redirects=True)
            if response.status_code >= 400:
                broken.append({
                    "href": link['href'],
                    "status": response.status_code
                })
        except requests.RequestException:
            broken.append({
                "href": link['href'],
                "status": None
            })
        
        # Rate limiting
        time.sleep(rate_limit)
    
    return broken
