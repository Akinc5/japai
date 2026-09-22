# Known Limitations

These are current repository behaviors, not roadmap promises.

- There is no authentication, authorization, or multi-tenant isolation in the local application.
- Approving content does not automatically create a publishing job.
- Publishing is simulation-only unless Buffer credentials and provider configuration are intentionally supplied.
- The demo seed contains synthetic leads and simulated analytics; they are not production evidence.
- Outreach drafts are reviewed but not sent by the current lead workflow.
- Thai and Tamil localization are not implemented.
- Video rendering, voiceover, and editing are not implemented; reel output is a script.
- Feedback learning is prompt-level lesson injection, not model fine-tuning or reinforcement learning.
- The vector-capable database is present, but the current demo retrieval path is primarily category/keyword based and embeddings may be null.
- The demo quota ceiling and per-session guard are application heuristics, not provider limits.
- Token usage and cost accounting are not recorded in the current AI run model.
- Native-language compliance blocklists and localization guidance should receive review from qualified native speakers and compliance professionals before production use.
- Optional environment variables for Firecrawl, Google Places, Hunter, and Buffer API keys do not by themselves activate integrations.
- API startup attempts to create tables and seed initial brands when none exist; production schema changes should still be managed through Alembic.
