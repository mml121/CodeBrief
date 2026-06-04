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
    model: str
    email_sender: str = ""
    email_password: str = ""
    email_smtp_host: str = ""
    email_smtp_port: int = 465


def load_config(repo: str, pr_number: int, model: str = "claude-3-haiku") -> Config:
    github_token = os.getenv("GITHUB_TOKEN")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    anthropic_endpoint = os.getenv("ANTHROPIC_ENDPOINT")

    if not github_token:
        raise ValueError("GITHUB_TOKEN missing from .env file.")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY missing from .env file.")
    if not anthropic_endpoint:
        raise ValueError("ANTHROPIC_ENDPOINT missing from .env file.")

    return Config(
        github_token=github_token,
        anthropic_api_key=anthropic_api_key,
        anthropic_endpoint=anthropic_endpoint,
        repo=repo,
        pr_number=pr_number,
        model=model,
        email_sender=os.getenv("EMAIL_SENDER") or "",
        email_password=os.getenv("EMAIL_PASSWORD") or "",
        email_smtp_host=os.getenv("EMAIL_SMTP_HOST") or ""
    )
