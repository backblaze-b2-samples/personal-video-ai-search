<!-- last_verified: 2026-06-09 -->
# Feature: People (Face Clustering)

## Purpose
Cluster the same person's face across the whole archive so you can name them
("Grandma") and browse every clip they appear in — Google-Photos-style, but for
video. Faces are detected, embedded, and clustered **entirely on-device** at $0
API cost; the cluster index lives in B2.

## Used By
- UI: `/people` page (`apps/web/src/components/people/`)
- Job: the index pipeline (`services/api/app/service/ingest.py`, stage 4)
- API: `GET /people`, `GET /people/available`, `GET /people/{id}/clips`, `POST /people/{id}/name`

## Core Functions
- `services/api/app/repo/faces.py` — `embed_faces()` (insightface detect + ArcFace embed), pure cosine clustering helpers
- `services/api/app/service/people.py` — `index_video_faces()`, `list_people()`, `name_person()`, `person_clips()`, `names_for_video_scenes()`

## Canonical Files
- Local face adapter: `services/api/app/repo/faces.py`
- People service: `services/api/app/service/people.py`

## Inputs
- The video's keyframe thumbnails (the same ones the vision stage produced)

## Outputs
- `people/index.json` in B2 — `FaceClusterIndex` (clusters with centroid + appearances)
- `Person[]` (cluster_id, name, face_count, video_count, cover_thumb_url) for the grid
- `Clip[]` for a person, playable inline

## Flow
- For each keyframe thumbnail, `insightface` detects faces and returns
  L2-normalized 512-d embeddings (ONNX, CPU)
- Each face is assigned to the nearest existing cluster if cosine distance ≤
  `FACE_CLUSTER_THRESHOLD`, otherwise it starts a new cluster; the centroid is a
  running normalized mean
- Re-indexing a video first drops its prior appearances (idempotent), then
  re-adds; empty clusters are pruned
- Naming a cluster writes `name` back to `people/index.json`

## Local model note
The first ingest with face indexing downloads the `buffalo_l` model pack once
(network required on first run). After that, detection is fully offline at $0.
If `insightface`/`onnxruntime` aren't installed, `GET /people/available` returns
`false` and the page shows a clear "face indexing not available" state.

## Edge Cases
- No faces in a frame → normal, contributes nothing
- Model not installed → degrade with the "available: false" state (no crash)
- Re-index → appearances replaced for that video, not duplicated

## UX States
- Loading: skeleton grid
- Unavailable: "Face indexing not available" empty state
- Empty: "No people yet"
- Loaded: cards; click to open a person's clips; pencil to name

## Verification
- Test files: `services/api/tests/test_faces_clustering.py` (pure helpers)
- Quick verify command: `pnpm test:api`
- Full verify command: `pnpm lint && pnpm lint:api && pnpm test:api && pnpm check:structure`
- Pass criteria: clustering-helper tests green; manual: a named person's clips load

## Related Docs
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Visual Scene Indexing](visual-indexing.md)
- [Cross-archive Search](search.md) — person filter
