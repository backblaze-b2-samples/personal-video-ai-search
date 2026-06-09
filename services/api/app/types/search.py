from pydantic import BaseModel


class SearchRequest(BaseModel):
    question: str
    # None = search across every ready video; otherwise scope to one.
    video_id: str | None = None
    # Optional structured filter: only return clips where this person (face
    # cluster) appears.
    person_id: str | None = None
    top_k: int = 8
    # When true and an answer model is configured, synthesize a short answer
    # over the retrieved clips with Claude.
    synthesize: bool = False


class Clip(BaseModel):
    """A matching moment, playable inline by seeking the original in B2."""

    video_id: str
    title: str
    scene_id: str
    timestamp: float
    caption: str
    tags: list[str]
    score: float
    thumb_url: str | None = None
    playback_url: str | None = None
    # Names of people detected in this scene (when face indexing ran).
    people: list[str] = []


class SearchResponse(BaseModel):
    question: str
    clips: list[Clip]
    answer: str | None = None
    # False when no provider/index is available — the UI shows a clear
    # "configure a provider and ingest a video" state instead of empty results.
    provider_configured: bool = True
