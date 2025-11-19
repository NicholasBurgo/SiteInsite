"""
Insight Report builder.
Analyzes run data and generates comprehensive Website Insight Reports.
"""
import os
import json
import uuid
from statistics import median
from typing import List, Dict, Any, Optional
from backend.core.types import InsightReport, InsightCategoryScore, InsightIssue, InsightAffectedPage, InsightStats
from backend.storage.runs import RunStore
from backend.storage.simhash import SimHash


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


def clamp_0_100(value: float) -> float:
    """Clamp a value to the range [0, 100]."""
    return max(0.0, min(100.0, value))


def calculate_content_depth_score(
    avg_words_per_page: float,
    pages_count: int,
    pages_dir: str,
    pages_index: List[Dict[str, Any]]
) -> float:
    """
    Calculate Content Depth Score (0-100) based on:
    - Normalized average words per page (0.5 weight)
    - Unique content ratio using SimHash (0.3 weight)
    - Keyword coverage score from headings/titles (0.2 weight)
    
    Rewards purposeful depth, not raw volume.
    """
    # 1. Normalized avg words per page (0-100 scale)
    # Recommended range: 300-2000 words for content-heavy pages
    # Below 300: penalize, above 2000: cap bonus
    if avg_words_per_page <= 0:
        normalized_words = 0.0
    elif avg_words_per_page < 100:
        normalized_words = (avg_words_per_page / 100) * 30  # 0-30
    elif avg_words_per_page < 300:
        normalized_words = 30 + ((avg_words_per_page - 100) / 200) * 40  # 30-70
    elif avg_words_per_page <= 2000:
        normalized_words = 70 + ((avg_words_per_page - 300) / 1700) * 30  # 70-100
    else:
        normalized_words = 100.0  # Cap at 100
    
    # 2. Unique content ratio using SimHash (0-100 scale)
    # Estimate uniqueness by comparing page content hashes
    unique_content_ratio = 100.0  # Default to high if we can't compute
    if pages_count > 0 and os.path.exists(pages_dir):
        simhash = SimHash()
        content_hashes = []
        unique_count = 0
        
        for filename in os.listdir(pages_dir):
            if not filename.endswith('.json'):
                continue
            page_file = os.path.join(pages_dir, filename)
            try:
                with open(page_file, 'r') as f:
                    page_data = json.load(f)
                
                # Extract text content
                text_content = page_data.get("text", "") or ""
                title = page_data.get("title", "") or ""
                # Use title + first 1000 chars for hash
                content_for_hash = f"{title}\n{text_content[:1000]}"
                
                if content_for_hash.strip():
                    page_hash = simhash.compute(content_for_hash)
                    # Check if similar to existing hashes
                    is_unique = True
                    for existing_hash in content_hashes:
                        if simhash.similarity(page_hash, existing_hash) > 0.8:
                            is_unique = False
                            break
                    
                    if is_unique:
                        unique_count += 1
                    content_hashes.append(page_hash)
            except Exception:
                continue
        
        if len(content_hashes) > 0:
            unique_content_ratio = (unique_count / len(content_hashes)) * 100.0
    
    # 3. Keyword coverage score (0-100 scale)
    # Estimate based on presence of headings and titles
    keyword_coverage_score = 50.0  # Default baseline
    if pages_count > 0 and os.path.exists(pages_dir):
        total_headings = 0
        pages_with_headings = 0
        
        for filename in os.listdir(pages_dir):
            if not filename.endswith('.json'):
                continue
            page_file = os.path.join(pages_dir, filename)
            try:
                with open(page_file, 'r') as f:
                    page_data = json.load(f)
                
                words_data = page_data.get("words", {})
                headings = words_data.get("headings", [])
                title = page_data.get("title", "")
                
                if headings:
                    total_headings += len(headings)
                    pages_with_headings += 1
                elif title:
                    pages_with_headings += 1
            except Exception:
                continue
        
        if pages_count > 0:
            # Reward pages with headings/titles
            heading_coverage = (pages_with_headings / pages_count) * 100.0
            avg_headings_per_page = total_headings / pages_count if pages_count > 0 else 0
            # Combine coverage and density
            keyword_coverage_score = clamp_0_100(
                (heading_coverage * 0.6) + (min(avg_headings_per_page / 5, 1.0) * 40)
            )
    
    # Combine with weights
    content_depth_score = clamp_0_100(
        0.5 * normalized_words +
        0.3 * unique_content_ratio +
        0.2 * keyword_coverage_score
    )
    
    return round(content_depth_score, 2)


def determine_nav_type(
    nav_items: List[Any],
    pages_count: int,
    pages_dir: str,
    pages_index: List[Dict[str, Any]]
) -> str:
    """
    Determine navigation type based on site structure.
    
    Returns one of:
    - "single_page": <= 5 pages, no nav tag
    - "simple_nav": nav tag with few links
    - "multi_section": nav tag with many top-level links
    - "app_style": many pages but few nav links (SPA-like)
    - "implicit_content_links": many internal links in body, no nav tag
    - "none_detected": no clear navigation pattern
    """
    # Count internal links from pages
    total_internal_links = 0
    if os.path.exists(pages_dir):
        for filename in os.listdir(pages_dir):
            if not filename.endswith('.json'):
                continue
            page_file = os.path.join(pages_dir, filename)
            try:
                with open(page_file, 'r') as f:
                    page_data = json.load(f)
                links = page_data.get("links", {})
                internal_links = links.get("internal", [])
                total_internal_links += len(internal_links)
            except Exception:
                continue
    
    nav_link_count = len(nav_items) if nav_items else 0
    
    # Decision logic
    if pages_count <= 5 and nav_link_count == 0:
        return "single_page"
    elif nav_link_count > 0:
        if nav_link_count >= 5:
            return "multi_section"
        else:
            return "simple_nav"
    elif total_internal_links > pages_count * 3:  # Many internal links
        return "implicit_content_links"
    elif pages_count > 20 and nav_link_count < 3:
        return "app_style"
    else:
        return "none_detected"


def calculate_crawlability_score(
    pages_count: int,
    pages_dir: str,
    pages_index: List[Dict[str, Any]],
    base_url: Optional[str]
) -> float:
    """
    Calculate Crawlability Score (0-100) based on:
    - Number of internal links
    - Presence of consistent nav or link hubs
    - Depth vs breadth (how many pages reachable from homepage within N hops)
    - Link density
    
    High score: Most pages reachable within 2-3 hops, healthy internal link count
    Low score: Many isolated pages, very few internal links
    """
    if pages_count == 0:
        return 0.0
    
    # Count total internal links
    total_internal_links = 0
    pages_with_internal_links = 0
    link_density_per_page = []
    
    if os.path.exists(pages_dir):
        for filename in os.listdir(pages_dir):
            if not filename.endswith('.json'):
                continue
            page_file = os.path.join(pages_dir, filename)
            try:
                with open(page_file, 'r') as f:
                    page_data = json.load(f)
                links = page_data.get("links", {})
                internal_links = links.get("internal", [])
                link_count = len(internal_links)
                total_internal_links += link_count
                link_density_per_page.append(link_count)
                if link_count > 0:
                    pages_with_internal_links += 1
            except Exception:
                continue
    
    # Calculate metrics
    avg_internal_links_per_page = total_internal_links / pages_count if pages_count > 0 else 0
    pages_with_links_ratio = pages_with_internal_links / pages_count if pages_count > 0 else 0
    
    # Score based on link density
    # Good sites have 5-20 internal links per page on average
    if avg_internal_links_per_page >= 5:
        link_density_score = 100.0
    elif avg_internal_links_per_page >= 2:
        link_density_score = 50 + ((avg_internal_links_per_page - 2) / 3) * 50  # 50-100
    elif avg_internal_links_per_page >= 0.5:
        link_density_score = (avg_internal_links_per_page / 0.5) * 50  # 0-50
    else:
        link_density_score = 0.0
    
    # Score based on pages with links ratio
    # Most pages should have at least some internal links
    pages_with_links_score = pages_with_links_ratio * 100.0
    
    # Estimate reachability (simplified: assume homepage links to many pages)
    # If we have many internal links, pages are likely reachable
    reachability_score = min(avg_internal_links_per_page / 10 * 100, 100.0)
    
    # Combine scores (weighted)
    crawlability_score = clamp_0_100(
        0.4 * link_density_score +
        0.3 * pages_with_links_score +
        0.3 * reachability_score
    )
    
    return round(crawlability_score, 2)


def build_insight_report(run_store: RunStore, run_id: str) -> InsightReport:
    """
    Load run data and compute a Website Insight Report with aggregated stats and issues.
    """
    run_dir = run_store.run_dir
    
    # Load meta.json
    meta_file = os.path.join(run_dir, "meta.json")
    meta_data = {}
    if os.path.exists(meta_file):
        with open(meta_file, 'r') as f:
            meta_data = json.load(f)
    
    # Load pages_index.json
    pages_index_file = os.path.join(run_dir, "pages_index.json")
    pages_index = []
    if os.path.exists(pages_index_file):
        with open(pages_index_file, 'r') as f:
            pages_index = json.load(f)
    
    # Load site.json
    site_file = os.path.join(run_dir, "site.json")
    site_data = {}
    base_url = None
    nav_items = []
    footer_data = {}
    if os.path.exists(site_file):
        with open(site_file, 'r') as f:
            site_data = json.load(f)
        base_url = site_data.get("baseUrl")
        nav_items = site_data.get("nav", [])
        footer_data = site_data.get("footer", {})
    
    # Extract indexability info from site.json
    # TODO: If crawler stores robots.txt/sitemap detection, add those fields to site.json
    robots_present = site_data.get("robots_present", False)
    sitemap_present = site_data.get("sitemap_present", False)
    
    # Detect HTTPS
    https_site = bool(base_url and base_url.startswith("https://"))
    
    # Load pages.json for additional data
    pages_file = os.path.join(run_dir, "pages.json")
    pages_data = []
    if os.path.exists(pages_file):
        with open(pages_file, 'r') as f:
            pages_data = json.load(f)
    
    # Extract performance data
    load_times: List[float] = []
    page_sizes: List[int] = []
    status_codes: Dict[str, int] = {}
    word_counts: List[int] = []
    media_counts: List[int] = []
    
    # Process pages_index.json for basic stats
    for page in pages_index:
        # Status codes
        status = page.get("status") or page.get("status_code")
        if status:
            status_str = str(status)
            status_codes[status_str] = status_codes.get(status_str, 0) + 1
        
        # Load times
        load_time = page.get("loadTimeMs")
        if load_time is not None and isinstance(load_time, (int, float)):
            load_times.append(float(load_time))
        
        # Page sizes
        size_bytes = page.get("contentLengthBytes")
        if size_bytes is not None and isinstance(size_bytes, (int, float)):
            page_sizes.append(int(size_bytes))
        
        # Word counts
        words = page.get("words", 0)
        if isinstance(words, (int, float)):
            word_counts.append(int(words))
        
        # Media counts
        media = page.get("mediaCount", 0)
        if isinstance(media, (int, float)):
            media_counts.append(int(media))
    
    # Also check meta.json pageLoad data if available
    page_load_data = meta_data.get("pageLoad", {})
    performance_summary = page_load_data.get("summary", {})
    performance_stats = performance_summary.get("performance_stats", {})
    performance_consistency = performance_summary.get("performance_consistency", "unknown")
    consistency_note = performance_summary.get("consistency_note", "")
    
    if page_load_data:
        page_load_pages = page_load_data.get("pages", [])
        for page in page_load_pages:
            load_time = page.get("load_time_ms")
            if load_time is not None and isinstance(load_time, (int, float)):
                if load_time not in load_times:  # Avoid duplicates
                    load_times.append(float(load_time))
            
            size_bytes = page.get("content_length_bytes")
            if size_bytes is not None and isinstance(size_bytes, (int, float)):
                if size_bytes not in page_sizes:  # Avoid duplicates
                    page_sizes.append(int(size_bytes))
    
    # Compute performance stats
    pages_count = len(pages_index) if pages_index else len(pages_data)
    if pages_count == 0:
        pages_count = 1  # Avoid division by zero
    
    # Use performance_stats from meta.json if available, otherwise compute from load_times
    if performance_stats and performance_stats.get("sample_count", 0) > 0:
        avg_load_ms = performance_stats.get("average", 0.0)
        median_load_ms = performance_stats.get("median", 0.0)
        p90_load_ms = performance_stats.get("p90", 0.0) or 0.0
        p75_load_ms = performance_stats.get("p75", 0.0) or 0.0
        p95_load_ms = percentile(load_times, 95) if load_times else 0.0  # Still compute p95
    else:
        # Fallback to computing from load_times
        avg_load_ms = sum(load_times) / len(load_times) if load_times else 0.0
        median_load_ms = median(load_times) if load_times else 0.0
        p90_load_ms = percentile(load_times, 90) if load_times else 0.0
        p75_load_ms = percentile(load_times, 75) if load_times else 0.0
        p95_load_ms = percentile(load_times, 95) if load_times else 0.0
    
    # Get perf_mode from meta.json
    perf_mode = meta_data.get("perf_mode", "controlled")
    
    slow_pages = [p for p in pages_index if p.get("loadTimeMs") and p.get("loadTimeMs", 0) > 1500]
    very_slow_pages = [p for p in pages_index if p.get("loadTimeMs") and p.get("loadTimeMs", 0) > 3000]
    
    avg_page_size_kb = (sum(page_sizes) / len(page_sizes) / 1024) if page_sizes else 0.0
    max_page_size_kb = (max(page_sizes) / 1024) if page_sizes else 0.0
    
    # Content stats
    total_words = sum(word_counts)
    avg_words_per_page = total_words / pages_count if pages_count > 0 else 0.0
    total_media_items = sum(media_counts)
    avg_media_per_page = total_media_items / pages_count if pages_count > 0 else 0.0
    
    # Build stats (bad_pages_count and broken_internal_links_count will be updated after analysis)
    stats = InsightStats(
        pagesCount=pages_count,
        totalWords=total_words,
        avgWordsPerPage=round(avg_words_per_page, 2),
        totalMediaItems=total_media_items,
        avgMediaPerPage=round(avg_media_per_page, 2),
        statusCounts=status_codes,
        avgLoadMs=round(avg_load_ms, 2),
        medianLoadMs=round(median_load_ms, 2),
        p90LoadMs=round(p90_load_ms, 2),
        p95LoadMs=round(p95_load_ms, 2),
        slowPagesCount=len(slow_pages),
        verySlowPagesCount=len(very_slow_pages),
        avgPageSizeKb=round(avg_page_size_kb, 2),
        maxPageSizeKb=round(max_page_size_kb, 2),
        badPagesCount=0,  # Will be updated after analysis
        brokenInternalLinksCount=0  # Will be updated after analysis
    )
    
    # Analyze pages for SEO/content issues
    pages_dir = os.path.join(run_dir, "pages")
    seo_issues: List[InsightIssue] = []
    content_issues: List[InsightIssue] = []
    
    # Store page data with metadata for building affected pages
    pages_missing_title = []
    pages_missing_description = []
    pages_missing_h1 = []
    pages_thin_content = []  # Page-type aware thin content (important pages only)
    pages_very_thin_content = []  # Page-type aware very thin content (important pages only)
    pages_with_broken_links = []
    images_missing_alt = []
    # Separate tracking for catalog/product pages with low text (soft issue)
    low_text_catalog_pages = []
    
    # Bad pages tracking (404/5xx)
    bad_pages = []  # 404, 410, 5xx pages
    
    # Broken internal links tracking
    broken_internal_links_global = []  # Global list of all broken internal links
    pages_with_broken_internal_links = []  # Pages that contain broken internal links
    
    # New checks: indexability, mobile, HTTPS, images
    noindex_pages = []
    no_viewport_pages = []
    mixed_content_pages = []
    pages_with_very_large_images = []
    pages_with_large_images = []
    pages_with_modern_images = []
    
    # Create a mapping of URL to page data from pages_index for quick lookup
    pages_index_map = {p.get("url", ""): p for p in pages_index}
    
    # Create status_by_url mapping for broken link detection
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
    
    # Create a mapping of URL to meta data from pages.json for meta tag checks
    pages_meta_map = {}
    if pages_data:
        for page_detail in pages_data:
            if isinstance(page_detail, dict):
                summary = page_detail.get("summary", {})
                url = summary.get("url", "")
                meta = page_detail.get("meta", {})
                if url:
                    pages_meta_map[url] = meta
    
    # Load individual page files for detailed analysis
    if os.path.exists(pages_dir):
        for filename in os.listdir(pages_dir):
            if not filename.endswith('.json'):
                continue
            page_file = os.path.join(pages_dir, filename)
            try:
                with open(page_file, 'r') as f:
                    page_data = json.load(f)
                
                url = page_data.get("url", "")
                title = page_data.get("title")
                description = page_data.get("description")
                word_count = page_data.get("words", {}).get("wordCount", 0)
                headings = page_data.get("words", {}).get("headings", [])
                broken_links = page_data.get("links", {}).get("broken", [])
                images = page_data.get("media", {}).get("images", [])
                internal_links = page_data.get("links", {}).get("internal", [])
                external_links = page_data.get("links", {}).get("external", [])
                
                # Check if this page itself is a bad page (404/5xx)
                page_index_entry = pages_index_map.get(url, {})
                status = page_index_entry.get("status") or page_index_entry.get("status_code") or page_data.get("status")
                if status:
                    if status == 404 or status == 410 or (status >= 500 and status < 600):
                        bad_pages.append({
                            "url": url,
                            "status_code": status
                        })
                
                # Check internal links for broken destinations
                # Only mark as broken if we actually crawled the link and got a bad status
                # Don't mark as broken just because it wasn't crawled (might be outside crawl scope)
                broken_internal_links_on_page = []
                if internal_links:
                    for link in internal_links:
                        link_url = link.get("href", "") if isinstance(link, dict) else str(link)
                        if not link_url:
                            continue
                        
                        # Check if link destination was crawled and has a bad status
                        link_status = status_by_url.get(link_url)
                        if link_status is not None:
                            # Only mark as broken if we actually got a bad status code
                            if link_status in [404, 410] or (link_status >= 500 and link_status < 600):
                                broken_internal_links_on_page.append({
                                    "href": link_url,
                                    "status": link_status
                                })
                        # If link_status is None, the link wasn't crawled - don't mark as broken
                        # (it might be outside crawl scope, depth limit, or just not discovered)
                
                # Track pages with broken internal links
                if broken_internal_links_on_page:
                    pages_with_broken_internal_links.append({
                        "url": url,
                        "broken_links": broken_internal_links_on_page,
                        "broken_count": len(broken_internal_links_on_page)
                    })
                    broken_internal_links_global.extend(broken_internal_links_on_page)
                
                # Check for missing title
                if not title or title.strip() == "":
                    pages_missing_title.append({"url": url, "note": None})
                
                # Check for missing description
                if not description or description.strip() == "":
                    pages_missing_description.append({"url": url, "note": "No meta description"})
                
                # Check for missing H1
                h1_found = any(h.get("tag", "").lower() == "h1" for h in headings)
                if not h1_found:
                    pages_missing_h1.append({"url": url, "note": None})
                
                # Get page_type from pages_index or page data
                page_index_entry = pages_index_map.get(url, {})
                page_type = page_index_entry.get("page_type") or page_data.get("stats", {}).get("page_type") or "generic"
                
                # Page-type aware thin content detection
                # Important content pages: article, landing, generic
                # Supporting pages: catalog, product, media_gallery, contact, utility
                is_important_content_page = page_type in ["article", "landing", "generic"]
                is_supporting_page = page_type in ["catalog", "product", "media_gallery", "contact", "utility"]
                
                # Skip bad pages (404/5xx) from content scoring
                status = page_index_entry.get("status") or page_index_entry.get("status_code") or page_data.get("status")
                is_bad_page = status and (status == 404 or status == 410 or (status >= 500 and status < 600))
                
                if not is_bad_page:
                    if is_important_content_page:
                        # Apply stricter thresholds for important content pages
                        if page_type == "article":
                            very_thin = word_count < 300
                            thin = word_count < 600
                        elif page_type == "landing":
                            very_thin = word_count < 80
                            thin = word_count < 150
                        else:  # generic
                            very_thin = word_count < 50
                            thin = word_count < 150
                        
                        if very_thin:
                            pages_very_thin_content.append({
                                "url": url, 
                                "word_count": word_count,
                                "page_type": page_type
                            })
                        elif thin:
                            pages_thin_content.append({
                                "url": url, 
                                "word_count": word_count,
                                "page_type": page_type
                            })
                    elif is_supporting_page:
                        # Only flag if literally empty or almost empty for supporting pages
                        if word_count < 10:
                            # Track as low-text catalog/product page (soft issue)
                            if page_type in ["catalog", "product"]:
                                low_text_catalog_pages.append({
                                    "url": url,
                                    "word_count": word_count,
                                    "page_type": page_type
                                })
                
                # Check for broken links
                if broken_links:
                    broken_count = len(broken_links)
                    pages_with_broken_links.append({"url": url, "broken_count": broken_count})
                
                # Check for images missing alt text
                missing_alt_count = sum(1 for img in images if not img.get("alt") or img.get("alt", "").strip() == "")
                if missing_alt_count > 0:
                    images_missing_alt.append({"url": url, "missing_alt_count": missing_alt_count})
                
                # NEW: Check for noindex meta tag
                page_meta = pages_meta_map.get(url, {})
                robots_content = page_meta.get("robots", "")
                if isinstance(robots_content, str) and "noindex" in robots_content.lower():
                    noindex_pages.append({"url": url, "note": None})
                
                # NEW: Check for viewport meta tag
                has_viewport = bool(page_meta.get("viewport"))
                if not has_viewport:
                    no_viewport_pages.append({"url": url, "note": None})
                
                # NEW: Check for mixed content (http:// assets on https:// site)
                if https_site:
                    all_links = [l.get("href", "") for l in internal_links + external_links]
                    all_image_urls = [img.get("url", "") for img in images]
                    all_assets = all_links + all_image_urls
                    has_mixed_content = any(asset.startswith("http://") for asset in all_assets if asset)
                    if has_mixed_content:
                        mixed_content_pages.append({"url": url, "note": None})
                
                # NEW: Image optimization checks
                large_image_threshold = 500 * 1024  # 500KB
                very_large_image_threshold = 1 * 1024 * 1024  # 1MB
                
                large_image_count = 0
                very_large_image_count = 0
                modern_format_count = 0  # webp/avif
                
                for img in images:
                    img_url = img.get("url", "")
                    if not img_url:
                        continue
                    
                    # Extract file extension
                    img_url_clean = img_url.split("?")[0].split("#")[0]
                    ext = img_url_clean.split(".")[-1].lower() if "." in img_url_clean else ""
                    
                    # Check image size (if available)
                    # Note: Image sizes aren't currently stored, so we'll estimate based on URL patterns
                    # or check if we have size info from response headers
                    size_bytes = img.get("bytes") or img.get("sizeBytes") or img.get("size", 0)
                    
                    if size_bytes and size_bytes > very_large_image_threshold:
                        very_large_image_count += 1
                    elif size_bytes and size_bytes > large_image_threshold:
                        large_image_count += 1
                    
                    # Check for modern formats
                    if ext in ("webp", "avif"):
                        modern_format_count += 1
                
                # Store page-level image metrics
                if very_large_image_count > 0:
                    pages_with_very_large_images.append({
                        "url": url,
                        "very_large_image_count": very_large_image_count
                    })
                elif large_image_count > 0:
                    pages_with_large_images.append({
                        "url": url,
                        "large_image_count": large_image_count
                    })
                
                if modern_format_count > 0:
                    pages_with_modern_images.append({"url": url})
                    
            except Exception as e:
                # Skip pages that can't be loaded
                continue
    
    # Build SEO issues
    if pages_missing_title:
        missing_title_pct = (len(pages_missing_title) / pages_count) * 100
        seo_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="seo",
            severity="high" if missing_title_pct > 20 else "medium",
            title="Missing Page Titles",
            description=f"{len(pages_missing_title)} pages ({missing_title_pct:.1f}%) are missing page titles.",
            affectedPages=[
                InsightAffectedPage(url=p["url"], note=p.get("note"))
                for p in pages_missing_title
            ]
        ))
    
    if pages_missing_description:
        missing_desc_pct = (len(pages_missing_description) / pages_count) * 100
        seo_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="seo",
            severity="high" if missing_desc_pct > 20 else "medium",
            title="Missing Meta Descriptions",
            description=f"{len(pages_missing_description)} pages ({missing_desc_pct:.1f}%) are missing meta descriptions.",
            affectedPages=[
                InsightAffectedPage(url=p["url"], note=p.get("note"))
                for p in pages_missing_description
            ]
        ))
    
    if pages_missing_h1:
        missing_h1_pct = (len(pages_missing_h1) / pages_count) * 100
        seo_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="seo",
            severity="medium" if missing_h1_pct > 10 else "low",
            title="Missing H1 Headings",
            description=f"{len(pages_missing_h1)} pages ({missing_h1_pct:.1f}%) are missing H1 headings.",
            affectedPages=[
                InsightAffectedPage(url=p["url"], note=p.get("note"))
                for p in pages_missing_h1
            ]
        ))
    
    if pages_with_broken_links:
        seo_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="seo",
            severity="high",
            title="Broken Links Detected",
            description=f"{len(pages_with_broken_links)} pages contain broken links.",
            affectedPages=[
                InsightAffectedPage(
                    url=p["url"],
                    note=f"{p.get('broken_count', 0)} broken links" if p.get("broken_count") else None
                )
                for p in pages_with_broken_links
            ]
        ))
    
    if images_missing_alt:
        seo_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="seo",
            severity="medium",
            title="Images Missing Alt Text",
            description=f"{len(images_missing_alt)} pages contain images without alt text.",
            affectedPages=[
                InsightAffectedPage(
                    url=p["url"],
                    note=f"{p.get('missing_alt_count', 0)} images without alt" if p.get("missing_alt_count") else None
                )
                for p in images_missing_alt
            ]
        ))
    
    # NEW: SEO - Indexability & crawlability issues
    if noindex_pages:
        seo_issues.append(InsightIssue(
            id="seo_noindex_pages",
            category="seo",
            severity="medium",
            title="Noindex Pages",
            description=f"{len(noindex_pages)} pages are marked as noindex. Make sure this is intentional.",
            affectedPages=[
                InsightAffectedPage(url=p["url"], note=p.get("note"))
                for p in noindex_pages
            ]
        ))
    
    if not robots_present:
        seo_issues.append(InsightIssue(
            id="seo_no_robots_txt",
            category="seo",
            severity="low",
            title="robots.txt Not Detected",
            description="A robots.txt file was not detected. While optional, adding one helps control how search engines crawl your site.",
            affectedPages=[]
        ))
    
    if not sitemap_present:
        seo_issues.append(InsightIssue(
            id="seo_no_sitemap",
            category="seo",
            severity="low",
            title="Sitemap Not Detected",
            description="An XML sitemap was not detected. Adding one helps search engines discover and index important pages.",
            affectedPages=[]
        ))
    
    # Calculate important pages metrics for content issues (needed before building issues)
    important_content_pages_for_issues = [
        p for p in pages_index 
        if p.get("page_type") in ["article", "landing", "generic"] or not p.get("page_type")
    ]
    important_pages_count_for_issues = len(important_content_pages_for_issues) if important_content_pages_for_issues else pages_count
    
    # Calculate avg words for important pages only
    important_word_counts_for_issues = [
        p.get("words", 0) for p in important_content_pages_for_issues 
        if isinstance(p.get("words"), (int, float))
    ]
    avg_words_important_pages = (
        sum(important_word_counts_for_issues) / len(important_word_counts_for_issues) 
        if important_word_counts_for_issues else avg_words_per_page
    )
    
    # Build content issues with page-type aware messaging
    if pages_very_thin_content:
        # Group by page type for better messaging
        article_pages = [p for p in pages_very_thin_content if p.get("page_type") == "article"]
        landing_pages = [p for p in pages_very_thin_content if p.get("page_type") == "landing"]
        generic_pages = [p for p in pages_very_thin_content if p.get("page_type") == "generic" or not p.get("page_type")]
        
        page_type_summary = []
        if article_pages:
            page_type_summary.append(f"{len(article_pages)} article")
        if landing_pages:
            page_type_summary.append(f"{len(landing_pages)} landing")
        if generic_pages:
            page_type_summary.append(f"{len(generic_pages)} generic")
        
        type_label = ", ".join(page_type_summary) if page_type_summary else "important"
        
        content_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="content",
            severity="high",
            title="Very Thin Content (Important Pages)",
            description=f"{len(pages_very_thin_content)} {type_label} page(s) have too little text for SEO.",
            affectedPages=[
                InsightAffectedPage(
                    url=p["url"], 
                    note=f"{p.get('word_count', 0)} words ({p.get('page_type', 'generic')})"
                )
                for p in pages_very_thin_content
            ]
        ))
    
    if pages_thin_content:
        content_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="content",
            severity="medium",
            title="Thin Content (Important Pages)",
            description=f"{len(pages_thin_content)} important page(s) could benefit from more content.",
            affectedPages=[
                InsightAffectedPage(
                    url=p["url"], 
                    note=f"{p.get('word_count', 0)} words ({p.get('page_type', 'generic')})"
                )
                for p in pages_thin_content
            ]
        ))
    
    # Soft issue for catalog/product pages with low text (optional)
    if low_text_catalog_pages:
        content_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="content",
            severity="low",
            title="Low-text Catalog/Product Pages (Optional)",
            description=f"{len(low_text_catalog_pages)} catalog/product page(s) have minimal descriptions. Adding more copy can help SEO but is optional.",
            affectedPages=[
                InsightAffectedPage(
                    url=p["url"],
                    note=f"{p.get('word_count', 0)} words ({p.get('page_type', 'catalog')})"
                )
                for p in low_text_catalog_pages  # Show all pages
            ]
        ))
    
    if avg_words_important_pages < 200 and important_pages_count_for_issues > 0:
        content_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="content",
            severity="low",
            title="Low Average Word Count (Important Pages)",
            description=f"Average words per important page ({avg_words_important_pages:.0f}) is below recommended 200 words.",
            affectedPages=[]
        ))
    
    # Build performance issues
    performance_issues: List[InsightIssue] = []
    if avg_load_ms > 2000:
        performance_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="performance",
            severity="high",
            title="Overall Slow Performance",
            description=f"Average page load time ({avg_load_ms:.0f}ms) exceeds 2000ms.",
            affectedPages=[]
        ))
    
    if p90_load_ms > 3000:
        performance_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="performance",
            severity="high",
            title="High P90 Load Time",
            description=f"90th percentile load time ({p90_load_ms:.0f}ms) exceeds 3000ms.",
            affectedPages=[]
        ))
    
    if very_slow_pages:
        performance_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="performance",
            severity="high",
            title="Very Slow Pages",
            description=f"{len(very_slow_pages)} pages take more than 3000ms to load.",
            affectedPages=[
                InsightAffectedPage(
                    url=p.get("url", ""),
                    note=f"{int(p.get('loadTimeMs', 0))} ms" if p.get("loadTimeMs") else None
                )
                for p in very_slow_pages
            ]
        ))
    
    if slow_pages:
        performance_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="performance",
            severity="medium",
            title="Slow Pages (>1500ms)",
            description=f"{len(slow_pages)} pages load slower than 1500 ms.",
            affectedPages=[
                InsightAffectedPage(
                    url=p.get("url", ""),
                    note=f"{int(p.get('loadTimeMs', 0))} ms" if p.get("loadTimeMs") else None
                )
                for p in slow_pages
            ]
        ))
    
    if max_page_size_kb > 1500:
        performance_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="performance",
            severity="medium",
            title="Very Heavy Page Detected",
            description=f"Largest page size ({max_page_size_kb:.0f}KB) exceeds 1500KB.",
            affectedPages=[]
        ))
    
    # NEW: Performance - Image optimization issues
    if pages_with_very_large_images:
        performance_issues.append(InsightIssue(
            id="perf_very_large_images",
            category="performance",
            severity="medium",
            title="Very Large Images",
            description=f"{len(pages_with_very_large_images)} pages contain images larger than 1MB. Consider compressing or resizing.",
            affectedPages=[
                InsightAffectedPage(
                    url=p["url"],
                    note=f"{p.get('very_large_image_count', 0)} image(s) > 1MB"
                )
                for p in pages_with_very_large_images
            ]
        ))
    
    # Check if site uses only legacy image formats
    if pages_count > 0 and not pages_with_modern_images:
        performance_issues.append(InsightIssue(
            id="perf_no_modern_images",
            category="performance",
            severity="low",
            title="No Modern Image Formats Detected",
            description="Images are served only as JPG/PNG/GIF. Consider using WebP or AVIF for faster loading.",
            affectedPages=[]
        ))
    
    # Build structure issues
    structure_issues: List[InsightIssue] = []
    if not nav_items or len(nav_items) == 0:
        structure_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="structure",
            severity="high",
            title="Navigation Not Detected",
            description="No navigation structure was found on the site.",
            affectedPages=[]
        ))
    
    footer_contact = footer_data.get("contact", {})
    footer_socials = footer_data.get("socials", [])
    if not footer_contact.get("email") and not footer_contact.get("phone") and not footer_socials:
        structure_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="structure",
            severity="medium",
            title="Missing Footer Contact Info",
            description="Footer is missing contact information and social links.",
            affectedPages=[]
        ))
    
    # Check URL depth (count path segments)
    deep_urls = []
    for page in pages_index:
        path = page.get("path", "")
        url = page.get("url", "")
        
        if path and path.count("/") > 4:  # More than 4 segments
            deep_urls.append({"url": url, "depth": path.count("/")})
    
    if deep_urls and len(deep_urls) > pages_count * 0.2:  # More than 20% of pages
        structure_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="structure",
            severity="low",
            title="Deep URL Structure",
            description=f"{len(deep_urls)} pages ({len(deep_urls)/pages_count*100:.1f}%) have very deep URL paths.",
            affectedPages=[
                InsightAffectedPage(url=p["url"], note=f"{p.get('depth', 0)} levels deep")
                for p in deep_urls
            ]
        ))
    
    # Note: Error pages (404/410/5xx) are handled below via bad_pages to avoid duplicates
    
    # NEW: Structure - HTTPS & mobile issues
    if base_url and base_url.startswith("http://"):
        structure_issues.append(InsightIssue(
            id="structure_http_only",
            category="structure",
            severity="high",
            title="Site Not Using HTTPS",
            description="The site is served over HTTP instead of HTTPS. This is bad for security, user trust, and SEO.",
            affectedPages=[]
        ))
    
    if https_site and mixed_content_pages:
        structure_issues.append(InsightIssue(
            id="structure_mixed_content",
            category="structure",
            severity="medium",
            title="Mixed Content Detected",
            description=f"{len(mixed_content_pages)} pages reference http:// resources on an https:// site. This can cause browser warnings.",
            affectedPages=[
                InsightAffectedPage(url=p["url"], note=p.get("note"))
                for p in mixed_content_pages
            ]
        ))
    
    if no_viewport_pages:
        structure_issues.append(InsightIssue(
            id="structure_no_viewport",
            category="structure",
            severity="medium",
            title="Mobile Viewport Not Set",
            description=f"{len(no_viewport_pages)} pages do not declare a mobile viewport. The site may not display well on phones.",
            affectedPages=[
                InsightAffectedPage(url=p["url"], note=p.get("note"))
                for p in no_viewport_pages
            ]
        ))
    
    # Add issues for broken internal links
    # Only includes links that were actually crawled and returned 404/410/5xx
    if pages_with_broken_internal_links:
        total_broken_links = len(broken_internal_links_global)
        structure_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="structure",
            severity="high" if total_broken_links > 10 else "medium",
            title="Broken Internal Links",
            description=f"{len(pages_with_broken_internal_links)} pages contain {total_broken_links} broken internal link(s) (returned 404, 410, or server errors).",
            affectedPages=[
                InsightAffectedPage(
                    url=p["url"],
                    note=f"{p.get('broken_count', 0)} broken link(s)"
                )
                for p in pages_with_broken_internal_links  # Show all pages
            ]
        ))
    
    # Add issues for bad pages (404/5xx)
    if bad_pages:
        # Group by status code for better messaging
        status_404 = [p for p in bad_pages if p.get("status_code") == 404]
        status_410 = [p for p in bad_pages if p.get("status_code") == 410]
        status_5xx = [p for p in bad_pages if p.get("status_code") and p.get("status_code") >= 500]
        
        if status_404 or status_410 or status_5xx:
            status_summary = []
            if status_404:
                status_summary.append(f"{len(status_404)} 404")
            if status_410:
                status_summary.append(f"{len(status_410)} 410")
            if status_5xx:
                status_summary.append(f"{len(status_5xx)} 5xx")
            
            structure_issues.append(InsightIssue(
                id=str(uuid.uuid4()),
                category="structure",
                severity="high",
                title="Not Found / Error Pages Crawled",
                description=f"{len(bad_pages)} URL(s) returned error responses ({', '.join(status_summary)}).",
                affectedPages=[
                    InsightAffectedPage(
                        url=p["url"],
                        note=f"Status {p.get('status_code')}"
                    )
                    for p in bad_pages  # Show all pages
                ]
            ))
    
    # Compute category scores (0-100) - stricter penalties so 100/100 is rare
    performance_score = 100
    
    # Penalize average load time
    if avg_load_ms > 1000:
        performance_score -= 5
    if avg_load_ms > 2000:
        performance_score -= 10
    
    # Penalize P90 load time
    if p90_load_ms > 2000:
        performance_score -= 5
    if p90_load_ms > 3000:
        performance_score -= 10
    
    # Penalize slow pages count
    slow_count = len(slow_pages)
    if slow_count > 0:
        performance_score -= 5
    if slow_count > 3:
        performance_score -= 5
    
    # Penalize very slow pages
    if very_slow_pages:
        performance_score -= 10
    
    # Penalize max page size
    if max_page_size_kb > 1024:  # >1MB
        performance_score -= 5
    if max_page_size_kb > 2048:  # >2MB
        performance_score -= 10
    
    # NEW: Penalize pages with very large images
    if pages_with_very_large_images and len(pages_with_very_large_images) / pages_count > 0.2:
        performance_score -= 5
    
    performance_score = max(0, min(100, performance_score))
    
    # SEO scoring with stricter penalties
    seo_score = 100
    
    missing_title_ratio = len(pages_missing_title) / pages_count if pages_count else 0
    missing_desc_ratio = len(pages_missing_description) / pages_count if pages_count else 0
    missing_h1_ratio = len(pages_missing_h1) / pages_count if pages_count else 0
    broken_link_count = len(pages_with_broken_links)
    images_missing_alt_count = len(images_missing_alt)
    images_missing_alt_ratio = images_missing_alt_count / pages_count if pages_count else 0
    
    if missing_title_ratio >= 0.1:  # 10% or more
        seo_score -= 10
    if missing_title_ratio > 0.3:
        seo_score -= 10
    
    if missing_desc_ratio >= 0.1:  # 10% or more
        seo_score -= 10
    if missing_desc_ratio > 0.3:
        seo_score -= 10
    
    if missing_h1_ratio >= 0.1:  # 10% or more
        seo_score -= 5
    if missing_h1_ratio > 0.3:
        seo_score -= 10
    
    if broken_link_count > 0:
        seo_score -= 5
    if broken_link_count > 10:
        seo_score -= 10
    
    # Penalize images missing alt text
    if images_missing_alt_ratio >= 0.3:  # 30% or more pages have images without alt
        seo_score -= 10
    elif images_missing_alt_ratio >= 0.1:  # 10% or more pages have images without alt
        seo_score -= 5
    elif images_missing_alt_count > 0:  # Any pages with missing alt text
        seo_score -= 2
    
    # NEW: Penalize indexability issues
    if noindex_pages and len(noindex_pages) / pages_count > 0.3:
        seo_score -= 5
    
    if not robots_present:
        seo_score -= 2
    
    if not sitemap_present:
        seo_score -= 2
    
    seo_score = max(0, min(100, seo_score))
    
    # Content scoring with page-type aware penalties
    # Only penalize based on important content pages
    important_content_pages = [
        p for p in pages_index 
        if p.get("page_type") in ["article", "landing", "generic"] or not p.get("page_type")
    ]
    important_pages_count = len(important_content_pages) if important_content_pages else pages_count
    
    # Calculate avg words for important pages only
    important_word_counts = [
        p.get("words", 0) for p in important_content_pages 
        if isinstance(p.get("words"), (int, float))
    ]
    avg_words_important_pages = (
        sum(important_word_counts) / len(important_word_counts) 
        if important_word_counts else avg_words_per_page
    )
    
    # Initialize content_score
    content_score = 100
    
    # Only penalize based on important content pages
    if important_pages_count > 0:
        thin_very_ratio = len(pages_very_thin_content) / important_pages_count
        thin_ratio = len(pages_thin_content) / important_pages_count
        
        if thin_very_ratio > 0.1:
            content_score -= 10
        if thin_very_ratio > 0.3:
            content_score -= 10
        
        if thin_ratio > 0.2:
            content_score -= 5
        if thin_ratio > 0.4:
            content_score -= 10
        
        # Use important pages average for scoring
        if avg_words_important_pages < 200:
            content_score -= 5
        if avg_words_important_pages < 100:
            content_score -= 10
    
    content_score = max(0, min(100, content_score))
    
    # Structure scoring with stricter penalties
    structure_score = 100
    
    if not nav_items or len(nav_items) == 0:
        structure_score -= 15
    
    if not footer_contact.get("email") and not footer_contact.get("phone") and not footer_socials:
        structure_score -= 10
    
    # Penalize error pages (404/410/5xx)
    bad_pages_count = len(bad_pages)
    if bad_pages_count > 0:
        structure_score -= 5
    if bad_pages_count > 5:
        structure_score -= 10
    
    if deep_urls and len(deep_urls) > 0:
        structure_score -= 5
    
    # NEW: Penalize HTTPS and mobile issues
    if not https_site:
        structure_score -= 10
    
    if mixed_content_pages:
        structure_score -= 5
    
    if no_viewport_pages and len(no_viewport_pages) / pages_count > 0.3:
        structure_score -= 5
    
    structure_score = max(0, min(100, structure_score))
    
    # Calculate new context-aware metrics
    pages_dir = os.path.join(run_dir, "pages")
    content_depth_score = calculate_content_depth_score(
        avg_words_per_page, pages_count, pages_dir, pages_index
    )
    nav_type = determine_nav_type(nav_items, pages_count, pages_dir, pages_index)
    crawlability_score = calculate_crawlability_score(
        pages_count, pages_dir, pages_index, base_url
    )
    
    # Optionally incorporate content_depth_score into content_score
    # Blend: 70% existing content_score, 30% content_depth_score
    content_score_blended = round(
        0.7 * content_score + 0.3 * (content_depth_score / 100 * 100)
    )
    content_score = max(0, min(100, content_score_blended))
    
    # Optionally incorporate crawlability_score into structure_score
    # Blend: 80% existing structure_score, 20% crawlability_score
    structure_score_blended = round(
        0.8 * structure_score + 0.2 * (crawlability_score / 100 * 100)
    )
    structure_score = max(0, min(100, structure_score_blended))
    
    # Build category scores
    categories = [
        InsightCategoryScore(
            category="performance",
            score=performance_score,
            issues=performance_issues
        ),
        InsightCategoryScore(
            category="seo",
            score=seo_score,
            issues=seo_issues
        ),
        InsightCategoryScore(
            category="content",
            score=content_score,
            issues=content_issues
        ),
        InsightCategoryScore(
            category="structure",
            score=structure_score,
            issues=structure_issues
        )
    ]
    
    # Overall score
    overall_score = round((performance_score + seo_score + content_score + structure_score) / 4)
    
    # Update stats with bad pages and broken links counts
    stats.badPagesCount = len(bad_pages)
    stats.brokenInternalLinksCount = len(broken_internal_links_global)
    
    return InsightReport(
        runId=run_id,
        baseUrl=base_url,
        overallScore=overall_score,
        categories=categories,
        stats=stats,
        contentDepthScore=content_depth_score,
        navType=nav_type,
        crawlabilityScore=crawlability_score,
        perfMode=perf_mode,
        performanceConsistency=performance_consistency if performance_consistency != "unknown" else None,
        consistencyNote=consistency_note if consistency_note else None
    )

