from pathlib import Path

from web_lead_automation.config import Settings


def test_settings_have_safe_defaults(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_PLACES_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("GOOGLE_PLACES_PAGE_SIZE", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("LEAD_DB_PATH", raising=False)
    monkeypatch.delenv("DEMO_OUTPUT_PATH", raising=False)
    monkeypatch.delenv("NETLIFY_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("NETLIFY_SITE_ID", raising=False)
    monkeypatch.delenv("NETLIFY_TIMEOUT_SECONDS", raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.google_places_api_key is None
    assert settings.google_places_timeout_seconds == 10.0
    assert settings.google_places_page_size == 20
    assert settings.openai_api_key is None
    assert settings.openai_model == "gpt-5.6-luna"
    assert settings.openai_timeout_seconds == 30.0
    assert settings.lead_db_path == Path("data/leads.sqlite3")
    assert settings.demo_output_path == Path("data/demos")
    assert settings.netlify_auth_token is None
    assert settings.netlify_site_id is None
    assert settings.netlify_timeout_seconds == 30.0


def test_settings_read_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_PLACES_TIMEOUT_SECONDS", "15")
    monkeypatch.setenv("GOOGLE_PLACES_PAGE_SIZE", "8")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.6-terra")
    monkeypatch.setenv("OPENAI_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("LEAD_DB_PATH", "tmp/test-leads.sqlite3")
    monkeypatch.setenv("DEMO_OUTPUT_PATH", "tmp/demos")
    monkeypatch.setenv("NETLIFY_AUTH_TOKEN", "netlify-token")
    monkeypatch.setenv("NETLIFY_SITE_ID", "netlify-site")
    monkeypatch.setenv("NETLIFY_TIMEOUT_SECONDS", "50")

    settings = Settings(_env_file=None)

    assert settings.app_env == "test"
    assert settings.log_level == "DEBUG"
    assert settings.google_places_api_key == "test-key"
    assert settings.google_places_timeout_seconds == 15.0
    assert settings.google_places_page_size == 8
    assert settings.openai_api_key == "openai-test-key"
    assert settings.openai_model == "gpt-5.6-terra"
    assert settings.openai_timeout_seconds == 45.0
    assert settings.lead_db_path == Path("tmp/test-leads.sqlite3")
    assert settings.demo_output_path == Path("tmp/demos")
    assert settings.netlify_auth_token == "netlify-token"
    assert settings.netlify_site_id == "netlify-site"
    assert settings.netlify_timeout_seconds == 50.0
