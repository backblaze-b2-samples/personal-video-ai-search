<!-- last_verified: 2026-06-09 -->
# Security

Security principles and implementation for Personal Video AI Search.

## Trust Boundaries

- **Frontend -> API**: CORS-restricted to configured origins, scoped to `GET/POST/DELETE/OPTIONS`
- **API -> B2**: Authenticated via `B2_APPLICATION_KEY_ID` + `B2_APPLICATION_KEY`, signature v4, explicit `B2_REGION`
- **Browser -> B2 (write)**: Presigned multipart PUT URLs (1-hour expiry). The
  browser uploads video parts directly to B2; the API never sees the bytes. The
  bucket CORS policy must allow `PUT` from the web origin and expose the `ETag`
  header — scope `allowedOrigins` to your real origin, not `*`.
- **Browser -> B2 (read)**: Presigned, Range-capable GET URLs (1-hour expiry)
  for inline clip playback and thumbnails; presigned download URLs in the File
  Browser force `Content-Disposition: attachment`.

## AI provider keys

- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` are kept separate from the `B2_*`
  credentials, loaded only via environment (pydantic-settings), and used only in
  the `repo/` adapter layer. They never reach the browser.
- With no provider key set, the pipeline degrades gracefully (a clear
  "configure a provider" state) rather than erroring — see RELIABILITY.md.

## Large-file handling

- Video never flows through the API. Presigned multipart caps server memory and
  request time regardless of file size (`MAX_VIDEO_SIZE`, default 5 GiB; reject
  oversized at create time, before any B2 call).
- The index pipeline downloads the source to a temp file for ffmpeg/ffprobe and
  cleans up; thumbnails and JSON artifacts are the only things written back.

## Upload Validation (generic /upload)

- Filename sanitization: path traversal, null bytes, unsafe chars stripped
- MIME/extension consistency check against allowlist
- Chunked streaming with size enforcement (100MB default)
- Content-type allowlist (images, text, archives, audio/video)
- Empty file rejection

## File Key Validation

- Empty keys rejected
- Path traversal patterns rejected (`../`, `%2e%2e`, backslashes, null bytes)
- The bucket is the only access boundary — add prefix scoping in
  `services/api/app/service/files.py::validate_key` if your deployment
  shares a bucket with other workloads

## Download Safety

- Presigned URLs force `Content-Disposition: attachment`
- Prevents inline rendering of user-uploaded content (XSS mitigation)

## Secrets Management

- All secrets loaded via environment variables (pydantic-settings)
- Never committed to source control
- `.env.example` documents required variables without values

## Agent Security Rules

- Never commit `.env`, credentials, or API keys
- Never weaken validation without explicit instruction
- Never bypass CORS, auth, or input sanitization
- Always validate at system boundaries
