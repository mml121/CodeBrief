from unidiff import PatchSet
from github.PullRequest import PullRequest as GithubPR
from code_brief.logger import get_logger

logger = get_logger("code_brief.diff")

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".exe", ".dll", ".bin",
    "package-lock.json", "poetry.lock", "Pipfile.lock", "yarn.lock",
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
            logger.debug(f"Skipping {file.filename} — {reason}")
            skipped.append({"filename": file.filename, "reason": reason})
            continue

        if not file.patch:
            logger.warning(f"No patch available for {file.filename} — skipping")
            skipped.append({"filename": file.filename, "reason": "patch unavailable"})
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
        logger.warning("No diff content found — all files were skipped or had no patch")
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

    logger.info(f"{len(files)} files parsed, {len(skipped)} skipped")
    return files, skipped
