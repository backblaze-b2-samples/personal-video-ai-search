"""People service — the archive-wide face index.

Detects faces in a video's keyframes, then merges them into a single
``FaceClusterIndex`` persisted to B2 (``people/index.json``). Faces close to an
existing cluster centroid join it; otherwise a new cluster (person) is created.
Naming a cluster ("Grandma") just writes its ``name`` back. The whole People
surface is backed entirely by this B2-stored index — no database."""

import logging

from app.repo import faces, video_store
from app.types import (
    Clip,
    FaceAppearance,
    FaceCluster,
    FaceClusterIndex,
    Keyframe,
    Person,
)

logger = logging.getLogger(__name__)


class PersonNotFoundError(Exception):
    def __init__(self, detail: str = "Person not found"):
        self.detail = detail
        super().__init__(detail)


def faces_available() -> bool:
    return faces.is_available()


def _load_index() -> FaceClusterIndex:
    data = video_store.get_json(video_store.people_index_key())
    if data:
        return FaceClusterIndex(**data)
    return FaceClusterIndex(model=faces.model_name(), dim=0, clusters=[])


def _save_index(index: FaceClusterIndex) -> None:
    video_store.put_json(
        video_store.people_index_key(), index.model_dump(mode="json")
    )


def index_video_faces(video_id: str, scenes: list[Keyframe]) -> int:
    """Detect + cluster faces across one video's scenes into the archive index.

    Returns the number of distinct people (clusters) this video contributes to.
    Idempotent per video: existing appearances for the video are dropped first
    so a re-index doesn't double-count.
    """
    if not faces.is_available():
        return 0

    index = _load_index()
    _drop_video(index, video_id)
    touched: set[str] = set()

    for scene in scenes:
        jpeg = _read_thumb(scene.thumb_key)
        if jpeg is None:
            continue
        for vector in faces.embed_faces(jpeg):
            cluster = _assign(index, vector)
            cluster.appearances.append(
                FaceAppearance(
                    video_id=video_id,
                    scene_id=scene.scene_id,
                    timestamp=scene.timestamp,
                    thumb_key=scene.thumb_key,
                )
            )
            touched.add(cluster.cluster_id)
            index.dim = len(vector)

    # Drop clusters that no longer have any appearances (e.g. after re-index).
    index.clusters = [c for c in index.clusters if c.appearances]
    _save_index(index)
    return len(touched)


def list_people() -> list[Person]:
    index = _load_index()
    people = [_to_person(c) for c in index.clusters]
    # Named people first, then by how often they appear.
    people.sort(key=lambda p: (p.name is None, -p.face_count))
    return people


def name_person(cluster_id: str, name: str) -> Person:
    index = _load_index()
    cluster = _find(index, cluster_id)
    cluster.name = name.strip() or None
    _save_index(index)
    return _to_person(cluster)


def person_clips(cluster_id: str) -> list[Clip]:
    """Every clip a person appears in, newest scenes first, playable inline."""
    index = _load_index()
    cluster = _find(index, cluster_id)
    playback_cache: dict[str, str | None] = {}
    clips: list[Clip] = []
    seen: set[tuple[str, str]] = set()
    for ap in cluster.appearances:
        dedup = (ap.video_id, ap.scene_id)
        if dedup in seen:
            continue
        seen.add(dedup)
        if ap.video_id not in playback_cache:
            playback_cache[ap.video_id] = _playback(ap.video_id)
        clips.append(
            Clip(
                video_id=ap.video_id,
                title=_video_title(ap.video_id),
                scene_id=ap.scene_id,
                timestamp=ap.timestamp,
                caption="",
                tags=[],
                score=1.0,
                thumb_url=_thumb_url(ap.thumb_key),
                playback_url=playback_cache[ap.video_id],
                people=[cluster.name] if cluster.name else [],
            )
        )
    clips.sort(key=lambda c: (c.video_id, c.timestamp))
    return clips


def names_for_video_scenes(video_id: str) -> dict[str, list[str]]:
    """Map ``scene_id -> [person names]`` for one video (named people only)."""
    index = _load_index()
    out: dict[str, list[str]] = {}
    for cluster in index.clusters:
        if not cluster.name:
            continue
        for ap in cluster.appearances:
            if ap.video_id == video_id:
                out.setdefault(ap.scene_id, []).append(cluster.name)
    return out


# --- internals --------------------------------------------------------------


def _assign(index: FaceClusterIndex, vector: list[float]) -> FaceCluster:
    centroids = [c.centroid for c in index.clusters]
    i, _dist = faces.nearest_centroid(vector, centroids)
    if i >= 0 and faces.matches(vector, centroids[i]):
        cluster = index.clusters[i]
        cluster.centroid = faces.update_centroid(
            cluster.centroid, cluster.face_count, vector
        )
        return cluster
    cluster = FaceCluster(
        cluster_id=f"p{len(index.clusters):04d}-{_short(vector)}",
        centroid=list(vector),
        cover_thumb_key="",
    )
    index.clusters.append(cluster)
    return cluster


def _drop_video(index: FaceClusterIndex, video_id: str) -> None:
    for cluster in index.clusters:
        cluster.appearances = [
            ap for ap in cluster.appearances if ap.video_id != video_id
        ]


def _find(index: FaceClusterIndex, cluster_id: str) -> FaceCluster:
    for cluster in index.clusters:
        if cluster.cluster_id == cluster_id:
            return cluster
    raise PersonNotFoundError()


def _to_person(cluster: FaceCluster) -> Person:
    videos = {ap.video_id for ap in cluster.appearances}
    cover = cluster.cover_thumb_key or (
        cluster.appearances[0].thumb_key if cluster.appearances else ""
    )
    return Person(
        cluster_id=cluster.cluster_id,
        name=cluster.name,
        face_count=cluster.face_count,
        video_count=len(videos),
        cover_thumb_url=_thumb_url(cover),
    )


def _read_thumb(key: str) -> bytes | None:
    try:
        return video_store.get_bytes(key)
    except RuntimeError:
        logger.warning("Could not read thumbnail %s for face detection", key)
        return None


def _thumb_url(key: str) -> str | None:
    if not key:
        return None
    try:
        return video_store.presigned_get(key)
    except RuntimeError:
        return None


def _playback(video_id: str) -> str | None:
    meta = video_store.get_json(video_store.meta_key(video_id))
    if not meta or not meta.get("source_key"):
        return None
    try:
        return video_store.presigned_get(meta["source_key"])
    except RuntimeError:
        return None


def _video_title(video_id: str) -> str:
    meta = video_store.get_json(video_store.meta_key(video_id))
    return (meta or {}).get("title", video_id)


def _short(vector: list[float]) -> str:
    import hashlib

    h = hashlib.sha1(
        ",".join(f"{x:.3f}" for x in vector[:8]).encode()
    ).hexdigest()
    return h[:6]
