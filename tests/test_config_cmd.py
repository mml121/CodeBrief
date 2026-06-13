import pytest
from typer.testing import CliRunner
from dotenv import dotenv_values
from code_brief.config_cmd import config_app
import code_brief.config_cmd as config_cmd_module

runner = CliRunner()


@pytest.fixture
def env_file(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("GITHUB_TOKEN=fake\n")
    monkeypatch.setattr(config_cmd_module, "ENV_PATH", path)
    return path


@pytest.fixture
def missing_env_file(tmp_path, monkeypatch):
    path = tmp_path / "does_not_exist" / ".env"
    monkeypatch.setattr(config_cmd_module, "ENV_PATH", path)
    return path


# --- show ---

def test_show_no_config_file(missing_env_file):
    result = runner.invoke(config_app, ["show"])
    assert result.exit_code == 1
    assert "No configuration found" in result.output


def test_show_displays_defaults(env_file):
    result = runner.invoke(config_app, ["show"])
    assert result.exit_code == 0
    assert "ANTHROPIC_MODEL" in result.output
    assert "claude-3-haiku" in result.output


def test_show_displays_custom_value(env_file):
    env_file.write_text("GITHUB_TOKEN=fake\nANTHROPIC_MODEL=claude-3-5-sonnet\n")
    result = runner.invoke(config_app, ["show"])
    assert result.exit_code == 0
    assert "claude-3-5-sonnet" in result.output


# --- set ---

def test_set_valid_key(env_file):
    result = runner.invoke(config_app, ["set", "ANTHROPIC_MODEL", "claude-3-5-sonnet"])
    assert result.exit_code == 0
    assert "ANTHROPIC_MODEL set to" in result.output

    values = dotenv_values(env_file)
    assert values["ANTHROPIC_MODEL"] == "claude-3-5-sonnet"


def test_set_is_case_insensitive(env_file):
    result = runner.invoke(config_app, ["set", "anthropic_model", "claude-3-5-sonnet"])
    assert result.exit_code == 0

    values = dotenv_values(env_file)
    assert values["ANTHROPIC_MODEL"] == "claude-3-5-sonnet"


def test_set_invalid_key(env_file):
    result = runner.invoke(config_app, ["set", "RANDOM_KEY", "value"])
    assert result.exit_code == 1
    assert "Unknown setting" in result.output


def test_set_rejects_invalid_numeric_value(env_file):
    result = runner.invoke(config_app, ["set", "MAX_RETRIES", "abc"])
    assert result.exit_code != 0
    assert "MAX_RETRIES must be an integer" in result.output


def test_set_rejects_non_positive_numeric_value(env_file):
    result = runner.invoke(config_app, ["set", "API_TIMEOUT", "0"])
    assert result.exit_code != 0
    assert "API_TIMEOUT must be greater than 0" in result.output


def test_set_no_config_file(missing_env_file):
    result = runner.invoke(config_app, ["set", "ANTHROPIC_MODEL", "claude-3-5-sonnet"])
    assert result.exit_code == 1
    assert "No configuration found" in result.output


# --- reset ---

def test_reset_valid_key(env_file):
    env_file.write_text("GITHUB_TOKEN=fake\nANTHROPIC_MODEL=claude-3-5-sonnet\n")
    result = runner.invoke(config_app, ["reset", "ANTHROPIC_MODEL"])
    assert result.exit_code == 0
    assert "reset to default" in result.output

    values = dotenv_values(env_file)
    assert values["ANTHROPIC_MODEL"] == "claude-3-haiku"


def test_reset_invalid_key(env_file):
    result = runner.invoke(config_app, ["reset", "RANDOM_KEY"])
    assert result.exit_code == 1
    assert "Unknown setting" in result.output


def test_reset_no_config_file(missing_env_file):
    result = runner.invoke(config_app, ["reset", "ANTHROPIC_MODEL"])
    assert result.exit_code == 1
    assert "No configuration found" in result.output
