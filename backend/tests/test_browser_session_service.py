from app.schemas.browser_session import BrowserSessionCreateResponse


def test_browser_session_response_shape() -> None:
    response = BrowserSessionCreateResponse.model_validate(
        {
            "browser_session_id": "bs_test",
            "user_id": "user_test",
            "timezone": "Europe/London",
            "locale": "en-GB",
            "status": "active",
            "created_at": "2026-04-18T10:00:00Z",
        }
    )

    assert response.browser_session_id == "bs_test"
    assert response.status == "active"
