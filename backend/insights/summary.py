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
    
    avg_load_ms = sum(load_times) / len(load_times) if load_times else 0.0
    median_load_ms = median(load_times) if load_times else 0.0
    p90_load_ms = percentile(load_times, 90) if load_times else 0.0
    p95_load_ms = percentile(load_times, 95) if load_times else 0.0
    
    slow_pages = [p for p in pages_index if p.get("loadTimeMs") and p.get("loadTimeMs", 0) > 1500]
    very_slow_pages = [p for p in pages_index if p.get("loadTimeMs") and p.get("loadTimeMs", 0) > 3000]
    
    avg_page_size_kb = (sum(page_sizes) / len(page_sizes) / 1024) if page_sizes else 0.0
    max_page_size_kb = (max(page_sizes) / 1024) if page_sizes else 0.0
    
    # Content stats
    total_words = sum(word_counts)
    avg_words_per_page = total_words / pages_count if pages_count > 0 else 0.0
    total_media_items = sum(media_counts)
    avg_media_per_page = total_media_items / pages_count if pages_count > 0 else 0.0
    
    # Build stats
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
        maxPageSizeKb=round(max_page_size_kb, 2)
    )
    
    # Analyze pages for SEO/content issues
    pages_dir = os.path.join(run_dir, "pages")
    seo_issues: List[InsightIssue] = []
    content_issues: List[InsightIssue] = []
    
    # Store page data with metadata for building affected pages
    pages_missing_title = []
    pages_missing_description = []
    pages_missing_h1 = []
    pages_thin_content = []  # < 150 words with word count
    pages_very_thin_content = []  # < 50 words with word count
    pages_with_broken_links = []
    images_missing_alt = []
    
    # New checks: indexability, mobile, HTTPS, images
    noindex_pages = []
    no_viewport_pages = []
    mixed_content_pages = []
    pages_with_very_large_images = []
    pages_with_large_images = []
    pages_with_modern_images = []
    
    # Create a mapping of URL to page data from pages_index for quick lookup
    pages_index_map = {p.get("url", ""): p for p in pages_index}
    
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
                
                # Check for thin content
                if word_count < 50:
                    pages_very_thin_content.append({"url": url, "word_count": word_count})
                elif word_count < 150:
                    pages_thin_content.append({"url": url, "word_count": word_count})
                
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
    
    # Build content issues
    if pages_very_thin_content:
        content_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="content",
            severity="high",
            title="Very Thin Content Pages",
            description=f"{len(pages_very_thin_content)} pages have less than 50 words.",
            affectedPages=[
                InsightAffectedPage(url=p["url"], note=f"{p.get('word_count', 0)} words")
                for p in pages_very_thin_content
            ]
        ))
    
    if pages_thin_content:
        content_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="content",
            severity="medium",
            title="Thin Content Pages",
            description=f"{len(pages_thin_content)} pages have less than 150 words.",
            affectedPages=[
                InsightAffectedPage(url=p["url"], note=f"{p.get('word_count', 0)} words")
                for p in pages_thin_content
            ]
        ))
    
    if avg_words_per_page < 200:
        content_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="content",
            severity="low",
            title="Low Average Word Count",
            description=f"Average words per page ({avg_words_per_page:.0f}) is below recommended 200 words.",
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
    
    # Check URL depth (count path segments) and error status pages
    deep_urls = []
    error_status_pages = []
    for page in pages_index:
        path = page.get("path", "")
        url = page.get("url", "")
        status = page.get("status") or page.get("status_code")
        
        if path and path.count("/") > 4:  # More than 4 segments
            deep_urls.append({"url": url, "depth": path.count("/")})
        
        if status and status >= 400:
            error_status_pages.append({"url": url, "status": status})
    
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
    
    if error_status_pages:
        structure_issues.append(InsightIssue(
            id=str(uuid.uuid4()),
            category="structure",
            severity="high",
            title="Error Pages (4xx/5xx)",
            description=f"{len(error_status_pages)} pages returned 4xx/5xx status codes.",
            affectedPages=[
                InsightAffectedPage(url=p["url"], note=str(p.get("status", "")))
                for p in error_status_pages
            ]
        ))
    
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
    
    if missing_title_ratio > 0.1:  # 10%
        seo_score -= 10
    if missing_title_ratio > 0.3:
        seo_score -= 10
    
    if missing_desc_ratio > 0.1:
        seo_score -= 10
    if missing_desc_ratio > 0.3:
        seo_score -= 10
    
    if missing_h1_ratio > 0.1:
        seo_score -= 5
    if missing_h1_ratio > 0.3:
        seo_score -= 10
    
    if broken_link_count > 0:
        seo_score -= 5
    if broken_link_count > 10:
        seo_score -= 10
    
    # NEW: Penalize indexability issues
    if noindex_pages and len(noindex_pages) / pages_count > 0.3:
        seo_score -= 5
    
    if not robots_present:
        seo_score -= 2
    
    if not sitemap_present:
        seo_score -= 2
    
    seo_score = max(0, min(100, seo_score))
    
    # Content scoring with stricter penalties
    content_score = 100
    
    thin_very_ratio = len(pages_very_thin_content) / pages_count if pages_count else 0
    thin_ratio = len(pages_thin_content) / pages_count if pages_count else 0
    
    if thin_very_ratio > 0.1:
        content_score -= 10
    if thin_very_ratio > 0.3:
        content_score -= 10
    
    if thin_ratio > 0.2:
        content_score -= 5
    if thin_ratio > 0.4:
        content_score -= 10
    
    if avg_words_per_page < 200:
        content_score -= 5
    if avg_words_per_page < 100:
        content_score -= 10
    
    content_score = max(0, min(100, content_score))
    
    # Structure scoring with stricter penalties
    structure_score = 100
    
    if not nav_items or len(nav_items) == 0:
        structure_score -= 15
    
    if not footer_contact.get("email") and not footer_contact.get("phone") and not footer_socials:
        structure_score -= 10
    
    error_status_pages_count = len(error_status_pages)
    if error_status_pages_count > 0:
        structure_score -= 5
    if error_status_pages_count > 5:
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
    
    return InsightReport(
        runId=run_id,
        baseUrl=base_url,
        overallScore=overall_score,
        categories=categories,
        stats=stats
    )

