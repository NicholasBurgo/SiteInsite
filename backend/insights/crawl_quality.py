"""
Crawl Quality Checklist computation.
Generates diagnostic metrics to validate crawl data quality.
"""
import os
import json
from typing import Dict, Any, List
from statistics import median


def percentile(data: List[float], p: float) -> float:
    """Calculate the p-th percentile of a list of numbers."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100
    f = int(k)
    c = k - f
    if f + 1 < len(sorted_data):
        return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
    return sorted_data[f]


def compute_crawl_quality(run_dir: str) -> Dict[str, Any]:
    """
    Compute crawl quality metrics from existing crawl data.
    
    Args:
        run_dir: Path to the run directory containing meta.json, pages_index.json, etc.
        
    Returns:
        Dictionary with crawl quality metrics matching the specified format.
    """
    # Initialize defaults
    quality = {
        "pages_crawled": 0,
        "unique_paths": 0,
        "duplicate_pages_detected": 0,
        "avg_load_time_ms": 0,
        "p90_load_time_ms": 0,
        "catalog_pages": 0,
        "article_pages": 0,
        "landing_pages": 0,
        "404_pages": 0,
        "broken_internal_links": 0,
        "thin_content_important_pages": 0,
        "thin_content_catalog_pages": 0,
        "nav_discovered": False,
        "footer_discovered": False,
        "overall_health": "GOOD"
    }
    
    # Load pages_index.json
    pages_index_file = os.path.join(run_dir, "pages_index.json")
    pages_index = []
    if os.path.exists(pages_index_file):
        try:
            with open(pages_index_file, 'r') as f:
                pages_index = json.load(f)
        except Exception as e:
            print(f"Error reading pages_index.json: {e}")
    
    # Load site.json for nav/footer detection
    site_file = os.path.join(run_dir, "site.json")
    site_data = {}
    if os.path.exists(site_file):
        try:
            with open(site_file, 'r') as f:
                site_data = json.load(f)
        except Exception as e:
            print(f"Error reading site.json: {e}")
    
    # Load meta.json for performance data
    meta_file = os.path.join(run_dir, "meta.json")
    meta_data = {}
    if os.path.exists(meta_file):
        try:
            with open(meta_file, 'r') as f:
                meta_data = json.load(f)
        except Exception as e:
            print(f"Error reading meta.json: {e}")
    
    # Load pages.json for additional data (broken links, thin content)
    pages_file = os.path.join(run_dir, "pages.json")
    pages_data = []
    if os.path.exists(pages_file):
        try:
            with open(pages_file, 'r') as f:
                pages_data = json.load(f)
        except Exception as e:
            print(f"Error reading pages.json: {e}")
    
    # Basic counts
    quality["pages_crawled"] = len(pages_index)
    
    # Count unique paths (detect duplicates)
    paths_seen = {}
    duplicate_count = 0
    for page in pages_index:
        path = page.get("path", "")
        if path:
            if path in paths_seen:
                duplicate_count += 1
            else:
                paths_seen[path] = True
    
    quality["unique_paths"] = len(paths_seen)
    quality["duplicate_pages_detected"] = duplicate_count
    
    # Page type counts
    for page in pages_index:
        page_type = page.get("page_type", "generic")
        if page_type == "catalog":
            quality["catalog_pages"] += 1
        elif page_type == "article":
            quality["article_pages"] += 1
        elif page_type == "landing":
            quality["landing_pages"] += 1
    
    # Status code counts (404 pages)
    for page in pages_index:
        status = page.get("status") or page.get("status_code")
        if status == 404:
            quality["404_pages"] += 1
    
    # Performance metrics from meta.json pageLoad data
    page_load_data = meta_data.get("pageLoad", {})
    load_times = []
    
    # Get load times from pages_index
    for page in pages_index:
        load_time = page.get("loadTimeMs")
        if load_time is not None and isinstance(load_time, (int, float)):
            load_times.append(float(load_time))
    
    # Also check pageLoad.pages if available
    if page_load_data:
        page_load_pages = page_load_data.get("pages", [])
        for page in page_load_pages:
            load_time = page.get("load_time_ms")
            if load_time is not None and isinstance(load_time, (int, float)):
                if load_time not in load_times:  # Avoid duplicates
                    load_times.append(float(load_time))
    
    if load_times:
        quality["avg_load_time_ms"] = int(round(sum(load_times) / len(load_times)))
        quality["p90_load_time_ms"] = int(round(percentile(load_times, 90)))
    
    # Navigation and footer detection
    nav_items = site_data.get("nav", [])
    quality["nav_discovered"] = bool(nav_items and len(nav_items) > 0)
    
    footer_data = site_data.get("footer", {})
    footer_columns = footer_data.get("columns", [])
    footer_socials = footer_data.get("socials", [])
    footer_contact = footer_data.get("contact", {})
    quality["footer_discovered"] = bool(
        footer_columns or footer_socials or 
        footer_contact.get("email") or footer_contact.get("phone")
    )
    
    # Broken internal links count
    # Create status_by_url mapping
    status_by_url = {}
    for page in pages_index:
        url = page.get("url", "")
        status = page.get("status") or page.get("status_code")
        if url and status:
            status_by_url[url] = status
    
    # Also check pages.json for status codes
    if pages_data:
        for page_detail in pages_data:
            if isinstance(page_detail, dict):
                summary = page_detail.get("summary", {})
                url = summary.get("url", "")
                status = summary.get("status") or summary.get("status_code")
                if url and status:
                    status_by_url[url] = status
    
    # Count broken internal links from pages.json
    broken_internal_links_count = 0
    pages_dir = os.path.join(run_dir, "pages")
    if os.path.exists(pages_dir):
        for filename in os.listdir(pages_dir):
            if not filename.endswith('.json'):
                continue
            page_file = os.path.join(pages_dir, filename)
            try:
                with open(page_file, 'r') as f:
                    page_data = json.load(f)
                
                internal_links = page_data.get("links", {}).get("internal", [])
                if internal_links:
                    for link in internal_links:
                        link_url = link.get("href", "") if isinstance(link, dict) else str(link)
                        if not link_url:
                            continue
                        
                        # Check if link destination was crawled and has a bad status
                        link_status = status_by_url.get(link_url)
                        if link_status is not None:
                            if link_status in [404, 410] or (link_status >= 500 and link_status < 600):
                                broken_internal_links_count += 1
            except Exception:
                continue
    
    quality["broken_internal_links"] = broken_internal_links_count
    
    # Thin content detection
    # Important pages: article, landing, generic
    # Catalog pages: catalog, product
    thin_content_important = 0
    thin_content_catalog = 0
    
    pages_index_map = {p.get("url", ""): p for p in pages_index}
    
    if os.path.exists(pages_dir):
        for filename in os.listdir(pages_dir):
            if not filename.endswith('.json'):
                continue
            page_file = os.path.join(pages_dir, filename)
            try:
                with open(page_file, 'r') as f:
                    page_data = json.load(f)
                
                url = page_data.get("url", "")
                page_index_entry = pages_index_map.get(url, {})
                page_type = page_index_entry.get("page_type") or page_data.get("stats", {}).get("page_type") or "generic"
                
                # Get word count
                words_data = page_data.get("words", {})
                if isinstance(words_data, dict):
                    word_count = words_data.get("wordCount", 0)
                else:
                    word_count = page_data.get("word_count", 0) or page_data.get("words", 0)
                
                # Skip bad pages (404/5xx) from content scoring
                status = page_index_entry.get("status") or page_index_entry.get("status_code") or page_data.get("status")
                is_bad_page = status and (status == 404 or status == 410 or (status >= 500 and status < 600))
                
                if not is_bad_page:
                    # Important content pages: article, landing, generic
                    if page_type in ["article", "landing", "generic"]:
                        # Apply thresholds for important content pages
                        if page_type == "article":
                            thin_threshold = 600
                        elif page_type == "landing":
                            thin_threshold = 150
                        else:  # generic
                            thin_threshold = 150
                        
                        if word_count < thin_threshold:
                            thin_content_important += 1
                    # Catalog/product pages
                    elif page_type in ["catalog", "product"]:
                        # Only flag if literally empty or almost empty
                        if word_count < 10:
                            thin_content_catalog += 1
            except Exception:
                continue
    
    quality["thin_content_important_pages"] = thin_content_important
    quality["thin_content_catalog_pages"] = thin_content_catalog
    
    # Determine overall_health based on heuristics
    pages_crawled = quality["pages_crawled"]
    nav_discovered = quality["nav_discovered"]
    pct_404 = (quality["404_pages"] / pages_crawled * 100) if pages_crawled > 0 else 0
    pct_thin_important = (thin_content_important / pages_crawled * 100) if pages_crawled > 0 else 0
    duplicate_pages = quality["duplicate_pages_detected"]
    article_landing_count = quality["article_pages"] + quality["landing_pages"]
    
    # BAD conditions
    if pages_crawled < 10:
        quality["overall_health"] = "BAD"
    elif not nav_discovered:
        quality["overall_health"] = "BAD"
    elif pct_404 > 25:
        quality["overall_health"] = "BAD"
    # WARNING conditions
    elif pct_thin_important > 20:
        quality["overall_health"] = "WARNING"
    elif duplicate_pages > pages_crawled * 0.1:  # More than 10% duplicates
        quality["overall_health"] = "WARNING"
    elif article_landing_count == 0 and pages_crawled > 5:
        quality["overall_health"] = "WARNING"
    else:
        quality["overall_health"] = "GOOD"
    
    return quality

