from pydantic import BaseModel


class FaceAppearance(BaseModel):
    """One detected face in one video, with where/when it was seen."""

    video_id: str
    scene_id: str
    timestamp: float
    thumb_key: str  # the keyframe thumbnail the face was detected in


class FaceCluster(BaseModel):
    """A group of faces the local model judged to be the same person.

    Centroid embedding lets us assign faces from newly ingested videos to an
    existing person. ``name`` is user-supplied (e.g. "Grandma") — null until
    named. The cluster index is persisted to B2 as people/index.json, so the
    People surface is backed entirely by B2.
    """

    cluster_id: str
    name: str | None = None
    centroid: list[float]
    cover_thumb_key: str
    appearances: list[FaceAppearance] = []

    @property
    def face_count(self) -> int:
        return len(self.appearances)


class FaceClusterIndex(BaseModel):
    """The archive-wide face index. Persisted to B2 as people/index.json."""

    model: str
    dim: int
    clusters: list[FaceCluster]


class Person(BaseModel):
    """A face cluster as surfaced on the People page (no raw vectors)."""

    cluster_id: str
    name: str | None
    face_count: int
    video_count: int
    cover_thumb_url: str | None = None


class NamePersonRequest(BaseModel):
    name: str
