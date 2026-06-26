<!-- last_verified: 2026-06-25 -->
# Reliability

Reliability expectations and practices for this project.

## Health Checks

- `GET /health` verifies B2 connectivity and returns `healthy` or `degraded`
- Health endpoint is always available, even when B2 is down

## Error Handling

- HTTP handlers return structured error responses with appropriate status codes
- External service failures (B2) are caught and surfaced as 500/503 responses
- No unhandled exceptions leak stack traces to clients

## Logging

- Structured JSON logging via Python stdlib
- Every request gets a `request_id` for tracing
- Log levels: ERROR for failures, WARNING for degraded state, INFO for requests

## Observability

- Request timing middleware logs duration for every request
- `/metrics` endpoint exposes basic Prometheus-format counters
- Upload success/failure counts tracked

## Graceful Degradation

- File listing returns empty list (not error) when B2 has no objects
- Metadata/probe failures don't block upload (return partial metadata)
- Frontend shows skeleton states while loading, error states on failure
- **No AI provider configured**: the index pipeline marks the video `uploaded`
  with a clear message and search returns `provider_configured: false`. The
  generic B2 surfaces (upload, files, dashboard) keep working.
- **Transcription failure**: indexing proceeds with the visual + face signals
  (audio is one of three signals, not a hard dependency).
- **Local face stack not installed**: `/people` reports `available: false`
  instead of erroring; the rest of the pipeline (transcript + scene tags +
  search) still runs.

## Index Pipeline

- Runs as a FastAPI **BackgroundTask** — no external job queue. State is
  persisted to `meta.json` in B2 at every stage so the Library reflects progress
  across restarts and the background worker never crashes the request.
- The pipeline is **idempotent**: re-index re-runs cleanly and face appearances
  for a video are replaced, not duplicated.
- This is sample-grade. For production scale, move ingest to a durable queue
  (Celery/RQ/Cloud Tasks) — noted in the tech-debt tracker.

## Deployment

- Railway health checks on `/health`
- Zero-downtime deploys via rolling updates
- Environment-specific configuration via env vars (no config files in prod)
- Search-filter UI rollout is backend-first and gated by
  `NEXT_PUBLIC_SEARCH_FILTERS_ENABLED`, which defaults to `false`. Deploy the
  backend first, drain old API instances until `/health` reports
  `features.search_filters: true` everywhere, then rebuild/redeploy the frontend
  with the flag set to `true`. Until then, the frontend hides the controls and
  omits `created_at_*` / `event_name` request fields. The runtime health check is
  only a defense-in-depth guard; the deploy-time flag is what prevents filtered
  requests from reaching old API instances during a rolling deploy.
- The backend rejects unknown `SearchRequest` fields so new clients fail closed
  instead of silently dropping filters.
