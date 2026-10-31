import re

import httpx

from app.core.config import get_settings


def _local_improve(kind: str, text: str, tone: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", compact) if s.strip()]
    if not sentences:
        sentences = [compact]
    lead = sentences[0].rstrip(".")
    rest = " ".join(sentences[1:])
    if kind == "bio":
        opener = {
            "professional": "I am a results-oriented software developer",
            "confident": "I build production-ready software with care and speed",
            "warm": "I enjoy building useful software with people, not just for them",
        }.get(tone, "I am a software developer")
        body = rest or compact
        return (
            f"{opener}. {lead}. {body} "
            "I focus on clear architecture, accessible interfaces, and shipping work that holds up in production."
        ).strip()
    return (
        f"{lead} — designed as a practical, end-to-end product. "
        f"{rest} Highlights include thoughtful UX, structured APIs, and a stack chosen for maintainability."
    ).strip()


def improve_text(kind: str, text: str, tone: str = "professional") -> tuple[str, str]:
    settings = get_settings()
    if not settings.openai_api_key:
        return _local_improve(kind, text, tone), "local"

    system = (
        "You improve professional portfolio writing. Return only the rewritten text. "
        "Keep facts, names, and technologies. Do not invent employers or degrees. "
        f"Tone: {tone}. Kind: {kind}."
    )
    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
        "temperature": 0.4,
    }
    try:
        with httpx.Client(timeout=25) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json=payload,
            )
            response.raise_for_status()
            improved = response.json()["choices"][0]["message"]["content"].strip()
            return improved, "openai"
    except Exception:
        return _local_improve(kind, text, tone), "local-fallback"
