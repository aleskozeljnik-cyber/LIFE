from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
import re


@dataclass(frozen=True)
class NormalizedItem:
    """Provider-neutral representation of one source item."""

    provider: str
    item_type: str
    external_id: str | None
    title: str | None = None
    body: str | None = None
    summary: str | None = None
    source_url: str | None = None
    occurred_at: datetime | None = None
    account_key: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class PersonRef:
    display_name: str | None = None
    email: str | None = None
    phone: str | None = None
    external_id: str | None = None


@dataclass(frozen=True)
class ProjectRef:
    name: str
    kind: str = "project"


class ProviderAdapter:
    """Contract for future connectors.

    Adapters normalize provider-specific payloads into the same Item model.
    They must not contain prioritization or user-facing decision logic.
    """

    provider: str

    async def initial_sync(self, user_id: str) -> list[NormalizedItem]:
        raise NotImplementedError

    async def incremental_sync(self, user_id: str, cursor: str | None) -> tuple[list[NormalizedItem], str | None]:
        raise NotImplementedError

    async def disconnect(self, user_id: str) -> None:
        raise NotImplementedError


def normalize_email(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().lower()


def normalize_name(value: str | None) -> str | None:
    if not value:
        return None
    return " ".join(value.strip().lower().split())


def item_key(item: NormalizedItem) -> tuple[str, str | None]:
    return item.provider, item.external_id


PROJECT_PATTERNS = (
    re.compile(r"^\s*\[project:\s*(.+?)\]\s*", re.I),
    re.compile(r"^\s*project:\s*(.+?)(?:\s*[|-]\s*|$)", re.I),
)

def extract_project_hint(title: str | None) -> ProjectRef | None:
    if not title:
        return None
    for pattern in PROJECT_PATTERNS:
        match = pattern.search(title)
        if match:
            name = match.group(1).strip(" -:|")
            if name:
                return ProjectRef(name=name)
    return None


TOPIC_STOPWORDS = {
    "re", "fw", "fwd", "the", "and", "for", "from", "with", "your", "this",
    "pozdravljeni", "pozdravljen", "prosim", "hvala", "sestanek", "termin",
    "potrditev", "račun", "racun", "plačilo", "placilo", "izstavitev",
    "pogodba", "informacija", "obvestilo", "dopis", "potrdilo", "vabilo",
    "naročilo", "narocilo", "ponudba", "faktura", "jutri", "danes",
}

def topic_tokens(title: str | None) -> set[str]:
    if not title:
        return set()
    tokens = {normalize_name(x) for x in re.findall(r"[\wÀ-ž]{4,}", title, flags=re.UNICODE)}
    return {x for x in tokens if x and x not in TOPIC_STOPWORDS}

def candidate_topic_names(rows: list[dict]) -> list[str]:
    """Return conservative topic candidates shared across at least two providers."""
    token_items: dict[str, set[tuple[str, str]]] = {}
    for row in rows:
        item_id = str(row.get("id"))
        provider = row.get("provider") or ""
        for token in topic_tokens(row.get("title")):
            token_items.setdefault(token, set()).add((provider, item_id))
    candidates = []
    for token, refs in token_items.items():
        providers = {provider for provider, _ in refs}
        if len(refs) >= 2 and len(providers) >= 2:
            candidates.append(token)
    return sorted(candidates)


def topic_anchor_tokens(title: str | None) -> set[str]:
    """Return distinctive, explainable anchors suitable for cross-source topic names."""
    if not title:
        return set()
    anchors = set()
    for raw in re.findall(r"[A-Za-zÀ-ž0-9]{3,}", title):
        normalized = normalize_name(raw)
        if not normalized or normalized in TOPIC_STOPWORDS:
            continue
        if raw.isupper() and len(raw) >= 3:
            anchors.add(normalized)
    return anchors


def candidate_topic_from_shared_person(rows: list[dict]) -> list[str]:
    """Find conservative topic anchors from shared canonical people.

    Prefer a 14-day window when timestamps exist; if Gmail timestamps are unavailable,
    require the same person across Gmail and Calendar and a strong Calendar anchor.
    """
    from datetime import timedelta, timezone

    by_person: dict[str, list[dict]] = {}
    for row in rows:
        for person_id in row.get("person_ids", []) or []:
            by_person.setdefault(str(person_id), []).append(row)

    candidates: set[str] = set()
    for person_rows in by_person.values():
        gmail = [r for r in person_rows if r.get("provider") == "gmail"]
        calendar = [r for r in person_rows if r.get("provider") == "calendar"]
        if not gmail or not calendar:
            continue

        for event in calendar:
            anchors = topic_anchor_tokens(event.get("title"))
            if not anchors:
                continue

            event_time = event.get("occurred_at")
            matched_by_time = False
            if event_time:
                for g in gmail:
                    gmail_time = g.get("occurred_at")
                    if not gmail_time:
                        continue
                    try:
                        gt = gmail_time
                        ct = event_time
                        if isinstance(gt, str):
                            gt = datetime.fromisoformat(gt.replace("Z", "+00:00"))
                        if isinstance(ct, str):
                            ct = datetime.fromisoformat(ct.replace("Z", "+00:00"))
                        if gt.tzinfo is None:
                            gt = gt.replace(tzinfo=timezone.utc)
                        if ct.tzinfo is None:
                            ct = ct.replace(tzinfo=timezone.utc)
                    except (TypeError, ValueError):
                        continue
                    if abs(gt - ct) <= timedelta(days=14):
                        matched_by_time = True
                        break

            # Without Gmail timestamps, only strong Calendar anchors may pass.
            if matched_by_time or not any(g.get("occurred_at") for g in gmail):
                candidates.update(anchors)

    return sorted(candidates)
