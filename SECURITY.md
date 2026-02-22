# Security Policy

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues through [GitHub's private security advisory feature](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) on this repository.

Include as much of the following as possible:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You can expect an acknowledgement within 7 days.

## Dual-Use Notice

SiteInsite includes features that can interact aggressively with web servers:

- **Proxy rotation** - cycles through proxy addresses to distribute requests
- **Bot avoidance strategies** - header randomization and request timing variation
- **JavaScript rendering** - headless browser support via Playwright
- **Cloudflare bypass** - advanced scraping fallback via Selenium

These features are intended for auditing websites **you own or have explicit permission to crawl**. Using this tool against third-party sites without authorization may violate their terms of service or applicable law. The authors are not responsible for misuse.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |
