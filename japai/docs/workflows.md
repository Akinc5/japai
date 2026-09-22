# Workflows

## Content and compliance

1. A request enters `/content/generate`, `/repurpose/generate`, `/leads/generate`, or an event/campaign flow.
2. The content agent assembles brand knowledge, restricted-claim instructions, lessons, and optimization context.
3. The generated body is stored as a content version with prompt metadata.
4. Localization creates a language-specific version when requested.
5. The compliance pipeline runs deterministic blocklists, claim extraction, deterministic claim verification, and LLM policy review as applicable.
6. A blocked or unsafe result is rejected or routed to human review. A malformed LLM review must not become an automatic pass.
7. Human reviewers can approve, edit, or reject from `/review`.
8. Decisions create feedback. Aggregated lessons are included in later content prompts.

## Opportunity to campaign

1. `/research/run` collects configured public observations.
2. `/opportunities/scores` exposes deterministic scoring without an LLM call.
3. `/opportunities/generate` persists opportunities and may ask the model only for a narrative for qualifying candidates.
4. `/campaigns/from-opportunity` creates a campaign brief.
5. Content generation uses that campaign as context.

## Lead prospecting

Lead fit is deterministic. The current scoring dimensions are category, size, location, and signals. `/leads/osm-live` can query Singapore data from OpenStreetMap/Overpass; `/leads/generate` persists leads and may create compliance-reviewed outreach drafts. Outreach is a draft workflow and does not send messages.

## Optimization

1. Analytics rows are aggregated by the optimization router.
2. `/optimization/aggregate` exposes the aggregate input for inspection.
3. `/optimization/analyze` asks the model to interpret the aggregate rather than raw event rows.
4. Insights store the numbers they cite and are listed through `/optimization/insights`.
5. Insights can be added to later content prompts. Simulated analytics remain labeled as directional.

## Publishing

1. A `publishing_jobs` row must exist with status `pending` and a valid content asset/version.
2. The worker claims due rows atomically with `FOR UPDATE SKIP LOCKED`.
3. It publishes through the selected provider.
4. Success becomes `published` or provider-accepted `scheduled`; failures preserve an error message.
5. Analytics synchronization refreshes one metric row per asset/platform/metric and marks simulated results.

Approving content does not currently create a publishing job automatically. Jobs are seeded with the worker CLI or inserted by an integrating workflow.
