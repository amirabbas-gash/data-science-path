# Architecture

## Decision

The application is a modular monolith deployed as a Next.js web process, a FastAPI API process, and managed PostgreSQL. This keeps the product easy to reason about and deploy while preserving clean service boundaries. Microservices and event infrastructure would add operational cost without improving this single-user-first workload.

```text
Browser ── same-origin /api rewrite ──► Next.js ──► FastAPI ──► PostgreSQL
                                             │          │
                                             │          ├─ recommendation policy
                                             │          ├─ curriculum/progress
                                             │          └─ export/analytics
                                             └─ responsive application UI
```

The web app proxies `/api/*` to FastAPI. Authentication cookies therefore remain first-party in normal deployments. FastAPI is the authorization boundary: every mutable or personal query contains the authenticated `user_id` predicate.

## Backend modules

- `core`: configuration, connection lifecycle, password and token primitives
- `models`: normalized SQLAlchemy entities and constraints
- `api`: HTTP contracts and authenticated routes
- `services/recommendations.py`: deterministic recommendation policy
- `data/seed.py`: idempotent, substantive curriculum content
- `alembic`: reproducible schema migrations

The recommendation engine returns ranked tasks and human-readable reasons. Its interface can later accept an LLM reranker, but the deterministic result remains the safe fallback and system of record.

## Recommendation policy

Tasks are first filtered by active curriculum version, available duration, completion state, and satisfied prerequisites. Scores then combine explicit task priority, unfinished work, low confidence/review state, weak demonstrated skills, duration fit, recent repetition penalty, and practical-work bonus. A greedy duration packer favors task-type diversity. No calendar streak or inactivity penalty appears in the calculation.

## Security boundaries

- Argon2 password hashes; raw passwords never persist
- Signed JWT in `HttpOnly`, `SameSite=Lax`, production `Secure` cookie with expiry
- Rate limits on registration and login
- Pydantic input constraints and SQLAlchemy parameterization
- One configured CORS origin; same-origin proxy is preferred
- No secrets in source or database
- Non-root container users and ephemeral application filesystems

Production must use a random 32+ byte `DSP_SECRET_KEY`, TLS, a restricted database role, and `DSP_SECURE_COOKIES=true`. For a multi-user public release, add email verification, password reset, CSRF tokens for unsafe methods, and an external rate-limit store before broad promotion.

## AI extension

No core route calls a model. A future `LearningAssistant` protocol may add explanations, practice generation, and reflection synthesis behind environment-configured provider/model settings. Failure or missing credentials must return the deterministic behavior unchanged.

