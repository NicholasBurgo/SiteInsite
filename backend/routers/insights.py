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
      border-left: 6px solid var(--accent-alt);
      padding-left: 14px;
      margin-top: 40px;
      margin-bottom: 12px;
      font-size: 20px;
      font-weight: bold;
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
      background: var(--neutral-light);
      padding: 14px;
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
      padding: 8px;
      text-align: left;
      border: 1px solid rgba(31, 35, 40, 0.15);
      color: #0D0F12;
    }}
    th {{
      background: var(--neutral-dark);
      color: var(--brand-text);
      font-weight: 700;
    }}
    tr:nth-child(even) {{
      background: #F9FAFB;
    }}
    tr:nth-child(odd) {{
      background: transparent;
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
      border-radius: 4px;
      font-size: 10px;
      color: white;
      background: var(--good);
      font-weight: 600;
    }}
    .badge-bad {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 10px;
      color: white;
      background: var(--bad);
      font-weight: 600;
    }}
    .badge-neutral {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 10px;
      color: #0D0F12;
      background: var(--accent-alt);
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
  </style>
</head>
<body>
  <!-- Branded Header -->
  <div style="background: #0D0F12; padding: 32px 0; text-align: center; border-bottom: 3px solid #4A90E2;">
    <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iMjAwIiB2aWV3Qm94PSIwIDAgODAwIDIwMCI+CiAgPHJlY3Qgd2lkdGg9IjgwMCIgaGVpZ2h0PSIyMDAiIGZpbGw9IiMwRDBGMTIiIC8+CiAgPHRleHQgeD0iNTAlIiB5PSI1MCUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiCiAgICAgICAgZm9udC1mYW1pbHk9IkludGVyLCBzeXN0ZW0tdWksIC1hcHBsZS1zeXN0ZW0sIEJsaW5rTWFjU3lzdGVtRm9udCwgJ1NlZ29lIFVJJywgc2Fucy1zZXJpZiIKICAgICAgICBmb250LXNpemU9IjY0IiBmaWxsPSIjRTZFQkYwIiBsZXR0ZXItc3BhY2luZz0iNiI+CiAgICBOT1ZJQU4gU1RVRElPUwogIDwvdGV4dD4KPC9zdmc+Cg==" alt="NOVIAN STUDIOS" style="width: 65%; max-width: 900px;" />
    <div style="margin-top: 12px; font-family: Inter, sans-serif; font-size: 14px; color: #A8C5DA; letter-spacing: 0.12em;">WEBSITE INSIGHT REPORT</div>
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
        
        # Top Fixes Section
        if top_issues:
            html += """
  <div class="section">
    <h2>Top Fixes</h2>
    <p class="muted">Focus on these changes first for the biggest impact.</p>
"""
            for idx, issue in enumerate(top_issues, 1):
                example_urls = ""
                if issue.affectedPages:
                    sample = issue.affectedPages[:3]
                    urls_str = "; ".join(p.url for p in sample)
                    if len(issue.affectedPages) > 3:
                        urls_str += f" (+{len(issue.affectedPages) - 3} more)"
                    example_urls = f'<div class="muted" style="margin-top: 4px;">Examples: {urls_str}</div>'
                
                html += f"""
    <div class="card">
      <strong>{idx}. {issue.title}</strong>
      <div class="muted" style="margin-top: 4px;">{issue.description}</div>
      {example_urls}
    </div>
"""
            html += """
  </div>
"""
        
        # Key Stats Section
        html += f"""
  <div class="section">
    <h2>Key Stats</h2>
    <table>
      <tr>
        <th>Pages</th>
        <th>Total Words</th>
        <th>Avg Words/Page</th>
        <th>Total Media</th>
      </tr>
      <tr>
        <td>{report.stats.pagesCount}</td>
        <td>{report.stats.totalWords:,}</td>
        <td>{report.stats.avgWordsPerPage:.1f}</td>
        <td>{report.stats.totalMediaItems}</td>
      </tr>
    </table>

    <table>
      <tr>
        <th>Avg Load Time</th>
        <th>Median Load Time</th>
        <th>90th Percentile</th>
        <th>Slow Pages</th>
        <th>Very Slow Pages</th>
      </tr>
      <tr>
        <td>{report.stats.avgLoadMs:.0f} ms</td>
        <td>{report.stats.medianLoadMs:.0f} ms</td>
        <td>{report.stats.p90LoadMs:.0f} ms</td>
        <td>{report.stats.slowPagesCount}</td>
        <td>{report.stats.verySlowPagesCount}</td>
      </tr>
    </table>
  </div>
"""
        
        # Category Sections
        for cat in report.categories:
            # Get summary text (first issue description or default)
            summary_text = "Review issues below for details."
            if cat.issues:
                summary_text = cat.issues[0].description[:150] + "..." if len(cat.issues[0].description) > 150 else cat.issues[0].description
            
            html += f"""
  <div class="section">
    <h2>{cat.category.title()}</h2>
    <div class="score-big">{cat.score}/100</div>
    <p class="muted" style="margin-top: 8px;">
      {summary_text}
    </p>
    
    <h3>Key Issues</h3>
    <ul>
"""
            # Show top 5 issues per category
            for issue in cat.issues[:5]:
                example_text = ""
                if issue.affectedPages:
                    example_url = issue.affectedPages[0].url
                    more_count = len(issue.affectedPages) - 1
                    example_text = f' <span class="muted">— e.g., {example_url}' + (f', +{more_count} more' if more_count > 0 else '') + '</span>'
                
                html += f"""
      <li>
        <strong>{issue.title}</strong>{example_text}
      </li>
"""
            if len(cat.issues) > 5:
                html += f"""
      <li class="muted">+{len(cat.issues) - 5} more issues not shown</li>
"""
            html += """
    </ul>
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
      <tr style="background: var(--neutral-dark); color: var(--brand-text);">
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
      <tr style="background: var(--neutral-dark); color: var(--brand-text);">
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


async def run_extractor_for_url(url: str, max_pages: int = 50) -> str:
    """
    Run the extraction pipeline for a URL and return the run_id.
    
    Args:
        url: The URL to extract
        max_pages: Maximum number of pages to crawl
    
    Returns:
        The run_id for the completed extraction
    """
    # Start the run
    req = StartRunRequest(url=url, maxPages=max_pages)
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
        
        for url in all_urls:
            try:
                run_id = await run_extractor_for_url(url, max_pages=50)
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
      border-left: 6px solid var(--accent-alt);
      padding-left: 14px;
      margin-top: 40px;
      margin-bottom: 12px;
      font-size: 20px;
      font-weight: bold;
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
      padding: 8px;
      text-align: left;
      border: 1px solid rgba(31, 35, 40, 0.15);
      color: #0D0F12;
    }}
    th {{
      background: var(--neutral-dark);
      color: var(--brand-text);
      font-weight: 700;
    }}
    tr:nth-child(even) {{
      background: #F9FAFB;
    }}
    tr:nth-child(odd) {{
      background: transparent;
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
      border-radius: 4px;
      font-size: 10px;
      color: white;
      background: var(--good);
      font-weight: 600;
    }}
    .badge-bad {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 10px;
      color: white;
      background: var(--bad);
      font-weight: 600;
    }}
    .badge-neutral {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 10px;
      color: #0D0F12;
      background: var(--accent-alt);
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
  <div style="background: #0D0F12; padding: 32px 0; text-align: center; border-bottom: 3px solid #4A90E2;">
    <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iMjAwIiB2aWV3Qm94PSIwIDAgODAwIDIwMCI+CiAgPHJlY3Qgd2lkdGg9IjgwMCIgaGVpZ2h0PSIyMDAiIGZpbGw9IiMwRDBGMTIiIC8+CiAgPHRleHQgeD0iNTAlIiB5PSI1MCUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiCiAgICAgICAgZm9udC1mYW1pbHk9IkludGVyLCBzeXN0ZW0tdWksIC1hcHBsZS1zeXN0ZW0sIEJsaW5rTWFjU3lzdGVtRm9udCwgJ1NlZ29lIFVJJywgc2Fucy1zZXJpZiIKICAgICAgICBmb250LXNpemU9IjY0IiBmaWxsPSIjRTZFQkYwIiBsZXR0ZXItc3BhY2luZz0iNiI+CiAgICBOT1ZJQU4gU1RVRElPUwogIDwvdGV4dD4KPC9zdmc+Cg==" alt="NOVIAN STUDIOS" style="width: 65%; max-width: 900px;" />
    <div style="margin-top: 12px; font-family: Inter, sans-serif; font-size: 14px; color: #A8C5DA; letter-spacing: 0.12em;">WEBSITE INSIGHT REPORT</div>
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
        <tr style="background: var(--neutral-dark); color: var(--brand-text);">
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
        <tr style="background: var(--neutral-dark); color: var(--brand-text);">
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
        <tr style="background: var(--neutral-dark); color: var(--brand-text);">
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
        <tr style="background: var(--neutral-dark); color: var(--brand-text);">
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
        <tr style="background: var(--neutral-dark); color: var(--brand-text);">
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

