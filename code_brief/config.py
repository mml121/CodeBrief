from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class Config:
    github_token: str
    repo : str
    pr_number : int

def load_config(repo: str, pr_number: int) -> Config:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN missing from .env file.")
    return Config(github_token=token, repo=repo, pr_number=pr_number)