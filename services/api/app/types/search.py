from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    # None = search across every ready video; otherwise scope to one.
    video_id: str | None = None
    # Optional structured filter: only return clips where this person (face
    # cluster) appears.
    person_id: str | None = None
    # Inclusive timezone-aware instants over the video's created_at timestamp.
    created_at_from: datetime | None = None
    created_at_to: datetime | None = None
    # Optional event/file-name filter. Event names are matched against the
    # ingested video title because B2 remains the sole datastore.
    event_name: str | None = Field(default=None, max_length=128)
    top_k: int = 8
    # When true and an answer model is configured, synthesize a short answer
    # over the retrieved clips with Claude.
    synthesize: bool = False

    @field_validator("event_name", mode="before")
    @classmethod
    def normalize_event_name(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_created_at_range(self) -> "SearchRequest":
        for value in (self.created_at_from, self.created_at_to):
            if value and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError("created_at filters must include a timezone")
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
