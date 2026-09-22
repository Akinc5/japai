# Frontend

The browser application is under `apps/web/`. It uses Next.js 14 App Router, React 18, and TypeScript. The API base URL is read from `NEXT_PUBLIC_API_URL` and defaults to the local API in the Docker Compose setup.

## Screens

| Route | Responsibility |
| --- | --- |
| `/` | Dashboard navigation and high-level entry points. |
| `/demo` | Interactive generation and exact-text compliance demo. |
| `/repurpose` | Generate and save repurposed content. |
| `/leads` | List, score, and discover prospects; link outreach drafts to review. |
| `/visual-studio` | Generate visual prompts and carousel structures. |
| `/events` | Browse events and trigger campaigns. |
| `/review` | Human review queue. |
| `/review/[id]` | Review detail and approve/edit/reject actions. |
| `/opportunities` | Inspect opportunity scores and create campaigns. |
| `/optimization` | Inspect aggregates and performance insights. |
| `/observability` | Inspect AI run history and summaries. |

## API client

`apps/web/lib/api.ts` centralizes browser-to-API calls. It handles response parsing and exposes typed or shaped helper functions for brands, review, metrics, opportunities, campaigns, leads, optimization, observability, demo, visual generation, events, and repurposing.

## UI behavior

- Screens show loading and error states around API calls.
- Review actions navigate back to the queue after a successful decision.
- Lead and opportunity records link generated content into review.
- The UI surfaces simulated analytics and demo quota state so users can distinguish recorded/demo behavior from live behavior.

## Development commands

Run these from `apps/web/` when working outside Docker:

```bash
npm install
npm run dev
npm run build
npm run lint
```
