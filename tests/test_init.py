from unittest.mock import patch, MagicMock
from code_brief.init import validate_github_token, validate_anthropic_connection


# --- test_github_token tests ---

def test_github_token_valid():
    mock_user = MagicMock()
    mock_user.login = "mohammed"
    with patch("code_brief.init.Github") as mock_github:
        mock_github.return_value.get_user.return_value = mock_user
        ok, msg = validate_github_token("fake-token")
        assert ok is True
        assert msg == "mohammed"


def test_github_token_invalid():
    from github.GithubException import GithubException
    with patch("code_brief.init.Github") as mock_github:
        mock_github.return_value.get_user.side_effect = GithubException(401, "Bad credentials")
        ok, msg = validate_github_token("bad-token")
        assert ok is False


# --- test_anthropic_connection tests ---

def test_anthropic_connection_valid():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    with patch("code_brief.init.httpx.post") as mock_post:
        mock_post.return_value = mock_response
        ok, msg = validate_anthropic_connection("fake-key", "https://fake-endpoint.com")
        assert ok is True


def test_anthropic_connection_invalid():
    with patch("code_brief.init.httpx.post") as mock_post:
        mock_post.side_effect = Exception("Connection refused")
        ok, msg = validate_anthropic_connection("bad-key", "https://fake-endpoint.com")
        assert ok is False
        assert "Connection refused" in msg