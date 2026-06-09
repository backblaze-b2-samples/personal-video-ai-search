"""Scene building — sample keyframes, write thumbnails to B2, caption/tag each
with the vision model, and attach the overlapping transcript text.

Pure orchestration over the repo layer; the output (a list of ``Keyframe``) is
what both the embedding index and the face stage consume."""

import logging

from app.repo import media, video_store, vision
from app.types import Keyframe, Transcript

logger = logging.getLogger(__name__)


def build_scenes(
    video_id: str, local_video_path: str, transcript: Transcript | None
) -> list[Keyframe]:
    """Sample keyframes, persist thumbnails, and describe each scene."""
    frames = media.sample_keyframes(local_video_path)
    scenes: list[Keyframe] = []
    for i, (timestamp, jpeg) in enumerate(frames):
        scene_id = f"s{i:04d}"
        key = video_store.thumb_key(video_id, scene_id)
        video_store.put_bytes(key, jpeg, "image/jpeg")

        described = vision.describe_keyframe(jpeg)
        scenes.append(
            Keyframe(
                scene_id=scene_id,
                timestamp=timestamp,
                thumb_key=key,
                caption=described["caption"],
                tags=described["tags"],
                transcript_text=_transcript_around(transcript, timestamp),
            )
        )
    return scenes


def scene_document(scene: Keyframe) -> str:
    """The text we embed for one scene: caption + tags + nearby speech."""
    parts = [scene.caption]
    if scene.tags:
        parts.append(", ".join(scene.tags))
    if scene.transcript_text:
        parts.append(scene.transcript_text)
    return ". ".join(p for p in parts if p).strip()


def _transcript_around(
    transcript: Transcript | None, timestamp: float, window: float = 8.0
) -> str:
    """Speech within +/- ``window`` seconds of the keyframe, joined."""
    if not transcript or not transcript.segments:
        return ""
    lo, hi = timestamp - window, timestamp + window
    texts = [
        seg.text
        for seg in transcript.segments
        if seg.end >= lo and seg.start <= hi and seg.text
    ]
    return " ".join(texts).strip()
