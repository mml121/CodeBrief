import pytest

from code_brief.config import load_config


def set_required_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "github-token")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")
    monkeypatch.setenv("ANTHROPIC_ENDPOINT", "https://example.com")


def test_load_config_reads_email_smtp_port(monkeypatch):
    set_required_env(monkeypatch)
    monkeypatch.setenv("EMAIL_SMTP_PORT", "587")

    config = load_config(repo="owner/repo", pr_number=3)

    assert config.email_smtp_port == 587


def test_load_config_rejects_invalid_integer(monkeypatch):
    set_required_env(monkeypatch)
    monkeypatch.setenv("MAX_RETRIES", "abc")

    with pytest.raises(ValueError, match="MAX_RETRIES must be an integer"):
        load_config(repo="owner/repo", pr_number=3)


def test_load_config_rejects_invalid_float(monkeypatch):
    set_required_env(monkeypatch)
    monkeypatch.setenv("API_TIMEOUT", "slow")

    with pytest.raises(ValueError, match="API_TIMEOUT must be a number"):
        load_config(repo="owner/repo", pr_number=3)
