# Integrations

## Google Gemini

The API uses the LLM client under `apps/api/core/llm_client.py` for model-backed generation, claim extraction, policy review, localization, and selected narratives. Model calls are recorded in `ai_runs`. Credentials are supplied through `GEMINI_API_KEY`; model selection is controlled by `GEMINI_MODEL`.

The demo applies local rate and daily-call guards. These are application controls, not Google quota guarantees.

## OpenStreetMap Overpass

The lead router can query live Singapore business data through the Overpass client in `apps/api/core/osm_client.py`. This powers `/leads/osm-live`. Network availability, upstream rate limits, and returned tag quality affect results.

## Buffer publishing

The worker publisher abstraction supports simulation and Buffer-backed publishing. Provider selection is controlled by `PUBLISHER_MODE` and credentials such as `BUFFER_ACCESS_TOKEN`. The worker records provider IDs and errors in `publishing_jobs`.

Configure real publishing only after validating the target profile and content approval policy. A configured token can cause external posts to be sent.

## Research sources

Research is implemented as a public-source workflow and stores source URLs with observations. The current product documentation references public reference pages. Optional Firecrawl, Google Places, and Hunter variables exist in configuration, but they are not prerequisites for the main local demo and should be treated as reserved integration points unless the code path is explicitly enabled.

## Database

PostgreSQL 16 is run with the `pgvector/pgvector:pg16` image. The current retrieval path is primarily structured/category/keyword based; having the vector-capable image does not mean embeddings are populated for every demo row.
