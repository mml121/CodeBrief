from unittest.mock import MagicMock

from typer.testing import CliRunner

from code_brief.cli import app

runner = CliRunner()


def test_invalid_output_mode_is_rejected():
    result = runner.invoke(app, ["--pr", "1", "--repo", "owner/repo", "--output", "bad"])

    assert result.exit_code != 0
    assert "Invalid value" in result.output


def test_empty_diff_skips_llm(monkeypatch):
    pull = MagicMock()
    pull.title = "Test PR"
    pull.additions = 0
    pull.deletions = 0

    monkeypatch.setattr("code_brief.cli.load_config", lambda repo, pr_number: MagicMock())
    monkeypatch.setattr("code_brief.cli.get_pr", lambda config: pull)
    monkeypatch.setattr("code_brief.cli.get_changed_files", lambda pr: ([], []))
    call_claude = MagicMock()
    monkeypatch.setattr("code_brief.cli.call_claude", call_claude)

    result = runner.invoke(app, ["--pr", "1", "--repo", "owner/repo"])

    assert result.exit_code == 0
    assert "No reviewable diff content found" in result.output
    call_claude.assert_not_called()
