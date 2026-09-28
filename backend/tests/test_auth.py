from app.auth import new_state, read_session, read_state, sign_session


def test_session_roundtrip():
    token = sign_session("user-123")
    assert read_session(token)["user_id"] == "user-123"


def test_oauth_state_roundtrip():
    state = new_state()
    assert read_state(state)["kind"] == "oauth"
