from dataclasses import dataclass
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

async def extract_obligation(text: str) -> ExtractedObligation:
    """AI extraction contract. Real Claude execution is enabled once ANTHROPIC_API_KEY is configured."""
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")
    # Keep provider-specific prompting isolated here so Gmail/Calendar adapters stay deterministic.
    raise NotImplementedError("Claude extraction adapter is the next implementation step")
