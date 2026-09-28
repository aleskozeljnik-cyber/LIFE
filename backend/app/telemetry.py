from psycopg.types.json import Jsonb

from .db import get_connection

ALLOWED_ACTIONS = {
    "authorization_connected",
    "authorization_revoked",
    "authorization_first_live",
    "sync",
    "sync_error",
    "calendar_read_error",
}


def sanitize_metadata(metadata: dict | None) -> dict:
    metadata = metadata or {}
    allowed = {
        "source_id",
        "obligation_id",
        "provider",
        "model",
        "status",
        "status_code",
        "message_count",
        "event_count",
        "messages_found",
        "messages_skipped",
        "prefilter_filtered",
        "messages_sent_to_ai",
        "obligations_created",
        "events_found",
        "events_skipped",
        "execution_ms",
    }
    result = {}
    for key in allowed:
        value = metadata.get(key)
        if isinstance(value, (str, int, float, bool)) and not isinstance(value, str) or isinstance(value, str):
            result[key] = value
    return result


def safe_sync_metadata(result: dict) -> dict:
    """Allow-list only numeric/technical sync telemetry; never source content."""
    safe_result = {}
    for source_name in ("gmail", "calendar"):
        item = result.get(source_name)
        if not isinstance(item, dict):
            continue
        safe_result[source_name] = {
            key: int(item[key])
            for key in (
                "messages_found",
                "events_found",
                "obligations_created",
                "messages_skipped",
                "events_skipped",
                "prefilter_filtered",
                "messages_sent_to_ai",
            )
            if key in item
        }
    return safe_result


async def record_usage_event(user_id: str, action: str, metadata: dict | None = None) -> None:
    if action not in ALLOWED_ACTIONS:
        return
    safe = sanitize_metadata(metadata)
    try:
        async with await get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "insert into usage_logs (user_id,action,metadata) values (%s,%s,%s)",
                    (user_id, action, Jsonb(safe)),
                )
            await conn.commit()
    except Exception:
        # Telemetry is non-blocking by design.
        return
