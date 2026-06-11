from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()


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
    email_smtp_port: int = 587
    slack_webhook_url: str = ""
    slack_channel: str = ""


def load_config(repo: str, pr_number: int) -> Config:
    github_token = os.getenv("GITHUB_TOKEN") or ""
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY") or ""
    anthropic_endpoint = os.getenv("ANTHROPIC_ENDPOINT") or ""

    if not github_token:
        raise ValueError("GITHUB_TOKEN is missing from your .env file")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is missing from your .env file")
    if not anthropic_endpoint:
        raise ValueError("ANTHROPIC_ENDPOINT is missing from your .env file")

    return Config(
        github_token=github_token,
        anthropic_api_key=anthropic_api_key,
        anthropic_endpoint=anthropic_endpoint,
        repo=repo,
        pr_number=pr_number,
        model=os.getenv("ANTHROPIC_MODEL") or "claude-3-haiku",
        max_tokens_per_chunk=int(os.getenv("MAX_TOKENS_PER_CHUNK") or 6000),
        llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS") or 1024),
        api_timeout=float(os.getenv("API_TIMEOUT") or 60.0),
        max_retries=int(os.getenv("MAX_RETRIES") or 3),
        retry_wait_min=int(os.getenv("RETRY_WAIT_MIN") or 2),
        retry_wait_max=int(os.getenv("RETRY_WAIT_MAX") or 10),
        email_sender=os.getenv("EMAIL_SENDER") or "",
        email_password=os.getenv("EMAIL_PASSWORD") or "",
        email_smtp_host=os.getenv("EMAIL_SMTP_HOST") or "",
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL") or "",
        slack_channel=os.getenv("SLACK_CHANNEL") or "",
    )