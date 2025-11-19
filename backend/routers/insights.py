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
from backend.core.types import InsightReport, ComparePayload, ComparisonReport, ComparedSite
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
        
        # Build HTML report (same structure as before, optimized for PDF)
        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>SiteInsite Report – {report.baseUrl or report.runId}</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 2rem;
      background: #ffffff;
      color: #111827;
    }}
    h1, h2, h3 {{
      margin-top: 0;
      margin-bottom: 0.4rem;
    }}
    p {{
      margin: 0.2rem 0;
    }}
    .score {{
      font-size: 2.5rem;
      font-weight: 700;
    }}
    .section {{
      background: #f9fafb;
      border-radius: 0.75rem;
      padding: 1.25rem 1.5rem;
      margin-bottom: 1.2rem;
      border: 1px solid #e5e7eb;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 0.75rem;
    }}
    .small {{
      font-size: 0.85rem;
      color: #6b7280;
    }}
    ul {{
      padding-left: 1.25rem;
    }}
    ol {{
      padding-left: 1.25rem;
    }}
  </style>
</head>
<body>
  <h1>SiteInsite Website Insight Report</h1>
  <p class="small">
    Site: <strong>{report.baseUrl or "Unknown"}</strong><br/>
    Run ID: {report.runId}<br/>
    Generated: {generated_at}
  </p>

  <div class="section">
    <h2>Overall Score</h2>
    <div class="score">{report.overallScore}/100</div>
  </div>
"""
        
        # Add Top Fixes section before Key Stats
        if top_issues:
            html += """
  <div class="section">
    <h2>Top Fixes</h2>
    <p class="small">Focus on these changes first to get the biggest impact.</p>
    <ol>
"""
            for issue in top_issues:
                example_urls = ""
                if issue.affectedPages:
                    sample = issue.affectedPages[:3]
                    urls_str = "; ".join(p.url for p in sample)
                    if len(issue.affectedPages) > 3:
                        urls_str += f" (+{len(issue.affectedPages) - 3} more)"
                    example_urls = f"<br/><span class='small'><strong>Examples:</strong> {urls_str}</span>"
                
                html += f"""
      <li>
        <strong>{issue.title}</strong> – {issue.description}{example_urls}
      </li>
"""
            html += """
    </ol>
  </div>
"""
        
        html += f"""
  <div class="section">
    <h2>Key Stats</h2>
    <div class="grid">
      <div><strong>Pages</strong><br/>{report.stats.pagesCount}</div>
      <div><strong>Total Words</strong><br/>{report.stats.totalWords}</div>
      <div><strong>Avg Words/Page</strong><br/>{report.stats.avgWordsPerPage:.1f}</div>
      <div><strong>Total Media</strong><br/>{report.stats.totalMediaItems}</div>
      <div><strong>Avg Load Time</strong><br/>{report.stats.avgLoadMs:.0f} ms</div>
      <div><strong>Median Load Time</strong><br/>{report.stats.medianLoadMs:.0f} ms</div>
      <div><strong>P90 Load Time</strong><br/>{report.stats.p90LoadMs:.0f} ms</div>
      <div><strong>Slow Pages (&gt;1500ms)</strong><br/>{report.stats.slowPagesCount}</div>
      <div><strong>Very Slow Pages (&gt;3000ms)</strong><br/>{report.stats.verySlowPagesCount}</div>
      <div><strong>Avg Page Size</strong><br/>{report.stats.avgPageSizeKb:.1f} KB</div>
      <div><strong>Max Page Size</strong><br/>{report.stats.maxPageSizeKb:.1f} KB</div>
    </div>
  </div>

  <div class="section">
    <h2>HTTP Statuses</h2>
    <ul>
      {"".join(f"<li>{code}: {count}</li>" for code, count in report.stats.statusCounts.items())}
    </ul>
  </div>

  <div class="section">
    <h2>Category Scores & Issues</h2>
    <div class="grid">
"""
        
        for cat in report.categories:
            html += f"""
      <div style="page-break-inside: avoid; margin-bottom: 1rem;">
        <h3>{cat.category.title()}</h3>
        <div class="score" style="font-size:1.6rem">{cat.score}/100</div>
"""
            for issue in cat.issues:
                html += f"""
        <div style="margin-top: 0.5rem; margin-bottom: 0.5rem;">
          <p><strong>{issue.title}</strong> – {issue.description}</p>
"""
                if issue.affectedPages:
                    html += "<ul>"
                    for p in issue.affectedPages[:50]:  # limit to 50 per issue in PDF
                        note = f" — {p.note}" if p.note else ""
                        html += f"<li>{p.url}{note}</li>"
                    html += "</ul>"
                    if len(issue.affectedPages) > 50:
                        html += f"<p class='small'>+ {len(issue.affectedPages) - 50} more pages not shown…</p>"
                html += "</div>"
            html += "</div>"
        
        html += """    </div>
  </div>
"""
        
        # Add Competitors Section if competitors are provided
        if competitor_reports:
            html += """
  <div class="section" style="page-break-before: always;">
    <h2>Competitor Comparison</h2>
    <p class="small">Summary reports for competitor sites analyzed alongside this audit.</p>
"""
            for comp_report in competitor_reports:
                html += f"""
    <div style="page-break-inside: avoid; margin-bottom: 2rem; padding: 1rem; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 0.5rem;">
      <h3>{comp_report.baseUrl or comp_report.runId}</h3>
      <div class="score" style="font-size: 1.8rem; margin: 0.5rem 0;">{comp_report.overallScore}/100</div>
      
      <div class="grid" style="margin-top: 1rem;">
        <div><strong>Pages</strong><br/>{comp_report.stats.pagesCount}</div>
        <div><strong>Total Words</strong><br/>{comp_report.stats.totalWords}</div>
        <div><strong>Avg Words/Page</strong><br/>{comp_report.stats.avgWordsPerPage:.1f}</div>
        <div><strong>Total Media</strong><br/>{comp_report.stats.totalMediaItems}</div>
        <div><strong>Avg Load Time</strong><br/>{comp_report.stats.avgLoadMs:.0f} ms</div>
        <div><strong>P90 Load Time</strong><br/>{comp_report.stats.p90LoadMs:.0f} ms</div>
        <div><strong>Slow Pages</strong><br/>{comp_report.stats.slowPagesCount}</div>
        <div><strong>Very Slow Pages</strong><br/>{comp_report.stats.verySlowPagesCount}</div>
        <div><strong>Avg Page Size</strong><br/>{comp_report.stats.avgPageSizeKb:.1f} KB</div>
      </div>
      
      <div style="margin-top: 1rem;">
        <h4>Category Scores</h4>
        <div class="grid">
"""
                for cat in comp_report.categories:
                    html += f"""
          <div>
            <strong>{cat.category.title()}</strong><br/>
            <span style="font-size: 1.2rem; font-weight: 600;">{cat.score}/100</span>
          </div>
"""
                html += """
        </div>
      </div>
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
        
        return ComparisonReport(
            primaryUrl=payload.primaryUrl,
            competitors=payload.competitors,
            siteReports=site_reports,
            scoreComparison=score_comp,
            performanceComparison=perf_comp,
            contentComparison=content_comp,
            seoComparison=seo_comp,
            structureComparison=structure_comp,
            opportunitySummary=opps
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
<html>
<head>
<style>
body {{
  font-family: Arial, sans-serif;
  padding: 40px;
  background: #f8fafc;
}}
h1, h2, h3 {{
  margin-bottom: 8px;
}}
.section {{
  background: #ffffff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 25px;
  border: 1px solid #e5e7eb;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
}}
th, td {{
  border: 1px solid #d1d5db;
  padding: 8px;
  font-size: 14px;
  text-align: left;
}}
th {{
  background: #f3f4f6;
}}
.small {{
  font-size: 12px;
  color: #444;
}}
pre {{
  font-size: 10px;
  overflow-x: auto;
  background: #f9fafb;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
}}
</style>
</head>
<body>
"""
    
    # Cover Page
    html += f"""
<div class="section">
  <h1>Competitor Battle Report</h1>
  <p><strong>Your site:</strong> {primary}</p>
  <p><strong>Competitors:</strong> {", ".join(competitors)}</p>
  <p class="small">Generated by SiteInsite</p>
</div>
"""
    
    # Score Showdown Table
    html += """
<div class="section">
  <h2>Score Comparison</h2>
  <table>
    <tr>
      <th>Metric</th>
      <th>Your Site</th>
"""
    for comp in competitors:
        html += f"<th>{comp}</th>"
    html += "</tr>"
    
    for metric, values in report.scoreComparison.items():
        html += f"<tr><td>{metric.title()}</td>"
        html += f"<td>{values.get(primary, 'N/A')}</td>"
        for comp in competitors:
            html += f"<td>{values.get(comp, 'N/A')}</td>"
        html += "</tr>"
    
    html += """
  </table>
</div>
"""
    
    # Content Depth Comparison
    html += """
<div class="section">
  <h2>Content Depth</h2>
  <table>
    <tr><th>Site</th><th>Total Words</th><th>Avg Words/Page</th><th>Long-Form Pages (>600 words)</th></tr>
"""
    for site in report.siteReports:
        rpt = site.report
        long_form = calculate_long_form_pages(site)
        html += f"""
    <tr>
      <td>{site.url}</td>
      <td>{rpt.stats.totalWords:,}</td>
      <td>{rpt.stats.avgWordsPerPage:.1f}</td>
      <td>{long_form}</td>
    </tr>"""
    html += """
  </table>
</div>
"""
    
    # Performance Showdown
    html += """
<div class="section">
  <h2>Performance Comparison</h2>
  <table>
    <tr><th>Site</th><th>Avg Load (ms)</th><th>P90 Load (ms)</th><th>Slow Pages</th><th>Very Slow</th></tr>
"""
    for site in report.siteReports:
        s = site.report.stats
        html += f"""
    <tr>
      <td>{site.url}</td>
      <td>{s.avgLoadMs:.0f}</td>
      <td>{s.p90LoadMs:.0f}</td>
      <td>{s.slowPagesCount}</td>
      <td>{s.verySlowPagesCount}</td>
    </tr>"""
    html += "</table></div>"
    
    # Technical SEO / Indexability Table
    html += """
<div class="section">
  <h2>Technical SEO Comparison</h2>
  <table>
    <tr><th>Site</th><th>Noindex Pages</th><th>Missing Sitemap</th><th>Missing Robots</th><th>Missing Viewport</th></tr>
"""
    for site in report.siteReports:
        rpt = site.report
        noindex_count = count_noindex_pages(site)
        sitemap_missing = check_sitemap_missing(site)
        robots_missing = check_robots_missing(site)
        no_viewport_count = count_no_viewport_pages(site)
        html += f"""
    <tr>
      <td>{site.url}</td>
      <td>{noindex_count}</td>
      <td>{'Yes' if sitemap_missing else 'No'}</td>
      <td>{'Yes' if robots_missing else 'No'}</td>
      <td>{no_viewport_count}</td>
    </tr>"""
    html += "</table></div>"
    
    # Opportunity Summary Section
    html += """
<div class="section">
  <h2>Top Opportunities</h2>
  <ul>
"""
    for opp in report.opportunitySummary:
        html += f"<li>{opp}</li>"
    html += "</ul></div>"
    
    # Optional: Individual Reports Appendix
    html += """
<div class="section">
  <h2>Full Reports</h2>
  <p class="small">Each site's full InsightReport is attached below.</p>
</div>
"""
    
    for site in report.siteReports:
        # Serialize report to JSON (compatible with both Pydantic v1 and v2)
        try:
            # Try Pydantic v2 method first
            report_json = site.report.model_dump_json(indent=2)
        except AttributeError:
            # Fall back to Pydantic v1 method
            try:
                report_json = site.report.json(indent=2)
            except AttributeError:
                # Last resort: use dict() and json.dumps
                report_dict = site.report.dict() if hasattr(site.report, 'dict') else site.report.model_dump()
                report_json = json.dumps(report_dict, indent=2, default=str)
        
        html += f"""
    <div class="section">
      <h3>{site.url}</h3>
      <pre class="small">{report_json}</pre>
    </div>
    """
    
    # Close HTML
    html += "</body></html>"
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

