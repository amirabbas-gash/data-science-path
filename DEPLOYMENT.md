# Deployment

Research was checked against official provider documentation on 2026-11-09. Prices and quotas change; re-check the linked pages immediately before provisioning.

## Hosting comparison

| Option | Current practical cost | Fit | Important constraint |
|---|---:|---|---|
| Vercel Hobby + Render Free API + Neon Free Postgres | $0 | Native Next.js CI/CD; Python container; durable independent Postgres | Render sleeps after 15 idle minutes and cold start is about a minute; Vercel Hobby is personal/non-commercial |
| Cloudflare Workers + Render Free API + Neon | $0 | Excellent edge/HTTPS and current OpenNext support | Adds an adapter and separate Workers build path |
| Render web + API + Neon | $0 | One dashboard; `onrender.com`; Docker/Python/Node support | Two free services share 750 monthly instance hours and both sleep |
| Railway Hobby including PostgreSQL | $5 minimum/month | Simplest all-in-one services, private networking, Git deploys | Free plan has only $1 monthly credit; Hobby requires a card |
| Fly.io + Neon | roughly $4–8/month for small always-on machines | Strong container control and regional placement | Usage billing and more operations than this app needs |
| Supabase Free DB + any frontend/API | $0 | Managed Postgres and optional managed auth | Free projects pause after one inactive week; no automatic backups |

Official references: [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/), [Cloudflare Next.js support](https://developers.cloudflare.com/workers/framework-guides/automatic-configuration/), [Render free limits](https://render.com/docs/free), [Render web services](https://render.com/docs/web-services), [Railway pricing](https://docs.railway.com/pricing/plans), [Fly resource pricing](https://fly.io/docs/about/pricing/), [Vercel Hobby](https://vercel.com/docs/plans/hobby), [Neon free plan announcement](https://neon.com/blog/neon-free-plan-1-gb-per-project), and [Supabase pricing](https://supabase.com/pricing).

## Recommendation

Use Vercel Hobby for the Next.js process, Render Free for FastAPI, and Neon Free for PostgreSQL for the initial private/personal deployment. This is selected after comparison, not by default: it costs $0, keeps the database independent of the sleeping API, provides managed TLS and provider subdomains, preserves Git-based deploys, and matches the existing account footprint. Neon currently documents 1 GB storage, 100 CU-hours per project, 10 branches, and a six-hour instant restore window on Free. The accepted tradeoff is Render's cold start. If that becomes annoying, move only the API to Railway Hobby or a small Fly machine; PostgreSQL and the web application remain portable.

## Provisioning boundary

Deployment requires the owner's authenticated GitHub, Vercel, Render, and Neon sessions. No credentials are present in this workspace, so provisioning cannot be truthfully completed from this environment.

## Exact deployment procedure

1. Push this repository to the configured GitHub remote after reviewing changes.
2. In Neon, create `data-science-path` in a nearby region. Copy the pooled PostgreSQL URL. Restrict dashboard access and record a recovery method.
3. In Render, create a Web Service from the repository with root `apps/api`, Docker runtime, Free plan, health check `/health`, and start command from the Dockerfile.
4. Set `DSP_DATABASE_URL` to the Neon pooled URL (change scheme to `postgresql+psycopg://`), `DSP_ENVIRONMENT=production`, `DSP_SECRET_KEY` to `openssl rand -hex 32`, `DSP_SECURE_COOKIES=true`, and temporarily set `DSP_FRONTEND_URL` after step 6. The API refuses to start in production with the development secret or insecure cookies.
5. The API container startup command runs `alembic upgrade head` and the idempotent `python -m app.data.seed` before Uvicorn. Confirm the Render deploy log shows both steps succeeded, then verify `/health` and `/api/docs` over HTTPS.
6. Import the repository into Vercel with root `apps/web`; set `API_INTERNAL_URL=https://<actual-render-service>.onrender.com`. Deploy and record the assigned `vercel.app` hostname.
7. Update Render `DSP_FRONTEND_URL=https://<actual-vercel-project>.vercel.app`, redeploy, and verify CORS. Unsafe browser requests carrying a different `Origin` are rejected with HTTP 403 as an additional CSRF defense.
8. Create an account from the production UI. Verify the cookie has `Secure`, `HttpOnly`, and `SameSite=Lax`; login failure is rate limited. The frontend's same-origin `/api` rewrite keeps the authentication cookie first-party while proxying requests to Render.
9. Complete a task, record a session, update a skill and milestone, create a reflection, then redeploy both services. Verify all records persist afterward.
10. Download the in-app JSON export and run a separate `pg_dump`; test restore into a disposable Neon branch.

Provider hostnames must be accepted from the dashboards at provisioning time. This project deliberately does not claim or invent them.

## Operations

- Run migrations before application start; seed is idempotent.
- Review GitHub Actions before merging. Container, backend, frontend, and test failures block release.
- Take weekly `pg_dump` backups and before every migration. Neon Free's restore window is useful but not a long-term backup.
- Rotate `DSP_SECRET_KEY` only with a planned forced logout; rotation invalidates all sessions.
- Monitor database size, API error logs, authentication rate-limit events, and Render cold-start behavior. Never log passwords, cookies, or database URLs.
