from app.schemas.auth import AuthenticatedUser


def test_authenticated_user_schema() -> None:
    user = AuthenticatedUser(id="user_123", email="hello@example.com")

    assert user.id == "user_123"
    assert user.email == "hello@example.com"

