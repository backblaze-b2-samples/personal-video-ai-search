<!-- last_verified: 2026-06-25 -->
# Feature: Cross-archive Search

## Purpose
Answer a natural-language query across the whole archive — by what's said,
what's on screen, or who's in it — and return the exact clips, playable inline.
The B2 **repeated small-read path**.

## Used By
- UI: `/search` page (`apps/web/src/components/search/clip-card.tsx`)
- API: `POST /search`

## Core Functions
- `services/api/app/service/search.py` — `search()` (embed query, numpy cosine over the B2 indexes)
- `services/api/app/repo/embeddings.py` — `embed_query()`
- `services/api/app/repo/llm.py` — `synthesize_answer()` (optional Claude)
- `services/api/app/service/people.py` — person filter + per-scene names

## Canonical Files
- Search service: `services/api/app/service/search.py`

## Inputs
- `SearchRequest`: question, optional video_id, optional person_id, optional
  `created_at_from` / `created_at_to` date range, optional event_name, top_k,
  synthesize

## Outputs
- `SearchResponse`: clips (video, scene, timestamp, caption, tags, score,
  thumb_url, playback_url, people), optional answer, provider_configured

## Flow
- If no embedding provider → return `provider_configured: false` (clear UI state, not a 500)
- Load every ready video's `embeddings.json` from B2
- If `person_id` is set, restrict candidate scenes to that face cluster's appearances
- If `created_at_from` / `created_at_to` is set, restrict candidates to videos
  created in that inclusive date range
- If `event_name` is set, restrict candidates to videos whose ingested title
  contains that event/file name
- Embed the query, score it against each scene vector with in-process numpy cosine
- Return the top-k clips, each with a presigned thumbnail and a presigned,
  Range-capable playback URL — the browser seeks the original with a `#t=` media
  fragment; no clip files are generated
- If `synthesize` and `ANTHROPIC_API_KEY` is set, generate a short cited answer
  over the top clips with `claude-haiku-4-5`

## Edge Cases
- No videos ready / no index → empty result with `provider_configured: true`
- Empty question → 400
- Synthesis failure → logged, returns clips with `answer: null`

## UX States
- Loading: skeleton clip grid
- Not configured: "No AI provider configured"
- Empty: "No matching clips"
- Loaded: optional answer card + clip grid (thumbnail → click to play)

## Verification
- Test files: `services/api/tests/test_pipeline_degradation.py`,
  `services/api/tests/test_search_filters.py`
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: degradation tests green; manual: query a "Ready" video, clips play at the right moment

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Visual Scene Indexing](visual-indexing.md)
- [People (Face Clustering)](people.md)
