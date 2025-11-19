import re
import json
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from urllib.parse import urlparse
import logging

try:
    import trafilatura
    from trafilatura.settings import use_config
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("trafilatura not available")

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ArticleExtractor:
    """Extract clean article content using trafilatura and custom parsing"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.clean_content = config.get('clean_content', True)

        # Configure trafilatura
        if TRAFILATURA_AVAILABLE:
            self.trafilatura_config = use_config()
            self.trafilatura_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
            self.trafilatura_config.set("DEFAULT", "MIN_EXTRACTED_SIZE", "200")
            self.trafilatura_config.set("DEFAULT", "INCLUDE_COMMENTS", "False")
            self.trafilatura_config.set("DEFAULT", "INCLUDE_TABLES", "False")

    def extract_article(self, html_content: str, url: str, site_name: str = None) -> Dict[str, Any]:
        """
        Extract article data from HTML content

        Returns structured article data with metadata
        """

        try:
            # Try trafilatura first for best results
            if TRAFILATURA_AVAILABLE:
                article_data = self._extract_with_trafilatura(html_content, url)
                if article_data.get('content'):
                    return self._post_process_article(article_data, url, site_name)

            # Fallback to custom extraction
            logger.debug(f"Using custom extraction for {url}")
            article_data = self._extract_with_bs4(html_content, url, site_name)
            return self._post_process_article(article_data, url, site_name)

        except Exception as e:
            logger.error(f"Article extraction failed for {url}: {str(e)}")
            return self._create_error_article(url, str(e))

    def _extract_with_trafilatura(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract article using trafilatura"""

        try:
            # Extract main content
            extracted = trafilatura.extract(
                html_content,
                config=self.trafilatura_config,
                include_comments=False,
                include_tables=False,
                include_images=False,
                include_formatting=False,
                include_links=False,
                favor_precision=True,
                prune_xpath=None
            )

            # Extract metadata
            metadata = trafilatura.extract_metadata(html_content, url)

            article_data = {
                'title': getattr(metadata, 'title', None) or self._extract_title_fallback(html_content),
                'content': extracted,
                'author': getattr(metadata, 'author', None),
                'publish_date': getattr(metadata, 'date', None),
                'description': getattr(metadata, 'description', None),
                'url': url,
                'extraction_method': 'trafilatura'
            }

            return article_data

        except Exception as e:
            logger.debug(f"Trafilatura extraction failed: {str(e)}")
            return {}

    def _extract_with_bs4(self, html_content: str, url: str, site_name: str = None) -> Dict[str, Any]:
        """Fallback extraction using BeautifulSoup"""

        soup = BeautifulSoup(html_content, 'html.parser')

        # Get site-specific selectors
        selectors = self._get_site_selectors(site_name)

        article_data = {
            'title': None,
            'content': None,
            'author': None,
            'publish_date': None,
            'url': url,
            'extraction_method': 'bs4_fallback'
        }

        # Extract title
        article_data['title'] = self._extract_title(soup)

        # Extract content
        article_data['content'] = self._extract_content(soup, selectors.get('article_selectors', []))

        # Extract author
        article_data['author'] = self._extract_author(soup, selectors.get('author_selectors', []))

        # Extract date
        article_data['publish_date'] = self._extract_date(soup, selectors.get('date_selectors', []))

        return article_data

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""

        # Try multiple selectors
        title_selectors = [
            'h1.entry-title',
            'h1.article-title',
            'h1.post-title',
            '.article-header h1',
            '.entry-header h1',
            'h1',
            'title'
        ]

        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 10:  # Reasonable title length
                    return title

        return None

    def _extract_title_fallback(self, html_content: str) -> Optional[str]:
        """Fallback title extraction"""

        # Try title tag
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()

        return None

    def _extract_content(self, soup: BeautifulSoup, article_selectors: List[str]) -> Optional[str]:
        """Extract article content"""

        # Try site-specific selectors first
        for selector in article_selectors:
            element = soup.select_one(selector)
            if element:
                content = self._clean_content(element.get_text())
                if content and len(content) > 100:  # Reasonable content length
                    return content

        # Fallback selectors
        fallback_selectors = [
            'article .entry-content',
            '.article-content',
            '.entry-content',
            '.post-content',
            'article',
            '.content',
            '.article-body',
            '.story-body',
            'main'
        ]

        for selector in fallback_selectors:
            element = soup.select_one(selector)
            if element:
                content = self._clean_content(element.get_text())
                if content and len(content) > 100:
                    return content

        return None

    def _extract_author(self, soup: BeautifulSoup, author_selectors: List[str]) -> Optional[str]:
        """Extract article author"""

        # Try site-specific selectors
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get_text(strip=True)
                if author and len(author) > 2:
                    return author

        # Fallback selectors
        fallback_selectors = [
            '.author-name',
            '.byline a',
            '.entry-author',
            '[rel="author"]',
            '.author'
        ]

        for selector in fallback_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get_text(strip=True)
                if author and len(author) > 2:
                    return author

        return None

    def _extract_date(self, soup: BeautifulSoup, date_selectors: List[str]) -> Optional[str]:
        """Extract publication date"""

        # Try site-specific selectors
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_text = element.get_text(strip=True)
                parsed_date = self._parse_date(date_text)
                if parsed_date:
                    return parsed_date

                # Try datetime attribute
                datetime_attr = element.get('datetime') or element.get('content')
                if datetime_attr:
                    parsed_date = self._parse_date(datetime_attr)
                    if parsed_date:
                        return parsed_date

        # Fallback selectors
        fallback_selectors = [
            'time',
            '.published',
            '.entry-date',
            '.post-date',
            '.date'
        ]

        for selector in fallback_selectors:
            element = soup.select_one(selector)
            if element:
                date_text = element.get_text(strip=True)
                parsed_date = self._parse_date(date_text)
                if parsed_date:
                    return parsed_date

                datetime_attr = element.get('datetime') or element.get('content')
                if datetime_attr:
                    parsed_date = self._parse_date(datetime_attr)
                    if parsed_date:
                        return parsed_date

        return None

    def _parse_date(self, date_string: str) -> Optional[str]:
        """Parse date string into ISO format"""

        if not date_string:
            return None

        # Common date patterns
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # ISO format
            r'(\d{2}/\d{2}/\d{4})',  # MM/DD/YYYY
            r'(\d{1,2}/\d{1,2}/\d{4})',  # M/D/YYYY
            r'([A-Za-z]+ \d{1,2}, \d{4})',  # Month DD, YYYY
            r'(\d{1,2} [A-Za-z]+ \d{4})',  # DD Month YYYY
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_string)
            if match:
                try:
                    # Try to parse the date
                    parsed = self._normalize_date(match.group(1))
                    if parsed:
                        return parsed.isoformat()
                except:
                    continue

        return None

    def _normalize_date(self, date_str: str) -> Optional[datetime]:
        """Normalize date string to datetime object"""

        try:
            # Try different formats
            formats = [
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%m/%d/%y',
                '%d/%m/%Y',
                '%B %d, %Y',
                '%b %d, %Y',
                '%d %B %Y',
                '%d %b %Y'
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

        except Exception:
            pass

        return None

    def _clean_content(self, content: str) -> str:
        """Clean extracted content"""

        if not content:
            return ""

        # Remove excessive whitespace
        content = re.sub(r'\n+', '\n', content)
        content = re.sub(r' +', ' ', content)

        # Remove common ad/tracking patterns
        ad_patterns = [
            r'Advertisement',
            r'Sponsored Content',
            r'Related Articles',
            r'You might also like',
            r'Subscribe to',
            r'Follow us on',
            r'Share this article'
        ]

        for pattern in ad_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)

        # Clean up spacing
        content = content.strip()

        return content

    def _get_site_selectors(self, site_name: str = None) -> Dict[str, List[str]]:
        """Get site-specific selectors"""

        if not site_name:
            return {}

        site_config = self.config.get('targets', {}).get(site_name, {})
        return {
            'article_selectors': site_config.get('article_selectors', []),
            'author_selectors': site_config.get('author_selectors', []),
            'date_selectors': site_config.get('date_selectors', [])
        }

    def _post_process_article(self, article_data: Dict[str, Any], url: str, site_name: str = None) -> Dict[str, Any]:
        """Post-process extracted article data"""

        # Ensure required fields
        processed = {
            'title': article_data.get('title', ''),
            'url': url,
            'content': article_data.get('content', ''),
            'author': article_data.get('author'),
            'publish_date': article_data.get('publish_date'),
            'extraction_method': article_data.get('extraction_method', 'unknown'),
            'word_count': len(article_data.get('content', '').split()) if article_data.get('content') else 0,
            'site_name': site_name or urlparse(url).netloc,
            'extracted_at': datetime.now().isoformat(),
            'success': bool(article_data.get('content'))
        }

        # Clean content if requested
        if self.clean_content and processed['content']:
            processed['content'] = self._clean_content(processed['content'])

        return processed

    def _create_error_article(self, url: str, error: str) -> Dict[str, Any]:
        """Create error article when extraction fails"""

        return {
            'title': '',
            'url': url,
            'content': '',
            'author': None,
            'publish_date': None,
            'extraction_method': 'error',
            'word_count': 0,
            'site_name': urlparse(url).netloc,
            'extracted_at': datetime.now().isoformat(),
            'success': False,
            'error': error
        }
