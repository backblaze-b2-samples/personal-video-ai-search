from pydantic import BaseModel


class Keyframe(BaseModel):
    """One sampled scene-change frame, with its AI visual description.

    The thumbnail is stored in B2; ``thumb_key`` points at it. ``caption`` and
    ``tags`` come from the vision model and, together with any overlapping
    transcript text, form the document we embed for search.
    """

    scene_id: str
    timestamp: float  # seconds into the video
    thumb_key: str
    caption: str = ""
    tags: list[str] = []
    transcript_text: str = ""


class SceneEmbedding(BaseModel):
    """A searchable scene: its combined text plus the embedding vector."""

    scene_id: str
    timestamp: float
    thumb_key: str
    caption: str
    tags: list[str]
    text: str  # caption + tags + overlapping transcript, embedded
    vector: list[float]


class SceneIndex(BaseModel):
    """The per-video multimodal index. Persisted to B2 as embeddings.json —
    this is the search index, so B2 stays the sole data store (no vector DB).
    """

    video_id: str
    model: str
    dim: int
    scenes: list[SceneEmbedding]
