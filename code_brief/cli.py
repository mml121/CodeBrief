import typer
from rich.console import Console
from rich.panel import Panel
from code_brief.config import load_config
from code_brief.github.client import get_pr
from code_brief.github.diff import get_changed_files
from code_brief.llm.anthropic import call_claude

app = typer.Typer()
console = Console()

@app.command()
def main(
        pr: int = typer.Option(..., "--pr", help="PR number to review"),
        repo: str = typer.Option(..., "--repo", help="Repository to review"),
        output: str = typer.Option("terminal", "--output", help="Output mode: terminal, github, slack, email"),
        dry_run: bool = typer.Option(False, "--dry-run", help="Fetch diff without calling LLM"),
        verbose: bool = typer.Option(False, "--verbose", help="Show detailed output"),
):
    console.print(Panel(f"[bold]CodeBrief[/bold] — analysing PR [cyan]#{pr}[/cyan] on [cyan]{repo}[/cyan]"))

    config = load_config(repo=repo, pr_number=pr)

    with console.status("[bold green]Fetching PR status from GitHub..."):
        pull = get_pr(config)
        files = get_changed_files(config)

    console.print(f"[green]✓[/green] Fetched PR: [bold]{pull.title}[/bold]")
    console.print(f"[green]✓[/green] {len(files)} files changed")

    if verbose:
        for f in files:
            console.print(f"    [dim]{f["filename"]}[/dim] +{f["additions"]} - {f["deletions"]}")

    if dry_run:
        console.print("\n[yellow]Dry run - skipping LLM call[/yellow]")
        return

    with console.status("[bold green]Analysing diff..."):
        summary = call_claude(config, pr_title=pull.title)

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