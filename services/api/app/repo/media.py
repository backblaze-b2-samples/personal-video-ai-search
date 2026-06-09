"""Media adapter — wraps the local ffmpeg/ffprobe tools and B2 downloads.

External tool calls live in the repo layer like any other adapter. ffmpeg is a
system prerequisite (see README / scripts/doctor.mjs). This adapter probes
container metadata, extracts a transcription-friendly audio track, and samples
scene-change keyframes (capped) that the vision + face stages consume.
"""

import contextlib
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from botocore.exceptions import ClientError

from app.config import settings
from app.repo.b2_client import get_s3_client

logger = logging.getLogger(__name__)


def download_to_temp(key: str, suffix: str = "") -> str:
    """Stream an object from B2 to a temp file and return its path."""
    client = get_s3_client()
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    try:
        client.download_file(settings.b2_bucket_name, key, path)
    except ClientError as e:
        raise RuntimeError(f"B2 download failed for '{key}': {e}") from e
    return path


def probe(path: str) -> dict:
    """Return ``{duration_seconds, width, height, fps, codec, bitrate}`` via
    ffprobe. Missing fields come back as ``None`` rather than raising."""
    cmd = [
        "ffprobe", "-v", "error",
        "-print_format", "json",
        "-show_format", "-show_streams", path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        logger.warning("ffprobe failed: %s", proc.stderr[-200:])
        return {}
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {}

    fmt = data.get("format", {})
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), {})

    return {
        "duration_seconds": _as_float(fmt.get("duration")),
        "width": _as_int(video.get("width")),
        "height": _as_int(video.get("height")),
        "fps": _parse_fps(video.get("avg_frame_rate")),
        "codec": video.get("codec_name"),
        "bitrate": _as_int(fmt.get("bit_rate")),
    }


def probe_bytes(data: bytes, suffix: str = "") -> dict:
    """Probe media held in memory (used by the generic /upload path). Writes a
    temp file because ffprobe needs a seekable input, then probes it."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        return probe(path)
    finally:
        with contextlib.suppress(OSError):
            os.unlink(path)


def extract_audio(video_path: str) -> str:
    """Extract a mono 16 kHz track suitable for transcription. Returns a path."""
    out = str(Path(tempfile.mkdtemp()) / "audio.m4a")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "aac", out,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extraction failed: {proc.stderr[-500:]}")
    return out


def sample_keyframes(video_path: str) -> list[tuple[float, bytes]]:
    """Sample scene-change keyframes, capped at ``MAX_KEYFRAMES_PER_VIDEO``.

    Returns ``[(timestamp_seconds, jpeg_bytes), ...]``. Uses ffmpeg's scene
    filter so frames track real visual cuts rather than a fixed cadence; falls
    back to evenly spaced frames if scene detection yields too few.
    """
    frames = _extract_scene_frames(video_path)
    if len(frames) < 2:
        frames = _extract_interval_frames(video_path)
    return frames[: settings.max_keyframes_per_video]


# --- internals --------------------------------------------------------------


def _extract_scene_frames(video_path: str) -> list[tuple[float, bytes]]:
    out_dir = Path(tempfile.mkdtemp())
    pattern = str(out_dir / "kf_%04d.jpg")
    cap = settings.max_keyframes_per_video
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", (
            f"select='gt(scene,{settings.scene_threshold})',"
            "showinfo,scale=640:-1"
        ),
        "-vsync", "vfr", "-frames:v", str(cap), pattern,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        logger.warning("ffmpeg scene sampling failed: %s", proc.stderr[-200:])
        return []
    timestamps = _parse_showinfo_timestamps(proc.stderr)
    return _read_jpegs(out_dir, timestamps)


def _extract_interval_frames(video_path: str) -> list[tuple[float, bytes]]:
    """Fallback: one frame every few seconds (short clips / few scene cuts)."""
    duration = probe(video_path).get("duration_seconds") or 0.0
    cap = settings.max_keyframes_per_video
    step = max(1.0, duration / cap) if duration else 2.0
    out_dir = Path(tempfile.mkdtemp())
    pattern = str(out_dir / "kf_%04d.jpg")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"fps=1/{step:.3f},scale=640:-1",
        "-frames:v", str(cap), pattern,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        logger.warning("ffmpeg interval sampling failed: %s", proc.stderr[-200:])
        return []
    files = sorted(out_dir.glob("kf_*.jpg"))
    return [(i * step, f.read_bytes()) for i, f in enumerate(files)]


def _read_jpegs(
    out_dir: Path, timestamps: list[float]
) -> list[tuple[float, bytes]]:
    files = sorted(out_dir.glob("kf_*.jpg"))
    result: list[tuple[float, bytes]] = []
    for i, f in enumerate(files):
        ts = timestamps[i] if i < len(timestamps) else float(i)
        result.append((ts, f.read_bytes()))
    return result


def _parse_showinfo_timestamps(stderr: str) -> list[float]:
    """Pull ``pts_time:<seconds>`` values logged by the showinfo filter."""
    out: list[float] = []
    for line in stderr.splitlines():
        marker = "pts_time:"
        idx = line.find(marker)
        if idx == -1:
            continue
        rest = line[idx + len(marker):].split()[0]
        val = _as_float(rest)
        if val is not None:
            out.append(val)
    return out


def _as_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_fps(rate: str | None) -> float | None:
    if not rate or "/" not in rate:
        return _as_float(rate)
    num, _, den = rate.partition("/")
    n, d = _as_float(num), _as_float(den)
    if not n or not d:
        return None
    return round(n / d, 3)
