from github import Github
from code_brief.config import Config
from code_brief.models import PRSummary


def format_github_comment(summary: PRSummary) -> str:
    lines = []

    lines.append("## CodeBrief Review")
    lines.append(f"`{summary.repo}` · PR #{summary.pr_number} · {len(summary.risks)} risks flagged")
    lines.append("")

    lines.append("### Summary")
    lines.append(summary.summary)
    lines.append("")

    if summary.risks:
        lines.append("### Risks")
        for risk in summary.risks:
            emoji = "🔴" if risk.severity == "HIGH" else "🟡" if risk.severity == "MED" else "🔵"
            lines.append(f"{emoji} **{risk.severity}** ({risk.confidence}%) {risk.description}")
        lines.append("")

    if summary.focus_areas:
        lines.append("### Reviewer Focus Areas")
        for i, area in enumerate(summary.focus_areas, 1):
            lines.append(f"{i}. {area}")

    return "\n".join(lines)


def deliver_github(summary: PRSummary, config: Config) -> None:
    client = Github(config.github_token)
    repo = client.get_repo(config.repo)
    pr = repo.get_pull(config.pr_number)
    comment = format_github_comment(summary)
    pr.create_issue_comment(comment)