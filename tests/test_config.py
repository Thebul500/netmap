"""Tests for configuration module."""


from netmap.config import Settings, settings


def test_settings_defaults():
    """Default settings are applied when no env vars set."""
    s = Settings()
    assert s.database_url == "postgresql+asyncpg://localhost:5432/netmap"
    assert len(s.secret_key) == 64  # token_hex(32) produces 64-char hex string
    assert s.access_token_expire_minutes == 30
    assert s.debug is False


def test_settings_from_env(monkeypatch):
    """Settings can be overridden via NETMAP_ prefixed env vars."""
    monkeypatch.setenv("NETMAP_DATABASE_URL", "postgresql+asyncpg://user:pw@db:5432/test")
    monkeypatch.setenv("NETMAP_SECRET_KEY", "override-from-env")
    monkeypatch.setenv("NETMAP_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("NETMAP_DEBUG", "true")

    s = Settings()
    assert s.database_url == "postgresql+asyncpg://user:pw@db:5432/test"
    assert s.secret_key == "override-from-env"
    assert s.access_token_expire_minutes == 60
    assert s.debug is True


def test_module_level_settings_instance():
    """Module-level settings singleton exists with correct type."""
    assert isinstance(settings, Settings)
