from rich.console import Console
from rich.markup import escape

from code_brief.models import PRSummary

console = Console()


def deliver_terminal(summary: PRSummary) -> None:
    console.print(f"\n[bold]Summary:[/bold]\n{escape(summary.summary)}")

    if summary.risks:
        console.print("\n[bold]Risks:[/bold]")
        for risk in summary.risks:
            colour = "red" if risk.severity == "HIGH" else "yellow" if risk.severity == "MED" else "blue"
            description = escape(risk.description)
            console.print(f"    [{colour}]{risk.severity}[/{colour}] ({risk.confidence}%) {description}")

    if summary.focus_areas:
        console.print("\n[bold]Reviewer Focus Areas:[/bold]")
        for i, area in enumerate(summary.focus_areas, 1):
            console.print(f"    {i}. {escape(area)}")
