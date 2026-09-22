# Contributing Notes

## Repository layout

- `apps/api/`: FastAPI application, agents, core clients, models, and routers.
- `apps/web/`: Next.js application and shared API client.
- `db/`: Alembic migrations and seed/fixture utilities.
- `worker/`: publishing and analytics background process.
- `tests/`: unit and compliance regression checks.
- `docs/`: technical documentation.

## Change boundaries

- Add API behavior in the owning router and agent/module; update [api-reference.md](api-reference.md) when a route changes.
- Add persistence through a model plus an Alembic migration; update [data-model.md](data-model.md).
- Add browser API calls through `apps/web/lib/api.ts` and document new screens in [frontend.md](frontend.md).
- Mark simulated or demo-only data explicitly in code and documentation.
- Avoid enabling real external publishing in local development by accident.

## Documentation standard

Document observable current behavior, required configuration, failure modes, and known limitations. Use the code as the final authority when a product description and implementation differ.
