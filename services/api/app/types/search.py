from datetime import date

from pydantic import BaseModel, model_validator


class SearchRequest(BaseModel):
    question: str
    # None = search across every ready video; otherwise scope to one.
    video_id: str | None = None
    # Optional structured filter: only return clips where this person (face
    # cluster) appears.
    person_id: str | None = None
    # Inclusive date range over the video's created_at timestamp.
    created_at_from: date | None = None
    created_at_to: date | None = None
    # Optional event/file-name filter. Event names are matched against the
    # ingested video title because B2 remains the sole datastore.
    event_name: str | None = None
    top_k: int = 8
    # When true and an answer model is configured, synthesize a short answer
    # over the retrieved clips with Claude.
    synthesize: bool = False

    @model_validator(mode="after")
    def validate_created_at_range(self) -> "SearchRequest":
        if (
            self.created_at_from
            and self.created_at_to
            and self.created_at_from > self.created_at_to
        ):
            raise ValueError("created_at_from must be on or before created_at_to")
        return self


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
