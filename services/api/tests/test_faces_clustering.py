"""Unit tests for the pure face-clustering helpers (no model / no SDK needed)."""

from app.repo import faces


def test_cosine_distance_identical_is_zero():
    v = [1.0, 0.0, 0.0]
    assert faces.cosine_distance(v, v) == 0.0


def test_cosine_distance_orthogonal_is_one():
    assert abs(faces.cosine_distance([1.0, 0.0], [0.0, 1.0]) - 1.0) < 1e-6


def test_nearest_centroid_empty():
    i, d = faces.nearest_centroid([1.0, 0.0], [])
    assert i == -1
    assert d == float("inf")


def test_nearest_centroid_picks_closest():
    centroids = [[1.0, 0.0], [0.0, 1.0]]
    i, _ = faces.nearest_centroid([0.9, 0.1], centroids)
    assert i == 0


def test_matches_respects_threshold(monkeypatch):
    monkeypatch.setattr(faces.settings, "face_cluster_threshold", 0.2)
    # near-identical → matches; orthogonal → does not
    assert faces.matches([1.0, 0.0], [0.99, 0.01])
    assert not faces.matches([1.0, 0.0], [0.0, 1.0])


def test_update_centroid_is_normalized():
    out = faces.update_centroid([1.0, 0.0], 1, [0.0, 1.0])
    norm = (out[0] ** 2 + out[1] ** 2) ** 0.5
    assert abs(norm - 1.0) < 1e-6
