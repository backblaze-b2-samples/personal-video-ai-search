"""Transcription adapter (OpenAI Whisper). The provider SDK is imported lazily
so this module imports cleanly without the SDK installed or a key set."""

import logging

from app.config import settings
from app.repo.errors import ProviderNotConfiguredError

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    return bool(settings.openai_api_key)


def transcribe(audio_path: str) -> dict:
    """Transcribe audio to ``{language, duration, segments:[{start,end,text}]}``.

    The service maps the returned dict into a typed ``Transcript``.
    """
    if not is_configured():
        raise ProviderNotConfiguredError(
            "Transcription requires OPENAI_API_KEY (model: "
            f"{settings.transcription_model})."
        )
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    with open(audio_path, "rb") as fh:
        resp = client.audio.transcriptions.create(
            model=settings.transcription_model,
            file=fh,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    segments: list[dict] = []
    for s in getattr(resp, "segments", None) or []:
        start = getattr(s, "start", None)
        end = getattr(s, "end", None)
        if start is None or end is None:
            continue
        segments.append(
            {
                "start": float(start),
                "end": float(end),
                "text": (getattr(s, "text", "") or "").strip(),
            }
        )
    return {
        "language": getattr(resp, "language", None),
        "duration": getattr(resp, "duration", None),
        "segments": segments,
    }
