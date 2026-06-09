<!-- last_verified: 2026-06-09 -->
# Feature: Video Ingest (presigned multipart)

## Purpose
Upload a (potentially multi-GB) video straight from the browser to Backblaze B2
using presigned multipart, so the API never buffers the bytes — the B2 **bulk
write path**.

## Used By
- UI: Library → "Add video" dialog (`apps/web/src/components/library/ingest-dialog.tsx`)
- API: `POST /videos/uploads`, `POST /videos/uploads/complete`

## Core Functions
- `apps/web/src/lib/api-client.ts` — `ingestVideo()` (orchestrates create → PUT parts → complete)
- `services/api/app/service/videos.py` — `create_upload()`, `complete_upload()`
- `services/api/app/repo/video_store.py` — `create_multipart`, `presign_part`, `complete_multipart`, `abort_multipart`

## Canonical Files
- Browser orchestration: `apps/web/src/lib/api-client.ts` (`ingestVideo`)
- B2 multipart adapter: `services/api/app/repo/video_store.py`

## Inputs
- `CreateUploadRequest`: filename, size_bytes, content_type

## Outputs
- `MultipartUpload`: video_id, source_key, upload_id, part_size, presigned part URLs
- `complete` → `Video` (status `uploaded`) and schedules the index pipeline
- Side effect: original written to `videos/{video_id}/source.{ext}` in B2

## Flow
- `POST /videos/uploads` → API creates a multipart upload on B2 and presigns one
  URL per part; records a `uploading` `meta.json` so the video shows immediately
- Browser PUTs each `file.slice()` directly to its presigned URL, reading the
  `ETag` from each response
- `POST /videos/uploads/complete` with the ordered part ETags → API finalizes
  the multipart upload and schedules `ingest.run_pipeline` as a background task

## Edge Cases
- Size > `MAX_VIDEO_SIZE` → 400 before any B2 call
- Missing ETag in a part response → the bucket CORS policy must expose `ETag`
  (see below); the client raises a clear error
- A failed/abandoned upload can be aborted via `abort_multipart`

## Bucket CORS
The browser PUTs parts cross-origin and must read the `ETag` header, so the
bucket needs a CORS rule allowing `PUT` from your web origin with
`Access-Control-Expose-Headers: ETag`. Example rule:

```json
[{
  "corsRuleName": "browser-multipart",
  "allowedOrigins": ["http://localhost:3000"],
  "allowedOperations": ["s3_put"],
  "allowedHeaders": ["*"],
  "exposeHeaders": ["etag"],
  "maxAgeSeconds": 3600
}]
```

## UX States
- Idle: dropzone
- Uploading: progress bar (% of bytes PUT to B2)
- Error: toast with the failure reason

## Verification
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: structural tests green; manual: add a video and watch it reach "Ready"

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Video Library](video-library.md)
- [docs/SECURITY.md](../SECURITY.md)
