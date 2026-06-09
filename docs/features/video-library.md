<!-- last_verified: 2026-06-09 -->
# Feature: Video Library

## Purpose
A sample-scoped asset explorer — every video ingested into this sample's B2
namespace (`VIDEO_PREFIX`), with its per-video pipeline status and watch /
re-index / delete actions. Distinct from the full-bucket File Browser, which is
kept as-is.

## Used By
- UI: `/library` page (`apps/web/src/components/library/`)
- API: `GET /videos`, `GET /videos/{id}/playback`, `POST /videos/{id}/reindex`,
  `DELETE /videos/{id}`

## Core Functions
- `apps/web/src/components/library/video-list.tsx` — table with status, length, scenes, people, size
- `apps/web/src/components/library/video-player-dialog.tsx` — inline player; streams the original from B2 over a presigned, Range-capable URL
- `apps/web/src/components/library/ingest-dialog.tsx` — multipart "Add video"
- `apps/web/src/components/library/status-badge.tsx` — pipeline status badge
- `services/api/app/service/videos.py` — `list_videos()`, `playback_url()`, `delete_video()`, `update_status()`

## Canonical Files
- Library list: `apps/web/src/components/library/video-list.tsx`
- Video service: `services/api/app/service/videos.py`

## Inputs
- None to view (loads automatically); actions take a `video_id`

## Outputs
- `GET /videos` → `Video[]` (status, duration, scene_count, people_count, size)
- `GET /videos/{id}/playback` → `{ url }` presigned GET for the original source
- `POST /videos/{id}/reindex` → re-runs the pipeline (idempotent)
- `DELETE /videos/{id}` → batch-deletes the whole `videos/{id}/` tree from B2

## Flow
- The list is built by scoped listing under `VIDEO_PREFIX` (`list_video_ids`) and
  loading each `meta.json`
- `useVideos` polls every 4s while any video is mid-pipeline so status is live:
  uploading → probing → transcribing → tagging → clustering → embedding → ready
- Watch opens an inline player dialog; `useVideoPlayback` fetches a short-lived
  presigned GET URL (only while open) and the browser streams the original over
  Range requests — seeking pulls just the bytes it needs, never the whole file
- Re-index schedules `ingest.run_pipeline` again; delete removes every derived
  artifact (audio, transcript, thumbnails, scene tags, embeddings) plus the source

## Edge Cases
- Failed pipeline → row shows a `Failed` badge + the error; re-index to retry
- No `OPENAI_API_KEY` → videos sit at `uploaded` with a "configure a provider" note
- Watch is disabled while a video is still `uploading` (the source object in B2
  is only finalized once the multipart upload completes); available at every
  later status, including `failed`
- Delete is irreversible (confirmation dialog)

## UX States
- Loading: skeleton rows
- Empty: "No videos yet"
- Error: inline `ErrorState` with retry

## Verification
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: structural tests green; manual: ingest → watch status → delete

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Video Ingest](video-ingest.md)
- [File Browser](file-browser.md) — the full-bucket explorer (kept from the starter)
