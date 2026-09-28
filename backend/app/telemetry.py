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
                "messages_found", "events_found", "obligations_created",
                "messages_skipped", "events_skipped", "prefilter_filtered",
                "messages_sent_to_ai",
            )
            if key in item
        }
    return {"result": safe_result}
