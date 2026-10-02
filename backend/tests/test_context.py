from app.context import NormalizedItem, item_key, normalize_email, normalize_name, extract_project_hint


def test_normalize_email_is_provider_neutral():
    assert normalize_email("  Janez.Novak@Example.COM ") == "janez.novak@example.com"


def test_normalize_name_collapses_whitespace():
    assert normalize_name("  Janez   Novak ") == "janez novak"


def test_item_key_is_stable_for_provider_external_id():
    item = NormalizedItem(provider="google_gmail", item_type="message", external_id="abc")
    assert item_key(item) == ("google_gmail", "abc")


def test_same_external_id_different_providers_are_not_duplicates():
    google = NormalizedItem(provider="google_gmail", item_type="message", external_id="abc")
    microsoft = NormalizedItem(provider="microsoft_outlook", item_type="message", external_id="abc")
    assert item_key(google) != item_key(microsoft)


def test_explicit_project_hint_is_normalized():
    project = extract_project_hint("[Project: TALUM] priprava sestanka")
    assert project is not None
    assert project.name == "TALUM"


from app.context import candidate_topic_names, candidate_topic_from_shared_person


def test_candidate_topic_requires_cross_source_presence():
    rows = [
        {"id": "1", "provider": "gmail", "title": "TALUM priprava"},
        {"id": "2", "provider": "calendar", "title": "TALUM sestanek"},
        {"id": "3", "provider": "gmail", "title": "račun sestanek"},
    ]
    assert "talum" in candidate_topic_names(rows)
    assert "sestanek" not in candidate_topic_names(rows)


def test_shared_person_can_surface_strong_calendar_anchor():
    rows = [
        {"id": "g1", "provider": "gmail", "title": "Dopis članom", "occurred_at": "2026-10-01T09:00:00+00:00", "person_ids": ["p1"]},
        {"id": "c1", "provider": "calendar", "title": "VABILO 7. REDNA SEJA UO RKGV", "occurred_at": "2026-10-02T10:00:00+00:00", "person_ids": ["p1"]},
    ]
    assert candidate_topic_from_shared_person(rows) == ["rkvg"]


from datetime import timezone
from app.pipeline import gmail_occurred_at_from_payload


def test_gmail_occurred_at_prefers_internal_date():
    value = gmail_occurred_at_from_payload({
        "internalDate": "1727863200000",
        "payload": {"headers": [{"name": "Date", "value": "Mon, 01 Jan 2020 00:00:00 +0000"}]},
    })
    assert value is not None
    assert value.tzinfo == timezone.utc
    assert value.year == 2024


def test_gmail_occurred_at_falls_back_to_rfc_date():
    value = gmail_occurred_at_from_payload({
        "payload": {"headers": [{"name": "Date", "value": "Mon, 01 Jan 2024 12:34:56 +0000"}]},
    })
    assert value is not None
    assert value.year == 2024
    assert value.hour == 12


def test_normalize_name_matches_common_provider_variants():
    assert normalize_name("  Aleš  Koželjnik. ") == "ales kozeljnik"


def test_normalize_name_does_not_keep_punctuation_as_identity():
    assert normalize_name("Janez-Novak") == "janez novak"


def test_topic_candidate_rejects_invoice_number_and_generic_token():
    rows = [
        {"id": "1", "provider": "gmail", "title": "ŠTEVILKA RAČUN 14001"},
        {"id": "2", "provider": "calendar", "title": "VABILO 14001"},
        {"id": "3", "provider": "gmail", "title": "SEJA priprava"},
        {"id": "4", "provider": "calendar", "title": "SEJA sestanek"},
    ]
    assert "14001" not in candidate_topic_names(rows)
    assert "seja" not in candidate_topic_names(rows)


def test_topic_candidate_keeps_distinctive_shared_anchor():
    rows = [
        {"id": "1", "provider": "gmail", "title": "RKGV priprava"},
        {"id": "2", "provider": "calendar", "title": "VABILO RKGV"},
    ]
    assert candidate_topic_names(rows) == ["rkgv"]
