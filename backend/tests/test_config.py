import pytest

from app.core import config


CORE_PRODUCTION_ENV_VARS = [
    "FRONTEND_ORIGINS",
    "FRONTEND_ORIGIN",
    "DATABASE_URL",
    "SUPABASE_URL",
    "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_SECRET_KEY",
    "CODEX_LB_BASE_URL",
    "CODEX_LB_API_KEY",
]


@pytest.fixture(autouse=True)
def clear_settings_cache():
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def test_development_cors_origins_include_localhost_alias(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000, https://testing.wandrix.example",
    )

    settings = config.get_settings()

    assert settings.environment == "development"
    assert settings.frontend_origins == (
        "http://localhost:3000",
        "https://testing.wandrix.example",
        "http://127.0.0.1:3000",
    )


def test_production_config_rejects_missing_core_values(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    for name in CORE_PRODUCTION_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError) as error:
        config.get_settings()

    message = str(error.value)
    assert "Production backend configuration is incomplete" in message
    assert "DATABASE_URL" in message
    assert "FRONTEND_ORIGINS" in message


def test_production_config_accepts_explicit_core_values(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("FRONTEND_ORIGINS", "https://app.wandrix.example")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://wandrix:secret@db.wandrix.internal:5432/wandrix",
    )
    monkeypatch.setenv("SUPABASE_URL", "https://wandrix.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_key")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_key")
    monkeypatch.setenv("CODEX_LB_BASE_URL", "https://llm.wandrix.example/v1")
    monkeypatch.setenv("CODEX_LB_API_KEY", "codex_lb_key")

    settings = config.get_settings()

    assert settings.environment == "production"
    assert settings.frontend_origins == ("https://app.wandrix.example",)
