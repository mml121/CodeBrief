import pytest
from unittest.mock import patch, MagicMock
from code_brief.llm.anthropic import clean_json, parse_response
from code_brief.config import Config


@pytest.fixture
def config():
    return Config(
        github_token="fake-token",
        anthropic_api_key="fake-key",
        anthropic_endpoint="https://fake-endpoint.com",
        repo="test/repo",
        pr_number=1,
    )


# --- clean_json tests ---

def test_clean_json_strips_markdown_fences():
    text = "```json\n{\"summary\": \"test\"}\n```"
    assert clean_json(text) == '{"summary": "test"}'


def test_clean_json_strips_plain_fences():
    text = "```\n{\"summary\": \"test\"}\n```"
    assert clean_json(text) == '{"summary": "test"}'


def test_clean_json_strips_preamble():
    text = "Here is the review:\n\n{\"summary\": \"test\", \"risks\": [], \"focus_areas\": []}"
    result = clean_json(text)
    assert result.startswith("{")


def test_clean_json_leaves_clean_json_alone():
    text = '{"summary": "test"}'
    assert clean_json(text) == '{"summary": "test"}'


# --- parse_response tests ---

def test_parse_response_valid(config):
    text = ('{"summary": "A good PR", "risks": [{"severity": "HIGH", "confidence": 90, "description": "Risk 1"}], '
            '"focus_areas": ["Check migrations"]}')
    summary = parse_response(text, config, pr_title="Test PR")
    assert summary.summary == "A good PR"
    assert len(summary.risks) == 1
    assert summary.risks[0].severity == "HIGH"
    assert summary.risks[0].confidence == 90
    assert summary.focus_areas == ["Check migrations"]


def test_parse_response_invalid_json_returns_fallback(config):
    summary = parse_response("this is not json", config, pr_title="Test PR")
    assert "unable to parse" in summary.summary.lower()
    assert summary.risks == []


def test_parse_response_missing_fields_uses_defaults(config):
    text = '{"summary": "Minimal response"}'
    summary = parse_response(text, config)
    assert summary.summary == "Minimal response"
    assert summary.risks == []
    assert summary.focus_areas == []


def test_parse_response_skips_risks_with_no_description(config):
    text = ('{"summary": "Test", "risks": [{"severity": "HIGH", "confidence": 90, "description": ""}, {"severity": '
            '"LOW", "confidence": 50, "description": "Real risk"}]}')
    summary = parse_response(text, config)
    assert len(summary.risks) == 1
    assert summary.risks[0].description == "Real risk"


def test_parse_response_sets_pr_title(config):
    text = '{"summary": "Test", "risks": [], "focus_areas": []}'
    summary = parse_response(text, config, pr_title="My PR")
    assert summary.title == "My PR"


def test_parse_response_sets_repo_and_pr_number(config):
    text = '{"summary": "Test", "risks": [], "focus_areas": []}'
    summary = parse_response(text, config)
    assert summary.repo == "test/repo"
    assert summary.pr_number == 1
