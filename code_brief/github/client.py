from github import Github
import logging
from code_brief.config import Config

logging.getLogger("github").setLevel(logging.WARNING)


def get_pr(config: Config):
    client = Github(config.github_token)
    repo = client.get_repo(config.repo)
    pr = repo.get_pull(config.pr_number)
    return pr
