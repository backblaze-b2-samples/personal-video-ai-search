from pydantic import BaseModel


class TranscriptSegment(BaseModel):
    start: float  # seconds from the start of the video
    end: float
    text: str


class Transcript(BaseModel):
    """Full transcript for a video. Persisted to B2 as transcript.json."""

    video_id: str
    language: str | None = None
    duration_seconds: float | None = None
    segments: list[TranscriptSegment]
