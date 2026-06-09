<!-- last_verified: 2026-06-09 -->
# Feature: Video Probing (generic upload metadata)

## Purpose
Extract media metadata (duration, resolution, fps, codec, bitrate) plus
checksums from files uploaded via the generic `/upload` path, and return it with
the upload result. This replaces the starter kit's PDF/EXIF extraction — a video
archive cares about media probing, not document metadata.

## Used By
- API: `POST /upload` (called after the small-asset B2 upload)
- UI: upload results, file metadata panel

## Core Functions
- `services/api/app/service/metadata.py` — `extract_metadata()`, `_probe()`
- `services/api/app/repo/media.py` — `probe()` / `probe_bytes()` (ffprobe adapter)
- `apps/web/src/components/files/file-metadata-panel.tsx` — displays metadata

## Canonical Files
- Probing service: `services/api/app/service/metadata.py`
- ffprobe adapter: `services/api/app/repo/media.py`

## Inputs
- file_data: bytes
- filename: string
- content_type: string

## Outputs
- `FileMetadataDetail`: filename, size_bytes, size_human, mime_type, extension, md5, sha256, uploaded_at
- Media (optional, video/audio only): duration_seconds, width, height, fps, codec, bitrate

## Flow
- Upload route stores the small asset in B2, then calls `extract_metadata()`
- Computes MD5 and SHA-256 hashes
- If `content_type` starts with `video/` or `audio/`, writes the bytes to a temp
  file and runs `ffprobe` (via the `repo/media.py` adapter) to read container +
  video-stream fields
- Returns a `FileMetadataDetail`; the frontend renders the "Media" section

## Edge Cases
- Non-media file → only common fields populated (hashes, size, extension)
- ffprobe missing or fails → media fields remain null; the upload still succeeds
- Corrupt media → ffprobe returns empty; logged at WARNING, no fields set

## UX States
- Not applicable (metadata is part of the upload response and file preview)

## Verification
- Test files: `services/api/tests/` (upload tests cover the path)
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: pytest green, no ruff violations

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [File Upload](file-upload.md)
- [Video Ingest](video-ingest.md) — the multipart path for large archive videos
