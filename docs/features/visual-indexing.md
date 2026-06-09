<!-- last_verified: 2026-06-09 -->
# Feature: Visual Scene Indexing

## Purpose
Describe what's *on screen* in each video so visual queries work — e.g. "the dog
jumps in the pool" — independent of the audio. Scene-change keyframes are
sampled, thumbnailed to B2, and captioned/tagged by a cheap multimodal model.

## Used By
- Job: the index pipeline (`services/api/app/service/ingest.py`, stage 3)
- API/UI: surfaces through Search results (caption, tags, thumbnail)

## Core Functions
- `services/api/app/repo/media.py` — `sample_keyframes()` (ffmpeg scene filter, capped)
- `services/api/app/repo/vision.py` — `describe_keyframe()` (gpt-4o-mini → JSON caption + tags)
- `services/api/app/service/scenes.py` — `build_scenes()`, `scene_document()`

## Canonical Files
- Keyframe sampling: `services/api/app/repo/media.py`
- Vision adapter: `services/api/app/repo/vision.py`

## Inputs
- Local copy of the source video (downloaded from B2 by the pipeline)
- The video's transcript (to attach overlapping speech to each scene)

## Outputs
- Thumbnails written to `videos/{video_id}/thumbs/{scene}.jpg` in B2
- `scenes.json` in B2 — `Keyframe[]` (scene_id, timestamp, thumb_key, caption, tags, transcript_text)
- Per scene, a combined document = caption + tags + nearby speech, fed to embeddings

## Flow
- `ffmpeg` selects frames where `scene > SCENE_THRESHOLD`, scaled to 640px wide,
  capped at `MAX_KEYFRAMES_PER_VIDEO`; falls back to evenly spaced frames for
  short clips with few cuts
- Each keyframe JPEG is uploaded to B2, then sent (base64) to `gpt-4o-mini` with
  a strict-JSON prompt asking for a one-sentence caption + 3–8 visual tags
- The overlapping transcript window (±8s) is attached so a scene carries both
  the visual and spoken context

## Edge Cases
- Scene detection yields <2 frames → interval-sampling fallback
- Vision model returns non-JSON → caption/tags default to empty (logged), scene still indexed
- No `OPENAI_API_KEY` → pipeline degrades (see Transcription / Search docs)

## Verification
- Test files: `services/api/tests/test_scenes.py` (document assembly)
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: pytest green; manual: a "Ready" video returns visually-relevant clips

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Cross-archive Search](search.md)
- [People (Face Clustering)](people.md)
