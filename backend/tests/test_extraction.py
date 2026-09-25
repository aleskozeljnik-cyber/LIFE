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
