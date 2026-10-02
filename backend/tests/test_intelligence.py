from app.intelligence import _context_evidence_links


def test_context_evidence_links_are_metadata_only_and_explainable():
    rows = [{
        "id": "ob-1",
        "context_item_id": "ctx-1",
        "context_external_id": "gmail-1",
        "external_id": "gmail-1",
        "provider": "gmail",
        "source_title": "Project update",
        "title": "Project update",
        "body": "must never be copied into evidence",
    }]

    obligation_links = _context_evidence_links(rows)
    assert obligation_links == [{
        "context_item_id": "ctx-1",
        "obligation_id": "ob-1",
        "life_item_id": None,
        "evidence_type": "obligation_source",
        "source_ref": {
            "provider": "gmail",
            "external_id": "gmail-1",
            "title": "Project update",
        },
    }]
    assert "body" not in obligation_links[0]["source_ref"]

    life_links = _context_evidence_links(rows, "life-1")
    assert life_links[0]["life_item_id"] == "life-1"
    assert life_links[0]["evidence_type"] == "life_item_source"


def test_context_evidence_links_skip_unresolved_source_items():
    rows = [{"id": "ob-1", "provider": "gmail", "title": "No context row"}]
    assert _context_evidence_links(rows) == []
