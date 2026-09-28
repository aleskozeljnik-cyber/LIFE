import httpx
from anthropic import AsyncAnthropic

from .config import settings

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

OBLIGATION_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "due_at": {"type": ["string", "null"]},
        "amount": {"type": ["number", "null"]},
        "currency": {"type": ["string", "null"]},
        "sender": {"type": ["string", "null"]},
        "category": {
            "type": "string",
            "enum": ["financial", "work", "personal", "legal", "family", "travel", "other"],
        },
        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
        "classification_reason": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": [
        "title",
        "summary",
        "due_at",
        "amount",
        "currency",
        "sender",
        "category",
        "priority",
        "classification_reason",
        "confidence",
    ],
}

SYSTEM_PROMPT = (
    "You are LIFE's obligation extraction engine. Extract only actionable obligations or commitments. "
    "Return one JSON object matching the provided schema, or null when there is no actionable obligation. "
    "Never invent missing facts. classification_reason must be a short, human-readable sentence explaining "
    "which evidence made the item actionable or important."
)


def configured_provider() -> str:
    return settings.ai_provider.strip().lower() or "gemini"


def configured_model() -> str:
    provider = configured_provider()
    if provider == "anthropic":
        return settings.anthropic_model
    if provider == "openrouter":
        return settings.openrouter_model
    return settings.gemini_model


async def generate_structured(source_text: str, correction_hint: str = "", source_type: str = "email") -> tuple[str, str] | None:
    provider = configured_provider()
    model = configured_model()
    user_prompt = (
        f"Source type: {source_type}\n\nContent:\n{source_text[:16000]}"
        + (f"\nPrior user correction preferences: {correction_hint}" if correction_hint else "")
    )

    if provider == "anthropic" and settings.anthropic_api_key:
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model=model,
            max_tokens=700,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = "".join(
            block.text for block in response.content
            if getattr(block, "type", None) == "text"
        )
        return raw, model

    if provider == "gemini" and settings.gemini_api_key:
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
                "responseJsonSchema": OBLIGATION_SCHEMA,
            },
        }
        url = GEMINI_URL.format(model=model)
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            response = await client.post(
                url,
                headers={"x-goog-api-key": settings.gemini_api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        parts = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [])
        )
        raw = "".join(part.get("text", "") for part in parts if part.get("text"))
        return raw, model

    if provider == "openrouter" and settings.openrouter_api_key:
        payload = {
            "model": model,
            "temperature": 0,
            "max_tokens": 700,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "life_obligation",
                    "strict": True,
                    "schema": OBLIGATION_SCHEMA,
                },
            },
        }
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "X-Title": "LIFE",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        raw = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return raw, data.get("model") or model

    return None
