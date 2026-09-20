# JAPAI — Autonomous AI Marketing Operating System

**A unified, next-generation AI marketing and compliance OS for JA Assure's three core verticals: Jade (Jewellers Block), Jaguar Transit (High-Value Cargo & Transit), and DoctorShield (Medical Indemnity).**

Combining the best-in-class multi-agent foundation with real-world lead discovery, visual prompt studio, and industry event trigger automation.

> **Try to break it yourself:** open **http://localhost:3000/demo**, pick a brand and language, and test any insurance marketing claim. It runs through the 4-step compliance gate in real time.

---

## 🚀 Unified Feature Suite

### 1. New Additions in JAPAI
- **🌐 Live Singapore OpenStreetMap Prospecting (`/leads`):** Real-time Overpass queries to discover live jewelry boutiques, medical centers, and logistics forwarders in Singapore (Orchard, Novena, Jurong).
- **🎨 Visual & Carousel Creative Studio (`/visual-studio`):** Generates Midjourney/Flux hero image prompts and structured 5-slide carousel breakdowns tailored to each brand's aesthetic.
- **🗓️ Industry Event Calendar & 1-Click Trigger Engine (`/events`):** Pre-configured trigger campaigns for SIJE (Singapore International Jewelry Expo), SMA Convention, and Singapore Maritime Week.

### 2. Core Foundation & Multi-Agent Architecture

**Research → content.** The research agent (`agents/research.py`) fetches public reference pages (Wikipedia articles on jewellery, marine insurance, freight, medical malpractice, MAS, and similar), summarizes them into structured notes with source URLs, and treats page text as untrusted input. The content agent (`agents/content.py`) writes platform-specific copy (`linkedin_post`, `instagram_carousel`, `reel_script`, `x_thread`). It pulls from the brand's knowledge base: approved claims go in as usable material, and restricted claims go in as explicit "do NOT say" instructions. The full system prompt is saved on every version, so you can inspect exactly what the model was told.

**The 4-step compliance gate** (`agents/compliance.py`). Most "AI compliance" amounts to asking an LLM whether the copy is OK. Here the LLM is only the last of four steps:

1. **Deterministic blocklist.** 16 English phrases, plus separate lists for Chinese, Malay and Indonesian. A hit blocks the copy immediately and skips steps 2–4, so blocked copy costs **zero** model calls.
2. **Claim extraction.** An LLM lists every checkable factual or coverage claim. Claims are always written out in English, even when the copy is in another language.
3. **Claim verification.** Each claim is matched against the brand's `approved_claim` and `restricted_claim` knowledge. No LLM is involved.
4. **LLM policy review.** The model sees the copy, the flagged claims and the brand's rules, and replies in Gemini's schema-enforced JSON mode. It returns a risk level, the offending phrases with a `policy_ref`, and a suggested revision. If the response is malformed, the verdict falls back to **review**, never to pass.

`block` goes straight to rejected and never reaches a human. `pass` and `review` go to the human queue, with different badges.

**Human review** (`/review`, `/review/[id]`). Reviewers see the copy, each compliance finding with its reason and policy code, and a provenance panel showing the actual knowledge chunks used. They can **Approve**, **Edit** (which creates a new version) or **Reject** (a reason tag and a note are required).

**Feedback → lessons loop** (`agents/lessons.py`). Each reject, edit, or approve-with-note is grouped into one lesson per brand and reason tag, with no LLM involved. The content agent adds the top lessons to its next system prompt, with real computed shares. The before/after is stored on every version:

| Jade version | Generated | Lessons in prompt |
|---|---|---|
| `0b1d6bb4…` | 05:44, before any feedback | none |
| `9e70db15…` | 05:51, after 3 reviewer decisions | *"Keep the tone consultative rather than promotional… (cited in 50% of past reviewer feedback, n=1)"* and one more |

```bash
curl -s localhost:8000/content/0b1d6bb4-759f-4cc3-a2f9-3417fbebfe35 | python3 -c "import sys,json;print(json.load(sys.stdin)['version_metadata']['system_prompt'])"
curl -s localhost:8000/content/9e70db15-0280-45d2-b5d7-801bba396c99 | python3 -c "import sys,json;print(json.load(sys.stdin)['version_metadata']['system_prompt'])"
```

> **What the loop does *not* show yet:** an outcome improvement. `GET /metrics/rejection-rate` (the widget on `/review`) groups decided versions (approved, or rejected by a reviewer or by a compliance block) into batches of 5. The demo data has only 7 decided agent versions across three brands, so each brand has **one batch**. That is a baseline, not a trend. The mechanism is in place and inspectable; there isn't yet enough data to claim the rejection rate goes down.

### Beyond the brief's minimum

**Opportunity agent** (`/opportunities`). Scoring uses **no LLM** and shows its working. Every opportunity stores the full calculation, and the UI displays it:

```
score = competitor_mentions×10 + recency_weight×20 + coverage_match×30   (capped at 100)
```

`recency_weight` drops to zero linearly over 30 days. `coverage_match` measures keyword overlap with the brand's own approved claims. The LLM is only called for candidates that score ≥ 25 and are backed by real research, and only to write the narrative, never the score. `GET /opportunities/scores` previews the whole scoring pass with zero LLM calls.

**Optimization agent** (`/optimization`). **It runs on simulated engagement data**, and the page says so in a red banner. `seed_simulated_analytics` writes 20 made-up Jade posts and 60 analytics rows, all flagged `is_simulated=true`. The seeder deliberately builds in two patterns and one decoy. The loop is still real and evidence-based: aggregation is deterministic, the model sees only the aggregate table, and each insight stores the numbers it came from so you can check them. It found both patterns and did not overstate the decoy:

| Insight | Cited | Live aggregate |
|---|---|---|
| Educational beats promotional | 4.38% vs 2.18% | 4.38 / 2.18 ✓ |
| Short hook beats long intro | 4.0% vs 2.56% | 4.0 / 2.56 ✓ |
| LinkedIn vs Instagram: keep distribution similar | 3.4% vs 3.38% | ✓ reported as flat, not sold as a finding |

These insights go into the content prompt next to the reviewer lessons, labelled *"SIMULATED data — treat as directional, not proven"*. Insights exist for Jade only. The angle and hook groupings depend on tags the seeder writes, and real generated copy isn't classified that way.

**Lead agent** (`/leads`). Fit scoring uses no LLM: `category×40 + size×30 + location×20 + signals×10`. The 22 prospects are **synthetic, hand-written businesses** (`source=seed_data`, `example.com` contacts), and the page says so. Outreach drafts go through the same compliance gate and the same review queue as content. Nothing is ever sent.

### Multi-brand

All three brands run the same agents. What differs per brand is the data: knowledge base (13 chunks each), research sources, and compliance rules. There are 16 rules: **6 global**, plus **2 Jade-only** (`JD-`), **4 Jaguar Transit-only** (`JT-`) and **4 DoctorShield-only** (`DS-`). A brand sees its own rules plus the global ones, never another brand's.

The same sentence, *"With DoctorShield behind you, a malpractice claim will be defended successfully and dismissed…"*, checked live through `/demo` under two brands:

| Checked as | Verdict | Rules cited |
|---|---|---|
| DoctorShield | block | `DS-OUTCOME-01` (no guaranteed legal outcomes), `DS-CLINICAL-01` |
| Jade | block | `MAS-ADV-01`, `CLAIM-SUBST-01`, `SUPERLATIVE-01`: global rules only, **no `DS-` rule** |

In the stored review data, brand-specific rules also fire only for their own brand. For example, `JT-CONTINUITY-01` flagged Jaguar Transit copy promising cover *"across air, sea, and land legs under a single policy"*. No Jade or DoctorShield review cites a `JT-` rule.

### Multilingual: English, Chinese (Simplified), Malay, Bahasa Indonesia

Localization (`agents/localization.py`) is **cultural adaptation, not translation**. The prompt says a faithful translation counts as a failed result. Each language gets its own market guidance (e.g. Chinese: family-business continuity, no hard-sell urgency; Malay: *amanah*, community framing). Malay and Indonesian are treated as separate languages with separate vocabulary and blocklists. One English Jade post, adapted:

| | The same sentence (back-translated) |
|---|---|
| **EN** | "…custom inventory represents both significant capital and **the culmination of artisanal expertise**." |
| **中文** | "…each piece of custom stock is a heavy capital outlay and **the crystallised craft of generations passed down**" (世代传承), matching the family-legacy framing in the guidance |
| **MS** | "…not merely business capital, but **the fruit of hard toil** (*penat lelah*) and valuable artistry"; a loss becomes a *musibah* (misfortune) |
| **ID** | same idea in Indonesian register, re-targeted from Singapore to **the Indonesian trade** |

Paragraph structure stays close to the source. The adaptation shows in framing and market targeting.

**Each language gets its own compliance check.** In the example above, the Chinese and Malay versions **passed**. The Indonesian version was sent to **review**: step 4 quoted the Indonesian sentence verbatim, cited `CLAIM-SUBST-01` and the Jade-only `JD-VALUE-01` (implying settlement at "true value"), and wrote its suggested revision **in Indonesian**. *Caveat: the non-English blocklists haven't been reviewed by a native speaker or a compliance officer.*

### Project 2: auto-publishing worker (`worker/`)

A separate container polls the `publishing_jobs` table, claims due jobs with `SELECT … FOR UPDATE SKIP LOCKED`, publishes them, and records `published` (with `external_post_id`), `scheduled`, or `failed` (with `error_message`). It then syncs engagement metrics back into `analytics`.

What it does today, stated plainly:

- **Approving content does NOT create a publishing job.** That link isn't wired. Jobs come from `python -m worker.main --seed` (three test jobs) or direct inserts.
- **Simulation mode unless `BUFFER_ACCESS_TOKEN` is set.** With `PUBLISHER_MODE=auto` (the default) and no token, "published" means the job row moved to `published` with an ID like `sim_linkedin_c5832169…`, and the metrics synced back are generated and flagged `is_simulated=true`. **Nothing is posted anywhere.**
- The Buffer publisher is covered by tests against mocked HTTP responses (success, 401, 429, missing token). It has **not** been run against a live Buffer account.

### Live judge demo (`/demo`)

Pick a brand and language, then type a claim. **Generate** mode writes copy about your topic and checks it. **Check my text exactly as written** runs compliance on your literal words. The page shows each of the four steps, built from the actual stored compliance review. Things to try:

- A forbidden phrase in check mode (*"guarantees a payout on every claim with no exceptions"*). It's blocked at step 1 with **zero** model calls.
- The DoctorShield sentence above, under DoctorShield and then under Jade.
- **简体中文**, which is generated, adapted, then checked against the Chinese blocklist.
- Prompt injection or an off-topic request. The input guard (length, injection patterns, topic terms) catches it before the model, at no cost, and doesn't echo your input back.

There is a 5-run limit per 120s per session. A daily budget is checked against real `ai_runs` counts. The 250-call ceiling is our own operational guess, not a documented Google limit. Near that ceiling the badge switches from **● LIVE** to **● LIVE PAUSED**, and results come from **real recorded runs** labelled **▶ RECORDED — NOT LIVE** with the time they were captured.

---

## What's explicitly not built, and why

We chose depth on compliance, feedback and explainability over covering every item in the brief.

| Not built | Why / what exists instead |
|---|---|
| **Video / Reels** | `reel_script` produces a script only. No rendering, voiceover or editing. |
| **Thai (and Tamil)** | Adding a language is a config entry plus a blocklist. We didn't add languages whose blocklist we couldn't check, because an unreviewed compliance list is worse than none. |
| **RL / fine-tuning** | "Learns from feedback" means **prompt-level few-shot injection**: reviewer decisions and engagement aggregates become text in the next prompt. No weights change, no reward model exists, and this isn't RLHF. It is visible and reversible by design. |
| **Approval → publish link** | The worker is built, but approval doesn't queue jobs (see Project 2). |
| **Real posting and real engagement data** | Simulation mode only. All analytics rows are `is_simulated=true`. |
| **Real lead sourcing / sending outreach** | Prospects are synthetic. Drafts are reviewed and never sent. Hunter / Google Places / Firecrawl keys are unused placeholders. |
| **Measured rejection-rate improvement** | Not enough reviewed volume yet (see the feedback loop above). |
| **Vector retrieval** | The `embedding` column exists but is NULL for all 54 chunks. Retrieval is by category and keyword. |
| **Auth / multi-tenancy** | Single-tenant local demo. |

---

## Architecture

```
 Research ─▶ Opportunity ─▶ Campaign ─▶ Content ──▶ Localization (zh-Hans / ms / id)
 (Wikipedia    (deterministic   (brief)    (RAG over         │  each language is its own asset
  pages)        score)                      knowledge +       ▼
                                            lessons +   4-step Compliance ─ block ─▶ rejected
 Lead agent ─▶ outreach draft ──────────▶   insights)          │ pass / review
 (synthetic)                                                   ▼
                                                   Human review (/review)
                                              approve │ edit │ reject ──▶ feedback ─▶ lessons ─┐
                                                      │                                        │
                                           (not wired)┊                     next prompt ◀──────┘
                                                      ▼                          ▲
                              publishing_jobs ◀── --seed / insert                │
                                    │                                            │
                          Worker (SKIP LOCKED) ─▶ Simulation │ Buffer            │
                                    │                                            │
                                    ▼                                            │
                               analytics ─▶ Optimization agent ─▶ insights ──────┘
```

**Stack** (from `docker-compose.yml` and the package files): four Docker Compose services.

- `postgres`: `pgvector/pgvector:pg16`
- `api`: Python 3.11, FastAPI 0.115, SQLAlchemy 2.0, Alembic (10 migrations, 19 tables), Google Gemini via `google-generativeai` (default `gemini-3.5-flash-lite`)
- `web`: Next.js 14, React 18, TypeScript
- `worker`: Python 3.11, APScheduler, `requests`

Every LLM call is logged to `ai_runs` (agent, model, prompt version, timing, status, error) and shown on `/observability`. Token counts and cost are not recorded, and the page says so.

---

## How to run

**Prerequisites:** Docker Desktop and a [Gemini API key](https://aistudio.google.com/apikey).

```bash
cp .env.example .env            # then set GEMINI_API_KEY=...
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python -m db.seed.load_demo_snapshot   # populated demo data, 0 LLM calls
curl localhost:8000/health      # {"status":"ok","db":"connected"}
```

Dashboard at **http://localhost:3000**, API at **http://localhost:8000** (OpenAPI docs at `/docs`).

On the first `up`, the worker starts before migrations and logs `relation "publishing_jobs" does not exist`. It recovers on its own once `alembic upgrade head` has run.

> **A fresh clone opens with the same data as the demo instance.** `db/fixtures/demo_snapshot.sql` is a data-only `pg_dump` of the demo database, taken after the real LLM runs that built it. It is captured output, not hand-written fixtures, and loading it makes no model calls. After loading you get 3 brands, 16 rules, 54 knowledge chunks (15 research notes), 9 opportunities, **13 items in `/review`** across three brands and four languages, 22 leads, 60 simulated analytics rows with 3 Jade insights, and 411 `ai_runs` on `/observability`. The version IDs in this README are the same on every clone. The loader replaces all table contents, so it refuses to run over a database that already has content unless you pass `--force`.
>
> To start empty instead, run `seed_brands`, `seed_compliance_rules` and `seed_brand_depth` (plus `seed_simulated_analytics` if you want the analytics data), then drive the pipeline through the API, which costs Gemini calls: `POST /research/run` → `/opportunities/generate` → `/campaigns/from-opportunity` → `/content/{version_id}/localize` → `/leads/generate` → `/optimization/analyze`.

| Env var | Required? | Notes |
|---|---|---|
| `GEMINI_API_KEY` | **yes** | The only key needed. |
| `GEMINI_MODEL` | no | Defaults to `gemini-3.5-flash-lite`. |
| `DATABASE_URL` | no | Leave blank. Compose sets it for `api` and `worker`. |
| `PUBLISHER_MODE` | no | `auto` (default), `simulation`, or `buffer`. |
| `BUFFER_ACCESS_TOKEN` | no | **Unset means simulation mode and nothing is posted.** If set with `auto`, the worker **will post real LinkedIn updates** for any pending job. |
| `BUFFER_PROFILE_ID_LINKEDIN` | no | Overrides Buffer profile auto-discovery. |
| `POLL_INTERVAL_SECONDS` | no | Worker poll interval (default 10). |
| `DEMO_DAILY_CALL_CEILING`, `DEMO_CALL_MARGIN`, `DEMO_RATE_LIMIT_RUNS`, `DEMO_RATE_LIMIT_WINDOW_SECONDS` | no | `/demo` guards (250 / 15 / 5 / 120). |
| `FIRECRAWL_API_KEY`, `GOOGLE_PLACES_API_KEY`, `HUNTER_API_KEY`, `BUFFER_API_KEY` | no | Unused placeholders. |

**Resetting.** `docker compose exec api python -m db.seed.reset_demo` wipes all generated data: opportunities, campaigns, content, reviews, feedback, lessons, leads, research notes, publishing jobs and analytics. It keeps brands, knowledge chunks and all 16 rules. It **keeps `ai_runs`** by default, because that table is the only record of cumulative LLM spend and it feeds both `/observability` and the `/demo` daily budget. Pass `--wipe-ai-runs` to clear it; the current count is printed first so the number isn't lost. To get the populated demo state back, run `load_demo_snapshot --force` (note that this also replaces `ai_runs` with the snapshot's copy).

**Tests:**

```bash
# No LLM calls
docker compose exec api python -m tests.unit.test_lessons_aggregation
docker compose exec api python -m tests.unit.test_lead_scoring
docker compose exec api python -m tests.unit.test_optimization_aggregation
docker compose exec api python -m tests.unit.test_brand_rule_scoping
docker compose exec api python -m tests.unit.test_demo_guards
docker compose exec api python -m tests.compliance_regression.verify_multilingual_blocklist
docker compose exec api python -m tests.compliance_regression.verify_lead_outreach
docker compose run --rm --no-deps -v "$PWD/tests:/app/tests" worker python -m tests.unit.test_publishing_worker   # 20 tests

# Spend LLM calls
docker compose exec api python -m tests.compliance_regression.verify_brand_rules       # ~4 calls
docker compose exec api python -m tests.compliance_regression.verify_phase3_pipeline   # 12 fixtures, ~24 calls
```

---

## Demo script (~10 min)

The demo database is already populated. **Don't reset before demoing.** Counts below are the shipped demo state. Generate-mode `/demo` runs use the real content agent, so they join this queue and the count goes up.

1. **`/review`**: *"13 items awaiting review across all three brands and four languages. 10 English, one each Chinese, Malay, Indonesian. None of them were blocked by the compliance gate."* (0 calls)
2. **Open the Indonesian (ID) Jade item**: *"Step 4 quotes the Indonesian sentence, cites `CLAIM-SUBST-01` and the Jade-only `JD-VALUE-01`, and writes the fix in Indonesian. Its Chinese and Malay siblings from the same English source passed. Each language is checked on its own."* Point at the provenance panel. (0 calls)
3. **Feedback loop**: run the two `curl` commands from the feedback-loop section. *"Before feedback, no lessons in the prompt. After three reviewer decisions, the lessons are injected with their shares."* Then show the rejection-rate widget and say it honestly: *"one batch per brand so far, which is a baseline, not yet a trend."* (0 calls)
4. **`/opportunities`**: *"Every score shows its arithmetic. The model writes the narrative, never the number."* (0 calls)
5. **`/optimization`** (Jade): *"The data is simulated and says so. The insights cite 4.38% vs 2.18%, you can check that against the table, and it refused to oversell the flat platform difference."* (0 calls)
6. **`/demo`, hand over the keyboard**: *"Try to break it."* Suggested order: the forbidden-phrase chip in check mode (0 calls), the DoctorShield sentence under DoctorShield then Jade (~2 calls each), 简体中文 in generate mode (~4 calls), a prompt injection (0 calls). Point at the **● LIVE** badge.
7. **Project 2 worker** (terminal). Say it up front: *"Approving content doesn't queue a publish job yet. These are seeded jobs, and without a Buffer token nothing leaves the machine."*
   ```bash
   docker compose exec worker python -m worker.main --health    # provider: simulation
   docker compose exec worker python -m worker.main --seed      # worker picks these up within ~10s
   docker compose logs --since 1m worker | grep -E "succeeded|failed:|Poll result"
   docker compose exec postgres psql -U ja_assure -d ja_assure -c \
     "SELECT platform, status, external_post_id, left(error_message,60) FROM publishing_jobs;"
   ```
   Expected: one `published` with a `sim_linkedin_…` ID, one `failed` with its error, one still `pending` (scheduled for tomorrow). Each job is claimed at most once.

Optional extras: **`/leads`** (scoring maths shown in full, synthetic-data banner) and **`/observability`** (every LLM call this system has made).

If the network or quota fails mid-demo, beats 1–5 are database reads and keep working, and `/demo` falls back to labelled recorded runs.

---

## Engineering notes

- **Compliance has a regression suite that gets re-run whenever nearby code changes.** 12 known-bad phrasings contain no blocklisted words, so the LLM steps have to catch them, not the substring scan. Separate suites cover brand-rule scoping, the multilingual blocklists, and outreach going through the same gate.
- **Demo and test data are kept out of real metrics.** Every content asset has an `origin` (`agent` / `manual` / `test_fixture` / `simulated`). The review queue, lessons and rejection-rate count only `agent`. Every analytics row carries `is_simulated`. The optimization aggregate accepts only `agent` and `simulated` posts. This was a real leak: before the filter, worker test posts moved Jade's LinkedIn figure from 3.40% to 3.82%. A regression test now covers it.
- **Concurrency on the worker was tested, not assumed.** Verifying the merge turned up three bugs, now fixed with regression tests: the poll job was registered paused and never ran; due jobs were re-claimed and would have re-posted to Buffer on every poll; and analytics sync added a new row set every pass. Claims use `SKIP LOCKED`. Analytics sync locks the job row, and it was checked under concurrent syncs to keep exactly one row per post, platform and metric.
