"""
Utility functions for SiteInsite
"""
import hashlib
import re
import mimetypes
import magic
from urllib.parse import urljoin, urlparse, parse_qs, urlunparse
from typing import Optional, Tuple, Dict, Any
import tiktoken


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """
    Normalize a URL by removing fragments, sorting query parameters,
    and resolving relative paths.
    """
    if base_url:
        url = urljoin(base_url, url)
    
    parsed = urlparse(url)
    
    # Remove fragment
    parsed = parsed._replace(fragment='')
    
    # Sort query parameters
    if parsed.query:
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        sorted_params = []
        for key in sorted(query_params.keys()):
            for value in sorted(query_params[key]):
                sorted_params.append(f"{key}={value}")
        parsed = parsed._replace(query='&'.join(sorted_params))
    
    # Normalize path
    path = parsed.path
    if not path:
        path = '/'
    elif not path.endswith('/') and '.' not in path.split('/')[-1]:
        path += '/'
    
    parsed = parsed._replace(path=path)
    
    return urlunparse(parsed)


def get_canonical_url(url: str, canonical_href: Optional[str] = None) -> str:
    """
    Get the canonical URL, preferring the canonical href if provided.
    """
    if canonical_href:
        return normalize_url(canonical_href)
    return normalize_url(url)


def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs are from the same domain"""
    try:
        domain1 = urlparse(url1).netloc.lower()
        domain2 = urlparse(url2).netloc.lower()
        return domain1 == domain2
    except:
        return False


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        return urlparse(url).netloc.lower()
    except:
        return ""


def is_internal_link(url: str, base_domain: str) -> bool:
    """Check if a URL is internal to the base domain"""
    try:
        url_domain = urlparse(url).netloc.lower()
        return url_domain == base_domain or url_domain.endswith(f".{base_domain}")
    except:
        return False


def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()


def extract_emails(text: str) -> list[str]:
    """Extract email addresses from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return list(set(emails))


def extract_phones(text: str) -> list[str]:
    """Extract phone numbers from text"""
    # Common phone number patterns
    phone_patterns = [
        r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',  # US format
        r'\+?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}',  # International
        r'\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # Simple US
    ]
    
    phones = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                phone = ''.join(match)
            else:
                phone = match
            # Clean up the phone number
            phone = re.sub(r'[^\d+]', '', phone)
            if len(phone) >= 10:  # Minimum phone length
                phones.append(phone)
    
    return list(set(phones))


def detect_content_type(content: bytes, url: str, content_type_header: Optional[str] = None) -> str:
    """
    Detect content type using multiple methods:
    1. Content-Type header
    2. File extension
    3. Magic bytes
    """
    # Try Content-Type header first
    if content_type_header:
        mime_type = content_type_header.split(';')[0].strip().lower()
        if mime_type in ['text/html', 'application/xhtml+xml']:
            return 'html'
        elif mime_type == 'application/pdf':
            return 'pdf'
        elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            return 'docx'
        elif mime_type in ['application/json', 'text/json']:
            return 'json'
        elif mime_type in ['text/csv', 'application/csv']:
            return 'csv'
        elif mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('text/'):
            return 'text'
    
    # Try file extension
    mime_type, _ = mimetypes.guess_type(url)
    if mime_type:
        if mime_type in ['text/html', 'application/xhtml+xml']:
            return 'html'
        elif mime_type == 'application/pdf':
            return 'pdf'
        elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            return 'docx'
        elif mime_type in ['application/json', 'text/json']:
            return 'json'
        elif mime_type in ['text/csv', 'application/csv']:
            return 'csv'
        elif mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('text/'):
            return 'text'
    
    # Try magic bytes
    try:
        mime_type = magic.from_buffer(content, mime=True)
        if mime_type in ['text/html', 'application/xhtml+xml']:
            return 'html'
        elif mime_type == 'application/pdf':
            return 'pdf'
        elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            return 'docx'
        elif mime_type in ['application/json', 'text/json']:
            return 'json'
        elif mime_type in ['text/csv', 'application/csv']:
            return 'csv'
        elif mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('text/'):
            return 'text'
    except:
        pass
    
    # Default to html for web content
    return 'html'


def calculate_text_hash(text: str, title: str = "") -> str:
    """
    Calculate a hash for text content to detect near-duplicates.
    Uses title + first 2000 chars of text.
    """
    content = f"{title}\n{text[:2000]}"
    return hashlib.sha1(content.encode('utf-8')).hexdigest()


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens in text using tiktoken"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except:
        # Fallback to word count estimation
        return len(text.split())


def get_word_count_bucket(word_count: int) -> str:
    """Get word count bucket for UI grouping"""
    if word_count < 100:
        return "0-99"
    elif word_count < 500:
        return "100-499"
    elif word_count < 1000:
        return "500-999"
    elif word_count < 2000:
        return "1000-1999"
    elif word_count < 5000:
        return "2000-4999"
    else:
        return "5000+"


def extract_path_segments(url: str) -> list[str]:
    """Extract path segments from URL"""
    try:
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if not path:
            return ['/']
        return ['/'] + path.split('/')
    except:
        return ['/']


def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except:
        return False


def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to max_length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


