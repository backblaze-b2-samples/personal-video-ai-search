"""Vision adapter — turns a sampled keyframe (JPEG bytes) into a short scene
caption plus a handful of tags using a cheap multimodal model (gpt-4o-mini).

This is the signal that powers visual queries like "the dog jumps in the
pool" — the model describes what is *on screen*, independent of the audio.
SDK imported lazily; degrades gracefully when no key is set."""

import base64
import json
import logging

from app.config import settings
from app.repo.errors import ProviderNotConfiguredError

logger = logging.getLogger(__name__)

_PROMPT = (
    "Describe this video keyframe for search. Respond with strict JSON: "
    '{"caption": "<one concrete sentence>", "tags": ["<3-8 short visual '
    'tags: subjects, actions, setting, objects>"]}. Be literal about what is '
    "visible; do not speculate."
)


def is_configured() -> bool:
    return bool(settings.openai_api_key)


def model_name() -> str:
    return settings.vision_model


def describe_keyframe(jpeg_bytes: bytes) -> dict:
    """Return ``{"caption": str, "tags": [str]}`` for one keyframe."""
    if not is_configured():
        raise ProviderNotConfiguredError(
            "Visual scene tagging requires OPENAI_API_KEY (model: "
            f"{settings.vision_model})."
        )
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    b64 = base64.b64encode(jpeg_bytes).decode("ascii")
    resp = client.chat.completions.create(
        model=settings.vision_model,
        response_format={"type": "json_object"},
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            }
        ],
    )
    raw = resp.choices[0].message.content or "{}"
    return _parse(raw)


def _parse(raw: str) -> dict:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Vision model returned non-JSON; falling back to empty")
        return {"caption": "", "tags": []}
    caption = str(data.get("caption", "")).strip()
    tags = [str(t).strip().lower() for t in data.get("tags", []) if str(t).strip()]
    return {"caption": caption, "tags": tags[:8]}
