/**
 * TypeScript type definitions for SiteInsite API responses and requests.
 */

export interface StartRunRequest {
  url: string;
  maxPages?: number;
  maxDepth?: number;
  concurrency?: number;
  renderBudget?: number;
  botAvoidanceEnabled?: boolean;
  perfMode?: "controlled" | "realistic" | "stress";
}

export interface RunProgress {
  runId: string;
  queued: number;
  visited: number;
  errors: number;
  etaSeconds?: number;
  hosts: Record<string, number>;
}

export interface PageSummary {
  pageId: string;
  url: string;
  contentType: string;
  title?: string;
  words: number;
  images: number;
  links: number;
  status?: number;
  status_code?: number;
  path?: string;
  type?: string;
  load_time_ms?: number;
  content_length_bytes?: number;
}

export interface PageDetail {
  summary: PageSummary;
  meta: Record<string, any>;
  text?: string;
  htmlExcerpt?: string;
  headings: string[];
  images: string[];
  links: string[];
  tables: any[];
  structuredData: any[];
  stats: Record<string, any>;
}

// Review and Confirmation Types
export interface BusinessProfile {
  name?: string;
  tagline?: string;
  phones: string[];
  emails: string[];
  socials: Record<string, string>;
  logo?: string;
  brand_colors: string[];
  sources: string[];
}

export interface ItemBase {
  id: string;
  title: string;
  description?: string;
  image?: string;
  price?: string;
  cta?: Record<string, string>;
  confidence: number;
  sources: string[];
}

export interface Location {
  id: string;
  name?: string;
  address?: string;
  phone?: string;
  hours?: Record<string, string>;
  latlng?: [number, number];
  confidence: number;
  sources: string[];
}

export interface NavItem {
  label: string;
  href?: string;
  children: NavItem[];
}

export interface DraftModel {
  runId: string;
  business: BusinessProfile;
  services: ItemBase[];
  products: ItemBase[];
  menu: ItemBase[];
  locations: Location[];
  team: ItemBase[];
  faqs: any[];
  testimonials: any[];
  policies: any[];
  media: any[];
  sitemap: {
    primary: NavItem[];
    secondary: NavItem[];
    footer: NavItem[];
  };
}

export interface ConfirmRequest {
  draft: DraftModel;
}

export interface FilterOptions {
  query: string;
  type: string;
  minWords: number;
}

export interface PageResult {
  pageId: string;
  title: string;
  url: string;
  type: string;
  words: number;
  images: number;
  links: number;
  status: number;
  status_code?: number;
  load_time_ms?: number | null;
  content_length_bytes?: number | null;
}

export interface SortOptions {
  field: string;
  direction: 'asc' | 'desc';
}

// Insight Report Types
export interface InsightAffectedPage {
  url: string;
  note?: string | null;
}

export interface InsightIssue {
  id: string;
  category: "performance" | "seo" | "content" | "structure";
  severity: "low" | "medium" | "high";
  title: string;
  description: string;
  affectedPages: InsightAffectedPage[];
}

export interface InsightCategoryScore {
  category: "performance" | "seo" | "content" | "structure";
  score: number; // 0–100
  issues: InsightIssue[];
}

export interface InsightStats {
  pagesCount: number;
  totalWords: number;
  avgWordsPerPage: number;
  totalMediaItems: number;
  avgMediaPerPage: number;
  statusCounts: Record<string, number>; // e.g. {"200": 18, "404": 1, "500": 1}
  avgLoadMs: number;
  medianLoadMs: number;
  p90LoadMs: number;
  p95LoadMs: number;
  slowPagesCount: number;
  verySlowPagesCount: number;
  avgPageSizeKb: number;
  maxPageSizeKb: number;
}

export interface KeywordMetrics {
  keyword: string;
  pages_used: number;
  total_occurrences: number;
  title_hits: number;
  h1_hits: number;
  h2_hits: number;
  slug_hits: number;
  anchor_hits: number;
  avg_density: number; // 0.0 – 1.0
  coverage_score: number; // 0–100
  onpage_score: number; // 0–100
  total_score: number; // 0–100
}

export interface SiteKeywordSummary {
  run_id: string;
  domain?: string | null;
  overall_keyword_score: number; // 0–100
  total_focus_keywords: number;
  keyword_metrics: KeywordMetrics[];
}

// [SEO_UNIFIED_SECTION] Unified SEO structure
export interface KeywordCoverageSummary {
  overall_score: number; // 0–100
  focus_keywords: string[];
  keyword_metrics: KeywordMetrics[];
}

export interface SeoHealthSection {
  score: number; // 0–100
  issues: InsightIssue[];
}

export interface SEOSection {
  health?: SeoHealthSection | null;
  keyword_coverage?: KeywordCoverageSummary | null;
}

export interface InsightReport {
  runId: string;
  baseUrl: string | null;
  overallScore: number;
  categories: InsightCategoryScore[];
  stats: InsightStats;
  // New context-aware metrics
  contentDepthScore?: number | null; // 0-100
  navType?: string | null; // "single_page", "simple_nav", "multi_section", "app_style", "implicit_content_links", "none_detected"
  crawlabilityScore?: number | null; // 0-100
  // Performance measurement metadata
  perfMode?: string | null; // "controlled", "realistic", "stress"
  performanceConsistency?: string | null; // "stable", "unstable"
  consistencyNote?: string | null; // Human-readable note about consistency
  // [SEO_UNIFIED_SECTION] Unified SEO section (health + keyword coverage)
  seo?: SEOSection | null;
  // Backward compatibility
  seo_keywords?: SiteKeywordSummary | null;
}

// Competitor Comparison Types
export interface ComparedSite {
  url: string;
  report: InsightReport;
}

export interface ComparisonRow {
  metric: string; // e.g. "avg_load_time_ms", "seo_score", "content_depth_score"
  label: string; // Human-readable label, e.g. "Avg Load Time", "SEO Score"
  primaryValue: number | string | null;
  competitorValue: number | string | null;
  difference: number | null; // null for non-numeric metrics
  direction: "better" | "worse" | "neutral" | "different"; // "different" for nav_type
  verdict: string; // Human-readable verdict, e.g. "You're slower", "Slightly behind"
}

export interface ComparisonReport {
  primaryUrl: string;
  competitors: string[];
  siteReports: ComparedSite[];
  scoreComparison: Record<string, Record<string, number>>;
  performanceComparison: Record<string, Record<string, number>>;
  contentComparison: Record<string, Record<string, number>>;
  seoComparison: Record<string, Record<string, number>>;
  structureComparison: Record<string, Record<string, number>>;
  opportunitySummary: string[];
  // New structured comparison array
  comparisons: ComparisonRow[];
}