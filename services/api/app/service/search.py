"""Search service — embed the question, score it against every video's scene
index (loaded from B2) with in-process numpy cosine similarity, and return the
best matching clips (playable inline by seeking the original in B2). Supports an
optional person filter (face cluster) and an optional Claude-synthesized answer.

The index lives in B2 (embeddings.json per video), so B2 stays the sole data
store — there is no vector database."""

import logging
from datetime import UTC, datetime

import numpy as np

from app.repo import embeddings, llm, video_store
from app.service import people as people_svc
from app.service import videos as videos_svc
from app.types import Clip, SceneIndex, SearchRequest, SearchResponse, Video, VideoStatus

logger = logging.getLogger(__name__)


def _cosine(query: np.ndarray, vector: list[float]) -> float:
    vec = np.asarray(vector, dtype="float32")
    denom = float(np.linalg.norm(query) * np.linalg.norm(vec))
    if denom == 0.0:
        return 0.0
    return float(np.dot(query, vec) / denom)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _matches_video_filters(
    video: Video,
    created_at_from: datetime | None,
    created_at_to: datetime | None,
    event_name: str,
) -> bool:
    created_at = _as_utc(video.created_at)
    if created_at_from and created_at < created_at_from:
        return False
    if created_at_to and created_at > created_at_to:
        return False
    # Event filters match the ingested video title because B2 remains the sole
    # datastore and there is no separate event metadata index.
    return not event_name or event_name in video.title.casefold()


def search(req: SearchRequest) -> SearchResponse:
    question = req.question.strip()
    if not question:
        raise ValueError("Question must not be empty")

    # No embedding provider → return a clear "not configured" state, not a 500.
    if not embeddings.is_configured():
        return SearchResponse(
            question=question, clips=[], answer=None, provider_configured=False
        )

    created_at_from = _as_utc(req.created_at_from) if req.created_at_from else None
    created_at_to = _as_utc(req.created_at_to) if req.created_at_to else None
    event_name = (req.event_name or "").casefold()

    videos_by_id = {v.video_id: v for v in videos_svc.list_videos()}
    if req.video_id:
        video = videos_by_id.get(req.video_id)
        target_ids = (
            [req.video_id]
            if video
            and video.status == VideoStatus.ready
            and _matches_video_filters(
                video, created_at_from, created_at_to, event_name
            )
            else []
        )
    else:
        target_ids = [
            vid
            for vid, v in videos_by_id.items()
            if v.status == VideoStatus.ready
            and _matches_video_filters(v, created_at_from, created_at_to, event_name)
        ]

    indexes: list[SceneIndex] = []
    for vid in target_ids:
        data = video_store.get_json(video_store.embeddings_key(vid))
        if data and data.get("scenes"):
            indexes.append(SceneIndex(**data))
    if not indexes:
        return SearchResponse(
            question=question, clips=[], answer=None, provider_configured=True
        )

    # Optional structured filter: restrict to scenes where a person appears.
    allowed: set[tuple[str, str]] | None = None
    if req.person_id:
        allowed = {
            (c.video_id, c.scene_id)
            for c in people_svc.person_clips(req.person_id)
        }

    query = np.asarray(embeddings.embed_query(question), dtype="float32")
    scored = [
        (_cosine(query, scene.vector), index.video_id, scene)
        for index in indexes
        for scene in index.scenes
        if allowed is None or (index.video_id, scene.scene_id) in allowed
    ]
    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[: max(1, req.top_k)]

    playback_cache: dict[str, str | None] = {}
    clips: list[Clip] = []
    for score, vid, scene in top:
        video = videos_by_id.get(vid)
        if vid not in playback_cache:
            playback_cache[vid] = _playback(video.source_key if video else None)
        names = people_svc.names_for_video_scenes(vid).get(scene.scene_id, [])
        clips.append(
            Clip(
                video_id=vid,
                title=video.title if video else vid,
                scene_id=scene.scene_id,
                timestamp=scene.timestamp,
                caption=scene.caption,
                tags=scene.tags,
                score=round(float(score), 4),
                thumb_url=_thumb(scene.thumb_key),
                playback_url=playback_cache[vid],
                people=names,
            )
        )

    answer = _synthesize(question, clips) if req.synthesize else None
    return SearchResponse(
        question=question, clips=clips, answer=answer, provider_configured=True
    )


def _playback(source_key: str | None) -> str | None:
    if not source_key:
        return None
    try:
        return video_store.presigned_get(source_key)
    except RuntimeError:
        return None


def _thumb(thumb_key: str) -> str | None:
    try:
        return video_store.presigned_get(thumb_key)
    except RuntimeError:
        return None


def _synthesize(question: str, clips: list[Clip]) -> str | None:
    if not (clips and llm.is_configured()):
        return None
    try:
        snippets = [c.caption or ", ".join(c.tags) for c in clips]
        return llm.synthesize_answer(question, snippets)
    except Exception:
        logger.warning("Answer synthesis failed", exc_info=True)
        return None
