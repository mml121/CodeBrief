import os

from unidiff import PatchSet
from code_brief.config import Config
from github import Github

def get_raw_diff(config: Config) -> str:
    client = Github(config.github_token)
    repo = client.get_repo(config.repo)
    pr = repo.get_pull(config.pr_number)

    diff_text = ""
    for file in pr.get_files():
        if file.patch:
            diff_text += f"--- a/{file.filename}\n"
            diff_text += f"+++ b/{file.filename}\n"
            diff_text += file.patch + "\n"

    return diff_text

def parse_diff(raw_diff: str) -> PatchSet:
    return PatchSet(raw_diff)

def get_changed_files(config: Config) -> list:
    raw = get_raw_diff(config)
    patch = parse_diff(raw)

    files = []
    for patched_file in patch:
        files.append({
            "filename": patched_file.path,
            "additions": patched_file.added,
            "deletions": patched_file.removed,
            "diff": str(patched_file)
        })

    return files