import pytest
from unittest.mock import MagicMock
from code_brief.github.diff import get_changed_files, should_skip, get_raw_diff


# --- should_skip tests ---

def test_should_skip_png():
    skip, reason = should_skip("image.png")
    assert skip is True
    assert "png" in reason


def test_should_skip_lock_file():
    skip, reason = should_skip("package-lock.json")
    assert skip is True


def test_should_skip_minified_js():
    skip, reason = should_skip("app.min.js")
    assert skip is True


def test_should_not_skip_python_file():
    skip, reason = should_skip("main.py")
    assert skip is False
    assert reason == ""


def test_should_not_skip_regular_json():
    skip, reason = should_skip("config.json")
    assert skip is False


# --- get_changed_files tests ---

VALID_DIFF = """--- a/main.py
+++ b/main.py
@@ -1,3 +1,4 @@
 line1
 line2
 line3
+print('hello')
"""


def make_mock_file(filename, patch=None):
    f = MagicMock()
    f.filename = filename
    f.patch = patch
    return f


def test_get_changed_files_normal():
    mock_pr = MagicMock()
    mock_pr.get_files.return_value = [
        make_mock_file("main.py", " line1\n line2\n line3\n+print('hello')\n"),
    ]
    files, skipped = get_changed_files(mock_pr)
    assert len(files) == 1
    assert files[0]["filename"] == "main.py"
    assert skipped == []


def test_get_changed_files_skips_binary():
    mock_pr = MagicMock()
    mock_pr.get_files.return_value = [
        make_mock_file("logo.png", None),
        make_mock_file("main.py", " line1\n line2\n line3\n+print('hello')\n"),
    ]
    files, skipped = get_changed_files(mock_pr)
    assert len(files) == 1
    assert len(skipped) == 1
    assert skipped[0]["filename"] == "logo.png"


def test_get_changed_files_skips_missing_patch():
    mock_pr = MagicMock()
    mock_pr.get_files.return_value = [
        make_mock_file("large_file.py", None),
    ]
    files, skipped = get_changed_files(mock_pr)
    assert files == []
    assert len(skipped) == 1
    assert "patch unavailable" in skipped[0]["reason"]


def test_get_changed_files_empty_pr():
    mock_pr = MagicMock()
    mock_pr.get_files.return_value = []
    files, skipped = get_changed_files(mock_pr)
    assert files == []
    assert skipped == []
