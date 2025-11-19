# SiteInsite Backend

FastAPI-based backend for website intelligence scanning with support for HTML, PDF, DOCX, JSON, CSV, and images.

## Features

- **Async crawling**: High-performance async HTTP client with rate limiting
- **Multi-format extraction**: HTML, PDF, DOCX, JSON, CSV, images
- **JavaScript rendering**: Optional Playwright integration
- **Smart extraction**: Uses readability, trafilatura, and custom extractors
- **Deduplication**: SimHash-based near-duplicate detection
- **File-based storage**: JSON storage with pagination and filtering
- **Swagger docs**: Auto-generated API documentation

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server**:
   ```bash
   uvicorn backend.app:app --reload --port 5051
   ```

3. **View API docs**: http://localhost:5051/docs

## API Endpoints

### Audit Runs
- `POST /api/runs/start` - Start new audit
- `GET /api/runs/{run_id}/progress` - Get audit progress
- `POST /api/runs/{run_id}/stop` - Stop running audit

### Pages
- `GET /api/pages/{run_id}` - List pages with filtering
- `GET /api/pages/{run_id}/{page_id}` - Get page details

## Configuration

Set environment variables or modify `backend/core/config.py`:

- `GLOBAL_CONCURRENCY`: Number of concurrent requests (default: 12)
- `PER_HOST_LIMIT`: Requests per host (default: 6)
- `REQUEST_TIMEOUT_SEC`: Request timeout (default: 20)
- `MAX_PAGES_DEFAULT`: Default page limit (default: 400)
- `RENDER_ENABLED`: Enable JavaScript rendering (default: False)
- `RENDER_BUDGET`: Percentage of pages to render (default: 0.10)

## Architecture

### Core Modules
- `app.py`: FastAPI application with CORS and routing
- `core/`: Configuration, types, and dependencies
- `routers/`: API route handlers

### Crawling
- `crawl/runner.py`: Main orchestration and worker loop
- `crawl/frontier.py`: URL queue management with politeness
- `crawl/fetch.py`: Async HTTP client with rate limiting
- `crawl/render_pool.py`: Playwright browser pool
- `crawl/robots.py`: Robots.txt compliance checker

### Extraction
- `extract/html.py`: HTML content extraction
- `extract/pdfs.py`: PDF text extraction
- `extract/docx_.py`: DOCX document extraction
- `extract/json_csv.py`: JSON/CSV data extraction
- `extract/images.py`: Image metadata extraction

### Storage
- `storage/runs.py`: File-based run storage
- `storage/simhash.py`: Near-duplicate detection

## Development

### Adding New Extractors
1. Create extractor function in `extract/` module
2. Add content type detection logic
3. Update `crawl/runner.py` to use new extractor
4. Add tests for extraction logic

### Testing
```bash
# Run tests (when implemented)
pytest backend/tests/
```

### Performance Tuning
- Increase `GLOBAL_CONCURRENCY` for faster crawling
- Adjust `PER_HOST_LIMIT` based on target site
- Enable `RENDER_ENABLED` for JavaScript-heavy sites
- Use SSD storage for better I/O performance
