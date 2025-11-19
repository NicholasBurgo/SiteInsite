# SiteInsite — Website Intelligence Engine

SiteInsite scans any website and generates a clear, actionable Website Insight Report covering SEO, speed, structure, accessibility, content, navigation, and performance.

## Why SiteInsite Exists

- **Business owners don't understand SEO reports** — Technical jargon and fragmented data make it hard to see the big picture
- **Developers waste time auditing sites manually** — No single tool provides comprehensive site analysis
- **Tools like ScreamingFrog are too technical** — They require expertise to interpret and act on
- **PageSpeed and Lighthouse only show performance** — They miss content quality, structure, and SEO health
- **SiteInsite gives everything in one place** — Human-friendly insights with actionable recommendations

## ✨ Key Features

- **Full-site crawling** — Scan hundreds of pages automatically
- **Structured content extraction** — Extract text, headings, links, and metadata
- **SEO health analysis** — Meta tags, heading structure, alt text, and more
- **Heading structure audit** — Identify missing or malformed heading hierarchies
- **Image + media insights** — Alt text analysis, image optimization opportunities
- **Navigation/footer extraction** — Understand site structure and navigation patterns
- **Content quality analysis** — Word count, readability, duplicate content detection
- **Page load performance** — Response times and performance metrics
- **Broken link detection** — Find 404s and broken internal/external links
- **PDF + DOCX + CSV extraction** — Extract content from documents
- **Accessibility flags** — Identify common accessibility issues
- **Competitor comparison** — Compare your site against competitors with side-by-side analysis
- **Competitor suggestions** — Get AI-suggested competitor URLs based on your domain
- **Actionable recommendations** — Clear, prioritized suggestions for improvement
- **HTML report export** — Shareable, visual insight reports
- **JSON Insight Report export** — Machine-readable audit data

## 🚀 How It Works

1. **Enter a website** — Provide the URL you want to analyze
2. **Optional: Compare with competitors** — Enable comparison mode and select competitors to benchmark against
3. **Crawler scans and extracts data** — SiteInsite intelligently crawls the site(s), respecting robots.txt
4. **Analyzer builds the Website Insight Report** — All data is processed and analyzed
5. **View report in the UI** — Explore insights, SEO breakdown, performance metrics, and comparison data
6. **Export or share** — Download HTML or JSON reports for further analysis

## 🛠 Tech Stack

- **FastAPI** — High-performance async API backend
- **aiohttp** — Async HTTP client for efficient crawling
- **React + TypeScript + Vite** — Modern, fast frontend
- **Tailwind** — Beautiful, responsive UI
- **SimHash** — Near-duplicate content detection
- **Readability + trafilatura** — Smart content extraction
- **tldextract** — Domain extraction for competitor suggestions
- **Cloudflare bypass** (optional) — Handle protected sites
- **Docker** — Containerized deployment

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (for FastAPI backend)
- **Node.js 18+** (for React frontend)
- **Git** (for cloning)

### Fedora Linux Setup

Fedora ships with most prerequisites, but a few development headers are needed to compile Python packages such as `lxml` and `Pillow`.

```bash
sudo dnf install \
  python3 python3-pip python3-virtualenv \
  nodejs npm \
  libxml2-devel libxslt-devel \
  gcc-c++ make file

# Optional: install browser deps for Playwright rendering
python3 -m pip install --upgrade pip
python3 -m pip install playwright
python3 -m playwright install-deps
python3 -m playwright install chromium
```

With the dependencies in place, the provided `scripts/dev.sh` and `scripts/build.sh` will create a project-local virtual environment (`.venv`) automatically when you run them.

### Option 1: Development Mode (Recommended)

1. **Start both servers**:
   ```bash
   # Cross-platform (recommended)
   python scripts/dev.py

   # Legacy helpers
   #   macOS/Linux: ./scripts/dev.sh
   #   Windows:     scripts\dev.bat
   ```

2. **Access the application**:
   - **Frontend UI**: http://localhost:5173
   - **Backend API**: http://localhost:5051  
   - **Swagger Docs**: http://localhost:5051/docs

### Option 2: Manual Setup

1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn backend.app:app --reload --port 5051
   ```

2. **Frontend** (in new terminal):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Option 3: Docker

```bash
docker-compose up --build
```

### Production Build

```bash
# On Windows (PowerShell)
.\scripts\build.sh

# On Linux/Mac
chmod +x scripts/build.sh
./scripts/build.sh
```

## 📖 How to Use

### 1. Starting an Audit

1. **Open the web interface**: http://localhost:5173
2. **Enter target URL**: e.g., `https://example.com`
3. **Optional: Enable competitor comparison**:
   - Check "Compare with competitors" checkbox
   - Click "Suggest Competitors" to get AI-suggested competitors (top 3 auto-selected)
   - Add custom competitor URLs manually
   - Select/deselect competitors as needed
4. **Click "Start Audit" or "Run Comparison Audit"**: The system will begin crawling
5. **Monitor progress**: Real-time updates in the left panel

### 2. Exploring Results

The interface has **three panels**:

- **Left Panel**: Audit controls and progress summary
- **Center Panel**: Page table with filtering options  
- **Right Panel**: Detailed page preview

### 3. Filtering and Search

- **Search**: Type in the search box to find pages by title/content
- **Content Type**: Filter by HTML, PDF, DOCX, JSON, CSV, Images
- **Min Words**: Show only pages with minimum word count
- **Status**: View successful pages vs. errors

### 4. Audit Review

After the audit completes, you can review and analyze the data:

1. **Navigate to Review**: Click "Review" on any completed audit
2. **Review Site Structure**: Explore navigation structure and footer content
3. **Analyze Page Content**: Review titles, descriptions, media alt text, and links
4. **Export Insight Report**: Generate HTML or JSON reports

The review interface provides:
- **Summary Tab**: Overview statistics and content quality recommendations
- **Content Tab**: Per-page analysis of media, files, words, and links
- **Structure Tab**: Navigation and footer analysis with recommendations

### 5. Page Details

Click any page in the table to see:
- **Full text content** (first 5000 characters)
- **Metadata** (title, author, creation date, etc.)
- **Headings** structure
- **Images** and links found
- **Statistics** (word count, image count, etc.)

## ⚙️ Configuration

Copy `env.example` to `.env` and customize:

```bash
cp env.example .env
```

### Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `GLOBAL_CONCURRENCY` | 12 | Number of concurrent requests |
| `PER_HOST_LIMIT` | 6 | Requests per host (politeness) |
| `REQUEST_TIMEOUT_SEC` | 20 | Request timeout in seconds |
| `MAX_PAGES_DEFAULT` | 400 | Default page limit |
| `RENDER_ENABLED` | false | Enable JavaScript rendering |
| `RENDER_BUDGET` | 0.10 | Percentage of pages to render with JS |

## 📁 Project Structure

```
SiteInsite/
├── backend/                    # FastAPI Backend
│   ├── app.py                 # Main FastAPI application
│   ├── routers/               # API route handlers
│   │   ├── __init__.py
│   │   ├── runs.py           # Audit run management endpoints
│   │   ├── pages.py          # Page listing/details endpoints
│   │   ├── review.py         # Review and aggregation endpoints
│   │   ├── confirm.py        # Confirmation workflow endpoints
│   │   ├── insights.py       # Insight report generation endpoints
│   │   └── competitors.py    # Competitor suggestion endpoints
│   ├── core/                 # Core configuration and types
│   │   ├── config.py         # Settings and environment config
│   │   ├── deps.py           # Dependency injection
│   │   └── types.py          # Pydantic models
│   ├── crawl/                # Crawling engine
│   │   ├── runner.py         # Main orchestration
│   │   ├── frontier.py       # URL queue management
│   │   ├── fetch.py          # Async HTTP client
│   │   ├── render_pool.py    # Playwright browser pool
│   │   └── robots.py         # Robots.txt compliance
│   ├── extract/              # Content extractors
│   │   ├── html.py           # HTML content extraction
│   │   ├── pdfs.py           # PDF text extraction
│   │   ├── docx_.py          # DOCX document extraction
│   │   ├── json_csv.py       # JSON/CSV data extraction
│   │   ├── images.py         # Image metadata extraction
│   │   ├── nav_footer.py     # Navigation and footer extraction
│   │   └── files_words_links.py # Structured content extraction
│   ├── insights/             # Insight generation
│   │   ├── __init__.py       # Insight report builder
│   │   ├── summary.py        # Summary generation
│   │   └── comparison.py     # Competitor comparison logic
│   ├── storage/              # Data storage
│   │   ├── runs.py           # File-based run storage
│   │   ├── simhash.py        # Near-duplicate detection
│   │   ├── confirmation.py   # Confirmation data storage
│   │   └── seed.py           # Seed generation utilities
│   ├── Dockerfile            # Backend container config
│   ├── requirements.txt      # Python dependencies
│   └── README.md            # Backend documentation
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── App.tsx          # Main application component
│   │   ├── main.tsx         # React entry point
│   │   ├── styles.css       # Tailwind CSS imports
│   │   ├── components/      # Reusable UI components
│   │   │   ├── TopBar.tsx
│   │   │   ├── RunSummary.tsx
│   │   │   ├── RunFilters.tsx
│   │   │   ├── RunTable.tsx
│   │   │   ├── PageDetail.tsx
│   │   │   ├── PrimeTabs.tsx
│   │   │   ├── ContentTabs.tsx
│   │   │   └── SummaryTab.tsx
│   │   ├── lib/             # Utilities and types
│   │   │   ├── api.ts       # API client functions
│   │   │   ├── types.ts     # TypeScript interfaces
│   │   │   ├── api.confirm.ts # Confirmation API client
│   │   │   └── types.confirm.ts # Confirmation types
│   │   └── pages/           # Page components
│   │       ├── Generator.tsx
│   │       ├── Review.tsx
│   │       ├── RunView.tsx
│   │       └── ConfirmPage.tsx
│   ├── Dockerfile           # Frontend container config
│   ├── index.html           # HTML template
│   ├── package.json         # Node.js dependencies
│   ├── tailwind.config.js   # Tailwind CSS config
│   ├── tsconfig.json        # TypeScript config
│   └── vite.config.ts      # Vite build config
├── scripts/                  # Development scripts
│   ├── dev.sh              # Linux/Mac dev startup
│   ├── dev.bat             # Windows dev startup
│   ├── build.sh            # Linux/Mac build script
│   └── build.bat           # Windows build script
├── runs/                    # Generated audit data
├── docker-compose.yml       # Multi-service Docker setup
├── .env.example            # Environment configuration template
├── LICENSE                 # MIT License
└── README.md              # This file
```

## Architecture

### Backend (FastAPI)

- **Crawler**: Async HTTP client with rate limiting and retry logic
- **Extractors**: Content-type specific extraction modules
- **Storage**: File-based storage with JSON serialization
- **Deduplication**: SimHash for near-duplicate detection
- **Rendering**: Optional Playwright pool for JavaScript pages

### Frontend (React + TypeScript)

- **Real-time Updates**: Live progress monitoring
- **Advanced Filtering**: Multi-criteria page filtering
- **Responsive Design**: Mobile-friendly interface
- **Virtualization**: Handle large datasets efficiently

## 📡 API Overview

### Core Endpoints

- `POST /api/runs/start` - Start new audit
- `GET /api/runs/{run_id}/progress` - Get audit progress
- `GET /api/runs/{run_id}/pages` - Get paginated pages
- `GET /api/runs/{run_id}/page/{page_id}` - Get page details
- `POST /api/runs/{run_id}/stop` - Stop running audit

### Review Endpoints

- `GET /api/review/{run_id}` - Get aggregated site data
- `GET /api/review/{run_id}/summary` - Get audit summary

### Confirmation Endpoints

- `GET /api/confirm/{run_id}/prime` - Get navigation, footer, and pages index
- `GET /api/confirm/{run_id}/content?page_path={path}` - Get structured page content
- `PATCH /api/confirm/{run_id}/prime/nav` - Update navigation structure
- `PATCH /api/confirm/{run_id}/prime/footer` - Update footer content
- `PATCH /api/confirm/{run_id}/content?page_path={path}` - Update page content
- `POST /api/confirm/{run_id}/seed` - Generate seed.json export

### Competitor Endpoints

- `GET /api/competitors/suggest?url={url}` - Get suggested competitor URLs based on domain
- `POST /api/compare` - Compare primary site with competitors and generate comparison report

### Content Types Supported

- **HTML**: Full text extraction with metadata, links, images
- **PDF**: Text extraction with page count and metadata
- **DOCX**: Document text with heading structure
- **JSON/CSV**: Schema inference and sample data
- **Images**: Metadata extraction (size, format, EXIF)

## Advanced Features

### Competitor Comparison

Compare your website against competitors to identify opportunities and benchmark performance:

1. **Enable comparison mode** in the Generator interface
2. **Get suggestions** - Click "Suggest Competitors" to receive AI-suggested competitor URLs
3. **Add custom competitors** - Manually add competitor URLs
4. **Run comparison** - The system will audit all sites and generate a side-by-side comparison report

The comparison report includes:
- **Score comparison** - Overall and category scores across all sites
- **Performance metrics** - Speed, response times, and optimization opportunities
- **Content analysis** - Word counts, media usage, and content quality
- **SEO comparison** - Meta tags, structure, and SEO health
- **Opportunity summary** - Actionable insights on where you can improve

**API Usage:**
```bash
# Get competitor suggestions
GET /api/competitors/suggest?url=https://example.com

# Run comparison
POST /api/compare
{
  "primaryUrl": "https://example.com",
  "competitors": ["https://competitor1.com", "https://competitor2.com"]
}
```

**Limits:**
- Maximum 10 sites per comparison (1 primary + 9 competitors)
- Each site is limited to 50 pages for comparison audits

### JavaScript Rendering

Enable Playwright for JavaScript-heavy sites:

```bash
pip install playwright
playwright install chromium
```

Set `RENDER_ENABLED=true` in your `.env` file.

### Rate Limiting

Configure per-domain rate limits:

```python
# In your configuration
PER_HOST_LIMIT = 6  # requests per host
REQUESTS_PER_SECOND = 2.0  # global rate limit
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure all dependencies are installed
2. **Port conflicts**: Change ports in `scripts/dev.sh`
3. **Memory issues**: Reduce `GLOBAL_CONCURRENCY` for large sites
4. **Timeout errors**: Increase `REQUEST_TIMEOUT_SEC`

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
```

### Performance Tuning

For large sites (500+ pages):
- Increase `GLOBAL_CONCURRENCY` to 20-30
- Set `PER_HOST_LIMIT` to 10-15
- Use SSD storage for better I/O performance
- Consider running on multiple machines

## 🗺 Roadmap

- **Enhanced competitor suggestions** — Replace placeholder logic with real SERP scraping and keyword-based discovery
- **PDF Report export** — Generate beautiful PDF insight reports
- **AI Rewrite Recommendations** — Get AI-powered content improvement suggestions
- **Automated weekly scans** — Schedule regular audits and track improvements over time
- **Competitor history tracking** — Store and track competitor trends over time

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- Issues: GitHub Issues
- Documentation: This README
- API Docs: http://localhost:5051/docs (when running)
