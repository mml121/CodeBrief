from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path
import os

CONFIG_DIR = Path.home() / ".codebrief"
ENV_PATH = CONFIG_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {value!r}") from exc


@dataclass
class Config:
    github_token: str
    anthropic_api_key: str
    anthropic_endpoint: str
    repo: str
    pr_number: int
    model: str = "claude-3-haiku"
    max_tokens_per_chunk: int = 6000
    llm_max_tokens: int = 1024
    api_timeout: float = 60.0
    max_retries: int = 3
    retry_wait_min: int = 2
    retry_wait_max: int = 10
    email_sender: str = ""
    email_password: str = ""
    email_smtp_host: str = ""
    email_smtp_port: int = 465


def load_config(repo: str, pr_number: int) -> Config:
    github_token = os.getenv("GITHUB_TOKEN") or ""
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY") or ""
    anthropic_endpoint = os.getenv("ANTHROPIC_ENDPOINT") or ""

    if not github_token:
        raise ValueError(
            f"GITHUB_TOKEN is missing. Run 'code-brief init' to set up CodeBrief.\n"
            f"Config file expected at: {ENV_PATH}"
        )
    if not anthropic_api_key:
        raise ValueError(
            f"ANTHROPIC_API_KEY is missing. Run 'code-brief init' to set up CodeBrief.\n"
            f"Config file expected at: {ENV_PATH}"
        )
    if not anthropic_endpoint:
        raise ValueError(
            f"ANTHROPIC_ENDPOINT is missing. Run 'code-brief init' to set up CodeBrief.\n"
            f"Config file expected at: {ENV_PATH}"
        )

    return Config(
        github_token=github_token,
        anthropic_api_key=anthropic_api_key,
        anthropic_endpoint=anthropic_endpoint,
        repo=repo,
        pr_number=pr_number,
        model=os.getenv("ANTHROPIC_MODEL") or "claude-3-haiku",
        max_tokens_per_chunk=_get_int("MAX_TOKENS_PER_CHUNK", 6000),
        llm_max_tokens=_get_int("LLM_MAX_TOKENS", 1024),
        api_timeout=_get_float("API_TIMEOUT", 60.0),
        max_retries=_get_int("MAX_RETRIES", 3),
        retry_wait_min=_get_int("RETRY_WAIT_MIN", 2),
        retry_wait_max=_get_int("RETRY_WAIT_MAX", 10),
        email_sender=os.getenv("EMAIL_SENDER") or "",
        email_password=os.getenv("EMAIL_PASSWORD") or "",
        email_smtp_host=os.getenv("EMAIL_SMTP_HOST") or "",
        email_smtp_port=_get_int("EMAIL_SMTP_PORT", 465),
    )
