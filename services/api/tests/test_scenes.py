"""Unit tests for scene document assembly (pure; no ffmpeg / no API)."""

from app.service import scenes as scenes_svc
from app.types import Keyframe, Transcript, TranscriptSegment


def _scene(**kw) -> Keyframe:
    base = dict(
        scene_id="s0001",
        timestamp=10.0,
        thumb_key="k/thumbs/s0001.jpg",
        caption="A dog leaps into a pool",
        tags=["dog", "pool", "jump"],
        transcript_text="",
    )
    base.update(kw)
    return Keyframe(**base)


def test_scene_document_combines_signals():
    doc = scenes_svc.scene_document(_scene(transcript_text="watch this!"))
    assert "dog leaps into a pool" in doc.lower()
    assert "dog, pool, jump" in doc
    assert "watch this!" in doc


def test_scene_document_handles_empty_caption_and_tags():
    doc = scenes_svc.scene_document(_scene(caption="", tags=[], transcript_text="hi"))
    assert doc == "hi"


def test_transcript_around_window():
    transcript = Transcript(
        video_id="v1",
        segments=[
            TranscriptSegment(start=0.0, end=3.0, text="early"),
            TranscriptSegment(start=9.0, end=11.0, text="match"),
            TranscriptSegment(start=40.0, end=42.0, text="late"),
        ],
    )
    text = scenes_svc._transcript_around(transcript, timestamp=10.0, window=4.0)
    assert text == "match"


def test_transcript_around_none():
    assert scenes_svc._transcript_around(None, 10.0) == ""
