from app.extraction import _mock_extract


def test_mock_extracts_actionable_invoice():
    result = _mock_extract(
        "Subject: Please pay invoice by today\nAmount: €12.345,67",
        "email",
    )
    assert result is not None
    assert result.amount == 12345.67
    assert result.currency == "EUR"
    assert result.priority == "high"
    assert result.category == "financial"
    assert result.confidence == 0.55


def test_mock_ignores_non_actionable_email():
    assert _mock_extract("Subject: FYI\nHere is the newsletter.", "email") is None


def test_candidate_prefilter_allows_actionable_mail():
    from app.extraction import is_ai_candidate
    assert is_ai_candidate("Subject: Please approve contract by Friday", "email")


def test_candidate_prefilter_drops_clear_newsletter():
    from app.extraction import is_ai_candidate
    assert not is_ai_candidate("Subject: Weekly newsletter\nHere are the latest stories.", "email")


def test_json_recovery_handles_fenced_payload():
    from app.extraction import _extract_json
    assert _extract_json("```json\n{\"title\":\"Pay invoice\"}\n```") == {"title": "Pay invoice"}
