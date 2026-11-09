# Data Science Path

Data Science Path is a production-oriented, adaptive learning platform for an experienced AI engineer moving toward applied data science. It recommends evidence-producing work that fits the time currently available; it never uses daily streaks as the primary success measure.

## What works

- Secure password login with Argon2 hashing, expiring HttpOnly JWT cookies, login rate limits, and user-scoped queries
- A 45-task, 74-hour, five-track curriculum with practical exercises and explicit completion evidence
- Explainable study plans for 15–600 minute windows, respecting prerequisites, incomplete work, confidence, skill weakness, fit, recency, and theory/practice balance
- Refresh-safe pause/resume session timer and manual session API
- Roadmap progress, independent self/demonstrated skill levels, three substantial projects, 17 milestones, resource library, searchable journal, analytics, settings, and versioned JSON export
- PostgreSQL schema and Alembic migrations, responsive light/dark UI, Docker Compose, tests, and GitHub Actions

## Local setup

The simplest path requires Docker 24+ with Compose:

```bash
cp .env.example .env
# Replace POSTGRES_PASSWORD and DSP_SECRET_KEY in .env
docker compose up --build
```

Open `http://localhost:3000`. The API documentation is at `http://localhost:8000/api/docs`.

For native development, run PostgreSQL, then:

```bash
cd apps/api
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
.venv/bin/alembic upgrade head
.venv/bin/python -m app.data.seed
.venv/bin/uvicorn app.main:app --reload

cd ../web
npm ci
npm run dev
```

## Tests

```bash
make test
# Full browser journey (requires the Docker stack):
cd apps/web && npx playwright install chromium && npm run test:e2e
```

See [ARCHITECTURE.md](ARCHITECTURE.md), [DATABASE.md](DATABASE.md), [CURRICULUM.md](CURRICULUM.md), [ROADMAP.md](ROADMAP.md), and [DEPLOYMENT.md](DEPLOYMENT.md).
