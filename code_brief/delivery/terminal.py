from rich.console import Console
from code_brief.models import PRSummary

console = Console()


def deliver_terminal(summary: PRSummary) -> None:
    console.print(f"\n[bold]Summary:[/bold]\n{summary.summary}")

    if summary.risks:
        console.print(f"\n[bold]Risks:[/bold]")
        for risk in summary.risks:
            colour = "red" if risk.severity == "HIGH" else "yellow" if risk.severity == "MEDIUM" else "blue"
            console.print(f"    [{colour}]{risk.severity}[/{colour}] ({risk.confidence}%) {risk.description}")

    if summary.focus_areas:
        console.print(f"\n[bold]Reviewer Focus areas:[/bold]")
        for i, area in enumerate(summary.focus_areas, 1):
            console.print(f"    {i}. {area}")
