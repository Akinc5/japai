# JAPAI Documentation

This folder is the maintained technical documentation set for JAPAI, the JA Assure AI marketing and compliance operating system.

## Start here

- [Architecture](architecture.md): runtime components, boundaries, and request flow.
- [API reference](api-reference.md): implemented FastAPI routes grouped by capability.
- [Data model](data-model.md): SQLAlchemy entities, relationships, and lifecycle states.
- [Workflows](workflows.md): content, compliance, review, lead, opportunity, optimization, and publishing flows.
- [Setup and operations](setup-and-operations.md): local startup, migrations, seed data, environment, and worker commands.
- [Frontend](frontend.md): Next.js screens and their API responsibilities.
- [Integrations](integrations.md): Gemini, OpenStreetMap, Buffer, and research integrations.
- [Testing](testing.md): available tests, what they cover, and LLM-call expectations.
- [Known limitations](known-limitations.md): current behavior, demo constraints, and explicitly unfinished links.

## Source of truth

The code is authoritative when this documentation and a narrative document disagree. In particular:

- API route declarations live under `apps/api/routers/`.
- Request and response behavior is implemented in those routers and agent modules.
- Persistence is defined by `apps/api/models/` and `db/migrations/`.
- Browser API calls are centralized in `apps/web/lib/api.ts`.
- The publishing worker is implemented under `worker/`.

## Product references

- [Project README](../README.md): product overview, demo script, and quick start.
- [Application documentation](../APP_DOCUMENTATION.md): broader product architecture and feature description.
