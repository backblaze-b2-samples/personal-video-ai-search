<!-- last_verified: 2026-06-09 -->
# AGENTS.md

This is the authoritative control surface for all coding agents. Read this first.

## 1. Repository Map

```
apps/web/          Next.js 16 frontend (App Router, Tailwind v4, shadcn/ui)
services/api/      FastAPI backend (layered: types/config/repo/service/runtime)
packages/shared/   Shared TypeScript types
docs/              System of record (features, workflows, security, reliability)
docs/exec-plans/   Execution plans and tech debt tracker
infra/railway/     Deployment config
```

## 2. App Surfaces

This app started from the Backblaze B2 full-stack starter foundation (Next.js +
FastAPI). The pieces below are load-bearing — keep them.

**Reusable B2 scaffolding (keep as-is)**
- **UI kit / design system.** `apps/web/src/components/ui/` (shadcn primitives),
  the design tokens in `apps/web/src/app/globals.css`, and the `/design`
  reference page. Build screens with these primitives; never edit the generated
  `components/ui/` files directly — restyle through tokens in `globals.css`.
- **File Browser (full-bucket explorer).** `/files`, `apps/web/src/app/files/`,
  `apps/web/src/components/files/`, and its sidebar entry. This is the *whole
  bucket*, not just this sample's prefix — keep it.
- **Upload (generic).** `/upload`, `apps/web/src/app/upload/`,
  `apps/web/src/components/upload/`, and its sidebar entry — small assets
  proxied through the API. Large video uses the multipart **Ingest** flow on the
  Library page instead, not this.

**This app's core**
- **Library** (`/library`, `apps/web/src/components/library/`) — sample-scoped
  explorer of ingested videos (scoped to `VIDEO_PREFIX`) with per-video pipeline
  status, plus the multipart Ingest dialog ("Add video") and re-index / delete.
- **Search** (`/search`, `apps/web/src/components/search/`) — natural-language
  query → ranked, playable clips. Optional person filter + Claude answer.
- **People** (`/people`, `apps/web/src/components/people/`) — face clusters
  surfaced as cards; name a cluster and browse that person's clips. Backed
  entirely by a B2-stored face index.
- **Pipeline** — repo: `video_store.py` (B2 multipart + artifacts + thumbnails),
  `media.py` (ffmpeg/ffprobe), `transcription.py` (Whisper), `vision.py`
  (gpt-4o-mini captions/tags), `faces.py` (local detect/embed + pure
  clustering), `embeddings.py`, `llm.py`; service: `ingest.py` (orchestrator),
  `scenes.py`, `people.py`, `search.py`, `videos.py`, `metadata.py`; runtime:
  `videos.py`, `search.py`, `people.py`.
- **Dashboard** (`/`, `apps/web/src/components/dashboard/`) — archive metrics
  (videos indexed, hours of footage, people identified, storage used) via the
  `useVideos` / `usePeople` hooks, plus a B2 activity chart. New aggregations
  flow through TanStack Query hooks in `apps/web/src/lib/queries.ts` — no bare
  `useEffect + fetch`.

**Why this contract exists**
- The UI kit, Files (full-bucket explorer), and Upload pages are the reusable
  B2-backed scaffolding. The video Library, Search, People, and the pipeline are
  this app's reason to exist. Keep both.

## 3. Architectural Invariants

**Backend layering**: `types` -> `config` -> `repo` -> `service` -> `runtime`

- No backward imports across layers
- No external SDKs (`boto3`, `openai`, `anthropic`, `insightface`, `onnxruntime`)
  outside `repo/`. `numpy`/`scikit-learn` math used by the service layer for
  cosine scoring is allowed — it is not an external service client.
- No business logic in route handlers (`runtime/`)
- All external APIs and tools (incl. ffmpeg) wrapped in `repo/` adapters
- All request/response data validated at boundary (Pydantic models)
- No shared mutable state across layers
- **B2 is the sole datastore** — originals, audio, thumbnails, transcripts, the
  embedding index, and the face-cluster index are all objects in the bucket. No
  database, no vector DB.

**Frontend**: shadcn/ui components in `src/components/ui/` are generated — never modify them.

**Data fetching**: every API call flows through TanStack Query hooks in
`apps/web/src/lib/queries.ts`. No bare `useEffect + fetch`. New endpoints touch
three files: `runtime/<router>.py`, `lib/api-client.ts`, `lib/queries.ts`.

## 4. Quality Expectations

- **DRY** — do not duplicate logic, types, or constants. Extract shared code only when used in 2+ places.
- Structured JSON logging only — no `print()` statements
- No raw SDK calls outside `repo/` layer
- Files stay under 300 lines
- Tests added or updated for every behavior change
- Docs updated in same PR as code changes
- Lint clean before merge
- Prefer boring, composable libraries over clever abstractions
- No implicit type assumptions — use typed models
- Graceful degradation: with no AI key, the pipeline returns a clear
  "not configured" state; it must never 500 or crash the background worker.

## 5. Mechanical Enforcement

| Rule | Enforced by |
|------|-------------|
| No backward imports | `tests/test_structure.py::test_no_backward_imports` |
| No external SDKs outside repo/ | `tests/test_structure.py::test_external_sdks_only_in_repo` |
| File size < 300 lines | `tests/test_structure.py::test_file_size_limits` |
| All layers exist | `tests/test_structure.py::test_all_layers_exist` |
| No bare print() | `ruff` rule T20 |
| Import ordering | `ruff` rule I001 |
| Frontend strict equality | `eslint` rule eqeqeq |
| No unused vars | `eslint` + `ruff` rules |

## 6. Commands

```bash
# Run
pnpm dev               # start both frontend and backend
pnpm dev:web           # frontend only
pnpm dev:api           # backend only

# Test & Lint
pnpm lint              # frontend lint (eslint)
pnpm build             # frontend type check + build
pnpm lint:api          # backend lint (ruff)
pnpm test:api          # backend tests (pytest)
pnpm check:structure   # structural boundary tests
pnpm test:e2e          # Playwright e2e tests
```

## 7. Agent Workflow

1. Read this file first.
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) before structural changes.
3. For non-trivial changes, create a plan in `docs/exec-plans/active/`.
4. Implement the smallest coherent change.
5. Run: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
6. Update docs in the same PR (see §9).
7. Move completed plans to `docs/exec-plans/completed/`.
8. Only change files relevant to the task. No drive-by improvements.

## 8. Frontend Conventions

See [docs/dev-workflows.md](docs/dev-workflows.md) for full details.

## 9. Doc Update Mapping

| Change Type | Update Location |
|-------------|-----------------|
| Feature logic, inputs, outputs, tests | `docs/features/<feature>.md` |
| User journeys | `docs/app-workflows.md` |
| System layout, deployments | `ARCHITECTURE.md` |
| Dev or testing process | `docs/dev-workflows.md` |
| Setup or scope changes | `README.md` |
| Security changes | `docs/SECURITY.md` |
| Reliability changes | `docs/RELIABILITY.md` |
| Active work plans | `docs/exec-plans/active/` |
| Known tech debt | `docs/exec-plans/tech-debt-tracker.md` |

If documentation and implementation conflict, update docs in the same PR. Documentation rot destroys agent reliability.

## 10. Doc Map

| Topic | Location |
|-------|----------|
| System layout, data flows, boundaries | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Feature docs | [docs/features/](docs/features/) |
| User journeys | [docs/app-workflows.md](docs/app-workflows.md) |
| Engineering workflows and testing | [docs/dev-workflows.md](docs/dev-workflows.md) |
| Security principles | [docs/SECURITY.md](docs/SECURITY.md) |
| Reliability expectations | [docs/RELIABILITY.md](docs/RELIABILITY.md) |
| Execution plans | [docs/exec-plans/](docs/exec-plans/) |
| Tech debt | [docs/exec-plans/tech-debt-tracker.md](docs/exec-plans/tech-debt-tracker.md) |

## 11. When Unsure

- Prefer boring, stable libraries
- Prefer small PRs over large changes
- Add tests with every change
- Never bypass lint rules without explicit instruction
- Ask before making destructive or irreversible changes
