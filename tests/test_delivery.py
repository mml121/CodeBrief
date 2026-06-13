from code_brief.delivery.email import format_email_body
from code_brief.delivery.github import format_github_comment
from code_brief.models import PRSummary, Risk


def make_summary() -> PRSummary:
    return PRSummary(
        pr_number=7,
        repo="owner/repo",
        title="Fix <bug>",
        summary="<script>alert(1)</script>",
        risks=[Risk(severity="MED", confidence=80, description="<b>bad</b>")],
        focus_areas=["Check [link](https://example.com)"],
    )


def test_email_body_escapes_dynamic_content():
    body = format_email_body(make_summary())
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in body
    assert "<b>bad</b>" not in body
    assert "&lt;b&gt;bad&lt;/b&gt;" in body


def test_github_comment_escapes_markdown_content():
    comment = format_github_comment(make_summary())
    assert r"\[link\]\(https://example\.com\)" in comment
    assert r"\<script\>alert\(1\)\</script\>" in comment
