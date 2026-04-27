from app.core.application import create_app


def test_app_builds() -> None:
    app = create_app()
    assert app.title == "Wandrix API"
