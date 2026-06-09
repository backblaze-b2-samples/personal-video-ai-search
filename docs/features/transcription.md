<!-- last_verified: 2026-06-09 -->
# Feature: Transcription

## Purpose
Produce a timestamped transcript per clip (what's said) — the third search
signal, alongside visual scene tags and faces.

## Used By
- Job: the index pipeline (`services/api/app/service/ingest.py`, stage 2)
- Consumed by: scene building (attaches overlapping speech to each keyframe)

## Core Functions
- `services/api/app/repo/media.py` — `extract_audio()` (ffmpeg → mono 16 kHz)
- `services/api/app/repo/transcription.py` — `transcribe()` (OpenAI Whisper, lazy SDK)

## Canonical Files
- Transcription adapter: `services/api/app/repo/transcription.py`

## Inputs
- The video's audio track (extracted from the B2 source by ffmpeg)

## Outputs
- `transcript.json` in B2 — `Transcript` (language, duration, timestamped segments)

## Flow
- ffmpeg extracts a mono 16 kHz AAC track suitable for transcription
- `whisper-1` transcribes with `verbose_json` + segment timestamps
- The service maps the response into a typed `Transcript` and writes it to B2

## Edge Cases
- No `OPENAI_API_KEY` → the pipeline marks the video `uploaded` with a "configure
  a provider" message (no crash)
- Transcription fails (e.g. silent/odd audio) → the pipeline logs a warning and
  proceeds with an empty transcript so the visual + face signals still index;
  audio is one of three signals, not a hard dependency

## Verification
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: degradation test green (`tests/test_pipeline_degradation.py`)

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Visual Scene Indexing](visual-indexing.md)
- [Cross-archive Search](search.md)
