from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.repo import embeddings, video_store
from app.service import people as people_svc
from app.service import search as search_svc
from app.service import videos as videos_svc
from app.types import SearchRequest, Video, VideoStatus


def _video(video_id: str, title: str, created_at: datetime) -> Video:
    return Video(
        video_id=video_id,
        title=title,
        status=VideoStatus.ready,
        source_key=f"videos/{video_id}/source.mp4",
        size_bytes=1,
        size_human="1 B",
        content_type="video/mp4",
        created_at=created_at,
    )


def _index(video_id: str, scene_id: str) -> dict:
    return {
        "video_id": video_id,
        "model": "test",
        "dim": 2,
        "scenes": [
            {
                "scene_id": scene_id,
                "timestamp": 12.0,
                "thumb_key": f"videos/{video_id}/thumbs/{scene_id}.jpg",
                "caption": f"{video_id} caption",
                "tags": ["tag"],
                "text": f"{video_id} text",
                "vector": [1.0, 0.0],
            }
        ],
    }


@pytest.fixture
def search_fixture(monkeypatch):
    videos = [
        _video(
            "too-early",
            "Early Birthday Setup",
            datetime(2026, 2, 14, 4, 59, tzinfo=UTC),
        ),
        _video(
            "birthday",
            "Birthday Party",
            datetime(2026, 2, 14, 15, 30, tzinfo=UTC),
        ),
        _video(
            "late-birthday",
            "Late Birthday Party",
            datetime(2026, 2, 15, 1, 30, tzinfo=UTC),
        ),
        _video(
            "final-ms-birthday",
            "Final Millisecond Birthday",
            datetime(2026, 2, 15, 4, 59, 59, 999999, tzinfo=UTC),
        ),
        _video(
            "vacation",
            "Beach Vacation",
            datetime(2026, 3, 5, 9, 0, tzinfo=UTC),
        ),
    ]
    indexes = {
        video_store.embeddings_key("too-early"): _index("too-early", "s0000"),
        video_store.embeddings_key("birthday"): _index("birthday", "s0001"),
        video_store.embeddings_key("late-birthday"): _index(
            "late-birthday", "s0003"
        ),
        video_store.embeddings_key("final-ms-birthday"): _index(
            "final-ms-birthday", "s0004"
        ),
        video_store.embeddings_key("vacation"): _index("vacation", "s0002"),
    }

    monkeypatch.setattr(embeddings, "is_configured", lambda: True)
    monkeypatch.setattr(embeddings, "embed_query", lambda question: [1.0, 0.0])
    monkeypatch.setattr(videos_svc, "list_videos", lambda: videos)
    monkeypatch.setattr(video_store, "get_json", lambda key: indexes.get(key))
    monkeypatch.setattr(video_store, "presigned_get", lambda key: f"https://b2/{key}")
    monkeypatch.setattr(people_svc, "names_for_video_scenes", lambda video_id: {})


def test_search_filters_by_created_at_range(search_fixture):
    resp = search_svc.search(
        SearchRequest(
            question="pool",
            created_at_from=datetime(2026, 2, 14, 5, 0, tzinfo=UTC),
            created_at_to=datetime(2026, 2, 15, 4, 59, 59, 999999, tzinfo=UTC),
        )
    )

    assert {clip.video_id for clip in resp.clips} == {
        "birthday",
        "late-birthday",
        "final-ms-birthday",
    }
    assert len(resp.clips) == 3


def test_search_preserves_microsecond_upper_bound(search_fixture):
    resp = search_svc.search(
        SearchRequest(
            question="pool",
            created_at_from=datetime(2026, 2, 14, 5, 0, tzinfo=UTC),
            created_at_to=datetime(2026, 2, 15, 4, 59, 59, 999998, tzinfo=UTC),
        )
    )

    assert {clip.video_id for clip in resp.clips} == {"birthday", "late-birthday"}
    assert len(resp.clips) == 2


def test_search_filters_by_event_name(search_fixture):
    resp = search_svc.search(
        SearchRequest(question="pool", event_name="  vacation  ")
    )

    assert [clip.video_id for clip in resp.clips] == ["vacation"]


def test_search_rejects_reversed_created_at_range():
    with pytest.raises(ValidationError):
        SearchRequest(
            question="pool",
            created_at_from=datetime(2026, 3, 1, tzinfo=UTC),
            created_at_to=datetime(2026, 2, 1, tzinfo=UTC),
        )


def test_search_rejects_timezone_naive_created_at_filter():
    with pytest.raises(ValidationError):
        SearchRequest(
            question="pool",
            created_at_from=datetime(2026, 2, 14),
        )


def test_search_rejects_oversized_event_name():
    with pytest.raises(ValidationError):
        SearchRequest(question="pool", event_name="x" * 129)


def test_search_normalizes_event_name_before_length_validation():
    empty = SearchRequest(question="pool", event_name=" " * 129)
    padded = SearchRequest(question="pool", event_name=f" {'x' * 128} ")

    assert empty.event_name is None
    assert padded.event_name == "x" * 128


async def test_search_api_rejects_oversized_event_name(client):
    resp = await client.post(
        "/search",
        json={"question": "pool", "event_name": "x" * 129},
    )

    assert resp.status_code == 422


async def test_search_api_rejects_unknown_filter_fields(client):
    resp = await client.post(
        "/search",
        json={"question": "pool", "created_at_start": "2026-02-14T00:00:00Z"},
    )

    assert resp.status_code == 422
