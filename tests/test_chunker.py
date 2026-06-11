import pytest  # noqa: F401
from code_brief.llm.chunker import count_tokens, chunk_files, needs_chunking
from code_brief.config import Config


@pytest.fixture
def config():
    return Config(
        github_token="fake-token",
        anthropic_api_key="fake-key",
        anthropic_endpoint="https://fake-endpoint.com",
        repo="test/repo",
        pr_number=1,
        max_tokens_per_chunk=100
    )


def make_file(filename: str, diff: str) -> dict:
    return {
        "filename": filename,
        "additions": diff.count("+"),
        "deletions": diff.count("-"),
        "diff": diff
    }


# --- count_tokens tests ---

def test_count_tokens_empty_string():
    assert count_tokens("") == 0


def test_count_tokens_returns_int():
    assert isinstance(count_tokens("hello world"), int)


def test_count_tokens_longer_text_has_more_tokens():
    short = count_tokens("hello")
    long = count_tokens("hello world this is a longer sentence")
    assert long > short


# --- needs_chunking tests ---

def test_needs_chunking_small_diff(config):
    files = [make_file("main.py", "small diff")]
    assert needs_chunking(files, config) is False


def test_needs_chunking_large_diff(config):
    big_diff = "x " * 200
    files = [make_file("main.py", big_diff)]
    assert needs_chunking(files, config) is True


def test_needs_chunking_empty_files(config):
    assert needs_chunking([], config) is False


# --- chunk_files tests ---

def test_chunk_files_single_small_file(config):
    files = [make_file("main.py", "small diff")]
    chunks = chunk_files(files, config)
    assert len(chunks) == 1
    assert chunks[0]["files"][0]["filename"] == "main.py"


def test_chunk_files_splits_large_diff(config):
    big_diff = "x " * 200
    files = [
        make_file("file1.py", big_diff),
        make_file("file2.py", big_diff),
    ]
    chunks = chunk_files(files, config)
    assert len(chunks) == 2


def test_chunk_files_groups_small_files(config):
    files = [
        make_file("file1.py", "tiny"),
        make_file("file2.py", "tiny"),
        make_file("file3.py", "tiny"),
    ]
    chunks = chunk_files(files, config)
    assert len(chunks) == 1
    assert len(chunks[0]["files"]) == 3


def test_chunk_files_empty_list(config):
    chunks = chunk_files([], config)
    assert chunks == []