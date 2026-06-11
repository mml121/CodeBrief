from code_brief.llm.prompt import build_prompt


def make_file(filename: str, additions: int = 5, deletions: int = 2) -> dict:
    return {
        "filename": filename,
        "additions": additions,
        "deletions": deletions,
        "diff": "+some added line\n-some removed line\n"
    }


# --- build_prompt tests ---

def test_build_prompt_contains_file_count():
    files = [make_file("main.py"), make_file("utils.py")]
    prompt = build_prompt(files)
    assert "2 changed files" in prompt


def test_build_prompt_contains_filenames():
    files = [make_file("main.py"), make_file("utils.py")]
    prompt = build_prompt(files)
    assert "main.py" in prompt
    assert "utils.py" in prompt


def test_build_prompt_contains_pr_title():
    files = [make_file("main.py")]
    prompt = build_prompt(files, pr_title="feat: add login")
    assert "feat: add login" in prompt


def test_build_prompt_no_title_skips_title_line():
    files = [make_file("main.py")]
    prompt = build_prompt(files, pr_title="")
    assert "PR Title:" not in prompt


def test_build_prompt_contains_diff_content():
    files = [make_file("main.py")]
    prompt = build_prompt(files)
    assert "+some added line" in prompt
    assert "-some removed line" in prompt


def test_build_prompt_contains_additions_deletions():
    files = [make_file("main.py", additions=10, deletions=3)]
    prompt = build_prompt(files)
    assert "+10" in prompt
    assert "-3" in prompt


def test_build_prompt_empty_files():
    prompt = build_prompt([])
    assert "0 changed files" in prompt
