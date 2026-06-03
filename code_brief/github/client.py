from github import Github
from code_brief.config import Config


def get_pr(config: Config):
    client = Github(config.github_token)
    repo = client.get_repo(config.repo)
    pr = repo.get_pull(config.pr_number)
    return pr
