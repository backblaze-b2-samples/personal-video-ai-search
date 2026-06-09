"""Graceful-degradation tests: with no AI key, the multimodal features must
return a clear 'not configured' state rather than crashing, and the generic B2
surfaces stay available."""

from app.repo import embeddings, vision
from app.service import ingest
from app.service.search import search
from app.types import SearchRequest, Video, VideoStatus


def test_search_without_provider_returns_unconfigured(monkeypatch):
    monkeypatch.setattr(embeddings, "is_configured", lambda: False)
    resp = search(SearchRequest(question="dog in the pool"))
    assert resp.provider_configured is False
    assert resp.clips == []
    assert resp.answer is None


def test_pipeline_marks_uploaded_without_provider(monkeypatch):
    captured = {}

    monkeypatch.setattr(vision, "is_configured", lambda: False)
    monkeypatch.setattr(embeddings, "is_configured", lambda: False)
    monkeypatch.setattr(
        ingest.videos_svc,
        "try_get",
        lambda vid: Video(
            video_id=vid,
            title="clip.mp4",
            status=VideoStatus.uploaded,
            source_key="k/source.mp4",
            size_bytes=1,
            size_human="1 B",
            content_type="video/mp4",
            created_at="2026-02-14T00:00:00Z",
        ),
    )

    def fake_update(video_id, status, **kw):
        captured["status"] = status
        captured["error"] = kw.get("error")

    monkeypatch.setattr(ingest.videos_svc, "update_status", fake_update)

    ingest.run_pipeline("clip-abc")
    assert captured["status"] == VideoStatus.uploaded
    assert "OPENAI_API_KEY" in (captured["error"] or "")


def test_search_empty_question_rejected():
    import pytest

    with pytest.raises(ValueError):
        search(SearchRequest(question="   "))
