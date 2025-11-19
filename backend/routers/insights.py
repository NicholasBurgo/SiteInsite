"""
Insights API routes for Website Insight Reports.
"""
import os
import io
import json
import asyncio
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import pdfkit
from backend.core.types import InsightReport, ComparePayload, ComparisonReport, ComparedSite, ComparisonRow
from backend.storage.runs import RunStore
from backend.insights.summary import build_insight_report
from backend.insights.comparison import generate_opportunities
from backend.pdf_config import get_pdfkit_config
from backend.routers.runs import manager as run_manager
from backend.core.types import StartRunRequest

router = APIRouter()

@router.get("/api/insights/{run_id}/summary", response_model=InsightReport)
async def get_insight_summary(run_id: str) -> InsightReport:
    """
    Get comprehensive Website Insight Report for a run.
    
    This endpoint analyzes all run data and generates a detailed insight report
    covering performance, SEO, content quality, and site structure.
    
    **Example Response:**
    ```json
    {
      "runId": "1761075695",
      "baseUrl": "https://example.com",
      "overallScore": 75,
      "categories": [
        {
          "category": "performance",
          "score": 80,
          "issues": [
            {
              "id": "issue-1",
              "category": "performance",
              "severity": "high",
              "title": "Very Slow Pages",
              "description": "3 pages take more than 3000ms to load.",
              "affectedPages": ["https://example.com/slow-page"]
            }
          ]
        }
      ],
      "stats": {
        "pagesCount": 15,
        "totalWords": 12500,
        "avgWordsPerPage": 833.33,
        "totalMediaItems": 45,
        "avgMediaPerPage": 3.0,
        "statusCounts": {"200": 14, "404": 1},
        "avgLoadMs": 1250.5,
        "medianLoadMs": 1100.0,
        "p90LoadMs": 2000.0,
        "p95LoadMs": 2500.0,
        "slowPagesCount": 3,
        "verySlowPagesCount": 1,
        "avgPageSizeKb": 450.5,
        "maxPageSizeKb": 1200.0
      }
    }
    ```
    """
    try:
        run_store = RunStore(run_id)
        if not os.path.exists(run_store.run_dir):
            raise HTTPException(status_code=404, detail="Run not found")
        
        return build_insight_report(run_store, run_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insight report: {str(e)}")

def generate_comparison_rows_for_pdf(primary_report: InsightReport, competitor_reports: list[InsightReport]) -> list[ComparisonRow]:
    """
    Generate comparison rows for PDF export when competitors are provided.
    Compares primary report against the first competitor (or aggregates if multiple).
    """
    if not competitor_reports:
        return []
    
    # Use first competitor for comparison (can extend to multiple later)
    competitor = competitor_reports[0]
    comparisons = []
    
    def get_category_score(r: InsightReport, category: str) -> float:
        cat = next((c for c in r.categories if c.category == category), None)
        return float(cat.score) if cat else 0.0
    
    # Overall Score
    primary_overall = float(primary_report.overallScore)
    comp_overall = float(competitor.overallScore)
    diff_overall = primary_overall - comp_overall
    comparisons.append(ComparisonRow(
        metric="overall_score",
        label="Overall Score",
        primaryValue=round(primary_overall, 1),
        competitorValue=round(comp_overall, 1),
        difference=round(diff_overall, 1),
        direction="better" if diff_overall > 5 else "worse" if diff_overall < -5 else "neutral",
        verdict="Slightly ahead overall" if diff_overall > 5 else "Slightly behind overall" if diff_overall < -5 else "Similar overall",
        category="overall"
    ))
    
    # Category Scores
    for category in ["performance", "seo", "content", "structure"]:
        primary_score = get_category_score(primary_report, category)
        comp_score = get_category_score(competitor, category)
        diff = primary_score - comp_score
        
        if abs(diff) < 3:
            verdict = f"Similar {category}"
            direction = "neutral"
        elif diff > 10:
            verdict = f"Stronger {category}"
            direction = "better"
        elif diff > 0:
            verdict = f"Slightly ahead in {category}"
            direction = "better"
        elif diff < -10:
            verdict = f"{category.capitalize()} lags behind"
            direction = "worse"
        else:
            verdict = f"Slightly behind in {category}"
            direction = "worse"
        
        comparisons.append(ComparisonRow(
            metric=f"{category}_score",
            label=category.capitalize(),
            primaryValue=round(primary_score, 1),
            competitorValue=round(comp_score, 1),
            difference=round(diff, 1),
            direction=direction,
            verdict=verdict,
            category=category
        ))
    
    # Performance Metrics
    primary_load = primary_report.stats.avgLoadMs
    comp_load = competitor.stats.avgLoadMs
    load_diff = primary_load - comp_load
    comparisons.append(ComparisonRow(
        metric="avg_load_time_ms",
        label="Avg Load Time",
        primaryValue=round(primary_load, 0),
        competitorValue=round(comp_load, 0),
        difference=round(load_diff, 0),
        direction="worse" if load_diff > 200 else "better" if load_diff < -200 else "neutral",
        verdict=f"You're {abs(load_diff):.0f}ms slower" if load_diff > 200 else f"You're {abs(load_diff):.0f}ms faster" if load_diff < -200 else "Similar load times",
        category="performance"
    ))
    
    # Content Depth Score
    if primary_report.contentDepthScore is not None and competitor.contentDepthScore is not None:
        primary_depth = primary_report.contentDepthScore
        comp_depth = competitor.contentDepthScore
        depth_diff = primary_depth - comp_depth
        comparisons.append(ComparisonRow(
            metric="content_depth_score",
            label="Content Depth",
            primaryValue=round(primary_depth, 1),
            competitorValue=round(comp_depth, 1),
            difference=round(depth_diff, 1),
            direction="worse" if depth_diff < -5 else "better" if depth_diff > 5 else "neutral",
            verdict="Needs richer content" if depth_diff < -5 else "Stronger content depth" if depth_diff > 5 else "Similar content depth",
            category="content"
        ))
    
    # Navigation Type
    if primary_report.navType and competitor.navType:
        nav_same = primary_report.navType == competitor.navType
        comparisons.append(ComparisonRow(
            metric="nav_type",
            label="Navigation Type",
            primaryValue=primary_report.navType,
            competitorValue=competitor.navType,
            difference=None,
            direction="different" if not nav_same else "neutral",
            verdict="Different structure types" if not nav_same else "Similar navigation structure",
            category="structure"
        ))
    
    # Crawlability Score
    if primary_report.crawlabilityScore is not None and competitor.crawlabilityScore is not None:
        primary_crawl = primary_report.crawlabilityScore
        comp_crawl = competitor.crawlabilityScore
        crawl_diff = primary_crawl - comp_crawl
        comparisons.append(ComparisonRow(
            metric="crawlability_score",
            label="Crawlability",
            primaryValue=round(primary_crawl, 1),
            competitorValue=round(comp_crawl, 1),
            difference=round(crawl_diff, 1),
            direction="worse" if crawl_diff < -10 else "better" if crawl_diff > 10 else "neutral",
            verdict="Bots find them easier" if crawl_diff < -10 else "Better bot traversal" if crawl_diff > 10 else "Similar crawlability",
            category="structure"
        ))
    
    # Pages count
    pages_diff = primary_report.stats.pagesCount - competitor.stats.pagesCount
    comparisons.append(ComparisonRow(
        metric="pages_count",
        label="Total Pages",
        primaryValue=primary_report.stats.pagesCount,
        competitorValue=competitor.stats.pagesCount,
        difference=pages_diff,
        direction="better" if pages_diff > 0 else "worse" if pages_diff < 0 else "neutral",
        verdict=f"{abs(pages_diff)} {'more' if pages_diff > 0 else 'fewer'} pages" if pages_diff != 0 else "Similar page count",
        category="content"
    ))
    
    # Total Words
    words_diff = primary_report.stats.totalWords - competitor.stats.totalWords
    comparisons.append(ComparisonRow(
        metric="total_words",
        label="Total Words",
        primaryValue=primary_report.stats.totalWords,
        competitorValue=competitor.stats.totalWords,
        difference=words_diff,
        direction="better" if words_diff > 0 else "worse" if words_diff < 0 else "neutral",
        verdict=f"{abs(words_diff):,} {'more' if words_diff > 0 else 'fewer'} words" if words_diff != 0 else "Similar word count",
        category="content"
    ))
    
    return comparisons


@router.get("/api/insights/{run_id}/export")
async def export_insight_report_pdf(
    run_id: str, 
    competitor_run_ids: str = Query(None, description="Comma-separated list of competitor run IDs to include in PDF")
):
    """
    Generate a client-friendly PDF Website Insight Report for this run.
    Optionally include competitor summaries if competitor_run_ids is provided (comma-separated).
    """
    try:
        run_store = RunStore(run_id)
        if not os.path.exists(run_store.run_dir):
            raise HTTPException(status_code=404, detail="Run not found")
        
        report = build_insight_report(run_store, run_id)
        generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        
        # Load competitor reports if provided
        competitor_reports = []
        if competitor_run_ids:
            run_id_list = [rid.strip() for rid in competitor_run_ids.split(',') if rid.strip()]
            for comp_run_id in run_id_list:
                try:
                    comp_store = RunStore(comp_run_id)
                    if os.path.exists(comp_store.run_dir):
                        comp_report = build_insight_report(comp_store, comp_run_id)
                        competitor_reports.append(comp_report)
                except Exception as e:
                    # Skip failed competitor reports, but continue
                    print(f"Warning: Failed to load competitor report {comp_run_id}: {e}")
                    continue
        
        # Generate comparison rows if competitors exist
        comparison_rows = []
        if competitor_reports:
            comparison_rows = generate_comparison_rows_for_pdf(report, competitor_reports)
        
        # Compute top fixes: sort by severity (high > medium > low) then affectedPages length
        def severity_rank(sev: str) -> int:
            if sev == "high":
                return 3
            if sev == "medium":
                return 2
            return 1
        
        all_issues = []
        for cat in report.categories:
            for issue in cat.issues:
                all_issues.append(issue)
        
        all_issues_sorted = sorted(
            all_issues,
            key=lambda i: (severity_rank(i.severity), len(i.affectedPages)),
            reverse=True,
        )
        top_issues = all_issues_sorted[:5]
        
        # Helper function to format values for display
        def format_value(val, is_time=False):
            if val is None:
                return "—"
            if isinstance(val, (int, float)):
                if is_time:
                    return f"{val:.0f} ms"
                return f"{val:,.0f}" if isinstance(val, float) else f"{val:,}"
            return str(val)
        
        def format_difference(diff, is_time=False):
            if diff is None:
                return "—"
            if isinstance(diff, (int, float)):
                sign = "+" if diff > 0 else ""
                if is_time:
                    return f"{sign}{diff:.0f} ms"
                return f"{sign}{diff:,.0f}" if isinstance(diff, float) else f"{sign}{diff:,}"
            return str(diff)
        
        # Load pages_index.json for page type breakdown
        pages_index_file = os.path.join(run_store.run_dir, "pages_index.json")
        pages_index = []
        if os.path.exists(pages_index_file):
            with open(pages_index_file, 'r') as f:
                pages_index = json.load(f)
        
        # Load meta.json for crawl date/time
        meta_file = os.path.join(run_store.run_dir, "meta.json")
        meta_data = {}
        crawl_date_time = generated_at  # Fallback to generated_at
        if os.path.exists(meta_file):
            try:
                with open(meta_file, 'r') as f:
                    meta_data = json.load(f)
                    started_at = meta_data.get("started_at")
                    if started_at:
                        try:
                            crawl_date_time = datetime.fromtimestamp(float(started_at)).strftime("%Y-%m-%d %H:%M UTC")
                        except (ValueError, TypeError, OSError):
                            crawl_date_time = generated_at
            except Exception:
                crawl_date_time = generated_at
        
        # Calculate page type breakdown for executive summary
        page_type_counts = {}
        if pages_index and isinstance(pages_index, list):
            for page in pages_index:
                if isinstance(page, dict):
                    page_type = page.get("page_type", "generic")
                    page_type_counts[page_type] = page_type_counts.get(page_type, 0) + 1
        
        # Build appendix key to letter mapping (will be populated after collecting all data)
        appendix_key_to_letter = {}
        
        # Helper function to get appendix letter for a key
        def get_appendix_letter(appendix_key):
            """Get the appendix letter for a given appendix key."""
            if not appendix_key or appendix_key not in appendix_key_to_letter:
                return None
            return appendix_key_to_letter[appendix_key]
        
        # Helper function to format URLs with examples and "more" note
        def format_urls_with_examples(affected_pages, max_examples=3, appendix_ref=None):
            """Format URLs showing only examples, with note about remaining pages."""
            if not affected_pages:
                return ""
            
            total_count = len(affected_pages)
            examples = affected_pages[:max_examples]
            remaining = total_count - len(examples)
            
            urls_html = ""
            for p in examples:
                note_part = f' <span class="muted">({p.note})</span>' if p.note else ''
                urls_html += f'<div class="url-example"><span class="url-text">• {p.url}</span>{note_part}</div>'
            
            if remaining > 0:
                appendix_text = f" (see Appendix {appendix_ref})" if appendix_ref else " (see Appendix)"
                urls_html += f'<div class="more-pages-note">(+ {remaining} more page{"s" if remaining > 1 else ""}{appendix_text})</div>'
            
            return urls_html
        
        # Helper function to get fix recommendation based on issue
        def get_fix_recommendation(issue_title, issue_category):
            """Return recommended fix text for common issues."""
            title_lower = issue_title.lower()
            
            if "missing h1" in title_lower:
                return "Ensure each page has exactly one <h1> describing the page's core topic."
            elif "missing title" in title_lower:
                return "Add unique, descriptive <title> tags to all pages. Include brand name and page purpose."
            elif "missing meta description" in title_lower:
                return "Add meta descriptions (150-160 characters) that summarize page content and include keywords."
            elif "very slow" in title_lower or "slow pages" in title_lower:
                return "Optimize images, minimize JavaScript, enable compression, and consider a CDN. Target <2000ms load time."
            elif "thin content" in title_lower:
                return "Add more substantive content (aim for 300+ words on important pages). Include headings, paragraphs, and relevant keywords."
            elif "broken" in title_lower and "link" in title_lower:
                return "Update or remove broken links. Use 301 redirects for moved pages, or return 410 Gone for permanently removed content."
            elif "not found" in title_lower or "404" in title_lower:
                return "Fix or redirect 404 pages. Use 301 redirects to relevant pages or return proper 404 pages with helpful navigation."
            elif "noindex" in title_lower:
                return "Review noindex tags. Remove them from pages you want indexed, or ensure they're intentional for duplicate/privacy pages."
            elif "viewport" in title_lower:
                return "Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"> to all pages."
            elif "mixed content" in title_lower:
                return "Update all http:// URLs to https:// for images, scripts, and stylesheets on HTTPS pages."
            elif "images missing alt" in title_lower:
                return "Add descriptive alt text to all images. Use keywords naturally and describe what the image shows."
            elif "large images" in title_lower:
                return "Compress images (use WebP/AVIF formats), resize to appropriate dimensions, and lazy-load below-the-fold images."
            elif "navigation not detected" in title_lower:
                return "Add a clear navigation menu with links to main sections. Use semantic HTML (<nav>) and ensure it's crawlable."
            elif "https" in title_lower and "not using" in title_lower:
                return "Migrate site to HTTPS. Obtain SSL certificate and configure server to serve all pages over HTTPS."
            else:
                return "Review the issue details and implement appropriate fixes based on best practices."
        
        # Collect all URLs for appendix with proper categorization
        appendix_data = {
            "very_slow_pages": [],
            "slow_pages": [],
            "thin_content_pages": [],
            "very_thin_content_pages": [],
            "low_text_catalog_pages": [],
            "broken_internal_links": [],
            "error_pages": [],
            "pages_with_broken_links": [],
            "missing_h1": [],
            "missing_title": [],
            "missing_description": [],
            "images_missing_alt": [],
            "noindex_pages": [],
            "no_viewport_pages": [],
            "mixed_content_pages": []
        }
        
        # Map issue titles to appendix categories
        appendix_mapping = {
            "very slow": "very_slow_pages",
            "slow pages": "slow_pages",
            "thin content": "thin_content_pages",
            "very thin content": "very_thin_content_pages",
            "low-text": "low_text_catalog_pages",
            "low text": "low_text_catalog_pages",
            "broken internal links": "broken_internal_links",
            "broken links": "pages_with_broken_links",
            "not found": "error_pages",
            "error pages": "error_pages",
            "404": "error_pages",
            "missing h1": "missing_h1",
            "missing page titles": "missing_title",
            "missing meta descriptions": "missing_description",
            "images missing alt": "images_missing_alt",
            "noindex": "noindex_pages",
            "viewport": "no_viewport_pages",
            "mixed content": "mixed_content_pages"
        }
        
        # Build HTML report with new structure
        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>SiteInsite Report – {report.baseUrl or report.runId}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    :root {{
      --brand-bg: #0D0F12;
      --brand-text: #E6EBF0;
      --accent: #4A90E2;
      --accent-alt: #A8C5DA;
      --neutral-light: #F4F5F7;
      --neutral-dark: #1F2328;
      --good: #00C853;
      --bad: #D32F2F;
      --neutral: #9CA3AF;
    }}
    body {{
      font-family: Inter, sans-serif;
      background: white;
      color: #0D0F12;
      margin: 48px;
      font-size: 12px;
      font-weight: 400;
    }}
    h1, h2, h3, h4 {{
      font-family: Inter, sans-serif;
      font-weight: 700;
      color: #0D0F12;
    }}
    h1 {{
      font-size: 24px;
      margin-bottom: 16px;
    }}
    h2 {{
      border-left: 6px solid #A8C5DA;
      padding-left: 14px;
      margin-top: 36px;
      margin-bottom: 12px;
      font-size: 20px;
      font-weight: bold;
      font-family: Inter, sans-serif;
      color: #0D0F12;
    }}
    h3 {{
      font-size: 16px;
      margin-top: 20px;
      margin-bottom: 8px;
      color: #0D0F12;
    }}
    h4 {{
      font-size: 14px;
      margin-top: 16px;
      margin-bottom: 8px;
      color: #0D0F12;
    }}
    .muted {{
      color: var(--neutral);
      font-size: 11px;
    }}
    .section {{
      margin-bottom: 32px;
      page-break-inside: avoid;
    }}
    .card {{
      background: #F4F5F7;
      padding: 13px;
      margin-bottom: 8px;
      border-radius: 8px;
      border: 1px solid #E5E7EB;
      color: #0D0F12;
    }}
    .card strong {{
      color: #0D0F12;
      font-weight: 700;
    }}
    .score-big {{
      font-size: 32px;
      font-weight: 700;
      color: #0D0F12;
      font-family: Inter, sans-serif;
    }}
    .pill {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 600;
      color: white;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 12px;
    }}
    th, td {{
      padding: 7px;
      text-align: left;
      border-bottom: 1px solid #E5E7EB;
      color: #0D0F12;
    }}
    th {{
      background: #F4F5F7;
      color: #0D0F12;
      font-weight: 700;
      border-bottom: 2px solid #E5E7EB;
    }}
    tr:nth-child(even) {{
      background: #F9FAFB;
    }}
    tr:nth-child(odd) {{
      background: #FFFFFF;
    }}
    .text-right {{
      text-align: right;
    }}
    .text-center {{
      text-align: center;
    }}
    .badge-good {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 9999px;
      font-size: 10px;
      color: white;
      background: #00C853;
      font-weight: 600;
    }}
    .badge-bad {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 9999px;
      font-size: 10px;
      color: white;
      background: #D32F2F;
      font-weight: 600;
    }}
    .badge-neutral {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 9999px;
      font-size: 10px;
      color: #0D0F12;
      background: #A8C5DA;
      font-weight: 600;
    }}
    ul {{
      padding-left: 1.25rem;
      margin: 8px 0;
      color: #0D0F12;
    }}
    li {{
      margin-bottom: 6px;
      color: #0D0F12;
    }}
    .report-info {{
      color: var(--neutral);
      font-size: 11px;
      margin-top: 16px;
    }}
    .score-section {{
      margin-top: 16px;
    }}
    .url-text {{
      font-size: 10px;
      color: #6B7280;
      line-height: 1.4;
      font-weight: 400;
    }}
    .url-example {{
      margin-top: 4px;
      margin-left: 16px;
    }}
    .more-pages-note {{
      font-size: 10px;
      color: #6B7280;
      font-style: italic;
      margin-top: 4px;
      margin-left: 16px;
    }}
    .appendix-section {{
      page-break-before: always;
      margin-top: 40px;
    }}
    .appendix-list {{
      margin-top: 12px;
      margin-bottom: 24px;
    }}
    .appendix-list li {{
      margin-bottom: 4px;
      font-size: 10px;
      color: #6B7280;
    }}
    .severity {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 600;
      color: white;
      margin-left: 8px;
    }}
    .severity.high {{
      background: #D32F2F;
    }}
    .severity.medium {{
      background: #FF9800;
    }}
    .severity.low {{
      background: #4A90E2;
    }}
    .severity.informational {{
      background: #9CA3AF;
    }}
    .issue-block {{
      margin-bottom: 20px;
      padding-bottom: 16px;
      border-bottom: 1px solid #E5E7EB;
    }}
    .issue-block:last-child {{
      border-bottom: none;
    }}
    .why-it-matters {{
      margin-top: 8px;
      margin-bottom: 8px;
      font-size: 11px;
      color: #6B7280;
    }}
    .fix-recommendation {{
      margin-top: 8px;
      padding: 8px;
      background: #F9FAFB;
      border-left: 3px solid #4A90E2;
      font-size: 11px;
      color: #0D0F12;
    }}
    .fix-recommendation strong {{
      color: #0D0F12;
      font-weight: 700;
    }}
    .opportunity-card {{
      background: #F4F5F7;
      padding: 16px;
      margin-bottom: 12px;
      border-radius: 8px;
      border: 1px solid #E5E7EB;
      border-left: 4px solid #4A90E2;
    }}
    .opportunity-card h4 {{
      margin-top: 0;
      margin-bottom: 8px;
      font-size: 14px;
    }}
    .executive-summary {{
      background: #F9FAFB;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 24px;
      border: 1px solid #E5E7EB;
    }}
    .executive-summary p {{
      margin-bottom: 12px;
      line-height: 1.6;
      color: #0D0F12;
    }}
    .page-type-table {{
      margin-top: 12px;
      margin-bottom: 16px;
    }}
    .snapshot {{
      background: #F4F5F7;
      padding: 16px;
      border-radius: 8px;
      border: 1px solid #E5E7EB;
      margin-bottom: 24px;
    }}
    .snapshot h2 {{
      margin-top: 0;
      margin-bottom: 12px;
      font-size: 18px;
      border-left: none;
      padding-left: 0;
    }}
    .snapshot h3 {{
      margin-top: 16px;
      margin-bottom: 8px;
      font-size: 14px;
    }}
    .snapshot p {{
      margin: 8px 0;
      color: #0D0F12;
    }}
    .snapshot strong {{
      color: #0D0F12;
      font-weight: 700;
    }}
    .snapshot ul {{
      margin: 8px 0;
      padding-left: 1.5rem;
    }}
    .snapshot li {{
      margin-bottom: 4px;
    }}
    .exec-summary {{
      margin-top: 12px;
      margin-bottom: 16px;
      line-height: 1.6;
      color: #0D0F12;
    }}
  </style>
</head>
<body>
  <!-- Branded Header -->
  <div style="background: #FFFFFF; padding: 32px 0; text-align: center; border-bottom: 3px solid #4A90E2; width: 100%;">
    <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iMjAwIiB2aWV3Qm94PSIwIDAgODAwIDIwMCI+CiAgPHJlY3Qgd2lkdGg9IjgwMCIgaGVpZ2h0PSIyMDAiIGZpbGw9IiNGRkZGRkYiIC8+CiAgPHRleHQgeD0iNTAlIiB5PSI1MCUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiCiAgICAgICAgZm9udC1mYW1pbHk9IkludGVyLCBzeXN0ZW0tdWksIC1hcHBsZS1zeXN0ZW0sIEJsaW5rTWFjU3lzdGVtRm9udCwgJ1NlZ29lIFVJJywgc2Fucy1zZXJpZiIKICAgICAgICBmb250LXNpemU9IjY0IiBmaWxsPSIjMEQwRjEyIiBsZXR0ZXItc3BhY2luZz0iNiI+CiAgICBOT1ZJQU4gU1RVRElPUwogIDwvdGV4dD4KPC9zdmc+Cg==" alt="NOVIAN STUDIOS" style="display: block; margin: 0 auto; max-width: 100%;" />
    <div style="margin-top: 12px; font-family: Inter, sans-serif; font-size: 14px; color: #4A90E2; letter-spacing: 0.12em;">Website Insight Report</div>
  </div>
  
  <!-- Cover / Header Section -->
  <div class="section">
    <div class="report-info">
      Site: {report.baseUrl or "Unknown"}<br />
      Run ID: {report.runId}<br />
      Generated: {generated_at}
    </div>
    <div class="score-section">
      <div class="muted">Overall Score</div>
      <div class="score-big">{report.overallScore}/100</div>
    </div>
  </div>
"""
        
        # Site Snapshot Section
        # Calculate page type counts for snapshot
        count_catalog = page_type_counts.get("catalog", 0) + page_type_counts.get("product", 0)
        count_article = page_type_counts.get("article", 0)
        count_landing = page_type_counts.get("landing", 0)
        count_other = sum(v for k, v in page_type_counts.items() if k not in ["catalog", "product", "article", "landing"])
        
        # Format performance metrics safely
        avg_load = report.stats.avgLoadMs if report.stats.avgLoadMs is not None else 0.0
        median_load = report.stats.medianLoadMs if report.stats.medianLoadMs is not None else 0.0
        p90_load = report.stats.p90LoadMs if report.stats.p90LoadMs is not None else 0.0
        perf_mode = report.perfMode or "controlled"
        consistency = report.performanceConsistency or "unknown"
        
        # Map consistency to variance label
        if consistency == "unstable":
            variance_label = "HIGH"
        elif consistency == "moderate":
            variance_label = "MODERATE"
        elif consistency == "stable":
            variance_label = "LOW"
        else:
            variance_label = "UNKNOWN"
        
        # Get pre-flight ping test results from meta.json
        preflight_info = ""
        try:
            run_store = RunStore(run_id)
            meta_file = os.path.join(run_store.run_dir, "meta.json")
            if os.path.exists(meta_file):
                with open(meta_file, 'r') as f:
                    meta_data = json.load(f)
                preflight = meta_data.get("preflight", {})
                if preflight.get("samples", 0) > 0:
                    preflight_info = f"""
      <h3>Network Baseline (RTT)</h3>
      <p><strong>Average RTT:</strong> {preflight.get('avg_rtt_ms', 0):.0f} ms</p>
      <p><strong>Min RTT:</strong> {preflight.get('min_rtt_ms', 0):.0f} ms</p>
      <p><strong>Max RTT:</strong> {preflight.get('max_rtt_ms', 0):.0f} ms</p>
      <p><strong>Samples:</strong> {preflight.get('samples', 0)}</p>
"""
        except Exception as e:
            print(f"Error loading pre-flight data: {e}")
        
        # Get JS vs Raw stats from performance_stats
        js_raw_info = ""
        try:
            # Access performance_stats from meta.json pageLoad summary
            run_store = RunStore(run_id)
            meta_file = os.path.join(run_store.run_dir, "meta.json")
            if os.path.exists(meta_file):
                with open(meta_file, 'r') as f:
                    meta_data = json.load(f)
                page_load = meta_data.get("pageLoad", {})
                perf_summary = page_load.get("summary", {})
                perf_stats = perf_summary.get("performance_stats", {})
                
                raw_stats = perf_stats.get("raw")
                js_stats = perf_stats.get("js")
                
                if raw_stats or js_stats:
                    js_raw_info = """
      <h3>JS vs Raw Benchmarks</h3>"""
                    if raw_stats:
                        js_raw_info += f"""
      <p><strong>Raw Pages:</strong> avg {raw_stats.get('average', 0):.0f} ms, p90 {raw_stats.get('p90', 0):.0f} ms, count {raw_stats.get('count', 0)}</p>"""
                    if js_stats:
                        js_raw_info += f"""
      <p><strong>JS Pages:</strong> avg {js_stats.get('average', 0):.0f} ms, p90 {js_stats.get('p90', 0):.0f} ms, count {js_stats.get('count', 0)}</p>"""
        except Exception as e:
            print(f"Error loading JS/Raw stats: {e}")
        
        # Build measurement mode note
        mode_note = ""
        if perf_mode == "controlled":
            mode_note = "Measurements taken in controlled mode (~5 Mbps simulated)."
        elif perf_mode == "realistic":
            mode_note = "Measurements taken in realistic mode (normal browser behavior)."
        else:
            mode_note = "Measurements taken in stress mode (high concurrency)."
        
        consistency_note = report.consistencyNote or ""
        if consistency_note:
            mode_note += f" {consistency_note}"
        
        html += f"""
  <!-- Site Snapshot Section -->
  <div class="section">
    <div class="snapshot">
      <h2>Site Snapshot</h2>
      <p><strong>Domain:</strong> {report.baseUrl or "Unknown"}</p>
      <p><strong>Crawl Date:</strong> {crawl_date_time}</p>
      <p><strong>Pages Crawled:</strong> {report.stats.pagesCount}</p>
      <h3>Performance Metrics</h3>
      <p><strong>Mode:</strong> {perf_mode.capitalize()}</p>
{preflight_info}
      <h3>Overall Performance</h3>
      <p><strong>Average Load:</strong> {avg_load:.0f} ms</p>
      <p><strong>Median:</strong> {median_load:.0f} ms</p>
      <p><strong>P90:</strong> {p90_load:.0f} ms</p>
      <p><strong>Min/Max:</strong> {report.stats.avgLoadMs - (report.stats.stdevLoadMs if hasattr(report.stats, 'stdevLoadMs') else 0):.0f} / {report.stats.avgLoadMs + (report.stats.stdevLoadMs if hasattr(report.stats, 'stdevLoadMs') else 0):.0f} ms</p>
      <p><strong>Variance:</strong> {variance_label}</p>
{js_raw_info}
      <p class="muted" style="margin-top: 12px; font-size: 12px; font-style: italic;">{mode_note}</p>
    </div>
  </div>
"""
        
        # Executive Summary Section
        page_type_breakdown = []
        for page_type, count in sorted(page_type_counts.items(), key=lambda x: x[1], reverse=True):
            page_type_label = page_type.replace("_", " ").title()
            page_type_breakdown.append(f"{count} {page_type_label.lower()}")
        
        page_type_summary = ", ".join(page_type_breakdown) if page_type_breakdown else "pages analyzed"
        
        # Generate top opportunities summary
        top_opportunities_summary = []
        for issue in top_issues[:3]:
            top_opportunities_summary.append(issue.title.lower())
        
        opportunities_text = ", ".join(top_opportunities_summary) if top_opportunities_summary else "various technical issues"
        
        # Generate verdict based on score
        if report.overallScore >= 80:
            verdict = "This site demonstrates strong technical foundations with room for optimization."
        elif report.overallScore >= 60:
            verdict = "This site has solid fundamentals but performance and content issues limit its potential."
        else:
            verdict = "This site requires significant improvements in performance, SEO, and content quality to compete effectively."
        
        html += f"""
  <div class="section">
    <h1>Executive Summary</h1>
    <div class="executive-summary">
      <p>
        <strong>Overall Score: {report.overallScore}/100</strong>
      </p>
      <p>
        This site has {report.stats.pagesCount} pages analyzed, with a breakdown of {page_type_summary}. 
        The analysis reveals {opportunities_text} as the primary areas for improvement.
      </p>
      <p>
        {verdict}
      </p>
    </div>
  </div>
"""
        
        # Top Opportunities Section
        if top_issues:
            # Generate executive summary paragraph based on category scores
            categories_list = report.categories if report.categories else []
            perf_score = next((cat.score for cat in categories_list if cat.category == "performance"), 0)
            content_score = next((cat.score for cat in categories_list if cat.category == "content"), 0)
            seo_score = next((cat.score for cat in categories_list if cat.category == "seo"), 0)
            structure_score = next((cat.score for cat in categories_list if cat.category == "structure"), 0)
            
            exec_summary_parts = []
            if perf_score < 60:
                exec_summary_parts.append("performance issues limit user experience")
            if content_score < 70:
                exec_summary_parts.append("content depth needs improvement")
            if seo_score < 70:
                exec_summary_parts.append("SEO fundamentals require attention")
            if structure_score > 85:
                exec_summary_parts.append("strong site structure")
            
            if exec_summary_parts:
                if len(exec_summary_parts) == 1:
                    exec_summary_text = f"This site has {exec_summary_parts[0]}. "
                elif len(exec_summary_parts) == 2:
                    exec_summary_text = f"This site has {exec_summary_parts[0]} and {exec_summary_parts[1]}. "
                else:
                    exec_summary_text = f"This site has {', '.join(exec_summary_parts[:-1])}, and {exec_summary_parts[-1]}. "
            else:
                exec_summary_text = "This site shows balanced performance across key areas. "
            
            exec_summary_text += "Focusing on the opportunities below will yield the largest benefit."
            
            html += f"""
  <div class="section">
    <h2>Top Opportunities</h2>
    <p><strong>Overall Score:</strong> {report.overallScore}/100</p>
    <p class="exec-summary">
      {exec_summary_text}
    </p>
    <p class="muted">Focus on these changes first for the biggest impact.</p>
"""
            for idx, issue in enumerate(top_issues[:5], 1):
                # Determine appendix reference
                issue_title_lower = issue.title.lower()
                appendix_ref = None
                for key, appendix_key in appendix_mapping.items():
                    if key in issue_title_lower:
                        appendix_ref = appendix_key
                        break
                
                example_urls = ""
                if issue.affectedPages:
                    # Determine appendix reference
                    issue_title_lower = issue.title.lower()
                    appendix_key_for_ref = None
                    for key, appendix_cat in appendix_mapping.items():
                        if key in issue_title_lower:
                            appendix_key_for_ref = appendix_cat
                            break
                    appendix_ref = get_appendix_letter(appendix_key_for_ref) if appendix_key_for_ref else None
                    # Show only examples (max 2 for top opportunities)
                    example_urls_html = format_urls_with_examples(issue.affectedPages, max_examples=2, appendix_ref=appendix_ref)
                    example_urls = f'<div style="margin-top: 8px;"><strong>Examples:</strong>{example_urls_html}</div>'
                
                fix_rec = get_fix_recommendation(issue.title, issue.category)
                
                html += f"""
    <div class="opportunity-card">
      <h4>{idx}. {issue.title} <span class="severity {issue.severity}">{issue.severity.title()}</span></h4>
      <div class="why-it-matters">
        <strong>Why it matters:</strong> {issue.description}
      </div>
      {example_urls}
      <div class="fix-recommendation">
        <strong>Fix Recommendation:</strong> {fix_rec}
      </div>
    </div>
"""
            html += """
  </div>
"""
        
        # First pass: Collect all URLs for appendix from all issues
        for cat in report.categories:
            for issue in cat.issues:
                issue_title_lower = issue.title.lower()
                appendix_key = None
                for key, appendix_cat in appendix_mapping.items():
                    if key in issue_title_lower:
                        appendix_key = appendix_cat
                        break
                
                if issue.affectedPages and appendix_key:
                    for p in issue.affectedPages:
                        if p.url not in appendix_data.get(appendix_key, []):
                            if appendix_key not in appendix_data:
                                appendix_data[appendix_key] = []
                            appendix_data[appendix_key].append(p.url)
        
        # Build appendix key to letter mapping based on what data we have
        appendix_sections_order = [
            "very_slow_pages",
            "slow_pages",
            "very_thin_content_pages",
            "thin_content_pages",
            "low_text_catalog_pages",
            "broken_internal_links",
            "pages_with_broken_links",
            "error_pages",
            "missing_h1",
            "missing_title",
            "missing_description",
            "images_missing_alt",
            "noindex_pages",
            "no_viewport_pages",
            "mixed_content_pages"
        ]
        
        appendix_letter = ord('A')
        for key in appendix_sections_order:
            if len(appendix_data.get(key, [])) > 0:
                appendix_key_to_letter[key] = chr(appendix_letter)
                appendix_letter += 1
        
        # Category Sections - Reorganized
        category_order = ["performance", "seo", "content", "structure"]
        category_descriptions = {
            "performance": "Page load times, image optimization, and overall site speed impact user experience and search rankings.",
            "seo": "Technical SEO elements like titles, descriptions, headings, and indexability affect search engine visibility.",
            "content": "Content depth, quality, and relevance determine how well pages rank and engage users.",
            "structure": "Site navigation, URL structure, and internal linking help search engines crawl and index your site."
        }
        
        # Separate errors & broken links into their own section
        errors_and_broken_links_issues = []
        
        for cat in report.categories:
            if cat.category not in category_order:
                continue
            
            # Get category description
            summary_text = category_descriptions.get(cat.category, "Review issues below for details.")
            
            html += f"""
  <div class="section">
    <h2>{cat.category.title()}</h2>
    <p class="muted" style="margin-top: 8px; margin-bottom: 16px;">
      {summary_text}
    </p>
    <div class="score-big" style="margin-bottom: 16px;">{cat.score}/100</div>
"""
            
            # Group issues by severity
            high_severity = [i for i in cat.issues if i.severity == "high"]
            medium_severity = [i for i in cat.issues if i.severity == "medium"]
            low_severity = [i for i in cat.issues if i.severity == "low"]
            
            # Process issues and collect for appendix
            all_category_issues = high_severity + medium_severity + low_severity
            
            for issue in all_category_issues:
                # Determine appendix category
                issue_title_lower = issue.title.lower()
                appendix_key = None
                for key, appendix_cat in appendix_mapping.items():
                    if key in issue_title_lower:
                        appendix_key = appendix_cat
                        break
                
                # Check if this is an error/broken link issue
                if ("broken" in issue_title_lower and "link" in issue_title_lower) or \
                   ("not found" in issue_title_lower or "error" in issue_title_lower or "404" in issue_title_lower):
                    errors_and_broken_links_issues.append(issue)
                    continue  # Skip adding to main category, will add to Errors section
                
                # Format affected pages (max 3-4 examples)
                affected_pages_html = ""
                if issue.affectedPages:
                    appendix_ref = get_appendix_letter(appendix_key) if appendix_key else None
                    affected_pages_html = format_urls_with_examples(issue.affectedPages, max_examples=3, appendix_ref=appendix_ref)
                    if affected_pages_html:
                        affected_pages_html = f'<div style="margin-top: 8px;"><strong>Examples:</strong>{affected_pages_html}</div>'
                
                fix_rec = get_fix_recommendation(issue.title, issue.category)
                
                html += f"""
    <div class="issue-block">
      <h3>{issue.title} <span class="severity {issue.severity}">{issue.severity.title()}</span></h3>
      <div class="why-it-matters">
        <strong>Why it matters:</strong> {issue.description}
      </div>
      {affected_pages_html}
      <div class="fix-recommendation">
        <strong>Fix Recommendation:</strong> {fix_rec}
      </div>
    </div>
"""
            
            html += """
  </div>
"""
        
        # Errors & Broken Links Section
        if errors_and_broken_links_issues:
            html += """
  <div class="section">
    <h2>Errors & Broken Links</h2>
    <p class="muted" style="margin-top: 8px; margin-bottom: 16px;">
      Broken links and error pages hurt user experience and can negatively impact SEO. Fix these issues promptly.
    </p>
"""
            for issue in errors_and_broken_links_issues:
                issue_title_lower = issue.title.lower()
                appendix_key = None
                for key, appendix_cat in appendix_mapping.items():
                    if key in issue_title_lower:
                        appendix_key = appendix_cat
                        break
                
                affected_pages_html = ""
                if issue.affectedPages:
                    appendix_ref = get_appendix_letter(appendix_key) if appendix_key else None
                    affected_pages_html = format_urls_with_examples(issue.affectedPages, max_examples=3, appendix_ref=appendix_ref)
                    if affected_pages_html:
                        affected_pages_html = f'<div style="margin-top: 8px;"><strong>Examples:</strong>{affected_pages_html}</div>'
                
                fix_rec = get_fix_recommendation(issue.title, issue.category)
                
                html += f"""
    <div class="issue-block">
      <h3>{issue.title} <span class="severity {issue.severity}">{issue.severity.title()}</span></h3>
      <div class="why-it-matters">
        <strong>Why it matters:</strong> {issue.description}
      </div>
      {affected_pages_html}
      <div class="fix-recommendation">
        <strong>Fix Recommendation:</strong> {fix_rec}
      </div>
    </div>
"""
            html += """
  </div>
"""
        
        # Page-Type Aware Content Section Summary Table
        # Calculate average words per page type
        page_type_stats = {}
        for page in pages_index:
            page_type = page.get("page_type", "generic")
            words = page.get("words", 0) or 0
            if page_type not in page_type_stats:
                page_type_stats[page_type] = {"count": 0, "total_words": 0}
            page_type_stats[page_type]["count"] += 1
            page_type_stats[page_type]["total_words"] += words
        
        # Add content section summary if we have content issues
        content_category = next((c for c in report.categories if c.category == "content"), None)
        if content_category and content_category.issues:
            html += """
  <div class="section">
    <h2>Content Analysis by Page Type</h2>
    <p class="muted" style="margin-top: 8px; margin-bottom: 16px;">
      Content requirements vary by page type. Catalog and product pages naturally have less text than articles.
    </p>
    <table class="page-type-table">
      <tr>
        <th>Page Type</th>
        <th>Count</th>
        <th>Avg Words</th>
        <th>Notes</th>
      </tr>
"""
            for page_type, stats in sorted(page_type_stats.items(), key=lambda x: x[1]["count"], reverse=True):
                count = stats["count"]
                avg_words = stats["total_words"] / count if count > 0 else 0
                page_type_label = page_type.replace("_", " ").title()
                
                # Generate notes based on page type and word count
                if page_type == "article":
                    if avg_words >= 600:
                        notes = "Good content depth"
                    elif avg_words >= 300:
                        notes = "Adequate content depth"
                    else:
                        notes = "Could use more content"
                elif page_type in ["catalog", "product"]:
                    if avg_words < 50:
                        notes = "Low text (expected for catalog/product pages)"
                    else:
                        notes = "Good descriptions"
                elif page_type == "landing":
                    if avg_words >= 150:
                        notes = "Good landing page content"
                    else:
                        notes = "Could benefit from more copy"
                else:
                    if avg_words >= 200:
                        notes = "Good content depth"
                    else:
                        notes = "Could use more content"
                
                html += f"""
      <tr>
        <td>{page_type_label}</td>
        <td>{count}</td>
        <td>{avg_words:.0f}</td>
        <td>{notes}</td>
      </tr>
"""
            html += """
    </table>
  </div>
"""
        
        # Competitive Overview Section (NEW)
        if comparison_rows:
            competitor_name = competitor_reports[0].baseUrl or competitor_reports[0].runId if competitor_reports else "Competitor"
            html += f"""
  <div class="section" style="page-break-before: always;">
    <h2>Competitive Overview</h2>
    <p class="muted">
      Comparing <strong>{report.baseUrl or report.runId}</strong> against <strong>{competitor_name}</strong>.
    </p>
    
    <table>
      <tr style="background: #F4F5F7; color: #0D0F12;">
        <th style="padding: 8px; text-align:left;">Metric</th>
        <th style="padding: 8px;">Your Site</th>
        <th style="padding: 8px;">Competitor</th>
        <th style="padding: 8px;">Difference</th>
        <th style="padding: 8px;">Verdict</th>
      </tr>
"""
            row_idx = 0
            for row in comparison_rows:
                row_idx += 1
                primary_display = format_value(row.primaryValue, is_time="load_time" in row.metric or "ms" in str(row.primaryValue))
                comp_display = format_value(row.competitorValue, is_time="load_time" in row.metric or "ms" in str(row.competitorValue))
                diff_display = format_difference(row.difference, is_time="load_time" in row.metric or "ms" in str(row.difference) if row.difference else False)
                
                badge_class = "badge-good" if row.direction == "better" else "badge-bad" if row.direction == "worse" else "badge-neutral"
                row_style = 'background: #F9FAFB;' if row_idx % 2 == 0 else ''
                
                html += f"""
      <tr style="{row_style}">
        <td><strong>{row.label}</strong></td>
        <td>{primary_display}</td>
        <td>{comp_display}</td>
        <td class="text-right">{diff_display}</td>
        <td>
          <span class="{badge_class}">{row.verdict}</span>
        </td>
      </tr>
"""
            html += """
    </table>
  </div>
"""
            
            # Detailed Category Comparison Sections
            for category in ["performance", "seo", "content", "structure"]:
                cat_rows = [r for r in comparison_rows if r.category == category]
                if not cat_rows:
                    # Fallback: match by metric name
                    cat_rows = [r for r in comparison_rows if category in r.metric]
                
                if cat_rows:
                    html += f"""
  <div class="section">
    <h2>{category.title()} Comparison</h2>
    <table>
      <tr style="background: #F4F5F7; color: #0D0F12;">
        <th style="padding: 8px; text-align:left;">Metric</th>
        <th style="padding: 8px;">Your Site</th>
        <th style="padding: 8px;">Competitor</th>
        <th style="padding: 8px;">Difference</th>
        <th style="padding: 8px;">Verdict</th>
      </tr>
"""
                    row_idx = 0
                    for row in cat_rows:
                        row_idx += 1
                        primary_display = format_value(row.primaryValue, is_time="load_time" in row.metric or "ms" in str(row.primaryValue))
                        comp_display = format_value(row.competitorValue, is_time="load_time" in row.metric or "ms" in str(row.competitorValue))
                        diff_display = format_difference(row.difference, is_time="load_time" in row.metric or "ms" in str(row.difference) if row.difference else False)
                        
                        badge_class = "badge-good" if row.direction == "better" else "badge-bad" if row.direction == "worse" else "badge-neutral"
                        row_style = 'background: #F9FAFB;' if row_idx % 2 == 0 else ''
                        
                        html += f"""
      <tr style="{row_style}">
        <td>{row.label}</td>
        <td>{primary_display}</td>
        <td>{comp_display}</td>
        <td class="text-right">{diff_display}</td>
        <td>
          <span class="{badge_class}">{row.verdict}</span>
        </td>
      </tr>
"""
                    html += """
    </table>
  </div>
"""
        
        # Competitor Snapshot Appendix
        if competitor_reports:
            html += """
  <div class="section" style="page-break-before: always;">
    <h2>Competitor Details</h2>
    <p class="muted">Detailed snapshots for each competitor site.</p>
"""
            for comp_report in competitor_reports:
                html += f"""
    <div class="card" style="margin-bottom: 16px;">
      <h3>{comp_report.baseUrl or comp_report.runId}</h3>
      <div class="muted">Overall Score: {comp_report.overallScore}/100</div>
      
      <table style="margin-top: 12px;">
        <tr>
          <th>Category</th>
          <th>Score</th>
        </tr>
"""
                for cat in comp_report.categories:
                    html += f"""
        <tr>
          <td>{cat.category.title()}</td>
          <td>{cat.score}/100</td>
        </tr>
"""
                html += """
      </table>
      
      <table style="margin-top: 12px;">
        <tr>
          <th>Pages</th>
          <th>Total Words</th>
          <th>Avg Load Time</th>
          <th>Slow Pages</th>
        </tr>
        <tr>
"""
                html += f"""
          <td>{comp_report.stats.pagesCount}</td>
          <td>{comp_report.stats.totalWords:,}</td>
          <td>{comp_report.stats.avgLoadMs:.0f} ms</td>
          <td>{comp_report.stats.slowPagesCount}</td>
        </tr>
      </table>
    </div>
"""
            html += """
  </div>
"""
        
        # Build Appendix Section
        # Define appendix sections in order (must match appendix_sections_order)
        appendix_sections_titles = {
            "very_slow_pages": "Very Slow Pages",
            "slow_pages": "Slow Pages",
            "very_thin_content_pages": "Very Thin Content (Important Pages)",
            "thin_content_pages": "Thin Content (Important Pages)",
            "low_text_catalog_pages": "Low-Text Catalog/Product Pages (Optional)",
            "broken_internal_links": "Broken Internal Links",
            "pages_with_broken_links": "Pages with Broken Links",
            "error_pages": "404 / Error Pages",
            "missing_h1": "Missing H1 Tags",
            "missing_title": "Missing Page Titles",
            "missing_description": "Missing Meta Descriptions",
            "images_missing_alt": "Images Missing Alt Text",
            "noindex_pages": "Noindex Pages",
            "no_viewport_pages": "Pages Without Viewport",
            "mixed_content_pages": "Mixed Content Pages"
        }
        
        # Use the same order as appendix_sections_order and only include sections with data
        active_appendix_sections = [(key, appendix_sections_titles[key]) for key in appendix_sections_order if len(appendix_data.get(key, [])) > 0]
        
        if active_appendix_sections:
            html += """
  <div class="appendix-section">
    <h1>Appendix — Full URL Listings</h1>
    <p class="muted">Complete lists of pages referenced in the main report.</p>
"""
            
            for key, title in active_appendix_sections:
                urls = appendix_data[key]
                # Deduplicate
                urls = list(dict.fromkeys(urls))  # Preserves order while removing duplicates
                
                # Get the letter from the mapping
                letter = appendix_key_to_letter.get(key, '?')
                
                html += f"""
    <div class="appendix-list">
      <h2>Appendix {letter} — {title}</h2>
      <ul>
"""
                for url in urls:
                    html += f'        <li>{url}</li>\n'
                html += """      </ul>
    </div>
"""
            
            html += """
  </div>
"""
        
        html += """
</body>
</html>"""
        
        # Convert HTML → PDF
        try:
            config = get_pdfkit_config()
            pdf_bytes = pdfkit.from_string(html, False, configuration=config)
        except OSError as e:
            # wkhtmltopdf not found or not executable
            error_msg = str(e)
            if "No wkhtmltopdf executable found" in error_msg or "which: no wkhtmltopdf" in error_msg:
                raise HTTPException(
                    status_code=503,
                    detail="PDF export requires wkhtmltopdf to be installed. Please install it or set WKHTMLTOPDF_PATH environment variable. See: https://wkhtmltopdf.org/downloads.html"
                )
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {error_msg}")
        except Exception as e:
            import traceback
            error_detail = f"Error generating PDF: {str(e)}\n{traceback.format_exc()}"
            print(error_detail)  # Log to console for debugging
            raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")
        
        buffer = io.BytesIO(pdf_bytes)
        filename = f"siteinsite-report-{report.runId}.pdf"
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF export: {str(e)}")


def generate_comparison_rows(site_reports: list[ComparedSite], primary_url: str) -> list[ComparisonRow]:
    """
    Generate structured comparison rows for side-by-side comparison.
    
    Creates human-readable comparison rows with verdicts for each metric.
    """
    if len(site_reports) < 2:
        return []
    
    primary = site_reports[0]
    competitors = site_reports[1:]
    
    # For now, compare primary against first competitor (can extend to multiple later)
    competitor = competitors[0] if competitors else None
    if not competitor:
        return []
    
    comparisons = []
    
    def get_category_score(report: InsightReport, category: str) -> float:
        """Get score for a specific category."""
        cat = next((c for c in report.categories if c.category == category), None)
        return float(cat.score) if cat else 0.0
    
    # Overall Score
    primary_overall = float(primary.report.overallScore)
    comp_overall = float(competitor.report.overallScore)
    diff_overall = primary_overall - comp_overall
    comparisons.append(ComparisonRow(
        metric="overall_score",
        label="Overall Score",
        primaryValue=round(primary_overall, 1),
        competitorValue=round(comp_overall, 1),
        difference=round(diff_overall, 1),
        direction="better" if diff_overall > 5 else "worse" if diff_overall < -5 else "neutral",
        verdict="Slightly ahead overall" if diff_overall > 5 else "Slightly behind overall" if diff_overall < -5 else "Similar overall",
        category="overall"
    ))
    
    # Category Scores
    for category in ["performance", "seo", "content", "structure"]:
        primary_score = get_category_score(primary.report, category)
        comp_score = get_category_score(competitor.report, category)
        diff = primary_score - comp_score
        
        if abs(diff) < 3:
            verdict = f"Similar {category}"
            direction = "neutral"
        elif diff > 10:
            verdict = f"Stronger {category}"
            direction = "better"
        elif diff > 0:
            verdict = f"Slightly ahead in {category}"
            direction = "better"
        elif diff < -10:
            verdict = f"{category.capitalize()} lags behind"
            direction = "worse"
        else:
            verdict = f"Slightly behind in {category}"
            direction = "worse"
        
        comparisons.append(ComparisonRow(
            metric=f"{category}_score",
            label=category.capitalize(),
            primaryValue=round(primary_score, 1),
            competitorValue=round(comp_score, 1),
            difference=round(diff, 1),
            direction=direction,
            verdict=verdict,
            category=category
        ))
    
    # Performance Metrics
    primary_load = primary.report.stats.avgLoadMs
    comp_load = competitor.report.stats.avgLoadMs
    load_diff = primary_load - comp_load
    comparisons.append(ComparisonRow(
        metric="avg_load_time_ms",
        label="Avg Load Time",
        primaryValue=round(primary_load, 0),
        competitorValue=round(comp_load, 0),
        difference=round(load_diff, 0),
        direction="worse" if load_diff > 200 else "better" if load_diff < -200 else "neutral",
        verdict=f"You're {abs(load_diff):.0f}ms slower" if load_diff > 200 else f"You're {abs(load_diff):.0f}ms faster" if load_diff < -200 else "Similar load times",
        category="performance"
    ))
    
    # Content Depth Score
    if primary.report.contentDepthScore is not None and competitor.report.contentDepthScore is not None:
        primary_depth = primary.report.contentDepthScore
        comp_depth = competitor.report.contentDepthScore
        depth_diff = primary_depth - comp_depth
        comparisons.append(ComparisonRow(
            metric="content_depth_score",
            label="Content Depth",
            primaryValue=round(primary_depth, 1),
            competitorValue=round(comp_depth, 1),
            difference=round(depth_diff, 1),
            direction="worse" if depth_diff < -5 else "better" if depth_diff > 5 else "neutral",
            verdict="Needs richer content" if depth_diff < -5 else "Stronger content depth" if depth_diff > 5 else "Similar content depth",
            category="content"
        ))
    
    # Navigation Type
    if primary.report.navType and competitor.report.navType:
        nav_same = primary.report.navType == competitor.report.navType
        comparisons.append(ComparisonRow(
            metric="nav_type",
            label="Navigation Type",
            primaryValue=primary.report.navType,
            competitorValue=competitor.report.navType,
            difference=None,
            direction="different" if not nav_same else "neutral",
            verdict="Different structure types" if not nav_same else "Similar navigation structure",
            category="structure"
        ))
    
    # Crawlability Score
    if primary.report.crawlabilityScore is not None and competitor.report.crawlabilityScore is not None:
        primary_crawl = primary.report.crawlabilityScore
        comp_crawl = competitor.report.crawlabilityScore
        crawl_diff = primary_crawl - comp_crawl
        comparisons.append(ComparisonRow(
            metric="crawlability_score",
            label="Crawlability",
            primaryValue=round(primary_crawl, 1),
            competitorValue=round(comp_crawl, 1),
            difference=round(crawl_diff, 1),
            direction="worse" if crawl_diff < -10 else "better" if crawl_diff > 10 else "neutral",
            verdict="Bots find them easier" if crawl_diff < -10 else "Better bot traversal" if crawl_diff > 10 else "Similar crawlability",
            category="structure"
        ))
    
    # SEO-specific metrics
    # Missing H1 percentage (estimate from issues)
    primary_seo_issues = [cat.issues for cat in primary.report.categories if cat.category == "seo"]
    comp_seo_issues = [cat.issues for cat in competitor.report.categories if cat.category == "seo"]
    primary_missing_h1 = sum(1 for issues in primary_seo_issues for issue in issues if "H1" in issue.title)
    comp_missing_h1 = sum(1 for issues in comp_seo_issues for issue in issues if "H1" in issue.title)
    if primary_missing_h1 != comp_missing_h1:
        comparisons.append(ComparisonRow(
            metric="missing_h1_count",
            label="Missing H1 Pages",
            primaryValue=primary_missing_h1,
            competitorValue=comp_missing_h1,
            difference=primary_missing_h1 - comp_missing_h1,
            direction="worse" if primary_missing_h1 > comp_missing_h1 else "better",
            verdict=f"{primary_missing_h1} vs {comp_missing_h1} pages missing H1",
            category="seo"
        ))
    
    return comparisons


async def wait_for_run_completion(run_id: str, timeout: int = 600) -> bool:
    """
    Wait for a run to complete by polling its progress.
    
    Args:
        run_id: The run ID to wait for
        timeout: Maximum time to wait in seconds (default 10 minutes)
    
    Returns:
        True if run completed successfully, False if timeout
    """
    start_time = time.time()
    poll_interval = 2  # Poll every 2 seconds
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            return False
        
        progress = await run_manager.progress(run_id)
        if progress is None:
            # Run finished and was cleaned up from memory, check if data exists
            run_store = RunStore(run_id)
            if os.path.exists(run_store.run_dir):
                return True
            return False
        
        if progress.get("is_complete", False):
            return True
        
        await asyncio.sleep(poll_interval)


async def run_extractor_for_url(url: str, max_pages: int = 50, bot_avoidance_enabled: bool | None = None) -> str:
    """
    Run the extraction pipeline for a URL and return the run_id.
    
    Args:
        url: The URL to extract
        max_pages: Maximum number of pages to crawl
        bot_avoidance_enabled: Whether to enable bot avoidance (defaults to None/False)
    
    Returns:
        The run_id for the completed extraction
    """
    # Start the run
    req = StartRunRequest(url=url, maxPages=max_pages, botAvoidanceEnabled=bot_avoidance_enabled)
    run_id = await run_manager.start(req)
    
    # Wait for completion
    completed = await wait_for_run_completion(run_id)
    if not completed:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction for {url} did not complete within timeout period"
        )
    
    return run_id


@router.post("/api/compare", response_model=ComparisonReport)
async def compare_sites(payload: ComparePayload) -> ComparisonReport:
    """
    Compare multiple sites (primary + competitors) and generate a comparison report.
    
    This endpoint:
    1. Extracts data from the primary URL and all competitor URLs
    2. Builds InsightReports for each site
    3. Generates a unified ComparisonReport with scores, stats, and opportunities
    
    **Example Request:**
    ```json
    {
      "primaryUrl": "https://example.com",
      "competitors": [
        "https://competitor1.com",
        "https://competitor2.com"
      ]
    }
    ```
    
    **Example Response:**
    ```json
    {
      "primaryUrl": "https://example.com",
      "competitors": ["https://competitor1.com", "https://competitor2.com"],
      "siteReports": [
        {
          "url": "https://example.com",
          "report": { ... }
        }
      ],
      "scoreComparison": {
        "overall": {
          "https://example.com": 75,
          "https://competitor1.com": 80
        }
      },
      "opportunitySummary": [
        "Competitors load faster. Optimize images, JS, and server response time."
      ]
    }
    ```
    """
    try:
        all_urls = [payload.primaryUrl] + payload.competitors
        
        if len(all_urls) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 sites (1 primary + 9 competitors) allowed per comparison"
            )
        
        # Run extraction for all URLs
        site_reports = []
        run_ids = []
        
        # Use botAvoidanceEnabled from payload, default to False if not specified
        bot_avoidance = payload.botAvoidanceEnabled if payload.botAvoidanceEnabled is not None else False
        
        for url in all_urls:
            try:
                run_id = await run_extractor_for_url(url, max_pages=50, bot_avoidance_enabled=bot_avoidance)
                run_ids.append((url, run_id))
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to extract {url}: {str(e)}"
                )
        
        # Build insight reports for each site
        for url, run_id in run_ids:
            try:
                run_store = RunStore(run_id)
                if not os.path.exists(run_store.run_dir):
                    raise HTTPException(
                        status_code=404,
                        detail=f"Run data not found for {url} (run_id: {run_id})"
                    )
                
                report = build_insight_report(run_store, run_id)
                site_reports.append(ComparedSite(url=url, report=report))
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to build insight report for {url}: {str(e)}"
                )
        
        # Ensure primary is first
        primary_index = next(
            (i for i, site in enumerate(site_reports) if site.url == payload.primaryUrl),
            0
        )
        if primary_index != 0:
            site_reports.insert(0, site_reports.pop(primary_index))
        
        # Build comparison tables
        def get_category_score(report: InsightReport, category: str) -> float:
            """Get score for a specific category."""
            cat = next((c for c in report.categories if c.category == category), None)
            return float(cat.score) if cat else 0.0
        
        def build_comp(category: str) -> dict[str, float]:
            """Build comparison dict for a category score."""
            out = {}
            for site in site_reports:
                out[site.url] = get_category_score(site.report, category)
            return out
        
        score_comp = {
            "overall": {site.url: float(site.report.overallScore) for site in site_reports},
            "performance": build_comp("performance"),
            "seo": build_comp("seo"),
            "content": build_comp("content"),
            "structure": build_comp("structure"),
        }
        
        # Build detailed performance comparison
        perf_comp = {
            "avgLoadMs": {site.url: site.report.stats.avgLoadMs for site in site_reports},
            "medianLoadMs": {site.url: site.report.stats.medianLoadMs for site in site_reports},
            "p90LoadMs": {site.url: site.report.stats.p90LoadMs for site in site_reports},
            "avgPageSizeKb": {site.url: site.report.stats.avgPageSizeKb for site in site_reports},
            "maxPageSizeKb": {site.url: site.report.stats.maxPageSizeKb for site in site_reports},
        }
        
        # Build content comparison
        content_comp = {
            "totalWords": {site.url: float(site.report.stats.totalWords) for site in site_reports},
            "avgWordsPerPage": {site.url: site.report.stats.avgWordsPerPage for site in site_reports},
            "totalMediaItems": {site.url: float(site.report.stats.totalMediaItems) for site in site_reports},
            "pagesCount": {site.url: float(site.report.stats.pagesCount) for site in site_reports},
        }
        
        # Build SEO comparison (using stats that relate to SEO)
        seo_comp = {
            "score": build_comp("seo"),
            # Could add more SEO-specific metrics here if needed
        }
        
        # Build structure comparison
        structure_comp = {
            "score": build_comp("structure"),
            # Could add more structure-specific metrics here if needed
        }
        
        # Generate opportunities
        opps = generate_opportunities(site_reports)
        
        # Generate structured comparison rows for UI/PDF
        comparisons = generate_comparison_rows(site_reports, payload.primaryUrl)
        
        return ComparisonReport(
            primaryUrl=payload.primaryUrl,
            competitors=payload.competitors,
            siteReports=site_reports,
            scoreComparison=score_comp,
            performanceComparison=perf_comp,
            contentComparison=content_comp,
            seoComparison=seo_comp,
            structureComparison=structure_comp,
            opportunitySummary=opps,
            comparisons=comparisons
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating comparison report: {str(e)}"
        )


def build_comparison_pdf_html(report: ComparisonReport) -> str:
    """
    Build HTML for competitor comparison PDF report.
    """
    primary = report.primaryUrl
    competitors = report.competitors
    
    # Helper function to calculate long-form pages (>600 words)
    def calculate_long_form_pages(site_report: ComparedSite) -> int:
        """Estimate long-form pages from stats."""
        stats = site_report.report.stats
        if stats.avgWordsPerPage > 0 and stats.pagesCount > 0:
            # Estimate: if avg is high, more pages are likely long-form
            # Simple heuristic: pages with >600 words
            if stats.avgWordsPerPage >= 600:
                # Most pages are long-form
                return int(stats.pagesCount * 0.8)
            elif stats.avgWordsPerPage >= 300:
                # Some pages are long-form
                return int(stats.pagesCount * 0.4)
            else:
                # Few pages are long-form
                return int(stats.pagesCount * 0.1)
        return 0
    
    # Helper function to count pages with noindex
    def count_noindex_pages(site_report: ComparedSite) -> int:
        """Count pages with noindex from SEO issues."""
        count = 0
        for cat in site_report.report.categories:
            if cat.category == "seo":
                for issue in cat.issues:
                    if "noindex" in issue.title.lower() or "noindex" in issue.description.lower():
                        count += len(issue.affectedPages)
        return count
    
    # Helper function to count pages without viewport
    def count_no_viewport_pages(site_report: ComparedSite) -> int:
        """Count pages without viewport from SEO issues."""
        count = 0
        for cat in site_report.report.categories:
            if cat.category == "seo":
                for issue in cat.issues:
                    if "viewport" in issue.title.lower() or "viewport" in issue.description.lower():
                        count += len(issue.affectedPages)
        return count
    
    # Helper function to check if sitemap is missing
    def check_sitemap_missing(site_report: ComparedSite) -> bool:
        """Check if sitemap is missing from SEO issues."""
        for cat in site_report.report.categories:
            if cat.category == "seo":
                for issue in cat.issues:
                    if "sitemap" in issue.title.lower() or "sitemap" in issue.description.lower():
                        return True
        return False
    
    # Helper function to check if robots.txt is missing
    def check_robots_missing(site_report: ComparedSite) -> bool:
        """Check if robots.txt is missing from SEO issues."""
        for cat in site_report.report.categories:
            if cat.category == "seo":
                for issue in cat.issues:
                    if "robots" in issue.title.lower() and "missing" in issue.title.lower():
                        return True
        return False
    
    html = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>SiteInsite Comparison Report</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    :root {{
      --brand-bg: #0D0F12;
      --brand-text: #E6EBF0;
      --accent: #4A90E2;
      --accent-alt: #A8C5DA;
      --neutral-light: #F4F5F7;
      --neutral-dark: #1F2328;
      --good: #00C853;
      --bad: #D32F2F;
      --neutral: #9CA3AF;
    }}
    body {{
      font-family: Inter, sans-serif;
      background: white;
      color: #0D0F12;
      margin: 48px;
      font-size: 12px;
      font-weight: 400;
    }}
    h1, h2, h3, h4 {{
      font-family: Inter, sans-serif;
      font-weight: 700;
      color: #0D0F12;
    }}
    h1 {{
      font-size: 24px;
      margin-bottom: 16px;
    }}
    h2 {{
      border-left: 6px solid #A8C5DA;
      padding-left: 14px;
      margin-top: 36px;
      margin-bottom: 12px;
      font-size: 20px;
      font-weight: bold;
      font-family: Inter, sans-serif;
      color: #0D0F12;
    }}
    h3 {{
      font-size: 16px;
      margin-top: 20px;
      margin-bottom: 8px;
      color: #0D0F12;
    }}
    h4 {{
      font-size: 14px;
      margin-top: 16px;
      margin-bottom: 8px;
      color: #0D0F12;
    }}
    .section {{
      margin-bottom: 32px;
      page-break-inside: avoid;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 12px;
    }}
    th, td {{
      padding: 7px;
      text-align: left;
      border-bottom: 1px solid #E5E7EB;
      color: #0D0F12;
    }}
    th {{
      background: #F4F5F7;
      color: #0D0F12;
      font-weight: 700;
      border-bottom: 2px solid #E5E7EB;
    }}
    tr:nth-child(even) {{
      background: #F9FAFB;
    }}
    tr:nth-child(odd) {{
      background: #FFFFFF;
    }}
    .small {{
      font-size: 12px;
      color: var(--neutral);
    }}
    .muted {{
      color: var(--neutral);
      font-size: 11px;
    }}
    .badge-good {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 9999px;
      font-size: 10px;
      color: white;
      background: #00C853;
      font-weight: 600;
    }}
    .badge-bad {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 9999px;
      font-size: 10px;
      color: white;
      background: #D32F2F;
      font-weight: 600;
    }}
    .badge-neutral {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 9999px;
      font-size: 10px;
      color: #0D0F12;
      background: #A8C5DA;
      font-weight: 600;
    }}
    pre {{
      font-size: 10px;
      overflow-x: auto;
      background: var(--neutral-light);
      padding: 10px;
      border-radius: 4px;
      border: 1px solid #E5E7EB;
      color: #0D0F12;
    }}
    ul {{
      padding-left: 1.25rem;
      margin: 8px 0;
      color: #0D0F12;
    }}
    li {{
      margin-bottom: 6px;
      color: #0D0F12;
    }}
  </style>
</head>
<body>
  <!-- Branded Header -->
  <div style="background: #FFFFFF; padding: 32px 0; text-align: center; border-bottom: 3px solid #4A90E2; width: 100%;">
    <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iMjAwIiB2aWV3Qm94PSIwIDAgODAwIDIwMCI+CiAgPHJlY3Qgd2lkdGg9IjgwMCIgaGVpZ2h0PSIyMDAiIGZpbGw9IiNGRkZGRkYiIC8+CiAgPHRleHQgeD0iNTAlIiB5PSI1MCUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiCiAgICAgICAgZm9udC1mYW1pbHk9IkludGVyLCBzeXN0ZW0tdWksIC1hcHBsZS1zeXN0ZW0sIEJsaW5rTWFjU3lzdGVtRm9udCwgJ1NlZ29lIFVJJywgc2Fucy1zZXJpZiIKICAgICAgICBmb250LXNpemU9IjY0IiBmaWxsPSIjMEQwRjEyIiBsZXR0ZXItc3BhY2luZz0iNiI+CiAgICBOT1ZJQU4gU1RVRElPUwogIDwvdGV4dD4KPC9zdmc+Cg==" alt="NOVIAN STUDIOS" style="display: block; margin: 0 auto; max-width: 100%;" />
    <div style="margin-top: 12px; font-family: Inter, sans-serif; font-size: 14px; color: #4A90E2; letter-spacing: 0.12em;">Website Insight Report</div>
  </div>
  
"""
    
    # Cover Page
    primary_site = next((s for s in report.siteReports if s.url == primary), None)
    competitor_site = report.siteReports[1] if len(report.siteReports) > 1 else None
    competitor_name = competitor_site.url if competitor_site else (competitors[0] if competitors else "Competitor")
    
    html += f"""
    <div class="section">
      <h1>Competitor Comparison Report</h1>
      <p class="muted"><strong>Your site:</strong> {primary}</p>
      <p class="muted"><strong>Competitor:</strong> {competitor_name}</p>
    </div>
"""
    
    # Competitive Overview Section (NEW)
    if report.comparisons:
        html += f"""
    <div class="section" style="page-break-before: always;">
      <h2>Competitive Overview</h2>
      <p class="muted">Side-by-side comparison of key metrics.</p>
      <table>
        <tr style="background: #F4F5F7; color: #0D0F12;">
          <th style="padding: 8px; text-align:left;">Metric</th>
          <th style="padding: 8px;">Your Site</th>
          <th style="padding: 8px;">{competitor_name}</th>
          <th style="padding: 8px;">Difference</th>
          <th style="padding: 8px;">Verdict</th>
        </tr>
"""
        row_idx = 0
        for comp_row in report.comparisons:
            row_idx += 1
            primary_val = comp_row.primaryValue
            comp_val = comp_row.competitorValue
            diff = comp_row.difference
            diff_str = f"{diff:+.1f}" if diff is not None else "—"
            badge_class = "badge-good" if comp_row.direction == "better" else "badge-bad" if comp_row.direction == "worse" else "badge-neutral"
            row_style = 'background: #F9FAFB;' if row_idx % 2 == 0 else ''
            html += f"""
        <tr style="{row_style}">
          <td><strong>{comp_row.label}</strong></td>
          <td>{primary_val}</td>
          <td>{comp_val}</td>
          <td>{diff_str}</td>
          <td><span class="{badge_class}">{comp_row.verdict}</span></td>
        </tr>"""
        html += """
      </table>
    </div>
"""
    
    # Detailed Category Comparison Sections
    if report.comparisons:
        # Performance Comparison
        perf_comps = [c for c in report.comparisons if "performance" in c.metric or "load_time" in c.metric]
        if perf_comps:
            html += f"""
    <div class="section">
      <h2>Performance Comparison</h2>
      <p class="muted">Load times and performance metrics.</p>
      <table>
        <tr style="background: #F4F5F7; color: #0D0F12;">
          <th style="padding: 8px; text-align:left;">Metric</th>
          <th style="padding: 8px;">Your Site</th>
          <th style="padding: 8px;">{competitor_name}</th>
          <th style="padding: 8px;">Verdict</th>
        </tr>
"""
            row_idx = 0
            for comp_row in perf_comps:
                row_idx += 1
                badge_class = "badge-good" if comp_row.direction == "better" else "badge-bad" if comp_row.direction == "worse" else "badge-neutral"
                row_style = 'background: #F9FAFB;' if row_idx % 2 == 0 else ''
                html += f"""
        <tr style="{row_style}">
          <td>{comp_row.label}</td>
          <td>{comp_row.primaryValue}</td>
          <td>{comp_row.competitorValue}</td>
          <td><span class="{badge_class}">{comp_row.verdict}</span></td>
        </tr>"""
            html += "</table></div>"
        
        # SEO Comparison
        seo_comps = [c for c in report.comparisons if "seo" in c.metric or "h1" in c.metric]
        if seo_comps:
            html += f"""
    <div class="section">
      <h2>SEO Comparison</h2>
      <p class="muted">On-page SEO and technical SEO metrics.</p>
      <table>
        <tr style="background: #F4F5F7; color: #0D0F12;">
          <th style="padding: 8px; text-align:left;">Metric</th>
          <th style="padding: 8px;">Your Site</th>
          <th style="padding: 8px;">{competitor_name}</th>
          <th style="padding: 8px;">Verdict</th>
        </tr>
"""
            row_idx = 0
            for comp_row in seo_comps:
                row_idx += 1
                badge_class = "badge-good" if comp_row.direction == "better" else "badge-bad" if comp_row.direction == "worse" else "badge-neutral"
                row_style = 'background: #F9FAFB;' if row_idx % 2 == 0 else ''
                html += f"""
        <tr style="{row_style}">
          <td>{comp_row.label}</td>
          <td>{comp_row.primaryValue}</td>
          <td>{comp_row.competitorValue}</td>
          <td><span class="{badge_class}">{comp_row.verdict}</span></td>
        </tr>"""
            html += "</table></div>"
        
        # Content & Depth Comparison
        content_comps = [c for c in report.comparisons if "content" in c.metric]
        if content_comps:
            html += f"""
    <div class="section">
      <h2>Content & Depth Comparison</h2>
      <p class="muted">Content quality and depth metrics.</p>
      <table>
        <tr style="background: #F4F5F7; color: #0D0F12;">
          <th style="padding: 8px; text-align:left;">Metric</th>
          <th style="padding: 8px;">Your Site</th>
          <th style="padding: 8px;">{competitor_name}</th>
          <th style="padding: 8px;">Verdict</th>
        </tr>
"""
            row_idx = 0
            for comp_row in content_comps:
                row_idx += 1
                badge_class = "badge-good" if comp_row.direction == "better" else "badge-bad" if comp_row.direction == "worse" else "badge-neutral"
                row_style = 'background: #F9FAFB;' if row_idx % 2 == 0 else ''
                html += f"""
        <tr style="{row_style}">
          <td>{comp_row.label}</td>
          <td>{comp_row.primaryValue}</td>
          <td>{comp_row.competitorValue}</td>
          <td><span class="{badge_class}">{comp_row.verdict}</span></td>
        </tr>"""
            html += "</table></div>"
        
        # Structure & Crawlability Comparison
        structure_comps = [c for c in report.comparisons if "structure" in c.metric or "nav" in c.metric or "crawlability" in c.metric]
        if structure_comps:
            html += f"""
    <div class="section">
      <h2>Structure & Crawlability Comparison</h2>
      <p class="muted">Navigation structure and bot crawlability.</p>
      <table>
        <tr style="background: #F4F5F7; color: #0D0F12;">
          <th style="padding: 8px; text-align:left;">Metric</th>
          <th style="padding: 8px;">Your Site</th>
          <th style="padding: 8px;">{competitor_name}</th>
          <th style="padding: 8px;">Verdict</th>
        </tr>
"""
            row_idx = 0
            for comp_row in structure_comps:
                row_idx += 1
                badge_class = "badge-good" if comp_row.direction == "better" else "badge-bad" if comp_row.direction == "worse" else "badge-neutral"
                row_style = 'background: #F9FAFB;' if row_idx % 2 == 0 else ''
                html += f"""
        <tr style="{row_style}">
          <td>{comp_row.label}</td>
          <td>{comp_row.primaryValue}</td>
          <td>{comp_row.competitorValue}</td>
          <td><span class="{badge_class}">{comp_row.verdict}</span></td>
        </tr>"""
            html += "</table></div>"
    
    # Opportunity Summary Section
    if report.opportunitySummary:
        html += """
    <div class="section">
      <h2>Top Opportunities</h2>
      <ul>
"""
        for opp in report.opportunitySummary:
            html += f"        <li>{opp}</li>"
        html += """
      </ul>
    </div>
"""
    
    # Competitor Snapshots Appendix (moved to end)
    html += """
    <div class="section" style="page-break-before: always;">
      <h2>Competitor Details</h2>
      <p class="muted">Detailed snapshots for each competitor site.</p>
    </div>
"""
    
    # Show competitor snapshots (skip primary, show only competitors)
    for site in report.siteReports:
        if site.url == primary:
            continue  # Skip primary site in appendix
        
        html += f"""
    <div class="section">
      <h3>Competitor Details: {site.url}</h3>
      <p class="muted"><strong>Overall Score:</strong> {site.report.overallScore}/100</p>
      <div style="margin-top: 1rem;">
        <h4>Category Scores</h4>
        <table>
          <tr><th>Category</th><th>Score</th></tr>"""
        for cat in site.report.categories:
            html += f"          <tr><td>{cat.category.title()}</td><td>{cat.score}/100</td></tr>"
        html += """
        </table>
      </div>
      <div style="margin-top: 1rem;">
        <h4>Key Stats</h4>
        <table>
          <tr><th>Metric</th><th>Value</th></tr>"""
        stats = site.report.stats
        html += f"""
          <tr><td>Pages</td><td>{stats.pagesCount}</td></tr>
          <tr><td>Total Words</td><td>{stats.totalWords:,}</td></tr>
          <tr><td>Avg Words/Page</td><td>{stats.avgWordsPerPage:.1f}</td></tr>
          <tr><td>Avg Load Time</td><td>{stats.avgLoadMs:.0f} ms</td></tr>
          <tr><td>P90 Load Time</td><td>{stats.p90LoadMs:.0f} ms</td></tr>
          <tr><td>Slow Pages</td><td>{stats.slowPagesCount}</td></tr>
          <tr><td>Very Slow Pages</td><td>{stats.verySlowPagesCount}</td></tr>
          <tr><td>Avg Page Size</td><td>{stats.avgPageSizeKb:.1f} KB</td></tr>
          <tr><td>Max Page Size</td><td>{stats.maxPageSizeKb:.1f} KB</td></tr>"""
        if site.report.contentDepthScore is not None:
            html += f"          <tr><td>Content Depth Score</td><td>{site.report.contentDepthScore:.1f}/100</td></tr>"
        if site.report.navType:
            html += f"          <tr><td>Navigation Type</td><td>{site.report.navType}</td></tr>"
        if site.report.crawlabilityScore is not None:
            html += f"          <tr><td>Crawlability Score</td><td>{site.report.crawlabilityScore:.1f}/100</td></tr>"
        html += """
        </table>
      </div>
    </div>
"""
    
    # Close HTML
    html += """
</body>
</html>"""
    return html


@router.post("/api/compare/export")
async def export_comparison_pdf(payload: ComparisonReport):
    """
    Export a competitor comparison report as PDF.
    
    Accepts a ComparisonReport payload and generates a PDF with:
    - Cover page
    - Score showdown table
    - Performance comparison
    - Content depth comparison
    - Technical SEO comparison
    - Opportunities summary
    - Full reports (appendix)
    """
    try:
        html = build_comparison_pdf_html(payload)
        
        # Convert HTML → PDF
        try:
            config = get_pdfkit_config()
            pdf_bytes = pdfkit.from_string(html, False, configuration=config)
        except OSError as e:
            # wkhtmltopdf not found or not executable
            error_msg = str(e)
            if "No wkhtmltopdf executable found" in error_msg or "which: no wkhtmltopdf" in error_msg:
                raise HTTPException(
                    status_code=503,
                    detail="PDF export requires wkhtmltopdf to be installed. Please install it or set WKHTMLTOPDF_PATH environment variable. See: https://wkhtmltopdf.org/downloads.html"
                )
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {error_msg}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")
        
        buffer = io.BytesIO(pdf_bytes)
        # Generate safe filename from primary URL
        safe_name = payload.primaryUrl.replace('https://', '').replace('http://', '').replace('www.', '')
        safe_name = ''.join(c if c.isalnum() or c in '.-_' else '_' for c in safe_name)
        safe_name = safe_name[:50]  # Limit length
        filename = f"siteinsite-comparison-{safe_name}.pdf"
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating comparison PDF: {str(e)}"
        )

