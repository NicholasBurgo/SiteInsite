"""
URL frontier for managing crawl queue with politeness and deduplication.

Handles URL normalization, depth tracking, and domain filtering to ensure
crawls stay within configured limits and respect site boundaries.
"""
import asyncio
from urllib.parse import urljoin, urlparse
from typing import Set, List, Optional
from collections import deque


class Frontier:
    """
    URL frontier for managing crawl queue with politeness and deduplication.
    """
    
    def __init__(self, start_url: str, max_pages: int = 400, max_depth: int = 5):
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.base_domain = urlparse(start_url).netloc
        
        # URL tracking
        self._seen: Set[str] = set()
        self._queue: deque = deque()
        self._depth_map: dict = {}
        
        # Initialize with start URL
        self.enqueue(start_url, depth=0)
        
    def enqueue(self, url: str, depth: int = None) -> bool:
        """
        Add URL to frontier if not seen and within limits.
        """
        if len(self._seen) >= self.max_pages:
            return False
            
        # Normalize URL
        normalized = self._normalize_url(url)
        if not normalized or normalized in self._seen:
            return False
            
        # Check domain
        parsed = urlparse(normalized)
        if parsed.netloc != self.base_domain:
            return False
            
        # Check depth
        if depth is None:
            depth = self._depth_map.get(url, 0)
        if depth > self.max_depth:
            return False
            
        self._seen.add(normalized)
        self._queue.append(normalized)
        self._depth_map[normalized] = depth
        return True
        
    def next_batch(self, size: int) -> List[str]:
        """
        Get next batch of URLs to process.
        """
        batch = []
        for _ in range(min(size, len(self._queue))):
            if self._queue:
                batch.append(self._queue.popleft())
        return batch
        
    def done(self) -> bool:
        """
        Check if frontier is exhausted.
        """
        return len(self._queue) == 0
        
    def _normalize_url(self, url: str) -> Optional[str]:
        """
        Normalize URL for deduplication.
        """
        try:
            parsed = urlparse(url)
            # Remove fragment
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            return normalized
        except:
            return None
            
    def get_stats(self) -> dict:
        """
        Get frontier statistics.
        """
        return {
            "queued": len(self._queue),
            "visited": len(self._seen),
            "max_pages": self.max_pages,
            "max_depth": self.max_depth
        }