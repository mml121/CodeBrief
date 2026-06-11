from unidiff import PatchSet
from github.PullRequest import PullRequest as GithubPR

SKIP_EXTENSIONS = {
    # binary
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".exe", ".dll", ".bin",
    # lock files
    "package-lock.json", "poetry.lock", "Pipfile.lock", "yarn.lock",
    # generated / minified
    ".min.js", ".min.css", ".pyc",
}


def should_skip(filename: str) -> tuple[bool, str]:
    for ext in SKIP_EXTENSIONS:
        if filename.endswith(ext):
            return True, f"skipped — {ext} file"
    return False, ""


def get_raw_diff(pr: GithubPR) -> tuple[str, list[dict]]:
    diff_text = ""
    skipped = []

    for file in pr.get_files():
        skip, reason = should_skip(file.filename)
        if skip:
            skipped.append({"filename": file.filename, "reason": reason})
            continue

        if not file.patch:
            skipped.append({"filename": file.filename, "reason": "skipped — patch unavailable"})
            continue

        diff_text += f"--- a/{file.filename}\n"
        diff_text += f"+++ b/{file.filename}\n"
        diff_text += file.patch + "\n"

    return diff_text, skipped


def parse_diff(raw_diff: str) -> PatchSet:
    return PatchSet(raw_diff)


def get_changed_files(pr: GithubPR) -> tuple[list, list[dict]]:
    raw, skipped = get_raw_diff(pr)

    if not raw:
        return [], skipped

    patch = parse_diff(raw)

    files = []
    for patched_file in patch:
        files.append({
            "filename": patched_file.path,
            "additions": patched_file.added,
            "deletions": patched_file.removed,
            "diff": str(patched_file)
        })

    return files, skipped