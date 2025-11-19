"""
Competitor comparison and opportunity generation.
Analyzes multiple InsightReports and generates actionable insights.
"""
from typing import List
from backend.core.types import ComparedSite


def generate_opportunities(reports: List[ComparedSite]) -> List[str]:
    """
    Generate opportunity insights by comparing the primary site against competitors.
    
    Args:
        reports: List of ComparedSite objects, where the first one is the primary site
        
    Returns:
        List of opportunity strings describing gaps and improvements
    """
    if len(reports) < 2:
        return []
    
    primary = reports[0]
    competitors = reports[1:]
    
    findings = []
    
    # 1. Content depth comparison
    primary_words = primary.report.stats.totalWords
    competitor_words = [c.report.stats.totalWords for c in competitors]
    
    for comp in competitors:
        comp_words = comp.report.stats.totalWords
        if comp_words > primary_words * 1.5:
            findings.append(
                f"{comp.url} publishes {comp_words:,} words vs {primary.url} at {primary_words:,}. "
                f"Consider adding more long-form content."
            )
        elif comp_words > primary_words * 1.2:
            findings.append(
                f"{comp.url} has {comp_words:,} words compared to {primary.url}'s {primary_words:,}. "
                f"Opportunity to expand content depth."
            )
    
    # 2. Performance gaps
    primary_load = primary.report.stats.avgLoadMs
    competitor_loads = [c.report.stats.avgLoadMs for c in competitors]
    min_competitor_load = min(competitor_loads) if competitor_loads else primary_load
    
    if primary_load > min_competitor_load * 1.2:
        fastest_competitor = min(competitors, key=lambda c: c.report.stats.avgLoadMs)
        findings.append(
            f"Competitors load faster ({fastest_competitor.report.stats.avgLoadMs:.0f}ms avg vs "
            f"{primary_load:.0f}ms). Optimize images, JavaScript, and server response time."
        )
    
    # Check P90 load times
    primary_p90 = primary.report.stats.p90LoadMs
    competitor_p90s = [c.report.stats.p90LoadMs for c in competitors]
    if competitor_p90s and primary_p90 > min(competitor_p90s) * 1.3:
        findings.append(
            f"P90 load time ({primary_p90:.0f}ms) is significantly higher than competitors. "
            f"Focus on optimizing slowest pages."
        )
    
    # 3. SEO gaps
    primary_seo = primary.report.overallScore
    competitor_seos = [c.report.overallScore for c in competitors]
    max_competitor_seo = max(competitor_seos) if competitor_seos else primary_seo
    
    if primary_seo < max_competitor_seo - 10:
        best_competitor = max(competitors, key=lambda c: c.report.overallScore)
        findings.append(
            f"Competitors have stronger overall scores ({best_competitor.report.overallScore} vs {primary_seo}). "
            f"Review on-page SEO elements (titles, descriptions, headings)."
        )
    
    # Check specific SEO category
    primary_seo_score = next(
        (cat.score for cat in primary.report.categories if cat.category == "seo"),
        0
    )
    competitor_seo_scores = [
        next((cat.score for cat in c.report.categories if cat.category == "seo"), 0)
        for c in competitors
    ]
    max_competitor_seo_score = max(competitor_seo_scores) if competitor_seo_scores else primary_seo_score
    
    if primary_seo_score < max_competitor_seo_score - 10:
        findings.append(
            f"Competitors have stronger on-page SEO scores. "
            f"Focus on improving meta titles, descriptions, and heading structure."
        )
    
    # 4. Content quality comparison
    primary_avg_words = primary.report.stats.avgWordsPerPage
    competitor_avg_words = [c.report.stats.avgWordsPerPage for c in competitors]
    max_competitor_avg = max(competitor_avg_words) if competitor_avg_words else primary_avg_words
    
    if primary_avg_words < max_competitor_avg * 0.8:
        findings.append(
            f"Average words per page ({primary_avg_words:.0f}) is lower than competitors. "
            f"Consider expanding page content depth."
        )
    
    # 5. Performance category comparison
    primary_perf_score = next(
        (cat.score for cat in primary.report.categories if cat.category == "performance"),
        0
    )
    competitor_perf_scores = [
        next((cat.score for cat in c.report.categories if cat.category == "performance"), 0)
        for c in competitors
    ]
    max_competitor_perf = max(competitor_perf_scores) if competitor_perf_scores else primary_perf_score
    
    if primary_perf_score < max_competitor_perf - 10:
        findings.append(
            f"Performance score ({primary_perf_score}) trails competitors. "
            f"Review page load times, image optimization, and resource loading strategies."
        )
    
    # 6. Structure comparison
    primary_structure_score = next(
        (cat.score for cat in primary.report.categories if cat.category == "structure"),
        0
    )
    competitor_structure_scores = [
        next((cat.score for cat in c.report.categories if cat.category == "structure"), 0)
        for c in competitors
    ]
    max_competitor_structure = max(competitor_structure_scores) if competitor_structure_scores else primary_structure_score
    
    if primary_structure_score < max_competitor_structure - 10:
        findings.append(
            f"Site structure score ({primary_structure_score}) is lower than competitors. "
            f"Review navigation, footer, and URL structure."
        )
    
    # 7. Page count comparison (more pages might indicate better content coverage)
    primary_pages = primary.report.stats.pagesCount
    competitor_pages = [c.report.stats.pagesCount for c in competitors]
    max_competitor_pages = max(competitor_pages) if competitor_pages else primary_pages
    
    if primary_pages < max_competitor_pages * 0.7:
        findings.append(
            f"Site has fewer pages ({primary_pages}) compared to competitors. "
            f"Consider expanding content coverage and adding more pages."
        )
    
    # 8. Media richness comparison
    primary_media = primary.report.stats.totalMediaItems
    competitor_media = [c.report.stats.totalMediaItems for c in competitors]
    max_competitor_media = max(competitor_media) if competitor_media else primary_media
    
    if primary_media < max_competitor_media * 0.7:
        findings.append(
            f"Site has fewer media items ({primary_media}) compared to competitors. "
            f"Consider adding more images, videos, or other media to enhance engagement."
        )
    
    # 9. Error rate comparison
    primary_errors = sum(
        count for status, count in primary.report.stats.statusCounts.items()
        if status.startswith("4") or status.startswith("5")
    )
    competitor_errors = [
        sum(
            count for status, count in c.report.stats.statusCounts.items()
            if status.startswith("4") or status.startswith("5")
        )
        for c in competitors
    ]
    
    if competitor_errors and primary_errors > max(competitor_errors):
        findings.append(
            f"Site has more error pages ({primary_errors}) than competitors. "
            f"Review and fix broken links and error pages."
        )
    
    # 10. Page size comparison
    primary_max_size = primary.report.stats.maxPageSizeKb
    competitor_max_sizes = [c.report.stats.maxPageSizeKb for c in competitors]
    avg_competitor_max = sum(competitor_max_sizes) / len(competitor_max_sizes) if competitor_max_sizes else primary_max_size
    
    if primary_max_size > avg_competitor_max * 1.5:
        findings.append(
            f"Largest page size ({primary_max_size:.0f}KB) is significantly larger than competitors. "
            f"Optimize page weight through compression and resource optimization."
        )
    
    return findings

