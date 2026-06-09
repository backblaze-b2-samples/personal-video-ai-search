"""Answer-synthesis adapter (Claude). Optional — search works without it.
SDK imported lazily."""

from app.config import settings
from app.repo.errors import ProviderNotConfiguredError

_PROMPT = (
    "You are helping someone search their personal video archive. Using only "
    "the numbered scene descriptions below, answer the question in a sentence "
    "or two and cite scenes inline like [1]. If the scenes do not contain the "
    "answer, say so plainly.\n\n"
    "Question: {question}\n\nScenes:\n{context}"
)


def is_configured() -> bool:
    return bool(settings.anthropic_api_key)


def synthesize_answer(question: str, snippets: list[str]) -> str:
    if not is_configured():
        raise ProviderNotConfiguredError(
            "Answer synthesis requires ANTHROPIC_API_KEY."
        )
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    context = "\n\n".join(f"[{i + 1}] {s}" for i, s in enumerate(snippets))
    message = client.messages.create(
        model=settings.answer_model,
        max_tokens=400,
        messages=[
            {
                "role": "user",
                "content": _PROMPT.format(question=question, context=context),
            }
        ],
    )
    parts = [
        block.text
        for block in message.content
        if getattr(block, "type", None) == "text"
    ]
    return "".join(parts).strip()
