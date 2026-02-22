# Contributing to SiteInsite

Thanks for your interest in contributing. This guide covers how to get set up locally, code standards, and the pull request process.

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git

### 1. Clone and install

```bash
git clone https://github.com/NicholasBurgo/SiteInsite.git
cd SiteInsite
```

**Backend:**

```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**

```bash
cd frontend
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` as needed. Defaults work for local development.

### 3. Run locally

One-command startup (recommended):

```bash
python scripts/dev.py
```

Or run separately:

```bash
# Terminal 1 - backend
uvicorn backend.app:app --reload --port 5051

# Terminal 2 - frontend
cd frontend && npm run dev
```

- Frontend: http://localhost:5173
- API docs: http://localhost:5051/docs

---

## Code Standards

### Python

- **Formatter:** [black](https://black.readthedocs.io/) (`line-length = 88`)
- **Linter:** flake8
- **Type checker:** mypy (strict mode enabled)

```bash
black backend/
flake8 backend/
mypy backend/
```

All public functions should have type hints and docstrings.

### TypeScript / React

- **Type checker:** `tsc` (strict mode via `tsconfig.json`)
- No `any` types without justification
- Prefer explicit return types on exported functions

```bash
cd frontend
npm run build   # catches type errors via tsc
```

### General

- No `print()` in backend routes or services - use `logging`
- No `console.log()` in frontend components
- No hardcoded `localhost` URLs in frontend - use relative `/api/` paths or `import.meta.env.VITE_API_URL`

---

## Pull Request Process

1. Fork the repo and create a branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. Make your changes and confirm:
   - `black`, `flake8`, and `mypy` pass for any Python changes
   - `npm run build` succeeds for any frontend changes
   - No new hardcoded secrets, emails, or localhost URLs introduced

3. Open a PR against `main` with a clear description of what changed and why.

4. PRs that add features should include a brief explanation of the use case.

## Reporting Bugs

Open a GitHub issue with:
- Steps to reproduce
- Expected vs actual behavior
- Python/Node version and OS

For security issues, see [SECURITY.md](SECURITY.md).
