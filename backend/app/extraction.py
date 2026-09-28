import json
import re
from dataclasses import dataclass

from .ai import generate_structured


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
    model: str


MOCK_MODEL = "rules-v1"

ACTION_WORDS = (
    "please", "must", "need to", "needs to", "deadline", "due",
    "reply", "review", "approve", "sign", "send", "pay", "confirm",
    "meeting", "appointment", "invoice", "payment", "renew", "book",
    "accept", "reject", "respond", "action required",
)


def is_ai_candidate(text: str, source_type: str) -> bool:
    if source_type == "calendar":
        return True
    lower = text.lower()
    return any(word in lower for word in ACTION_WORDS)


def _mock_extract(text: str, source_type: str, reason: str | None = None) -> ExtractedObligation | None:
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    lower = text.lower()
    title = "Calendar commitment" if source_type == "calendar" else "Email follow-up"
    for line in lines:
        if source_type == "email" and line.lower().startswith("subject:"):
            title = line.split(":", 1)[1].strip()[:300] or title
            break
        if source_type == "calendar" and line.lower().startswith("event:"):
            title = line.split(":", 1)[1].strip()[:300] or title
            break
    if not is_ai_candidate(text, source_type):
        return None
    priority = "high" if any(word in lower for word in ("urgent", "asap", "today", "overdue", "deadline")) else "medium"
    category = "financial" if any(word in lower for word in ("invoice", "payment", "eur", "€", "cost", "price")) else "work"
    amount = None
    match = re.search(r"(?:€|eur\s*)(\d[\d.,]*)", lower)
    if match:
        try:
            amount = float(match.group(1).replace(".", "").replace(",", "."))
        except ValueError:
            amount = None
    classification_reason = reason or "Rule-based classification; configure an AI provider for model-based extraction."
    return ExtractedObligation(
        title, text[:2000], None, amount,
        "EUR" if amount is not None else None, None,
        category, priority, classification_reason, 0.55, MOCK_MODEL
    )


def _extract_json(raw: str) -> dict | None:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*```$", "", raw).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.S)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None


def _build_result(data: dict, model: str) -> ExtractedObligation:
    priority = str(data.get("priority", "medium")).lower()
    category = str(data.get("category", "other")).lower()
    if priority not in {"high", "medium", "low"}:
        priority = "medium"
    if category not in {"financial", "work", "personal", "legal", "family", "travel", "other"}:
        category = "other"
    try:
        confidence = max(0.0, min(1.0, float(data.get("confidence", 0))))
    except (TypeError, ValueError):
        confidence = 0.0
    try:
        amount = float(data["amount"]) if data.get("amount") is not None else None
    except (TypeError, ValueError):
        amount = None
    return ExtractedObligation(
        str(data.get("title", "Untitled obligation"))[:300],
        str(data.get("summary", ""))[:2000],
        str(data["due_at"]) if data.get("due_at") else None,
        amount,
        str(data["currency"]) if data.get("currency") else None,
        str(data["sender"]) if data.get("sender") else None,
        category,
        priority,
        str(data.get("classification_reason", "No reason supplied."))[:500],
        confidence,
        model,
    )


async def extract_obligation(text: str, correction_hint: str = "", source_type: str = "email") -> ExtractedObligation | None:
    # Cheap deterministic gate: only likely-actionable emails reach the AI API.
    if not is_ai_candidate(text, source_type):
        return None
    try:
        generated = await generate_structured(text, correction_hint, source_type)
    except Exception as exc:
        generated = None
        fallback_reason = f"AI provider error ({type(exc).__name__}); LIFE used a safe fallback."
    else:
        fallback_reason = "AI provider unavailable; LIFE used a safe fallback."
    if generated is None:
        return _mock_extract(text, source_type, fallback_reason)
    raw, model = generated
    data = _extract_json(raw)
    if data is None:
        return _mock_extract(text, source_type, "AI returned invalid JSON; LIFE used a safe fallback.")
    if not data:
        return None
    return _build_result(data, model)
