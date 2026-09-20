# JA Assure — Project 2 ("The Hands") Worker

Background publishing worker and social platform integration for **JA Assure**.

Project 2 connects to Project 1 exclusively through the shared **`publishing_jobs`** queue table. It polls for approved and scheduled content, dispatches posts to social providers (**Buffer** for **LinkedIn** and multi-channel posting, with a self-contained **Simulation/Mock mode**), transitions job statuses, records external post IDs or failure errors, and syncs engagement metrics back into the `analytics` table.

---

## Architecture & Contract

```
[Project 1: Review Queue]
        │
        ▼ (writes approved content)
 ┌────────────────────────────────────────────────────────┐
 │                   publishing_jobs                      │
 │ ────────────────────────────────────────────────────── │
 │ id: UUID                                               │
 │ content_asset_id: UUID (FK -> content_assets)          │
 │ content_version_id: UUID (FK -> content_versions)      │
 │ platform: 'linkedin' | 'x' | 'instagram' | ...         │
 │ status: 'pending'|'scheduled'|'publishing'|'published' │
 │         |'failed'|'cancelled'                          │
 │ scheduled_at: timestamptz (optional)                   │
 │ published_at: timestamptz (set on publish)             │
 │ external_post_id: text (ID returned by provider)       │
 │ error_message: text (set on failure)                   │
 └────────────────────────────────────────────────────────┘
        │
        ▼ (SELECT ... FOR UPDATE SKIP LOCKED)
 ┌────────────────────────────────────────────────────────┐
 │              Project 2: Publishing Worker              │
 │ ────────────────────────────────────────────────────── │
 │ 1. Atomic Claim: status -> 'publishing'               │
 │ 2. Content Read: fetch body from content_versions     │
 │ 3. Dispatch: Buffer API (LinkedIn) or Simulation       │
 │ 4. Update Status: 'published' or 'failed' + error msg  │
 │ 5. Analytics Sync: write metrics to 'analytics' table  │
 └────────────────────────────────────────────────────────┘
```

### Safety & Idempotency Guarantees
- **Row-Level Locking**: Uses PostgreSQL `FOR UPDATE SKIP LOCKED` so concurrent polling sweeps or multiple worker instances never double-claim or double-post the same row.
- **Immediate State Transition**: Claimed jobs are transitioned to `status='publishing'` inside the claim transaction so subsequent sweeps ignore them.
- **Zero Data Corruption**: On network, auth, or validation failure, the job status moves to `'failed'` with the exact error message preserved in `error_message`. It is never deleted or corrupted.
- **Scheduled Content**: A `pending` job with `scheduled_at` in the future is skipped until due, then published immediately.
- **Status meanings**: `pending` = in our queue (only status the poller claims). `scheduled` = already handed to the provider for later posting — terminal for the worker and **never re-claimed**, so a due job can't be re-sent to Buffer on every poll.
- **Not automatic yet**: approving content in the review dashboard does **not** create a `publishing_jobs` row. Jobs are created by `--seed` or inserted directly; wiring approval to the queue was deliberately left out of this merge.

---

## Social Provider Integration

### 1. Buffer (Primary Provider)
- **Target Platform**: **LinkedIn** (default; extensible to Twitter/X, Instagram, Facebook).
- **Authentication**: Bearer token via `BUFFER_ACCESS_TOKEN`.
- **Channel Discovery**: Automatically resolves connected channel/profile IDs via `/profiles.json`, or overrides with `BUFFER_PROFILE_ID_LINKEDIN`.
- **Endpoints**:
  - `POST /updates/create.json` (direct posting with `now=true`, or scheduled with `scheduled_at`).
  - `GET /updates/<id>/interactions.json` (analytics pull-back for impressions, likes, clicks, comments, shares).

### 2. Simulation / Mock Mode
- Automatically active when `PUBLISHER_MODE=simulation` or when `BUFFER_ACCESS_TOKEN` is unset/placeholder.
- Fully offline and deterministic: generates realistic post IDs (`sim_linkedin_<hash>`) and engagement metrics without needing external network calls or credentials.
- Supports deliberate error testing (e.g. `[SIMULATE_FAIL]` in body or invalid platforms like `myspace_unsupported`).

---

## Configuration (`.env`)

Add the following environment variables to your `.env` file (see `.env.example`):

```bash
# Database connection
DATABASE_URL=postgresql+psycopg2://ja_assure:ja_assure_pw@localhost:5432/ja_assure

# Provider mode: 'auto', 'buffer', or 'simulation'
PUBLISHER_MODE=auto

# Buffer Configuration (leave empty to use Simulation mode)
BUFFER_ACCESS_TOKEN=your_buffer_access_token_here
BUFFER_PROFILE_ID_LINKEDIN=your_buffer_linkedin_profile_id_here

# Worker Settings
POLL_INTERVAL_SECONDS=10
BATCH_SIZE=5
MAX_RETRIES=3
```

---

## How to Run

### 1. Single-Pass Sweep (CLI / Cron)
Processes all currently due jobs once and exits:
```bash
python -m worker.main --once
```

### 2. Continuous Polling Daemon
Starts background scheduling (using APScheduler or resilient polling loop):
```bash
python -m worker.main --poll --interval 10
```

### 3. Check Provider Connectivity
```bash
python -m worker.main --health
```

### 4. Sync Engagement Analytics (Stretch Goal)
Pulls reach and engagement metrics for published posts and writes to `analytics`.
Each sync **refreshes one row per (asset, platform, metric) in place** — it never appends a
new set. The optimization agent counts `engagement_rate` rows as posts, so append-only syncs
would make one post look like many. Any legacy duplicates are collapsed on the next sync.
The published job row is locked during sync so two workers can't double-insert.
```bash
python -m worker.main --sync-analytics
```

### 5. Running with Docker Compose
The worker is included as a service in `docker-compose.yml`:
```bash
docker compose up -d worker
docker compose logs -f worker
```

---

## Self-Contained Verification

You can fully verify the worker without needing live Project 1 AI generations:

### Step 1: Run the Unit Test Suite
Runs the full 15-test test suite covering all requirements from the brief:
```bash
python -m tests.unit.test_publishing_worker
```
Test suite validates:
- Simulation publisher success path & scheduled path
- Deliberate failure trigger & unsupported platform rejection
- Analytics generation
- Buffer 401 Unauthorized, 429 Rate limit, and missing token handling
- Buffer successful post creation
- Worker `pending` -> `published` transition with `external_post_id` and `published_at`
- Worker `pending` -> `failed` transition with `error_message`
- Missing `ContentVersion` handling
- Idempotency & double-processing prevention
- Scheduled future job safety
- Analytics sync into `analytics` table

### Step 2: Seed Test Data into Local Database
```bash
python -m worker.main --seed
```
Seeds:
1. Ready LinkedIn job (`status='pending'`).
2. Future scheduled LinkedIn job (`status='pending'`, `scheduled_at` tomorrow).
3. Intentional failure job (`platform='myspace_unsupported'`).

### Step 3: Execute Worker Sweep
```bash
python -m worker.main --once
```
Observe:
- Ready job transitions to `status='published'`, `external_post_id` populated, `published_at` timestamp set.
- Intentional failure job transitions to `status='failed'`, `error_message` records descriptive failure.
- Future scheduled job remains `status='pending'` until its `scheduled_at` passes.

### Step 4: Verify Idempotency (Double-Processing Check)
Run `--once` a second time:
```bash
python -m worker.main --once
```
Observe:
- `claimed: 0`, no jobs re-processed, no duplicate postings.
