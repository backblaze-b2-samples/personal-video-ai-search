<!-- last_verified: 2026-06-09 -->
# Architecture

Personal Video AI Search indexes a personal video archive on three signals —
transcript, visual scene tags, and clustered faces — and stores everything in
Backblaze B2. There is no database: the search index and the face-cluster index
are JSON objects in the bucket.

## Components

- **apps/web/** — Next.js 16 frontend (App Router, Tailwind v4, shadcn/ui)
  - Dashboard with archive metrics + B2 activity chart
  - Library — sample-scoped video explorer with pipeline status, multipart
    ingest, re-index / delete
  - Search — natural-language query → ranked, playable clips
  - People — face clusters; name a person, browse their clips
  - File Browser (full-bucket) + generic Upload — kept from the starter
  - Dark mode via `next-themes`
- **services/api/** — FastAPI backend (layered architecture)
  - Presigned multipart upload (browser → B2 direct, multi-GB)
  - Multimodal index pipeline (background task): probe → transcribe → scene
    caption/tag → face cluster → embed → persist to B2
  - Cross-archive semantic search with in-process numpy cosine over the B2 index
  - People / face-cluster surface backed by a B2-stored index
  - Health check, structured JSON logging, Prometheus metrics
- **packages/shared/** — TypeScript type definitions mirroring the Pydantic
  models, consumed by `apps/web/` as a workspace dependency

## Backend Layering

```
types/     Pydantic models — no logic, no imports from other layers
  |
config/    Settings (pydantic-settings) — depends only on types
  |
repo/      Adapters: B2 (boto3), ffmpeg/ffprobe, Whisper, vision, faces,
  |        embeddings, LLM — no business logic
service/   Business logic — orchestrates repo adapters, returns types
  |
runtime/   FastAPI routes — calls service, never repo directly
```

### Layering Rules

1. Dependencies flow downward only: `types` -> `config` -> `repo` -> `service` -> `runtime`
2. No backward imports (e.g., service must not import from runtime)
3. External SDKs/tools (`boto3`, `openai`, `anthropic`, `insightface`,
   `onnxruntime`, and the ffmpeg subprocess calls) live only in `repo/`.
   `numpy`/`scikit-learn` math is allowed in `service/` for cosine scoring.
4. All boundary data uses Pydantic models (no raw dicts across layers)
5. Each file stays under 300 lines

### Directory Structure

```
services/api/
  main.py                  App entrypoint, middleware, router registration
  app/
    types/                 video, transcript, scene, face, search, files, stats
    config/                Settings (B2_*, AI providers, prefix, caps)
    repo/                  b2_client, video_store, media, transcription,
                           vision, faces, embeddings, llm, errors
    service/               ingest (orchestrator), scenes, people, search,
                           videos, files, metadata, upload
    runtime/               videos, search, people, files, upload, health, metrics
  tests/                   pytest (structural + pure-unit + degradation)
```

## B2 object layout

All of this sample's objects live under `VIDEO_PREFIX` (default
`personal-video-ai-search/`) so the bucket can be shared with the full-bucket
File Browser and other samples.

```
personal-video-ai-search/
  videos/{video_id}/
    source.{ext}        original upload (multi-GB, presigned multipart)
    audio.m4a           extracted audio (transcription input)
    transcript.json     Whisper segments with timestamps
    thumbs/{scene}.jpg  sampled keyframe thumbnails
    scenes.json         keyframe captions + tags
    embeddings.json     the multimodal search index (vectors + text)
    faces.json          per-video detected faces (audit)
    meta.json           title, probe fields, pipeline status, counts
  people/index.json     archive-wide face clusters (the People surface)
```

## Data Flows

- **Ingest (bulk write)**: Browser `POST /videos/uploads` → API opens a
  presigned multipart upload → browser PUTs each part **directly to B2** → API
  `POST /videos/uploads/complete` finalizes and schedules the pipeline. The API
  never buffers the video bytes.
- **Index pipeline (background task)**: download source from B2 → `ffprobe`
  metadata → extract audio + Whisper transcript → sample scene-change keyframes
  (`ffmpeg`), write thumbnails to B2, caption/tag each with gpt-4o-mini →
  detect/embed faces locally and merge into the archive cluster index → embed
  every scene (text-embedding-3-small) → write `embeddings.json`. Status is
  persisted to `meta.json` at each stage.
- **Search (repeated small reads)**: `POST /search` → embed query → load each
  ready video's `embeddings.json` from B2 → in-process numpy cosine → ranked
  clips, each with a presigned thumbnail URL and a presigned, Range-capable
  playback URL (the browser seeks the original via a `#t=` media fragment).
  Optional person filter (face cluster) and optional Claude answer.
- **People**: `GET /people` reads `people/index.json`; naming a cluster writes
  it back; `GET /people/{id}/clips` returns that person's appearances.
- **File Browser / generic upload / delete**: unchanged from the starter, over
  the same repo layer.

## Boundary Invariants

- **No external SDK leakage**: boto3, AI provider SDKs, the local face stack,
  and ffmpeg subprocess calls are confined to `app/repo/`.
- **B2 is the sole datastore**: no database, no vector DB. The index and face
  index are JSON objects.
- **No raw dicts at boundaries**: typed Pydantic models cross every layer.
- **Graceful degradation**: with no `OPENAI_API_KEY`, the pipeline marks the
  video `uploaded` with a clear message and search returns
  `provider_configured: false`; the generic B2 surfaces keep working.

## Deployment

- **Local dev** — `pnpm dev` runs both services via `concurrently` (web on
  `:3000`, API on `:8000`). ffmpeg must be on `PATH`.
- **Railway** — two services from the same repo; the API build installs ffmpeg.
  See `infra/railway/README.md`.

## Trust Boundaries

See [docs/SECURITY.md](docs/SECURITY.md).

- **Frontend → API** — CORS-restricted to configured origins
- **API → B2** — authenticated via application key, signature v4, explicit region
- **Browser → B2 (write)** — presigned multipart PUTs; the bucket CORS policy
  must allow PUT and expose the ETag header
- **Browser → B2 (read)** — presigned, Range-capable GETs for playback/thumbnails

## Observability

- Structured JSON logging on all requests with `request_id`
- Request timing middleware
- `/metrics` (Prometheus format) and `/health` (B2 connectivity)

## Canonical Files

- Pipeline orchestrator: `services/api/app/service/ingest.py`
- B2 video data access (multipart + artifacts): `services/api/app/repo/video_store.py`
- ffmpeg/ffprobe adapter: `services/api/app/repo/media.py`
- Vision + faces adapters: `services/api/app/repo/vision.py`, `repo/faces.py`
- Search service: `services/api/app/service/search.py`
- People service: `services/api/app/service/people.py`
- B2 S3 client (UA + region): `services/api/app/repo/b2_client.py`
- Config: `services/api/app/config/settings.py`
- Structural tests: `services/api/tests/test_structure.py`
- Frontend API client / data layer: `apps/web/src/lib/api-client.ts`, `lib/queries.ts`
- Shared TypeScript types: `packages/shared/src/types.ts`

## Core Features

- [Video Ingest](docs/features/video-ingest.md)
- [Visual Scene Indexing](docs/features/visual-indexing.md)
- [People (Face Clustering)](docs/features/people.md)
- [Transcription](docs/features/transcription.md)
- [Cross-archive Search](docs/features/search.md)
- [Video Library](docs/features/video-library.md)
- [File Browser](docs/features/file-browser.md)
- [Dashboard](docs/features/dashboard.md)

## References

- [docs/SECURITY.md](docs/SECURITY.md)
- [docs/RELIABILITY.md](docs/RELIABILITY.md)
- [AGENTS.md](AGENTS.md)
