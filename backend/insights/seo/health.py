"""
[SEO_UNIFIED_SECTION] SEO Health checks module.
Extracts technical SEO health checks from the main summary builder.
"""
import os
import json
import uuid
from typing import List, Dict, Any, Optional
from backend.core.types import InsightIssue, InsightAffectedPage
from backend.storage.runs import RunStore


def compute_seo_health(
    run_store: RunStore,
    pages_index: List[Dict[str, Any]],
    pages_data: List[Dict[str, Any]],
    site_data: Dict[str, Any],
    pages_count: int
) -> Dict[str, Any]:
    """
    [SEO_UNIFIED_SECTION] Compute SEO health checks and score.
    
    Returns a dictionary with:
    - score: int (0-100)
    - issues: List[InsightIssue]
    """
    run_dir = run_store.run_dir
    pages_dir = os.path.join(run_dir, "pages")
    
    base_url = site_data.get("baseUrl")
    robots_present = site_data.get("robots_present", False)
    sitemap_present = site_data.get("sitemap_present", False)
    https_site = bool(base_url and base_url.startswith("https://"))
    
    seo_issues: List[InsightIssue] = []
    
    # Track SEO issues
    pages_missing_title = []
    pages_missing_description = []
    pages_missing_h1 = []
    pages_with_broken_links = []
    images_missing_alt = []
    noindex_pages = []
    no_viewport_pages = []
    mixed_content_pages = []
    
    # Create mappings for quick lookup
    pages_index_map = {p.get("url", ""): p for p in pages_index}
    status_by_url = {}
    for page in pages_index:
        url = page.get("url", "")
        status = page.get("status") or page.get("status_code")
        if url and status:
            status_by_url[url] = status
    
    if pages_data:
        for page_detail in pages_data:
            if isinstance(page_detail, dict):
                summary = page_detail.get("summary", {})
                url = summary.get("url", "")
                status = summary.get("status") or summary.get("status_code")
                if url and status:
                    status_by_url[url] = status
    
    pages_meta_map = {}
    if pages_data:
        for page_detail in pages_data:
            if isinstance(page_detail, dict):
                summary = page_detail.get("summary", {})
                url = summary.get("url", "")
                meta = page_detail.get("meta", {})
                if url:
                    pages_meta_map[url] = meta
    
    # Analyze pages
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
                
                # Check for broken links
                if broken_links:
                    broken_count = len(broken_links)
                    pages_with_broken_links.append({"url": url, "broken_count": broken_count})
                
                # Check for images missing alt text
                missing_alt_count = sum(1 for img in images if not img.get("alt") or img.get("alt", "").strip() == "")
                if missing_alt_count > 0:
                    images_missing_alt.append({"url": url, "missing_alt_count": missing_alt_count})
                
                # Check for noindex meta tag
                page_meta = pages_meta_map.get(url, {})
                robots_content = page_meta.get("robots", "")
                if isinstance(robots_content, str) and "noindex" in robots_content.lower():
                    noindex_pages.append({"url": url, "note": None})
                
                # Check for viewport meta tag
                has_viewport = bool(page_meta.get("viewport"))
                if not has_viewport:
                    no_viewport_pages.append({"url": url, "note": None})
                
                # Check for mixed content
                if https_site:
                    all_links = [l.get("href", "") for l in internal_links + external_links]
                    all_image_urls = [img.get("url", "") for img in images]
                    all_assets = all_links + all_image_urls
                    has_mixed_content = any(asset.startswith("http://") for asset in all_assets if asset)
                    if has_mixed_content:
                        mixed_content_pages.append({"url": url, "note": None})
            
            except Exception:
                continue
    
    # Build SEO issues
    if pages_missing_title:
        missing_title_pct = (len(pages_missing_title) / pages_count) * 100 if pages_count > 0 else 0
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
        missing_desc_pct = (len(pages_missing_description) / pages_count) * 100 if pages_count > 0 else 0
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
        missing_h1_pct = (len(pages_missing_h1) / pages_count) * 100 if pages_count > 0 else 0
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
    
    # Compute SEO score
    seo_score = 100
    
    missing_title_ratio = len(pages_missing_title) / pages_count if pages_count > 0 else 0
    missing_desc_ratio = len(pages_missing_description) / pages_count if pages_count > 0 else 0
    missing_h1_ratio = len(pages_missing_h1) / pages_count if pages_count > 0 else 0
    broken_link_count = len(pages_with_broken_links)
    images_missing_alt_count = len(images_missing_alt)
    images_missing_alt_ratio = images_missing_alt_count / pages_count if pages_count > 0 else 0
    
    if missing_title_ratio >= 0.1:
        seo_score -= 10
    if missing_title_ratio > 0.3:
        seo_score -= 10
    
    if missing_desc_ratio >= 0.1:
        seo_score -= 10
    if missing_desc_ratio > 0.3:
        seo_score -= 10
    
    if missing_h1_ratio >= 0.1:
        seo_score -= 5
    if missing_h1_ratio > 0.3:
        seo_score -= 10
    
    if broken_link_count > 0:
        seo_score -= 5
    if broken_link_count > 10:
        seo_score -= 10
    
    if images_missing_alt_ratio >= 0.3:
        seo_score -= 10
    elif images_missing_alt_ratio >= 0.1:
        seo_score -= 5
    elif images_missing_alt_count > 0:
        seo_score -= 2
    
    if noindex_pages and len(noindex_pages) / pages_count > 0.3 if pages_count > 0 else False:
        seo_score -= 5
    
    if not robots_present:
        seo_score -= 2
    
    if not sitemap_present:
        seo_score -= 2
    
    seo_score = max(0, min(100, seo_score))
    
    return {
        'score': seo_score,
        'issues': seo_issues
    }





