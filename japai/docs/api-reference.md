# API Reference

Base URL: `http://localhost:8000`. FastAPI interactive documentation is available at `/docs` and `/redoc`.

The route modules under `apps/api/routers/` are authoritative for payload schemas and response fields. The table below inventories the implemented HTTP surface.

## Health and brands

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | API service status and phase. |
| GET | `/health` | Database connectivity health check. |
| GET | `/brands` | List configured brands. |

## Content and campaigns

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/content/generate` | Generate a content version for a brand and brief. |
| POST | `/content/{content_version_id}/localize` | Create a localized version. |
| GET | `/content/languages` | List supported localization languages. |
| GET | `/content/{content_version_id}` | Retrieve a content version and compliance metadata. |
| POST | `/campaigns/from-opportunity` | Create a campaign from an opportunity. |

## Compliance and review

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/review/pending` | List content awaiting human review. |
| GET | `/review/{content_version_id}` | Retrieve review detail, findings, and provenance. |
| POST | `/review/{content_version_id}/decision` | Approve, edit, or reject a version. |
| GET | `/metrics/rejection-rate` | Return rejection-rate batches by brand. |

## Research and opportunities

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/research/run` | Run configured research sources for a brand. |
| GET | `/research/observations` | List stored research observations. |
| POST | `/opportunities/generate` | Generate opportunities from research. |
| GET | `/opportunities` | List opportunities, optionally filtered by brand. |
| GET | `/opportunities/scores` | Preview deterministic opportunity scores. |

## Leads

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/leads/generate` | Generate scored leads and optional outreach drafts. |
| GET | `/leads` | List leads, optionally filtered by brand. |
| GET | `/leads/scores` | Preview lead scoring. |
| GET | `/leads/osm-live` | Query live Singapore prospects through Overpass. |
| GET | `/leads/{lead_id}` | Retrieve a lead and outreach state. |

## Optimization and observability

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/optimization/aggregate` | Preview analytics aggregation. |
| POST | `/optimization/analyze` | Create performance insights from aggregate data. |
| GET | `/optimization/insights` | List stored performance insights. |
| GET | `/observability/runs` | List recorded AI runs. |
| GET | `/observability/summary` | Summarize AI run count, status, and latency. |

## Demo and creative tools

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/demo/quota-status` | Show live/paused demo quota state. |
| GET | `/demo/fallback-examples` | Return recorded fallback examples. |
| GET | `/demo/suggestions` | Return demo prompt suggestions. |
| POST | `/demo/run` | Run the interactive generation or exact-text compliance demo. |
| POST | `/visual/generate` | Generate visual prompt and carousel output. |
| GET | `/events` | List configured industry events. |
| GET | `/events/{event_id}` | Retrieve one event. |
| POST | `/events/trigger` | Trigger an event campaign. |
| GET | `/repurpose/templates` | List repurposing templates. |
| POST | `/repurpose/generate` | Generate repurposed content. |
| POST | `/repurpose/save-to-queue` | Save repurposed content to the review queue. |

## Error behavior

The API maps known failures to structured JSON:

- `400` for invalid input and not-found conditions represented as `ValueError`.
- `502` for malformed LLM responses.
- `503` when Gemini is unavailable because of credentials, quota, or network failure.
- `500` for unexpected errors, with the full traceback kept in API logs.

## API conventions

- IDs are UUIDs.
- JSON is the transport format.
- Optional filters commonly use `brand_id`, `limit`, `hours`, or `language` query parameters.
- There is no authentication or tenant context in the current local demo.
