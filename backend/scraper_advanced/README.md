# Advanced News Scraper

A production-grade web scraper specifically designed for scraping news sites like Newsmax, Breitbart, and OANN that employ sophisticated anti-bot protection including Cloudflare, behavioral fingerprinting, and rate limiting.

## Features

### 🛡️ Anti-Bot Evasion
- **Full Browser Fingerprint Spoofing**: Randomized canvas, WebGL, fonts, screen resolution, timezone, language
- **TLS Fingerprinting**: Uses `curl_cffi` with Chrome impersonation (Chrome 124/126)
- **Residential Proxy Rotation**: Automatic proxy health checking and rotation
- **Undetected Browser Fallback**: `undetected-chromedriver` + `selenium-stealth` when HTTP fails

### 🤖 Human Behavior Simulation
- Random delays (3.2–9.7s) with normal distribution
- Homepage visits (5–15% chance) before articles
- Mouse movements and scrolling in browser mode
- Session persistence with cookies/localStorage

### ☁️ Cloudflare Bypass
- **FlareSolverr Integration**: Docker sidecar for IUAM challenges
- **cloudscraper**: Fast bypass for common protections
- **CAPTCHA Handling**: Automatic 2Captcha integration for hCaptcha

### 📊 Smart Features
- Exponential backoff retry (2s, 8s, 30s)
- Proxy auto-ban on failures
- Concurrent requests with rate limiting
- Clean article extraction with trafilatura

## Quick Start

### Docker Setup (Recommended)

1. **Start the scraper stack**:
```bash
docker-compose up scraper flaresolverr
```

2. **Test the scraper**:
```bash
docker-compose run --rm scraper python -m scraper_advanced.cli test --site newsmax
```

3. **Scrape articles**:
```bash
# Single article
docker-compose run --rm scraper python -m scraper_advanced.cli scrape \
  "https://www.newsmax.com/article-url" --site newsmax

# Multiple articles from site
docker-compose run --rm scraper python -m scraper_advanced.cli scrape-site newsmax \
  --urls "url1" "url2" "url3" --concurrency 3
```

### Local Setup

1. **Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure proxies** (edit `config.yaml`):
```yaml
scraper:
  proxies:
    enabled: true
    residential:
      - host: "your-proxy-host"
        port: 8080
        username: "user"
        password: "pass"
        country: "US"
```

3. **Run the scraper**:
```bash
# Test scrape
python -m scraper_advanced.cli test --site newsmax

# Scrape single article
python -m scraper_advanced.cli scrape "https://www.newsmax.com/article" --site newsmax

# Health check
python -m scraper_advanced.cli health
```

## Configuration

The scraper uses a comprehensive YAML configuration file (`config.yaml`):

### Proxy Configuration
```yaml
scraper:
  proxies:
    enabled: true
    rotation_strategy: "round_robin"  # round_robin, random, geo_targeted
    geo_target: "US"
    residential:
      - host: "proxy1.provider.com"
        port: 8080
        username: "user1"
        password: "pass1"
        country: "US"
```

### Human Behavior Settings
```yaml
scraper:
  human_delays:
    min_delay: 3.2
    max_delay: 9.7
    homepage_visit_chance: 0.15  # 15% chance
    asset_fetch_chance: 0.10     # 10% chance
```

### Site-Specific Selectors
```yaml
scraper:
  targets:
    newsmax:
      base_url: "https://www.newsmax.com"
      article_selectors:
        - ".article-content"
        - ".entry-content"
      author_selectors:
        - ".author-name"
        - ".byline"
```

## CLI Commands

### Scrape Single Article
```bash
python -m scraper_advanced.cli scrape <URL> [--site SITE] [--output FILE]
```

### Scrape Multiple Articles
```bash
python -m scraper_advanced.cli scrape-site <SITE> --urls <URL1> <URL2> [--concurrency N]
python -m scraper_advanced.cli scrape-site <SITE> --url-file urls.txt
```

### Health Check
```bash
python -m scraper_advanced.cli health
```

### Show Statistics
```bash
python -m scraper_advanced.cli stats
```

### Test Scrape
```bash
python -m scraper_advanced.cli test [--site newsmax|breitbart|oann]
```

## Output Format

Articles are saved as JSONL with the following structure:

```json
{
  "title": "Article Title",
  "url": "https://www.newsmax.com/article",
  "content": "Clean article text without ads...",
  "author": "John Doe",
  "publish_date": "2024-01-15T10:30:00",
  "site_name": "newsmax",
  "word_count": 842,
  "extraction_method": "trafilatura",
  "success": true,
  "extracted_at": "2024-01-15T10:35:22.123456",
  "scraper_metadata": {
    "timestamp": 1705313722.123456,
    "version": "1.0.0"
  }
}
```

## Architecture

### Core Components

1. **ProxyManager**: Residential proxy rotation and health checking
2. **FingerprintSpoofer**: Browser fingerprint randomization
3. **HumanBehaviorEngine**: Realistic browsing patterns
4. **CloudflareBypass**: Anti-bot protection bypass
5. **AdvancedHttpClient**: HTTP requests with TLS impersonation
6. **UndetectedChromeFallback**: Browser automation fallback
7. **ArticleExtractor**: Clean content extraction with trafilatura

### Request Flow

1. **Proxy Selection**: Choose healthy residential proxy
2. **Fingerprint Generation**: Create realistic browser fingerprint
3. **Human Delay**: Apply randomized delays
4. **HTTP Request**: Try curl_cffi with Chrome impersonation
5. **Cloudflare Check**: Detect and bypass challenges
6. **Browser Fallback**: Use undetected Chrome if HTTP fails
7. **Content Extraction**: Extract clean article text
8. **Output**: Save structured data

## Troubleshooting

### Common Issues

**Proxy Connection Failed**
- Check proxy credentials in `config.yaml`
- Verify proxy server is accessible
- Try different proxy provider

**Cloudflare Challenges**
- Ensure FlareSolverr is running: `docker-compose up flaresolverr`
- Check FlareSolverr logs for errors
- Some sites may require manual CAPTCHA solving

**Browser Fallback Issues**
- Install Chrome: `apt-get install google-chrome-stable`
- Check Chrome version compatibility
- Ensure sufficient system resources

**Low Success Rate**
- Reduce concurrency: `--concurrency 1`
- Increase delays in config
- Check proxy quality
- Verify target site selectors

### Monitoring

**Health Check**:
```bash
python -m scraper_advanced.cli health
```

**Statistics**:
```bash
python -m scraper_advanced.cli stats
```

**Logs**: Set log level with `--log-level DEBUG`

## Performance Tuning

### For High Volume Scraping
- Increase concurrent requests: `--concurrency 5-10`
- Use more proxies (10+ recommended)
- Enable session reuse
- Monitor proxy health with health checks

### For Stealth (Low Volume)
- Reduce concurrency: `--concurrency 1-2`
- Increase delays in config
- Enable homepage visits
- Use geo-targeted proxies

## Security Notes

- **Never** use this tool for illegal activities
- Respect `robots.txt` and site terms of service
- Use residential proxies from legitimate providers
- Implement rate limiting to avoid overwhelming sites
- Monitor for IP bans and adjust proxy rotation accordingly

## Development

### Adding New Sites
1. Add site configuration to `config.yaml`
2. Test selectors with browser developer tools
3. Update site detection in `scraper.py`

### Extending Functionality
- Add new bypass methods in `CloudflareBypass`
- Implement custom extraction in `ArticleExtractor`
- Add new fingerprinting in `FingerprintSpoofer`

## License

See main project LICENSE file.
