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
    assert candidate_topic_from_shared_person(rows) == ["rkgv"]


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


def test_life_item_evidence_is_source_backed_shape():
    # Evidence must identify the underlying provider/source rather than only
    # repeating a generated Life Item summary.
    row = {
        "id": "obligation-1",
        "provider": "gmail",
        "source_title": "Re: TALUM",
        "sender": "person@example.com",
        "due_at": None,
    }
    from app.intelligence import _evidence
    evidence = _evidence([row])
    assert evidence == [{
        "obligation_id": "obligation-1",
        "provider": "gmail",
        "title": "Re: TALUM",
        "sender": "person@example.com",
        "due_at": None,
        "relationship": "direct_source",
    }]


def test_decide_action_type_prefers_explicit_source_intent():
    from app.intelligence import _action_type, _next_action
    rows = [{
        "id": "1",
        "provider": "gmail",
        "title": "Prosimo odgovor do jutri",
        "summary": "Potrebujemo vaš odgovor na ponudbo.",
        "sender": "person@example.com",
        "source_title": "Prosimo odgovor do jutri",
    }]
    assert _action_type(rows) == "reply"
    assert _next_action(rows) == "Odgovori na zahtevo iz povezanega sporočila."


def test_decide_action_type_does_not_turn_generic_meeting_into_reply():
    from app.intelligence import _action_type, _next_action
    rows = [{
        "id": "1",
        "provider": "calendar",
        "title": "Sestanek TALUM",
        "summary": "Jutri ob 10:00.",
        "source_title": "Sestanek TALUM",
    }]
    assert _action_type(rows) == "review"
    assert _next_action(rows) == "Preglej zahtevano vsebino in uredi naslednji korak."


def test_decide_filters_real_promotional_and_notification_noise():
    from app.intelligence import _noise
    assert _noise({"title": "Super prihranki za vikend - izkoristite jih!", "summary": "SPAR e-novičke", "category": "financial"})
    assert _noise({"title": "We double your winnings!", "summary": "newsletter bet-at-home Bet now!", "category": "financial"})
    assert _noise({"title": "Head of Market & Product Design", "summary": "LinkedIn Job Alert", "category": "work"})
    assert _noise({"title": "Express One obvestilo o dostavi", "summary": "tracking information", "category": "work"})


def test_decide_does_not_promote_generic_invoice_noun_without_action():
    from app.intelligence import _actionability
    row = {
        "provider": "gmail",
        "title": "ŠTEVILKA RAČUN 14001",
        "summary": "V prilogi vam pošiljamo račun v pdf obliki.",
        "priority": "medium",
        "due_at": None,
    }
    assert _actionability(row) < 0.55


def test_decide_keeps_explicit_action_request_actionable():
    from app.intelligence import _actionability
    row = {
        "provider": "gmail",
        "title": "Action required: LEI renewal",
        "summary": "Please renew the LEI before the deadline.",
        "priority": "medium",
        "due_at": None,
    }
    assert _actionability(row) >= 0.55

def test_teams_source_is_linked_before_context_persistence_and_prefilter():
    import inspect
    from app.pipeline import sync_teams_and_extract

    source = inspect.getsource(sync_teams_and_extract)
    source_pos = source.index("select id from sources")
    context_pos = source.index("_persist_context_item")
    prefilter_pos = source.index("is_ai_candidate")
    assert source_pos < context_pos < prefilter_pos
