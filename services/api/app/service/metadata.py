"""Metadata extraction for the generic /upload path.

This app indexes a video archive, so the starter kit's PDF (PyPDF2) and image
EXIF (Pillow) extractors are replaced with media probing (duration, resolution,
fps, codec, bitrate) via ffprobe. Checksums / size / mime are kept. ffprobe is
wrapped in the repo layer like any other external tool."""

import hashlib
import logging
from datetime import UTC, datetime

from app.repo import media
from app.types import FileMetadataDetail
from app.types.formatting import humanize_bytes

logger = logging.getLogger(__name__)

_PROBEABLE_PREFIXES = ("video/", "audio/")


def extract_metadata(
    file_data: bytes,
    filename: str,
    content_type: str,
) -> FileMetadataDetail:
    md5 = hashlib.md5(file_data, usedforsecurity=False).hexdigest()
    sha256 = hashlib.sha256(file_data).hexdigest()
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    extra: dict = {}
    if content_type.startswith(_PROBEABLE_PREFIXES):
        extra = _probe(file_data, extension)

    return FileMetadataDetail(
        filename=filename,
        size_bytes=len(file_data),
        size_human=humanize_bytes(len(file_data)),
        mime_type=content_type,
        extension=extension,
        md5=md5,
        sha256=sha256,
        uploaded_at=datetime.now(UTC),
        **extra,
    )


def _probe(file_data: bytes, extension: str) -> dict:
    try:
        probed = media.probe_bytes(file_data, suffix=f".{extension}" if extension else "")
    except Exception:
        logger.warning("Media probe failed", exc_info=True)
        return {}
    # Only forward keys the model knows about.
    return {
        k: probed.get(k)
        for k in ("duration_seconds", "width", "height", "fps", "codec", "bitrate")
        if probed.get(k) is not None
    }
