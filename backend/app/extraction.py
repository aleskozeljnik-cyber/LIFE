import json
from dataclasses import dataclass
from anthropic import AsyncAnthropic
from .config import settings

@dataclass
class ExtractedObligation:
    title: str
    summary: str
    due_at: str | None
    amount: float | None
    currency: str | None
    sender: str | None
    category: str
    priority: str
    classification_reason: str
    confidence: float

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are LIFE's obligation extraction engine. Extract only actionable obligations or commitments.
Return strict JSON object or null.
Fields: title, summary, due_at, amount, currency, sender, category, priority, classification_reason, confidence.
category: financial|work|personal|legal|family|travel|other.
priority: high|medium|low.
due_at: ISO-8601 or null. amount: number or null. confidence: 0..1.
classification_reason must explain in plain language why this item is actionable and why its priority/category were chosen.
Never invent missing facts. If there is no actionable obligation, return null."""

async def extract_obligation(text: str, correction_hint: str = "", source_type: str = "email") -> ExtractedObligation | None:
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    context = "\nPrior user correction preferences: " + correction_hint if correction_hint else ""
    response = await client.messages.create(model=MODEL, max_tokens=700, system=SYSTEM_PROMPT, messages=[{"role": "user", "content": f"Source type: {source_type}\n\nContent:\n{text[:16000]}{context}"}])
    raw = "".join(block.text for block in response.content if getattr(block, "type", None) == "text").strip()
    if raw.startswith("```"):
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)
    if data is None:
        return None
    priority = str(data.get("priority", "medium")).lower()
    category = str(data.get("category", "other")).lower()
    if priority not in {"high", "medium", "low"}: priority = "medium"
    if category not in {"financial", "work", "personal", "legal", "family", "travel", "other"}: category = "other"
    confidence = max(0.0, min(1.0, float(data.get("confidence", 0))))
    amount = float(data["amount"]) if data.get("amount") is not None else None
    return ExtractedObligation(str(data.get("title", "Untitled obligation"))[:300], str(data.get("summary", ""))[:2000], data.get("due_at"), amount, str(data["currency"]) if data.get("currency") else None, str(data["sender"]) if data.get("sender") else None, category, priority, str(data.get("classification_reason", "No reason supplied."))[:500], confidence)