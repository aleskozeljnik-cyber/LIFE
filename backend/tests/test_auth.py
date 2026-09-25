from app.auth import read_session, sign_session


def test_session_roundtrip():
    token = sign_session("user-123")
    assert read_session(token)["user_id"] == "user-123"
