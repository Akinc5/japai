# JAPAI — Autonomous AI Marketing Operating System
## Complete System Documentation & Product Architecture

---

## 1. Executive Summary

**JAPAI** is a domain-specific, autonomous AI Marketing & Compliance Operating System engineered specifically for specialized niche insurance verticals. It is tailored for **JA Assure’s three flagship insurance product lines**:

1. **Jade** — Jewellers Block Insurance (high-end jewelry stores, artisanal workshops, diamond/gemstone merchants).
2. **Jaguar Transit** — High-Value Cargo & Transit Insurance (air, sea, road transit, cross-border freight forwarding).
3. **DoctorShield** — Medical Malpractice & Professional Indemnity Insurance (private clinics, specialists, surgeons).

Unlike generic AI copywriting wrappers, JAPAI implements:
* **A 4-Step Deterministic + LLM Compliance Gate** ensuring insurance claims comply with MAS (Monetary Authority of Singapore) regulations and brand-specific underwriting rules.
* **Cultural Localization Engine** (English, Simplified Chinese, Bahasa Melayu, Bahasa Indonesia) with cultural framing rather than direct translation.
* **Continuous Human-in-the-Loop Feedback Loop** where reviewer rejections and edits automatically refine future generation prompts.
* **Live OpenStreetMap Singapore Prospecting Engine** for real-time local lead discovery across Orchard, Novena, and Jurong.
* **Visual & Carousel Creative Studio** generating prompt blueprints for Midjourney/Flux and 5-slide educational carousels.
* **Industry Event Calendar & Trigger Automation** (SIJE, SMA Convention, Singapore Maritime Week).
* **Automated Background Publishing Worker** with atomic Postgres lock claiming (`SKIP LOCKED`) and Buffer/LinkedIn integrations.

---

## 2. High-Level Architecture

```mermaid
graph TD
    subgraph Frontend [Web Application (Next.js 14 / Tailwind / Vanilla CSS)]
        UI[Dashboard / Demo / Repurpose / Leads / Visual Studio / Events / Observability]
    end

    subgraph Backend [FastAPI Application (Python 3.11)]
        API[FastAPI Routers & Endpoints]
        LLM[Gemini 1.5 / 2.0 Flash Client with Fallbacks]
        Gate[4-Step Compliance Engine]
        OsmClient[OpenStreetMap Overpass API Client]
        Agents[Multi-Agent System: Research, Content, Optimization, Lessons]
    end

    subgraph Database [PostgreSQL with pgvector]
        DB[(Knowledge Base, Brand Claims, Rules, Content Versions, Leads, Jobs)]
    end

    subgraph Worker [Autonomous Background Worker]
        PubWorker[Publishing Worker / APScheduler / Buffer Sync]
    end

    UI -->|REST / JSON| API
    API --> LLM
    API --> Gate
    API --> OsmClient
    API --> Agents
    API --> DB
    PubWorker --> DB
```

---

## 3. Core Modules & Key Features

### 🏛️ 1. Multi-Brand Knowledge Base & Isolation
* Each brand (`Jade`, `Jaguar Transit`, `DoctorShield`) has strictly partitioned knowledge chunks in PostgreSQL:
  * **Approved Claims**: Factual coverage limits, validated policy features.
  * **Restricted Claims**: Unsubstantiated claims, prohibited promises (e.g. "guaranteed win in court").
  * **Rule Engine**: 6 global insurance rules (MAS advertising standards, superlative restrictions) + 10 brand-specific rules (`JD-`, `JT-`, `DS-`).

### 🛡️ 2. The 4-Step Compliance Gate
Insurance marketing copy is strictly audited through a multi-tier safety pipeline:
1. **Deterministic Blocklist (0 Model Calls)**: 16 English phrases + separate Chinese, Malay, and Indonesian blocklists. Immediate hard block.
2. **Claim Extraction (LLM)**: Extracts all checkable factual and coverage assertions in standardized English.
3. **Claim Verification (Deterministic)**: Matches extracted claims against approved and restricted knowledge vectors without calling an LLM.
4. **Policy Review (LLM JSON Mode)**: Evaluates nuances, cites exact policy codes, and proposes compliant replacement copy. If malformed, defaults to `review` (never silently passes).

### 🔄 3. Continuous Feedback & Lessons Engine
* When human reviewers approve, edit, or reject copy with reason tags, the system groups feedback into actionable lessons.
* The content generator dynamically injects top historical reviewer lessons into prompt instructions with calculated statistical confidence weights.

### 🌐 4. Live Singapore OpenStreetMap Prospecting (`/leads`)
* Connects directly to the **Overpass API** to query live registered businesses across Singapore:
  * Jewelry merchants along **Orchard Road** & **Chinatown**.
  * Medical centers & specialist clinics in **Novena Medical Hub**.
  * Freight forwarders & logistics hubs in **Jurong Industrial District**.
* Calculates business fit scores and generates personalized, compliance-checked outreach emails.

### 🎨 5. Visual Studio & Carousel Studio (`/visual-studio`)
* **Hero Image Blueprints**: Generates high-fidelity visual prompts tailored for Midjourney/Flux adhering to luxury, medical, or industrial aesthetics.
* **5-Slide Carousel Generator**: Formats structured educational carousel slides with hooks, core breakdown, data evidence, and call-to-action (CTA).

### 🗓️ 6. Event Trigger Engine (`/events`)
* Monitors regional industry milestones:
  * **SIJE** (Singapore International Jewelry Expo)
  * **SMA National Medical Convention**
  * **Singapore Maritime Week**
* Provides 1-click campaign launching with pre-configured regulatory angles and tailored CTAs.

### ⚙️ 7. Autonomous Publishing Worker (`worker/`)
* Runs as a standalone background service using APScheduler.
* Claims approved posts using atomic `SELECT ... FOR UPDATE SKIP LOCKED` database queries.
* Dispatches to social networks (Buffer / LinkedIn) and tracks analytics telemetry.

---

## 4. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | **Next.js 14 (App Router), React 18, TypeScript** | Responsive, dark-mode SaaS user interface |
| **Backend API** | **FastAPI (Python 3.11), Pydantic v2, Uvicorn** | High-performance asynchronous API & agent orchestration |
| **LLM & AI** | **Google Gemini 2.0 / 1.5 Flash (via `google-genai`)** | Content generation, claim extraction, policy validation |
| **Database** | **PostgreSQL 16 with `pgvector` & SQLAlchemy / Alembic** | Vector search, relational schema, job queue |
| **External APIs** | **OpenStreetMap (Overpass API), Firecrawl, Buffer** | Live map prospecting, web research, social distribution |
| **Containerization** | **Docker & Docker Compose** | Multi-service local and server deployment |
| **Cloud Hosting** | **Vercel (Web), Render (API & Worker), Supabase (Postgres)** | 24/7 serverless & managed production infrastructure |

---

## 5. Web Application Routes

| Path | Name | Description |
| :--- | :--- | :--- |
| **`/`** | **Dashboard** | Overview of active campaigns, recent approvals, and performance metrics. |
| **`/demo`** | **Interactive Compliance Demo** | Live testing playground to submit claims and observe the 4-step compliance gate in real time. |
| **`/repurpose`** | **Content Repurposing** | Transforms raw source text or blog articles into multi-channel compliant posts (LinkedIn, Twitter, Email, Carousels). |
| **`/leads`** | **Lead Prospecting** | Live OSM map business discovery and customized outreach generation. |
| **`/visual-studio`**| **Visual Creative Studio** | Generates luxury Midjourney image prompts and 5-slide carousels. |
| **`/events`** | **Event Trigger Engine** | High-impact campaign triggers for upcoming regional expos and conferences. |
| **`/review`** | **Human Review Queue** | Reviewer inbox for approving, editing, or rejecting generated drafts. |
| **`/opportunities`**| **Market Opportunities** | Algorithmic scoring of industry trends and competitor intelligence. |
| **`/optimization`** | **Campaign Optimization** | Evidence-based analysis of engagement metrics and format effectiveness. |
| **`/observability`**| **Observability & Tracing** | Real-time monitoring of model latencies, token consumption, and rate limit quotas. |

---

## 6. Deployment & Operations

### Local Development (Docker Compose)
```bash
docker compose up --build
```
* Web UI: `http://localhost:3000`
* API Docs: `http://localhost:8000/docs`

### Production Cloud Architecture
1. **Frontend**: Hosted on **Vercel** with `NEXT_PUBLIC_API_URL` pointing to backend.
2. **Backend API**: Hosted on **Render** (Docker Web Service, Port 8000).
3. **Database**: Managed PostgreSQL on **Supabase** (with `pgvector` extension enabled).
4. **Worker**: Background worker process executing scheduled jobs and analytics synchronization.
