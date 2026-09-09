from pathlib import Path

from web_lead_automation.config import Settings


def test_settings_have_safe_defaults(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
    monkeypatch.delenv("LEAD_DB_PATH", raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.google_places_api_key is None
    assert settings.lead_db_path == Path("data/leads.sqlite3")


def test_settings_read_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test-key")
    monkeypatch.setenv("LEAD_DB_PATH", "tmp/test-leads.sqlite3")

    settings = Settings(_env_file=None)

    assert settings.app_env == "test"
    assert settings.log_level == "DEBUG"
    assert settings.google_places_api_key == "test-key"
    assert settings.lead_db_path == Path("tmp/test-leads.sqlite3")
