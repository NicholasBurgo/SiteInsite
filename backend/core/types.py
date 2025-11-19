from pydantic import BaseModel, Field, root_validator
from typing import Any, List, Optional, Dict, Tuple, Literal

class StartRunRequest(BaseModel):
    url: str
    maxPages: int | None = None
    maxDepth: int = 5
    concurrency: int | None = None
    renderBudget: float | None = None
    botAvoidanceEnabled: bool | None = None
    perfMode: Literal["controlled", "realistic", "stress"] | None = None

class RunProgress(BaseModel):
    runId: str
    queued: int
    visited: int
    errors: int
    etaSeconds: int | None
    hosts: dict[str, int]

class PageSummary(BaseModel):
    pageId: str
    url: str
    contentType: str
    title: str | None = None
    words: int = 0
    images: int = 0
    links: int = 0
    status: int | None = None
    path: str | None = None
    type: str | None = None  # HTML/PDF/DOCX/JSON/CSV/IMG
    load_time_ms: Optional[int] = None
    content_length_bytes: Optional[int] = None
    status_code: int | None = None
    page_type: str | None = None  # article, landing, catalog, product, media_gallery, contact, utility, generic

    @root_validator(pre=True)
    def _sync_status_codes(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        status = values.get("status")
        status_code = values.get("status_code")
        if status is None and status_code is not None:
            values["status"] = status_code
        elif status_code is None and status is not None:
            values["status_code"] = status
        return values

class PageDetail(BaseModel):
    summary: PageSummary
    meta: dict
    text: str | None = None
    htmlExcerpt: str | None = None
    headings: list[str] = []
    images: list[str] = []
    links: list[str] = []
    tables: list[dict] = []
    structuredData: list[dict] = []
    stats: dict = {}


class PageResult(BaseModel):
    pageId: str
    url: str
    contentType: str | None = None
    title: str | None = None
    words: int = 0
    images: int = 0
    links: int = 0
    status: int | None = None
    status_code: int | None = None
    path: str | None = None
    type: str | None = None
    load_time_ms: Optional[int] = None
    content_length_bytes: Optional[int] = None
    page_type: str | None = None  # article, landing, catalog, product, media_gallery, contact, utility, generic

    @root_validator(pre=True)
    def _sync_status_codes(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        status = values.get("status")
        status_code = values.get("status_code")
        if status is None and status_code is not None:
            values["status"] = status_code
        elif status_code is None and status is not None:
            values["status_code"] = status
        return values

# Review and Confirmation Models
class BusinessProfile(BaseModel):
    name: str | None = None
    tagline: str | None = None
    phones: list[str] = []
    emails: list[str] = []
    socials: dict[str, str] = {}  # {"facebook": "...", "instagram": "..."}
    logo: str | None = None
    brand_colors: list[str] = []  # hex list
    sources: list[str] = []       # pageIds

class ItemBase(BaseModel):
    id: str
    title: str
    description: str | None = None
    image: str | None = None
    price: str | None = None
    cta: dict[str, str] | None = None
    confidence: float = 0.0
    sources: list[str] = []

class Location(BaseModel):
    id: str
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    hours: dict[str, str] | None = None
    latlng: tuple[float, float] | None = None
    confidence: float = 0.0
    sources: list[str] = []

class NavItem(BaseModel):
    label: str
    href: str | None = None
    children: list["NavItem"] = []

class DraftModel(BaseModel):
    runId: str
    business: BusinessProfile
    services: list[ItemBase] = []
    products: list[ItemBase] = []
    menu: list[ItemBase] = []
    locations: list[Location] = []
    team: list[ItemBase] = []          # use title as name, description as role
    faqs: list[dict] = []              # {q,a,confidence,sources}
    testimonials: list[dict] = []      # {author,text,confidence,sources}
    policies: list[dict] = []          # privacy/terms
    media: list[dict] = []             # {src,alt,role}
    sitemap: dict = Field(default_factory=lambda: {  # proposed navs
        "primary": [],
        "secondary": [],
        "footer": [],
    })

class ConfirmRequest(BaseModel):
    draft: DraftModel

# Insight Report Models
class InsightAffectedPage(BaseModel):
    url: str
    note: str | None = None  # e.g. "1875 ms", "No meta description", "42 words"

class InsightIssue(BaseModel):
    id: str
    category: Literal["performance", "seo", "content", "structure"]
    severity: Literal["low", "medium", "high"]
    title: str
    description: str
    affectedPages: list[InsightAffectedPage] = []

class InsightCategoryScore(BaseModel):
    category: Literal["performance", "seo", "content", "structure"]
    score: int  # 0–100
    issues: list[InsightIssue] = []

class InsightStats(BaseModel):
    pagesCount: int
    totalWords: int
    avgWordsPerPage: float
    totalMediaItems: int
    avgMediaPerPage: float
    statusCounts: dict[str, int]  # e.g. {"200": 18, "404": 1, "500": 1}
    avgLoadMs: float
    medianLoadMs: float
    p90LoadMs: float
    p95LoadMs: float
    slowPagesCount: int
    verySlowPagesCount: int
    avgPageSizeKb: float
    maxPageSizeKb: float
    badPagesCount: int = 0  # 404, 410, 5xx pages
    brokenInternalLinksCount: int = 0  # Total broken internal links found

class InsightReport(BaseModel):
    runId: str
    baseUrl: str | None
    overallScore: int
    categories: list[InsightCategoryScore]
    stats: InsightStats
    # New context-aware metrics
    contentDepthScore: float | None = None  # 0-100
    navType: str | None = None  # "single_page", "simple_nav", "multi_section", "app_style", "implicit_content_links", "none_detected"
    crawlabilityScore: float | None = None  # 0-100
    # Performance measurement metadata
    perfMode: str | None = None  # "controlled", "realistic", "stress"
    performanceConsistency: str | None = None  # "stable", "unstable"
    consistencyNote: str | None = None  # Human-readable note about consistency

# Competitor Comparison Models
class ComparedSite(BaseModel):
    url: str
    report: InsightReport

class ComparisonMetric(BaseModel):
    name: str
    primary: float | int | str
    competitors: dict[str, float | int | str]

class ComparisonRow(BaseModel):
    """A single comparison row for side-by-side comparison."""
    metric: str  # e.g. "avg_load_time_ms", "seo_score", "content_depth_score"
    label: str  # Human-readable label, e.g. "Avg Load Time", "SEO Score"
    primaryValue: float | int | str | None
    competitorValue: float | int | str | None
    difference: float | int | None  # null for non-numeric metrics
    direction: Literal["better", "worse", "neutral", "different"]  # "different" for nav_type
    verdict: str  # Human-readable verdict, e.g. "You're slower", "Slightly behind"
    category: str | None = None  # Optional category for filtering: "performance", "seo", "content", "structure", "overall"

class ComparisonReport(BaseModel):
    primaryUrl: str
    competitors: list[str]
    siteReports: list[ComparedSite]
    scoreComparison: dict[str, dict[str, float]]  # e.g. {"overall": {"https://primary.com": 75, "https://comp1.com": 80}}
    performanceComparison: dict[str, dict[str, float]]
    contentComparison: dict[str, dict[str, float]]
    seoComparison: dict[str, dict[str, float]]
    structureComparison: dict[str, dict[str, float]]
    opportunitySummary: list[str]  # Generated insights
    # New structured comparison array
    comparisons: list[ComparisonRow] = []  # Structured comparison rows for UI/PDF

class ComparePayload(BaseModel):
    primaryUrl: str
    competitors: list[str]
    botAvoidanceEnabled: bool | None = None