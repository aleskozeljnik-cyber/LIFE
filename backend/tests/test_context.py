from app.context import NormalizedItem, item_key, normalize_email, normalize_name


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
