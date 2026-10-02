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
