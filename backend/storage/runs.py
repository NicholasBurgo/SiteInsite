"""
File-based storage for audit runs.

Manages persistence of page data, metadata, and statistics using JSON files.
Supports pagination, filtering, and async I/O operations.
"""
import os
import json
import time
import statistics
from typing import List, Optional, Dict, Any
from backend.core.types import PageSummary, PageDetail, PageResult
from backend.crawl.frontier import Frontier
from backend.insights.crawl_quality import compute_crawl_quality
from backend.crawl.performance import aggregate_performance_samples, compute_performance_consistency
from backend.storage.async_io import get_async_writer


def percentile(data: List[float], p: float) -> float:
    """
    Calculate the p-th percentile of a list of numbers.
    
    Args:
        data: List of numeric values
        p: Percentile value (0-100)
    
    Returns:
        float: The p-th percentile value
    """
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100
    f = int(k)
    c = k - f
    if f + 1 < len(sorted_data):
        return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
    return sorted_data[f]


def compute_stats_from_values(values: List[float]) -> Dict[str, Any]:
    """
    Compute statistical metrics from a list of values.
    
    Args:
        values: List of numeric values
    
    Returns:
        dict: Statistics including average, median, percentiles, min, max, stdev, count
    """
    if not values:
        return {}
    
    count = len(values)
    avg = statistics.mean(values)
    median_val = statistics.median(values)
    p75_val = percentile(values, 75)
    p90_val = percentile(values, 90)
    min_val = min(values)
    max_val = max(values)
    stdev_val = statistics.stdev(values) if count > 1 else 0.0
    
    return {
        "average": round(avg, 2),
        "median": round(median_val, 2),
        "p75": round(p75_val, 2),
        "p90": round(p90_val, 2),
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "stdev": round(stdev_val, 2),
        "count": count
    }

class RunStore:
    """
    File-based storage for extraction runs.
    
    Manages JSON file storage for pages and metadata, with support for
    async I/O, pagination, filtering, and statistics computation.
    """
    
    def __init__(self, run_id: str, data_dir: str = "runs", meta_overrides: dict | None = None):
        """
        Initialize run storage.
        
        Args:
            run_id: Unique identifier for the audit run
            data_dir: Base directory for storing run data
            meta_overrides: Optional dictionary to override metadata values
        """
        self.run_id = run_id
        self.data_dir = data_dir
        self.run_dir = os.path.join(data_dir, run_id)
        self.pages_file = os.path.join(self.run_dir, "pages.json")
        self.meta_file = os.path.join(self.run_dir, "meta.json")
        
        # Ensure directory exists
        os.makedirs(self.run_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        if not os.path.exists(self.pages_file):
            with open(self.pages_file, 'w') as f:
                json.dump([], f)
        
        if not os.path.exists(self.meta_file):
            with open(self.meta_file, 'w') as f:
                json.dump({
                    "run_id": run_id,
                    "started_at": time.time(),
                    "status": "running",
                    "pages": [],
                    "errors": []
                }, f)
        
        if meta_overrides:
            try:
                with open(self.meta_file, 'r') as f:
                    meta = json.load(f)
                meta.update(meta_overrides)
                with open(self.meta_file, 'w') as f:
                    json.dump(meta, f)
            except Exception as e:
                print(f"Error updating run meta: {e}")
    
    async def save_doc(self, doc: dict):
        """Save extracted document asynchronously."""
        writer = get_async_writer()
        
        def update_pages(new_doc, existing_pages):
            """Update function to append new doc to existing pages."""
            if existing_pages is None:
                return [new_doc]
            existing_pages.append(new_doc)
            return existing_pages
        
        await writer.write_json(self.pages_file, doc, update_func=update_pages)
    
    async def log_error(self, url: str, error_type: str):
        """Log error for URL asynchronously."""
        writer = get_async_writer()
        
        error_entry = {
            "url": url,
            "error_type": error_type,
            "timestamp": time.time()
        }
        
        def update_meta(new_error, existing_meta):
            """Update function to append error to existing meta."""
            if existing_meta is None:
                return {"errors": [new_error]}
            if "errors" not in existing_meta:
                existing_meta["errors"] = []
            existing_meta["errors"].append(new_error)
            return existing_meta
        
        await writer.write_json(self.meta_file, error_entry, update_func=update_meta)
    
    def create_mock_data(self):
        """Create mock data for testing the confirmation page."""
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
                "headings": ["Welcome to Example Business", "Our Services", "Contact Us"],
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
                "headings": ["Our Services", "Web Development", "Consulting", "Digital Marketing"],
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
        with open(self.pages_file, 'w') as f:
            json.dump(mock_pages, f)
        
        # Update meta with successful status
        with open(self.meta_file, 'r') as f:
            meta = json.load(f)
        
        meta.update({
            "status": "completed",
            "completed_at": time.time(),
            "pages": [page["summary"]["pageId"] for page in mock_pages],
            "errors": []
        })
        
        with open(self.meta_file, 'w') as f:
            json.dump(meta, f)
    
    def list_pages(self, page: int = 1, size: int = 50, q: str = None, 
                   type_filter: str = None, min_words: int = 0) -> List[PageSummary]:
        """List pages with filtering and pagination."""
        try:
            with open(self.pages_file, 'r') as f:
                pages = json.load(f)
            
            # If no pages, create mock data for testing
            if not pages:
                self.create_mock_data()
                with open(self.pages_file, 'r') as f:
                    pages = json.load(f)
            
            # Filter pages
            filtered_pages = []
            for page_data in pages:
                summary = page_data.get("summary", {})
                
                # Apply filters
                if type_filter and summary.get("type") != type_filter:
                    continue
                if min_words > 0 and summary.get("words", 0) < min_words:
                    continue
                if q and q.lower() not in str(summary).lower():
                    continue
                
                filtered_pages.append(PageSummary(**summary))
            
            # Paginate
            start = (page - 1) * size
            end = start + size
            return filtered_pages[start:end]
            
        except Exception as e:
            print(f"Error listing pages: {e}")
            return []
    
    def get_page(self, page_id: str) -> Optional[PageDetail]:
        """Get specific page by ID."""
        try:
            with open(self.pages_file, 'r') as f:
                pages = json.load(f)
            
            # If no pages, create mock data for testing
            if not pages:
                self.create_mock_data()
                with open(self.pages_file, 'r') as f:
                    pages = json.load(f)
            
            for page_data in pages:
                if page_data.get("summary", {}).get("pageId") == page_id:
                    return PageDetail(**page_data)
            
            return None
            
        except Exception as e:
            print(f"Error getting page: {e}")
            return None
    
    def progress_snapshot(self, frontier: Frontier) -> Dict[str, Any]:
        """Get progress snapshot."""
        try:
            with open(self.pages_file, 'r') as f:
                pages = json.load(f)
            
            with open(self.meta_file, 'r') as f:
                meta = json.load(f)
            
            # Count errors
            error_count = len(meta.get("errors", []))
            
            # Get frontier stats
            frontier_stats = frontier.get_stats()
            
            return {
                "runId": self.run_id,
                "queued": frontier_stats["queued"],
                "visited": frontier_stats["visited"],
                "errors": error_count,
                "etaSeconds": None,  # Could calculate based on rate
                "hosts": {}  # Could track per-host stats
            }
            
        except Exception as e:
            print(f"Error getting progress: {e}")
            return {
                "runId": self.run_id,
                "queued": 0,
                "visited": 0,
                "errors": 0,
                "etaSeconds": None,
                "hosts": {}
            }
    
    def finalize(self):
        """Finalize the run."""
        try:
            with open(self.meta_file, 'r') as f:
                meta = json.load(f)
            try:
                with open(self.pages_file, 'r') as pf:
                    pages_data = json.load(pf)
            except Exception as read_err:
                print(f"Error reading pages for performance summary: {read_err}")
                pages_data = []

            page_results: List[PageResult] = []
            page_load_pages: List[Dict[str, Any]] = []

            for page in pages_data:
                summary = page.get("summary", {})
                if not summary:
                    continue
                result = PageResult(
                    pageId=summary.get("pageId"),
                    url=summary.get("url"),
                    contentType=summary.get("contentType"),
                    title=summary.get("title"),
                    words=summary.get("words", 0),
                    images=summary.get("images", 0),
                    links=summary.get("links", 0),
                    status=summary.get("status"),
                    status_code=summary.get("status_code"),
                    path=summary.get("path"),
                    type=summary.get("type"),
                    load_time_ms=summary.get("load_time_ms"),
                    content_length_bytes=summary.get("content_length_bytes"),
                )
                page_results.append(result)
                page_load_pages.append({
                    "pageId": result.pageId,
                    "url": result.url,
                    "status": result.status,
                    "status_code": result.status_code,
                    "words": result.words,
                    "images": result.images,
                    "links": result.links,
                    "load_time_ms": result.load_time_ms,
                    "content_length_bytes": result.content_length_bytes,
                    "performance_samples": page.get("performance_samples")  # Include samples
                })

            # Pass pages_data to compute_performance_summary for accessing performance_samples
            performance_summary = compute_performance_summary(page_results, pages_data)
            
            # Compute crawl quality checklist
            try:
                crawl_quality = compute_crawl_quality(self.run_dir)
                meta["crawl_quality"] = crawl_quality
                
                # Print crawl quality summary to console
                print("\n" + "="*60)
                print("CRAWL QUALITY CHECKLIST")
                print("="*60)
                print(f"Pages Crawled: {crawl_quality['pages_crawled']}")
                print(f"Unique Paths: {crawl_quality['unique_paths']}")
                print(f"Duplicate Pages: {crawl_quality['duplicate_pages_detected']}")
                print(f"Avg Load Time: {crawl_quality['avg_load_time_ms']}ms")
                print(f"P90 Load Time: {crawl_quality['p90_load_time_ms']}ms")
                print(f"\nPage Types:")
                print(f"  - Catalog: {crawl_quality['catalog_pages']}")
                print(f"  - Article: {crawl_quality['article_pages']}")
                print(f"  - Landing: {crawl_quality['landing_pages']}")
                print(f"\nIssues:")
                print(f"  - 404 Pages: {crawl_quality['404_pages']}")
                print(f"  - Broken Internal Links: {crawl_quality['broken_internal_links']}")
                print(f"  - Thin Content (Important): {crawl_quality['thin_content_important_pages']}")
                print(f"  - Thin Content (Catalog): {crawl_quality['thin_content_catalog_pages']}")
                print(f"\nStructure:")
                print(f"  - Nav Discovered: {crawl_quality['nav_discovered']}")
                print(f"  - Footer Discovered: {crawl_quality['footer_discovered']}")
                print(f"\nOverall Health: {crawl_quality['overall_health']}")
                print("="*60 + "\n")
            except Exception as e:
                print(f"Error computing crawl quality: {e}")
            
            meta["status"] = "completed"
            meta["completed_at"] = time.time()
            meta["pages"] = [result.pageId for result in page_results if result.pageId]
            meta["pageLoad"] = {
                "pages": page_load_pages,
                "summary": performance_summary
            }
            
            with open(self.meta_file, 'w') as f:
                json.dump(meta, f)
                
        except Exception as e:
            print(f"Error finalizing run: {e}")


def compute_performance_summary(pages: List[PageResult], pages_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Compute aggregate performance metrics from page results with statistical analysis.
    Supports multiple samples per URL and separate JS/raw stats.
    
    Args:
        pages: List of PageResult objects
        pages_data: Optional list of full page data dictionaries (for accessing performance_samples)
    """
    if pages_data is None:
        pages_data = []
    
    # Build a mapping of URL to page data for accessing performance_samples
    url_to_page_data = {}
    for page_data in pages_data:
        summary = page_data.get("summary", {})
        url = summary.get("url")
        if url:
            url_to_page_data[url] = page_data
    
    # Collect all load times from pages and samples
    all_load_times: List[float] = []
    raw_load_times: List[float] = []
    js_load_times: List[float] = []
    
    successful_pages = []
    
    for page in pages:
        if page.status != 200:
            continue
        
        # Check if page has performance_samples
        page_data = url_to_page_data.get(page.url)
        performance_samples = page_data.get("performance_samples") if page_data else None
        
        if performance_samples:
            # Aggregate samples for this page
            aggregated = aggregate_performance_samples(performance_samples)
            if aggregated and aggregated.get("avg_load_ms"):
                effective_load_ms = aggregated["avg_load_ms"]
                render_mode = aggregated.get("render_mode", "raw")
                
                all_load_times.append(effective_load_ms)
                if render_mode == "raw":
                    raw_load_times.append(effective_load_ms)
                elif render_mode == "js":
                    js_load_times.append(effective_load_ms)
                
                # Update page with aggregated metrics
                page.load_time_ms = int(effective_load_ms)
                successful_pages.append(page)
        elif page.load_time_ms is not None:
            # Single sample (legacy or non-controlled mode)
            all_load_times.append(float(page.load_time_ms))
            raw_load_times.append(float(page.load_time_ms))  # Assume raw if not specified
            successful_pages.append(page)
    
    if not all_load_times:
        return {}
    
    # Compute overall stats
    overall_stats = compute_stats_from_values(all_load_times)
    
    # Compute raw stats
    raw_stats = compute_stats_from_values(raw_load_times) if raw_load_times else {}
    
    # Compute JS stats
    js_stats = compute_stats_from_values(js_load_times) if js_load_times else {}
    
    # Performance consistency check
    consistency, consistency_note = compute_performance_consistency(all_load_times)
    
    # Find fastest and slowest pages
    fastest_page = min(successful_pages, key=lambda p: p.load_time_ms or float('inf'))
    slowest_page = max(successful_pages, key=lambda p: p.load_time_ms or float('-inf'))
    
    result = {
        # Legacy fields (backward compatibility)
        "avg_load_ms": int(round(overall_stats.get("average", 0))),
        "median_load_ms": int(round(overall_stats.get("median", 0))),
        "p75_load_ms": int(round(overall_stats.get("p75", 0))),
        "p90_load_ms": int(round(overall_stats.get("p90", 0))),
        "min_load_ms": int(round(overall_stats.get("min", 0))),
        "max_load_ms": int(round(overall_stats.get("max", 0))),
        "stdev_load_ms": round(overall_stats.get("stdev", 0), 2),
        "sample_count": overall_stats.get("count", 0),
        "performance_consistency": consistency,
        "consistency_note": consistency_note,
        "fastest": {
            "url": fastest_page.url,
            "load_ms": fastest_page.load_time_ms
        },
        "slowest": {
            "url": slowest_page.url,
            "load_ms": slowest_page.load_time_ms
        },
        # Enhanced performance_stats structure
        "performance_stats": {
            "overall": overall_stats,
            "raw": raw_stats if raw_stats else None,
            "js": js_stats if js_stats else None
        }
    }
    
    return result