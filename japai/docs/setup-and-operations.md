# Setup and Operations

## Prerequisites

- Docker Desktop with Compose support.
- A Gemini API key for model-backed flows.
- PowerShell, Bash, or an equivalent shell for command execution.

## Start locally

```bash
cp .env.example .env
# Set GEMINI_API_KEY in .env
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python -m db.seed.load_demo_snapshot
```

Services:

- Web UI: `http://localhost:3000`
- API: `http://localhost:8000`
- OpenAPI UI: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

The demo snapshot loader is intended for a blank database. Use its force option only when replacing existing data is deliberate.

## Fresh or reset data

Seed a smaller environment with the scripts under `db/seed/`, including `seed_brands.py`, `seed_compliance_rules.py`, `seed_brand_depth.py`, and `seed_simulated_analytics.py`.

Reset generated data while retaining core brand, knowledge, and rule data:

```bash
docker compose exec api python -m db.seed.reset_demo
```

Use the script's `--wipe-ai-runs` option only when removing historical model-call accounting is intended.

## Worker commands

```bash
docker compose exec worker python -m worker.main --health
docker compose exec worker python -m worker.main --seed
docker compose exec worker python -m worker.main --once
docker compose exec worker python -m worker.main --poll
docker compose exec worker python -m worker.main --sync-analytics
```

The default worker provider is simulation unless a Buffer access token and compatible configuration are supplied. Simulation mode never posts externally.

## Configuration

| Variable | Purpose | Default/current behavior |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy database connection | Compose supplies service-local URL. |
| `GEMINI_API_KEY` | Gemini authentication | Required for model-backed flows. |
| `GEMINI_MODEL` | Gemini model name | API settings default is `gemini-3.6-flash`; verify `.env` for overrides. |
| `PUBLISHER_MODE` | `auto`, `simulation`, or `buffer` provider selection | `auto`. |
| `BUFFER_ACCESS_TOKEN` | Enables real Buffer publishing when configured | Empty means simulation. |
| `BUFFER_PROFILE_ID_LINKEDIN` | Optional Buffer profile override | Empty by default. |
| `POLL_INTERVAL_SECONDS` | Worker polling interval | `10`. |
| `DEMO_DAILY_CALL_CEILING` | Demo guard ceiling | `250`. |
| `DEMO_CALL_MARGIN` | Pause margin before ceiling | `15`. |
| `DEMO_RATE_LIMIT_RUNS` | Per-session run limit | `5`. |
| `DEMO_RATE_LIMIT_WINDOW_SECONDS` | Per-session window | `120`. |
| `FIRECRAWL_API_KEY`, `GOOGLE_PLACES_API_KEY`, `HUNTER_API_KEY`, `BUFFER_API_KEY` | Reserved integration settings | Not required by the current primary flows. |

## Logs and diagnosis

```bash
docker compose logs -f api
docker compose logs -f worker
docker compose ps
curl http://localhost:8000/health
```

API error responses expose a safe summary; detailed tracebacks are in the API container logs. A worker started before migrations may log missing-table errors and recover after `alembic upgrade head`.

## Migrations

Create or apply migrations from the repository root using Alembic. Never treat `Base.metadata.create_all` as a replacement for migration history in a shared environment.
