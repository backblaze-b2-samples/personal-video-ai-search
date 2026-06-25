<!-- last_verified: 2026-06-25 -->
# Tech Debt Tracker

Known tech debt items. Agents update this when they discover or create tech debt.

| Description | Impact | Proposed Resolution | Priority | Status |
|---|---|---|---|---|
| Index pipeline runs as an in-process FastAPI BackgroundTask | No retry/backpressure at scale; lost on hard crash mid-stage (state is persisted, but the in-flight stage isn't resumed) | Move ingest to a durable queue (Celery/RQ/Cloud Tasks) for production | Medium | Open (sample-grade by design) |
| No mobile uploader | Web drag-and-drop multipart only; can't capture-and-upload from a phone | Add a mobile/PWA capture flow reusing the presigned multipart API | Low | Future (out of scope for v1, per plan) |
| Face cluster merge is greedy single-pass | Good enough for an archive demo; can over-split a person across very different lighting/angles | Add an offline re-cluster pass (e.g. sklearn AgglomerativeClustering over all embeddings) | Low | Open |
| Date/event filter in Search is stubbed | Search supports person filter but not date/event yet | Add `created_at` range + event-name filter to `SearchRequest` and the UI | Low | Resolved |
| `datetime.utcnow()` deprecated in Python 3.12+ | Naive datetimes, future breakage | Replace with `datetime.now(UTC)` in `repo/b2_client.py`, `service/metadata.py` | High | Resolved |
| S3 client recreated on every API call | Connection pool wasted, added latency | Cache client as module-level singleton via `lru_cache` | High | Resolved |
| `get_upload_stats()` pagination broken at 1000 objects | Stats silently wrong for large buckets | Check `IsTruncated` + use `ContinuationToken` | High | Resolved |
| `record_upload()` never called | `/metrics` always reports 0 uploads | Call from `runtime/upload.py` after successful upload | Medium | Resolved |
| Metrics counters not thread-safe | Race conditions under concurrent requests | Use `threading.Lock` (matches `service/files.py` pattern) | Medium | Resolved |
| `_humanize_bytes` duplicated in Python (repo + service) | DRY violation, drift risk | Extract to `app/types/formatting.py` shared util | Medium | Resolved |
| `humanizeBytes` duplicated in TypeScript | DRY violation | Extract to `lib/utils.ts` | Low | Open |
| `formatDate` duplicated in TypeScript | DRY violation | Extract to `lib/utils.ts` | Low | Open |
| No test harness for feature specs | No automated verification | Add pytest fixtures + test files per feature | Medium | Resolved (partial — tests added for upload, files, activity, errors) |
