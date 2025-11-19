# Universal Site Extractor v2 - Deep Project Scan

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Complete File Structure](#complete-file-structure)
4. [Core Functionality](#core-functionality)
5. [Data Flow & Processing](#data-flow--processing)
6. [Output Files & Data Structures](#output-files--data-structures)
7. [Frontend Components](#frontend-components)
8. [Backend API Endpoints](#backend-api-endpoints)
9. [Advanced Features](#advanced-features)
10. [Configuration & Environment](#configuration--environment)
11. [Dependencies & Technologies](#dependencies--technologies)
12. [Scripts & Automation](#scripts--automation)
13. [Testing & Development](#testing--development)
14. [Deployment](#deployment)

---

## Project Overview

**Universal Site Extractor v2** is a full-stack web scraping and content extraction system designed to crawl websites, extract structured content, and prepare it for site generation. It's a complete rewrite that provides:

- **Multi-format extraction**: HTML, PDF, DOCX, JSON, CSV, and images
- **Smart content extraction**: Uses readability, trafilatura, and custom extractors
- **Real-time monitoring**: Live progress updates and statistics
- **Confirmation workflow**: Review and edit extracted data before seeding
- **Seed generation**: Export generator-ready JSON for site building
- **Bot avoidance**: Advanced anti-detection techniques for protected sites
- **Advanced scraper**: Specialized scraper for news sites with Cloudflare protection

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + TypeScript)             │
│  - Generator UI, Review Interface, Confirmation Page         │
│  - Real-time progress monitoring                             │
│  - Advanced filtering and search                            │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────────┐
│              Backend (FastAPI + Python)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Crawler    │  │  Extractors  │  │   Storage    │     │
│  │  - Frontier  │  │  - HTML      │  │  - Runs      │     │
│  │  - Fetcher   │  │  - PDF       │  │  - Confirm   │     │
│  │  - Bot Avoid │  │  - DOCX      │  │  - Seed      │     │
│  └──────────────┘  │  - JSON/CSV  │  └──────────────┘     │
│                    │  - Images    │                        │
│                    └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│              Advanced Scraper (Optional)                     │
│  - Cloudflare bypass (FlareSolverr)                        │
│  - Proxy rotation                                           │
│  - Fingerprint spoofing                                     │
│  - Human behavior simulation                                │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User starts extraction** → Frontend sends request to `/api/runs/start`
2. **Crawler initializes** → Frontier creates URL queue, Fetcher prepares HTTP client
3. **Pages are crawled** → Concurrent requests with rate limiting
4. **Content is extracted** → Type-specific extractors process each page
5. **Data is stored** → RunStore saves pages, ConfirmationStore saves structured data
6. **User reviews** → Confirmation page allows editing navigation, footer, page content
7. **Seed is generated** → SeedBuilder combines edited data into generator-ready JSON

---

## Complete File Structure

```
SiteTestGenerator/
├── backend/                          # FastAPI Backend
│   ├── app.py                        # Main FastAPI application entry point
│   ├── requirements.txt              # Python dependencies
│   ├── pyproject.toml                # Python project configuration
│   ├── Dockerfile                    # Backend container configuration
│   ├── README.md                     # Backend-specific documentation
│   │
│   ├── core/                         # Core configuration and types
│   │   ├── __init__.py
│   │   ├── config.py                 # Settings and environment configuration
│   │   ├── deps.py                   # Dependency injection utilities
│   │   ├── types.py                  # Pydantic models (PageSummary, PageDetail, DraftModel, etc.)
│   │   └── utils.py                 # Utility functions
│   │
│   ├── crawl/                        # Crawling engine
│   │   ├── __init__.py
│   │   ├── runner.py                # Main orchestration (RunManager, RunState)
│   │   ├── frontier.py              # URL queue management (Frontier class)
│   │   ├── fetch.py                 # Async HTTP client (Fetcher, FetchResponse)
│   │   ├── render_pool.py           # Playwright browser pool (optional JS rendering)
│   │   ├── robots.py                # Robots.txt compliance
│   │   └── bot_avoidance.py         # Bot detection avoidance (BotAvoidanceStrategy)
│   │
│   ├── extract/                      # Content extractors
│   │   ├── __init__.py
│   │   ├── html.py                  # HTML content extraction (readability + trafilatura)
│   │   ├── pdfs.py                  # PDF text extraction (pypdf)
│   │   ├── docx_.py                 # DOCX document extraction (python-docx)
│   │   ├── json_csv.py              # JSON/CSV data extraction
│   │   ├── images.py                # Image metadata extraction (Pillow)
│   │   ├── nav_footer.py            # Navigation and footer extraction
│   │   ├── files_words_links.py     # Structured content extraction
│   │   ├── aggregate.py             # Business data aggregation (DraftModel builder)
│   │   └── rollups.py               # Cross-page analysis and rollups
│   │
│   ├── storage/                      # Data storage
│   │   ├── __init__.py
│   │   ├── runs.py                  # File-based run storage (RunStore)
│   │   ├── simhash.py               # Near-duplicate detection (SimHash)
│   │   ├── confirmation.py          # Confirmation data storage (ConfirmationStore)
│   │   └── seed.py                  # Seed generation utilities (SeedBuilder)
│   │
│   ├── routers/                      # API route handlers
│   │   ├── __init__.py
│   │   ├── runs.py                  # Run management endpoints
│   │   ├── pages.py                 # Page listing/details endpoints
│   │   ├── review.py                # Review and aggregation endpoints
│   │   └── confirm.py               # Confirmation workflow endpoints
│   │
│   └── scraper_advanced/             # Advanced news scraper (optional)
│       ├── __init__.py
│       ├── README.md                # Advanced scraper documentation
│       ├── config.yaml               # Scraper configuration
│       ├── Dockerfile                # Scraper container config
│       ├── cli.py                    # Command-line interface
│       ├── scraper.py                # Main scraper logic
│       ├── http_client.py            # Advanced HTTP client (curl_cffi)
│       ├── cloudflare_bypass.py      # Cloudflare protection bypass
│       ├── fingerprint_spoofer.py    # Browser fingerprint randomization
│       ├── proxy_manager.py          # Residential proxy rotation
│       ├── human_behavior.py         # Human-like browsing patterns
│       ├── selenium_fallback.py      # Undetected Chrome fallback
│       ├── article_extractor.py      # Clean article extraction
│       ├── config_loader.py          # YAML configuration loader
│       ├── demo.py                   # Demo script
│       └── example.py                # Example usage
│
├── frontend/                         # React Frontend
│   ├── index.html                   # HTML template
│   ├── package.json                 # Node.js dependencies
│   ├── package-lock.json            # Locked dependency versions
│   ├── tsconfig.json                # TypeScript configuration
│   ├── tsconfig.node.json           # TypeScript config for Node
│   ├── vite.config.ts               # Vite build configuration
│   ├── tailwind.config.js            # Tailwind CSS configuration
│   ├── postcss.config.js            # PostCSS configuration
│   ├── Dockerfile                   # Frontend container config
│   │
│   └── src/
│       ├── main.tsx                  # React entry point
│       ├── App.tsx                   # Main application component (routing)
│       ├── styles.css                # Tailwind CSS imports
│       │
│       ├── components/               # Reusable UI components
│       │   ├── TopBar.tsx           # Top navigation bar
│       │   ├── RunSummary.tsx      # Run progress summary
│       │   ├── RunFilters.tsx      # Page filtering controls
│       │   ├── RunTable.tsx         # Page table with virtualization
│       │   ├── PageDetail.tsx       # Page detail view
│       │   ├── PrimeTabs.tsx        # Navigation/footer editing tabs
│       │   ├── ContentTabs.tsx      # Page content editing tabs
│       │   ├── SummaryTab.tsx      # Summary statistics tab
│       │   ├── NavigationTree.tsx   # Hierarchical navigation tree
│       │   ├── ModeSwitch.tsx       # View mode switcher
│       │   ├── Checkpoint.tsx       # Checkpoint component
│       │   ├── CheckpointDropdown.tsx # Checkpoint selector
│       │   └── ThemeDemos.tsx       # Theme demonstration
│       │
│       ├── lib/                     # Utilities and types
│       │   ├── api.ts               # API client functions
│       │   ├── types.ts             # TypeScript interfaces
│       │   ├── api.confirm.ts       # Confirmation API client
│       │   └── types.confirm.ts     # Confirmation types
│       │
│       └── pages/                   # Page components
│           ├── Generator.tsx        # Main generator page
│           ├── SiteGenerator.tsx   # Site generator interface
│           ├── Review.tsx           # Review page
│           ├── RunView.tsx          # Run detail view
│           ├── ConfirmPage.tsx      # Confirmation workflow page
│           ├── ThemeDesigner.tsx    # Theme designer interface
│           │
│           └── tabs/                # Confirmation page tabs
│               ├── SummaryTab.tsx   # Run overview and statistics
│               ├── BusinessTab.tsx  # Business information
│               ├── AssetsTab.tsx    # Media and images
│               ├── ParagraphsTab.tsx # Text content
│               ├── NavbarTab.tsx    # Navigation structure
│               └── TruthTableTab.tsx # Unified data table
│
├── scripts/                         # Development scripts
│   ├── dev.sh                      # Linux/Mac dev startup
│   ├── dev.bat                     # Windows dev startup
│   ├── dev.py                      # Cross-platform dev script
│   ├── dev-fedora.sh               # Fedora-specific dev script
│   ├── build.sh                    # Linux/Mac build script
│   └── build.bat                   # Windows build script
│
├── runs/                            # Generated extraction data (gitignored)
│   └── {run_id}/                   # Per-run directories
│       ├── meta.json                # Run metadata
│       ├── pages.json               # All extracted pages
│       ├── pages_index.json         # Pages index for confirmation
│       ├── site.json                # Site-level data (nav, footer, brand)
│       ├── pages/                   # Individual page files
│       │   └── {page_id}.json      # Structured page content
│       └── seed/                    # Generated seed data
│           └── seed.json            # Generator-ready seed file
│
├── docker-compose.yml               # Multi-service Docker setup
├── env.example                      # Environment configuration template
├── LICENSE                          # MIT License
├── README.md                        # Main project documentation
├── CONFIRMATION_PAGE_README.md      # Confirmation page documentation
├── TESTING_GUIDE.md                 # Testing instructions
└── PROJECT_DEEP_SCAN.md             # This file

```

---

## Core Functionality

### 1. Web Crawling

**Frontier (URL Queue Management)**
- Maintains a queue of URLs to visit
- Enforces domain restrictions (only same domain)
- Depth limiting (max_depth parameter)
- Page limit (max_pages parameter)
- URL normalization and deduplication

**Fetcher (HTTP Client)**
- Async HTTP requests with aiohttp
- Rate limiting (global and per-host)
- Request timeout handling
- Bot avoidance integration
- Performance tracking (load_time_ms, content_length_bytes)

**Bot Avoidance**
- Randomized delays (0.6-2.4s default)
- Per-host request intervals
- Browser fingerprint spoofing
- Multiple browser profiles (Chrome, Safari, iOS)
- Bot detection (CAPTCHA, status codes)
- Header randomization

### 2. Content Extraction

**HTML Extraction** (`extract/html.py`)
- Uses `readability-lxml` for main content
- Uses `trafilatura` for text extraction
- Extracts:
  - Title (with heuristics for homepage detection)
  - Meta tags and Open Graph data
  - Links (internal/external classification)
  - Images (with alt text, dimensions)
  - Headings (h1-h6 hierarchy)
  - Tables
  - Structured data (JSON-LD, microdata)
  - Navigation structure
  - Footer content

**PDF Extraction** (`extract/pdfs.py`)
- Uses `pypdf` for text extraction
- Extracts metadata (title, author, creation date)
- Page count
- Full text content

**DOCX Extraction** (`extract/docx_.py`)
- Uses `python-docx` for document parsing
- Extracts headings with hierarchy
- Document properties (title, author, keywords)
- Full text content

**JSON/CSV Extraction** (`extract/json_csv.py`)
- JSON: Schema inference, sample data extraction
- CSV: Header detection, row parsing, sample rows

**Image Extraction** (`extract/images.py`)
- Uses `Pillow` for image processing
- Extracts dimensions, format, EXIF data
- Metadata extraction

**Structured Content** (`extract/files_words_links.py`)
- Organizes content into:
  - Media (images, videos, GIFs)
  - Files (downloadable PDFs, DOCX, etc.)
  - Words (headings, paragraphs, word count)
  - Links (internal, external, broken)

### 3. Data Storage

**RunStore** (`storage/runs.py`)
- File-based storage in `runs/{run_id}/`
- Saves `pages.json` with all extracted pages
- Maintains `meta.json` with run metadata:
  - Run status (running, completed)
  - Start/completion timestamps
  - Page IDs list
  - Errors log
  - Performance summary (avg_load_ms, fastest/slowest pages)
- Progress tracking
- Finalization with performance metrics

**ConfirmationStore** (`storage/confirmation.py`)
- Manages confirmation workflow data
- `site.json`: Navigation, footer, brand info
- `pages_index.json`: List of all pages with metadata
- `pages/{page_id}.json`: Structured page content
- Methods for updating navigation, footer, page content

**SeedBuilder** (`storage/seed.py`)
- Combines edited site data with page content
- Generates `seed.json` in generator-ready format
- Maps content to components (hero, section, gallery, files)

**SimHash** (`storage/simhash.py`)
- Near-duplicate detection using SimHash algorithm
- Prevents crawling duplicate content

### 4. Business Data Aggregation

**BusinessAggregator** (`extract/aggregate.py`)
- Analyzes all extracted pages
- Builds `DraftModel` with:
  - Business profile (name, tagline, phones, emails, socials, logo, brand colors)
  - Services (extracted from service pages)
  - Products (extracted from product pages)
  - Menu items (for restaurants)
  - Locations (addresses, phones, hours)
  - Team members
  - FAQs
  - Testimonials
  - Policies (privacy, terms)
  - Media files
  - Sitemap structure

**RollupGenerator** (`extract/rollups.py`)
- Cross-page analysis
- Generates rollups for:
  - Contacts (emails, phones, addresses)
  - Services (frequency analysis)
  - Navigation (common nav items)
  - Images (domains, types, alt text analysis)
  - Top paths (most common URL patterns)
  - Word count distribution
  - Content type distribution
  - Error summary

---

## Data Flow & Processing

### Extraction Workflow

1. **User Input**
   - URL to crawl
   - Max pages (default: 400)
   - Max depth (default: 5)
   - Concurrency (default: 12)
   - Bot avoidance enabled/disabled

2. **Crawler Initialization**
   - RunManager creates RunState
   - Frontier initialized with start URL
   - Fetcher created with settings
   - BotAvoidanceStrategy optional

3. **Crawling Loop**
   - Frontier provides next batch of URLs
   - Fetcher makes async HTTP requests
   - Bot avoidance applies delays and headers
   - Response is checked for bot blocks

4. **Content Extraction**
   - Content type detected
   - Appropriate extractor called
   - Structured content saved to `pages/{page_id}.json`
   - Page added to pages_index.json
   - Links extracted and added to frontier

5. **Site Data Extraction** (first page only)
   - Navigation extracted
   - Footer extracted
   - Brand info extracted
   - Saved to `site.json`

6. **Run Finalization**
   - Performance metrics calculated
   - Meta.json updated with completion status
   - Run marked as complete

### Confirmation Workflow

1. **User Reviews Data**
   - Accesses `/confirm/{run_id}`
   - Views navigation, footer, pages

2. **Editing**
   - Navigation: Drag-and-drop reordering
   - Footer: Edit columns, socials, contact
   - Pages: Edit title, description, media alt text, links

3. **Seed Generation**
   - User clicks "Generate Seed"
   - SeedBuilder combines:
     - Edited `site.json` (nav, footer)
     - Selected page files from `pages/`
   - Creates `seed/seed.json` with component structure

---

## Output Files & Data Structures

### Run Directory Structure

```
runs/{run_id}/
├── meta.json              # Run metadata
├── pages.json             # All extracted pages (full PageDetail objects)
├── pages_index.json       # Pages index (lightweight summaries)
├── site.json              # Site-level data
├── pages/                 # Individual page files
│   └── {page_id}.json    # Structured page content
└── seed/                  # Generated seed (after confirmation)
    └── seed.json         # Generator-ready seed file
```

### meta.json Structure

```json
{
  "run_id": "1763062060",
  "started_at": 1763062060.7766647,
  "status": "completed",
  "completed_at": 1763062070.9758418,
  "pages": ["page_id1", "page_id2", ...],
  "errors": [
    {
      "url": "https://example.com/broken",
      "error_type": "fetch_failed",
      "timestamp": 1763062065.123
    }
  ],
  "botAvoidanceEnabled": false,
  "pageLoad": {
    "pages": [
      {
        "pageId": "abc123",
        "url": "https://example.com/page",
        "status": 200,
        "words": 500,
        "images": 10,
        "links": 25,
        "load_time_ms": 1234,
        "content_length_bytes": 45678
      }
    ],
    "summary": {
      "avg_load_ms": 1500,
      "fastest": {
        "url": "https://example.com/fast",
        "load_ms": 500
      },
      "slowest": {
        "url": "https://example.com/slow",
        "load_ms": 3000
      }
    }
  }
}
```

### site.json Structure

```json
{
  "baseUrl": "https://example.com",
  "nav": [
    {
      "id": "nav1",
      "label": "Home",
      "href": "https://example.com/",
      "order": 0,
      "path": "/",
      "children": []
    }
  ],
  "footer": {
    "columns": [
      {
        "heading": "Products",
        "links": [
          {
            "label": "Product 1",
            "href": "https://example.com/product1"
          }
        ]
      }
    ],
    "socials": [
      {
        "platform": "facebook",
        "url": "https://facebook.com/example",
        "label": "Facebook"
      }
    ],
    "contact": {
      "email": "info@example.com",
      "phone": "+1-555-123-4567"
    }
  },
  "brand": {
    "logo": "https://example.com/logo.png",
    "name": "Example Company"
  }
}
```

### pages_index.json Structure

```json
[
  {
    "pageId": "abc123",
    "titleGuess": "Home Page",
    "path": "/",
    "url": "https://example.com/",
    "status": 200,
    "status_code": 200,
    "words": 500,
    "mediaCount": 10,
    "loadTimeMs": 1234,
    "contentLengthBytes": 45678
  }
]
```

### pages/{page_id}.json Structure

```json
{
  "url": "https://example.com/page",
  "path": "/page",
  "status": 200,
  "title": "Page Title",
  "description": "Page description",
  "canonical": "https://example.com/page",
  "media": {
    "images": [
      {
        "url": "https://example.com/image.jpg",
        "alt": "Image alt text",
        "width": 800,
        "height": 600
      }
    ],
    "videos": [],
    "gifs": []
  },
  "files": [
    {
      "url": "https://example.com/file.pdf",
      "type": "pdf",
      "label": "Download PDF"
    }
  ],
  "words": {
    "headings": [
      {
        "tag": "h1",
        "text": "Main Heading"
      }
    ],
    "paragraphs": ["Paragraph 1", "Paragraph 2"],
    "wordCount": 500
  },
  "links": {
    "internal": [
      {
        "label": "Internal Link",
        "href": "https://example.com/internal"
      }
    ],
    "external": [],
    "broken": []
  },
  "extractedAt": "2024-01-15T10:30:00Z"
}
```

### seed/seed.json Structure

```json
{
  "baseUrl": "https://example.com",
  "nav": [...],
  "footer": {...},
  "pages": [
    {
      "path": "/",
      "components": [
        {
          "type": "hero",
          "props": {
            "heading": "Welcome",
            "text": ["Paragraph 1", "Paragraph 2"],
            "images": [...]
          }
        },
        {
          "type": "section",
          "props": {
            "html": "<p>Content</p>"
          }
        },
        {
          "type": "gallery",
          "props": {
            "images": [...]
          }
        }
      ]
    }
  ]
}
```

---

## Frontend Components

### Main Pages

**SiteGenerator** (`pages/SiteGenerator.tsx`)
- Main entry point
- URL input and run configuration
- Start/stop run controls

**Generator** (`pages/Generator.tsx`)
- Alternative generator interface

**RunView** (`pages/RunView.tsx`)
- Run detail view with three panels:
  - Left: Run summary and controls
  - Center: Page table with filters
  - Right: Page detail preview

**Review** (`pages/Review.tsx`)
- Review extracted data
- Business profile, services, locations

**ConfirmPage** (`pages/ConfirmPage.tsx`)
- Multi-tab confirmation interface:
  - Summary Tab: Statistics and overview
  - Prime Tab: Navigation and footer editing
  - Content Tab: Per-page content editing
  - Summary Tab: Content quality recommendations

**ThemeDesigner** (`pages/ThemeDesigner.tsx`)
- Theme customization interface

### Key Components

**RunTable** (`components/RunTable.tsx`)
- Virtualized table for large page lists
- Filtering by type, word count, status
- Search functionality
- Sorting

**PageDetail** (`components/PageDetail.tsx`)
- Displays full page content
- Metadata, headings, images, links
- Statistics

**PrimeTabs** (`components/PrimeTabs.tsx`)
- Navigation and footer editing
- Drag-and-drop reordering

**ContentTabs** (`components/ContentTabs.tsx`)
- Per-page content editing
- Media, files, words, links

**SummaryTab** (`components/SummaryTab.tsx`)
- Run statistics
- Confidence distribution
- Performance metrics

---

## Backend API Endpoints

### Run Management (`/api/runs`)

- `POST /api/runs/start` - Start new extraction
  - Request: `{url, maxPages?, maxDepth?, concurrency?, renderBudget?, botAvoidanceEnabled?}`
  - Response: `{runId}`

- `GET /api/runs/list` - List all runs
  - Response: `[{runId, status, started_at, completed_at, url}]`

- `GET /api/runs/{run_id}/progress` - Get run progress
  - Response: `{runId, queued, visited, errors, etaSeconds, hosts, is_complete}`

- `POST /api/runs/{run_id}/stop` - Stop running extraction
  - Response: `{stopped: true}`

- `GET /api/runs/{run_id}/meta` - Get run metadata
  - Response: Full meta.json content

- `DELETE /api/runs/{run_id}/delete` - Delete a run
  - Response: `{deleted: true}`

- `DELETE /api/runs/delete-all` - Delete all runs
  - Response: `{deleted: count}`

### Page Management (`/api/pages`)

- `GET /api/pages/{run_id}` - List pages with pagination
  - Query params: `page`, `size`, `q` (search), `type`, `min_words`
  - Response: `{pages: PageSummary[], total, page, size}`

- `GET /api/pages/{run_id}/{page_id}` - Get page details
  - Response: `PageDetail` object

### Review (`/api/review`)

- `GET /api/review/{run_id}/draft` - Get aggregated draft model
  - Response: `DraftModel` with business profile, services, locations, etc.

- `POST /api/review/{run_id}/confirm` - Confirm and save draft
  - Request: `{draft: DraftModel}`
  - Response: `{success, message, runId, confirmedAt}`

- `GET /api/review/{run_id}/confirmed` - Get confirmed draft
  - Response: Confirmed draft data

- `GET /api/review/{run_id}/summary` - Get run summary
  - Response: Statistics, confidence distribution, performance metrics

### Confirmation (`/api/confirm`)

- `GET /api/confirm/{run_id}/status` - Check extraction status
  - Response: `{isComplete, hasData, pagesCount, progress}`

- `GET /api/confirm/{run_id}/prime` - Get prime data (nav, footer, pages)
  - Response: `{baseUrl, nav, footer, pages}`

- `GET /api/confirm/{run_id}/content` - Get page content
  - Query param: `page_path`
  - Response: Structured page content

- `PATCH /api/confirm/{run_id}/prime/nav` - Update navigation
  - Request: `NavNode[]`
  - Response: `{message}`

- `PATCH /api/confirm/{run_id}/prime/footer` - Update footer
  - Request: Footer object
  - Response: `{message}`

- `PATCH /api/confirm/{run_id}/content` - Update page content
  - Query param: `page_path`
  - Request: Content object
  - Response: `{message}`

- `POST /api/confirm/{run_id}/seed` - Generate seed.json
  - Response: `{message, seedPath}`

---

## Advanced Features

### 1. Advanced News Scraper

Located in `backend/scraper_advanced/`, this is a specialized scraper for protected news sites:

**Features:**
- **Cloudflare Bypass**: FlareSolverr integration for IUAM challenges
- **Proxy Rotation**: Residential proxy support with health checking
- **Fingerprint Spoofing**: Randomized browser fingerprints
- **Human Behavior**: Realistic delays, mouse movements, scrolling
- **TLS Fingerprinting**: curl_cffi with Chrome impersonation
- **Browser Fallback**: Undetected Chrome + Selenium Stealth

**Configuration:**
- YAML-based config (`config.yaml`)
- Site-specific selectors
- Proxy configuration
- Human behavior settings

**Docker Integration:**
- Separate Docker service
- FlareSolverr sidecar
- Network isolation

### 2. Bot Avoidance

**BotAvoidanceStrategy** (`crawl/bot_avoidance.py`):
- Randomized delays (0.6-2.4s)
- Per-host request intervals (1.2s default)
- Multiple browser profiles (Chrome Windows/Linux, Safari Mac/iOS)
- Header randomization (User-Agent, Accept-Language, Viewport-Width)
- Bot detection (status codes, CAPTCHA keywords)
- Block event tracking

**Detection:**
- Status code blocklist (403, 409, 423, 429, 503)
- Content keyword detection ("robot or human", "captcha", etc.)
- Block event logging

### 3. JavaScript Rendering

**Render Pool** (`crawl/render_pool.py`):
- Optional Playwright integration
- Browser pool for JS-heavy sites
- Render budget (percentage of pages to render)
- Timeout handling

### 4. SimHash Deduplication

**SimHash** (`storage/simhash.py`):
- Near-duplicate detection
- Prevents crawling similar content
- Hash-based similarity comparison

---

## Configuration & Environment

### Environment Variables (`env.example`)

```bash
# User agent
BASE_USER_AGENT="UniversalExtractor/2.0 (+contact@example.com)"

# Concurrency
GLOBAL_CONCURRENCY=12
PER_HOST_LIMIT=6

# Timeouts
REQUEST_TIMEOUT_SEC=20
RENDER_TIMEOUT_SEC=30

# Limits
MAX_PAGES_DEFAULT=400
MAX_DEPTH_DEFAULT=5

# Rendering
RENDER_ENABLED=false
RENDER_BUDGET=0.10
MIN_TEXT_DENSITY=200

# Storage
RUNS_DIR=runs
MAX_FILE_SIZE_MB=50

# Retry
MAX_RETRIES=3
RETRY_DELAY_BASE=1.0
RETRY_DELAY_MAX=60.0

# Rate limiting
REQUESTS_PER_SECOND=2.0
BURST_SIZE=5

# Content processing
MAX_TEXT_LENGTH=1000000
MAX_IMAGE_SIZE_MB=10

# Logging
LOG_LEVEL=INFO
LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Docker Compose

**Services:**
- `api`: FastAPI backend (port 5051)
- `web`: React frontend (port 5173)
- `scraper`: Advanced news scraper
- `flaresolverr`: Cloudflare bypass service (port 8191)

---

## Dependencies & Technologies

### Backend Dependencies

**Core:**
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server
- `aiohttp` - Async HTTP client
- `pydantic` - Data validation
- `pydantic-settings` - Settings management

**Content Extraction:**
- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML parser
- `readability-lxml` - Main content extraction
- `trafilatura` - Text extraction
- `pypdf` - PDF parsing
- `python-docx` - DOCX parsing
- `Pillow` - Image processing

**Advanced Scraping:**
- `playwright` - Browser automation
- `curl-cffi` - TLS fingerprinting
- `undetected-chromedriver` - Chrome automation
- `selenium` - Browser automation
- `selenium-stealth` - Stealth mode
- `cloudscraper` - Cloudflare bypass
- `httpx[http2]` - HTTP/2 client
- `fake-useragent` - User agent generation
- `faker` - Fake data generation

**Utilities:**
- `orjson` - Fast JSON parsing
- `python-magic` - File type detection
- `Brotli` - Compression
- `pyyaml` - YAML parsing
- `numpy` - Numerical operations
- `psutil` - System utilities

### Frontend Dependencies

**Core:**
- `react` - UI framework
- `react-dom` - React DOM bindings
- `react-router-dom` - Routing
- `typescript` - Type safety

**UI Libraries:**
- `tailwindcss` - CSS framework
- `lucide-react` - Icon library
- `@tanstack/react-query` - Data fetching
- `@tanstack/react-virtual` - Virtualization
- `react-hot-toast` - Notifications

**Build Tools:**
- `vite` - Build tool
- `@vitejs/plugin-react` - React plugin
- `autoprefixer` - CSS autoprefixing
- `postcss` - CSS processing

---

## Scripts & Automation

### Development Scripts

**dev.py** - Cross-platform development script
- Creates virtual environment
- Installs dependencies
- Starts backend and frontend

**dev.sh / dev.bat** - Platform-specific dev scripts
- Linux/Mac: `dev.sh`
- Windows: `dev.bat`

**dev-fedora.sh** - Fedora-specific setup
- Installs system dependencies
- Sets up Python environment

**build.sh / build.bat** - Production build scripts
- Builds frontend
- Prepares for deployment

### Startup Scripts

**start-backend.sh** - Backend server startup
**start-frontend.sh** - Frontend server startup
**start-fedora.sh** - Fedora-specific startup

---

## Testing & Development

### Testing Guide

See `TESTING_GUIDE.md` for:
- Backend testing with mock data
- API endpoint testing
- Frontend testing
- Confirmation page testing

### Mock Data

The system includes mock data generation for testing:
- Business profiles
- Services and products
- Locations
- Team members
- Media files

---

## Deployment

### Docker Deployment

```bash
docker-compose up --build
```

**Services:**
- Backend: `http://localhost:5051`
- Frontend: `http://localhost:5173`
- FlareSolverr: `http://localhost:8191`

### Manual Deployment

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn backend.app:app --host 0.0.0.0 --port 5051
```

**Frontend:**
```bash
cd frontend
npm install
npm run build
npm run preview
```

---

## Additional Features & Notes

### 1. Title Extraction Heuristics

The HTML extractor uses sophisticated title extraction:
- Tries Open Graph title first
- Falls back to `<title>` tag
- Uses first h1 as fallback
- Detects homepage and uses "Home" for company name titles
- Filters out phone numbers, CTAs, and promotional text

### 2. Navigation Extraction

Multi-strategy navigation extraction:
- Looks for `<nav>` elements
- Checks `[role="navigation"]`
- Falls back to header links
- Handles dropdowns and megamenus
- Filters out non-navigation items (phones, emails, CTAs)

### 3. Footer Extraction

Structured footer extraction:
- Groups links by headings
- Extracts social media links
- Identifies contact information (email, phone)
- Platform detection for social links

### 4. Performance Tracking

Every page tracks:
- Load time (milliseconds)
- Content length (bytes)
- Status code
- Word count
- Image count
- Link count

Aggregated into performance summary in meta.json.

### 5. Error Handling

Comprehensive error handling:
- Fetch errors logged to meta.json
- Bot block detection
- Extraction errors handled gracefully
- Error types tracked for analysis

### 6. Content Type Detection

Automatic content type detection:
- HTML: `text/html`
- PDF: `application/pdf`
- DOCX: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- JSON: `application/json`
- CSV: `text/csv`
- Images: Various image MIME types

### 7. URL Normalization

Frontier normalizes URLs:
- Removes fragments
- Handles relative URLs
- Converts to absolute URLs
- Deduplicates similar URLs

### 8. Seed Generation Logic

SeedBuilder creates component structure:
- Hero sections (large image + heading)
- Content sections (paragraphs)
- Image galleries
- File downloads
- Maps structured content to generator components

---

## Summary

This is a comprehensive, production-ready web scraping and content extraction system with:

- **Full-stack architecture**: FastAPI backend + React frontend
- **Multi-format support**: HTML, PDF, DOCX, JSON, CSV, images
- **Advanced features**: Bot avoidance, Cloudflare bypass, fingerprint spoofing
- **Complete workflow**: Crawling → Extraction → Review → Confirmation → Seed Generation
- **Rich data structures**: Navigation, footer, business profiles, services, locations
- **Performance tracking**: Load times, content sizes, error rates
- **Real-time monitoring**: Live progress updates
- **Docker support**: Full containerization
- **Comprehensive documentation**: Multiple README files and guides

The system is designed to be extensible, with clear separation of concerns and modular architecture.

