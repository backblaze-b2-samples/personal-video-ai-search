# Scaffold plan — `personal-video-ai-search`

> Source of truth: `.claude/scratch/vcsk-1a183b9e-e884-48b0-b0d3-799107ec0c63/`
> (fresh clone of `vibe-coding-starter-kit`). Delta computed against that tree.
> Parent standards: `../CLAUDE.md` (S3-only, custom UA, `B2_*` env names).

## ⚠️ Overlap check (read first)

`sampleapps/.local/` already contains **`video-semantic-search`** — a built
sample that is *transcript-only* "chat with your long-form video" (Whisper →
text embeddings → timestamped moments; lectures/podcasts/calls). It is the same
starter-kit lineage and shares Upload/Library/Search surfaces.

`personal-video-ai-search` is positioned as a **deliberately different** sample,
not an iteration of that one. The differentiators are:

| Axis | video-semantic-search (exists) | personal-video-ai-search (this) |
|------|--------------------------------|----------------------------------|
| Content | Long-form professional video (1 file, deep) | **Personal archive** (many short clips, broad) |
| Index signal | Transcript only (audio) | **Visual scene tags + faces + transcript** (multimodal) |
| Headline query | "what minute did they discuss X" (in-video) | "find the clip where the **dog jumps in the pool**" / "all clips from **grandma's 80th**" (**cross-archive, visual + people**) |
| Distinct surface | — | **People** (face clusters you name, Google-Photos-style) |
| Framing | Developer tool | Consumer "AI photos, but for video" |

If you feel this is still too close to ship as a separate sample, this is the
moment to redirect — see **Decisions for sign-off** at the bottom.

---

## 1. Purpose

`personal-video-ai-search` is a self-hostable "AI photo search, for your video
library." You upload an entire personal video archive (phone clips, home
videos) straight to Backblaze B2; a pipeline indexes every clip on three
signals — **a Whisper transcript, AI visual scene tags/captions from sampled
keyframes, and detected/clustered faces** — and stores the whole index in B2.
You then ask in plain language ("find the clip where the dog jumps in the
pool") or browse by **person** ("show me all clips of grandma") and get back
the exact clips, playable inline by seeking the original in B2.

It is built for two audiences: **consumers/prosumers** who want private,
own-your-data video search instead of a cloud-photos silo, and **developers**
who want a worked reference for a *data-heavy, multimodal* AI pipeline where B2
is the sole datastore (originals, audio, thumbnails, transcripts, the
embedding index, and the face-cluster index — no database). It exercises B2's
**bulk write path** (presigned multipart, browser→B2 direct, multi-GB) and its
**repeated small-read path** (presigned range reads to seek clips, thumbnail
fetches) — the access pattern called out in the concept.

## 2. Architecture delta from `vibe-coding-starter-kit`

The starter kit is the ceiling. Keep the scaffolding, strip nothing structural,
add the multimodal pipeline + people/search surfaces.

### KEEP as-is (starter contract — do not strip/rename/replace)
- **UI kit / design system** — `apps/web/src/components/ui/`, design tokens in
  `globals.css`, the `/design` reference page.
- **File Browser (full-bucket explorer)** — `/files`, `apps/web/src/app/files/`,
  `apps/web/src/components/files/`, `lib/file-tree.ts`. **Non-negotiable keep.**
  Sidebar "Files" entry stays.
- **Upload surface** — `/upload` route + `components/upload/` (extended in *add*
  for multipart; the page and nav entry stay).
- **Backend layering** — `types → config → repo → service → runtime`; boto3 only
  in `repo/`; Pydantic at boundaries; <300-line files; structural tests;
  `/health`, `/metrics`, JSON logging; TanStack Query data layer.
- **Sidebar nav shell**, settings page, command palette, dark mode.

### TRIM (remove / shrink from starter)
- **PDF/EXIF metadata extraction** — `service/metadata.py`'s PDF (`PyPDF2`) and
  image-EXIF (`Pillow`) paths and their deps are irrelevant to a video archive.
  Replace with **video probing** (duration/codec/resolution/fps via ffprobe).
  Keep checksum/size/mime fields.
- **100 MB single-`put_object` upload cap** — replaced by presigned multipart
  (see *add*). The simple `put_object` path is retained only for small internal
  artifacts (thumbnails, index JSON) written server-side.
- **Default dashboard stats** (generic upload counts) — replaced with
  archive-relevant metrics (see *add*).

### ADD (new for `personal-video-ai-search`)
- **Presigned multipart upload** (browser→B2 direct, multi-GB) — repo:
  `create_multipart_upload`/`presign part`/`complete`; new runtime + service +
  `/upload` UI wiring. Config `MAX_VIDEO_SIZE` (default 5 GiB), `VIDEO_PREFIX`.
- **Ingest pipeline** (`service/ingest.py`, orchestrates, idempotent, status per
  video persisted to B2):
  - `repo/media.py` — ffmpeg/ffprobe: probe metadata, extract audio,
    **scene-change keyframe sampling** (capped `MAX_KEYFRAMES_PER_VIDEO`,
    default 8), write thumbnails to B2.
  - `repo/transcription.py` — Whisper transcript (timestamped segments) → B2.
  - `repo/vision.py` — per-keyframe **scene caption + tags** via a cheap
    multimodal model → B2.
  - `repo/faces.py` — **local** face detect + embed + cluster (no API cost);
    cluster centroids + per-clip assignments → B2. *(scope = sign-off Q2)*
  - `repo/embeddings.py` — embed `transcript + caption + tags` per scene/clip;
    index (`embeddings.json`) → B2. `repo/llm.py` — optional answer synthesis.
- **Cross-archive Search** (`/search`, `runtime/search.py`, `service/search.py`)
  — NL query → embed → cosine over the B2 index across *all* videos → ranked
  clips with thumbnails, playable inline (presigned + seek). Optional structured
  filters: by **person** (face cluster) and by date/event. Optional Claude
  synthesized answer.
- **People** (`/people`, `runtime/people.py`, `service/people.py`) — the
  distinct surface: face clusters surfaced as cards; name a cluster ("Grandma")
  and browse every clip that person appears in. Backed entirely by the
  B2-stored face index.
- **Library** (`/library`) — **sample-specific asset explorer scoped to
  `VIDEO_PREFIX`** (non-negotiable add): each ingested video with pipeline
  status (probing/transcribing/tagging/clustering/embedding/ready/failed),
  duration, scene count, people count, size; re-index / delete actions.
- **Adapted Dashboard** — videos indexed, hours of footage, scenes tagged,
  people identified, clips embedded, B2 storage used; upload-activity chart;
  recent videos table. Flows through the same layering + queries.ts.
- **Graceful degradation** — with no AI key set, generic B2 features
  (upload/files/dashboard) work; pipeline surfaces a clear "configure a
  provider" state instead of crashing. (Mirrors the precedent sibling.)

## 3. B2 surface (S3-compatible only — no b2-native)

All access via the boto3 S3 client in `repo/`. No b2-native API anywhere.

- `create_multipart_upload` / `UploadPart` (presigned) / `complete_multipart_upload`
  / `abort_multipart_upload` — browser→B2 direct video upload (**bulk write**).
- `put_object` — server-written artifacts: thumbnails, transcript JSON, caption
  JSON, `embeddings.json` index, face-cluster index, per-video status.
- `get_object` / presigned GET with **Range** — clip playback (seek originals),
  thumbnail + index reads (**repeated small reads**).
- `list_objects_v2` — Library (scoped to `VIDEO_PREFIX`) and File Browser
  (full bucket).
- `head_object` — metadata / existence checks.
- `delete_object` / `delete_objects` — delete a video and its derived artifacts.
- **Custom user agent** `user_agent_extra="b2ai-personal-video-ai-search"` on the
  S3 client. **Env names** standardized: `B2_APPLICATION_KEY_ID`,
  `B2_APPLICATION_KEY`, `B2_BUCKET_NAME`, `B2_REGION`, `B2_ENDPOINT`.
- **b2-native usage: none.** ✅

## 4. Key features (seed README + `docs/features/*` stubs)

1. **Video ingest** — presigned multipart, browser→B2 direct, multi-GB; API
   never buffers bytes. → `docs/features/video-ingest.md`
2. **Visual scene indexing** — ffmpeg scene-change keyframes → multimodal
   captions + tags; the signal that powers "dog jumps in the pool."
   → `docs/features/visual-indexing.md`
3. **People (face clustering)** — local face detect/embed/cluster across the
   archive; name a person, browse their clips; powers "all clips of grandma."
   → `docs/features/people.md`  *(depth = sign-off Q2)*
4. **Transcription** — Whisper timestamped transcript per clip, a third search
   signal. → `docs/features/transcription.md`
5. **Cross-archive search** — NL + optional person/date filters → ranked,
   playable clips; optional Claude-synthesized answer.
   → `docs/features/search.md`
6. **Video Library** — sample-scoped explorer with per-video pipeline status +
   re-index/delete. → `docs/features/video-library.md`
   (**File Browser** doc kept from starter for full-bucket browse.)

### External API provider
- **Primary (one required key): OpenAI** — `OPENAI_API_KEY` covers all three
  paid steps: **Whisper** (`whisper-1`) transcription, **`gpt-4o-mini`** vision
  for keyframe captions/tags, **`text-embedding-3-small`** embeddings. One key,
  newest cost-efficient tier (not flagship).
  - *Deviation from the api-provider-selection.md "Anthropic-first" default,
    justified:* Anthropic has no audio-transcription endpoint, and the goal is
    one key covering transcription+vision+embeddings. OpenAI is the only single
    provider that does. Consistent with the sibling sample.
- **Optional: Anthropic** — `ANTHROPIC_API_KEY`, `claude-haiku-4-5` for the
  optional synthesized answer over top clips (Anthropic's strength; cheapest
  tier).
- **Faces: local, $0 API** — no provider key; see Q2.
- **Estimated cost, one full demo run (~4 clips, ~12 min total, ≤8 keyframes
  each):** Whisper ≈ $0.07; vision tagging (~32 small images, gpt-4o-mini)
  ≈ $0.03; embeddings ≈ <$0.01; optional Haiku synthesis (a few queries)
  ≈ <$0.02. **Total ≈ $0.13, well under the $1 ceiling.** Caps in config keep
  it bounded: `MAX_KEYFRAMES_PER_VIDEO`, `MAX_VIDEO_SIZE`, scene threshold.

## 5. Doc transforms

**Rewrite** (starter → this app):
- `README.md` — new hero ("AI photo search, for your video library"), what-it-
  looks-like (Dashboard/Library/Search/People), how-it-works pipeline diagram,
  feature list, tech stack (+ Whisper/vision/faces/ffmpeg), quick start (+ AI
  key + ffmpeg prereq), UTM retag.
- `ARCHITECTURE.md` — add pipeline data flows, the new repo adapters, B2 as
  sole multimodal store, region/UA notes.
- `AGENTS.md` — repo map + "building on this kit" contract updated for the new
  routes/adapters; keep invariants verbatim.
- `docs/features/dashboard.md` — archive metrics.
- `docs/features/metadata-extraction.md` → **video probing** (ffprobe), drop
  PDF/EXIF.
- `docs/app-workflows.md`, `docs/dev-workflows.md` — new journeys (ingest →
  index → search/people) + ffmpeg/AI-key dev setup; retag slug refs.
- `docs/SECURITY.md`, `docs/RELIABILITY.md` — presigned multipart, large-file
  handling, partial-pipeline degradation, key handling.

**Keep ~as-is:** `docs/features/file-browser.md`, `docs/features/file-upload.md`
(annotate for multipart), `docs/design-system.md`, `docs/features/_template.md`.

**New stubs (from `_template.md`):** `video-ingest.md`, `visual-indexing.md`,
`people.md`, `transcription.md`, `search.md`, `video-library.md`.

**Delete:** none structural.

## 6. Rename table (`vibe-coding-starter-kit` → `personal-video-ai-search`)

| Kind | From | To |
|------|------|----|
| kebab slug / root pkg | `vibe-coding-starter-kit` | `personal-video-ai-search` |
| web pkg | `@vibe-coding-starter-kit/web` | `@personal-video-ai-search/web` |
| shared pkg | `@vibe-coding-starter-kit/shared` | `@personal-video-ai-search/shared` |
| pnpm `--filter` refs (package.json, README, AGENTS) | `@vibe-coding-starter-kit/web` | `@personal-video-ai-search/web` |
| Title Case display | "Vibe Coding Starter Kit" | "Personal Video AI Search" |
| FastAPI app title (`main.py`) | "OSS Starter Kit API" | "Personal Video AI Search API" |
| user agent (`repo/b2_client.py:45`) | `b2ai-oss-start` | `b2ai-personal-video-ai-search` |
| UTM content tag (all README/doc links) | `utm_content=b2ai-oss-start` | `utm_content=b2ai-personal-video-ai-search` |
| env key id | `B2_KEY_ID` (+ `b2_key_id`) | `B2_APPLICATION_KEY_ID` (+ `b2_application_key_id`) |
| env region | *(absent)* | **add** `B2_REGION` (+ `b2_region` field, `region_name=` on client) |
| sidebar/layout/title strings, `next.config.ts`, `layout.tsx`, command palette, doctor.mjs, infra/railway/README | kit name / `B2_KEY_ID` | sample name / `B2_APPLICATION_KEY_ID` |

> `user_agent_extra`/UTM derived as `b2ai-<slug>` (matches sibling + starter
> convention). If the board sub-issue specifies a different `user_agent_extra`,
> that value wins — not available in this invocation; flag if it differs.

## 7. Open questions from the concept — proposed resolutions (defaults)

- **Transcode / HLS vs originals?** → **Originals only.** Playback by presigned
  URL + Range/seek to the clip timestamp (sibling precedent). No transcoding —
  cheaper, simpler, and it shows off B2's range-read path. (Override if you want
  HLS, but that's production scope, not sample scope.)
- **Mobile uploader?** → **Out of scope for v1.** Web drag-and-drop multipart
  uploader only; note mobile as a future direction in the tech-debt tracker.

## Decisions for sign-off

1. **Positioning vs the existing `video-semantic-search` sample** — build as the
   distinct "visual + people / AI-photos-for-video" sample, build a lighter
   "visual tags only" variant, or hold and rethink?
2. **Face clustering depth** — local model (real People feature, no API cost,
   adds an ML dependency + first-run model download), a hosted face API (extra
   provider key), or defer faces to a documented future feature?
3. Defaults above (OpenAI primary + optional Anthropic; originals-only playback;
   web-only uploader) — accept or adjust?
