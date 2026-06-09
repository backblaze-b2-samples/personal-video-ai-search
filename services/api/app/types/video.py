from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class VideoStatus(StrEnum):
    """Lifecycle of a video as it moves through the multimodal index pipeline.

    The pipeline runs three signals after the upload lands in B2: a Whisper
    transcript, AI scene captions/tags from sampled keyframes, and local face
    clustering. ``embedding`` is the final paid step before ``ready``.
    """

    uploading = "uploading"
    uploaded = "uploaded"
    probing = "probing"
    transcribing = "transcribing"
    tagging = "tagging"          # vision captions + tags per keyframe
    clustering = "clustering"    # local face detect + embed + cluster
    embedding = "embedding"      # build the searchable index
    ready = "ready"
    failed = "failed"


class Video(BaseModel):
    """A source video and its pipeline state. Persisted to B2 as meta.json."""

    video_id: str
    title: str
    status: VideoStatus
    source_key: str
    size_bytes: int
    size_human: str
    content_type: str
    created_at: datetime
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    codec: str | None = None
    # Index summary, surfaced in the Library.
    scene_count: int | None = None
    people_count: int | None = None
    clip_count: int | None = None  # searchable scene/clip embeddings
    error: str | None = None


class CreateUploadRequest(BaseModel):
    filename: str
    size_bytes: int
    content_type: str = "video/mp4"


class PresignedPart(BaseModel):
    part_number: int
    url: str


class MultipartUpload(BaseModel):
    """Everything the browser needs to PUT parts directly to B2."""

    video_id: str
    source_key: str
    upload_id: str
    part_size: int
    parts: list[PresignedPart]


class CompletedPart(BaseModel):
    part_number: int
    etag: str


class CompleteUploadRequest(BaseModel):
    video_id: str
    source_key: str
    upload_id: str
    title: str
    size_bytes: int
    content_type: str = "video/mp4"
    parts: list[CompletedPart]
