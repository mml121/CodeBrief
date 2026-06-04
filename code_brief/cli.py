import typer
from rich.console import Console
from rich.panel import Panel
from code_brief.config import load_config
from code_brief.delivery.email import deliver_email
from code_brief.delivery.github import deliver_github
from code_brief.github.client import get_pr
from code_brief.github.diff import get_changed_files
from code_brief.llm.anthropic import call_claude
from code_brief.delivery.terminal import deliver_terminal

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
    console.print(f"[green]✓[/green] {len(files)} files changed · +{pull.additions} lines added · -{pull.deletions} lines removed")

    if verbose:
        for f in files:
            console.print(f"    [dim]{f["filename"]}[/dim] +{f["additions"]} -{f["deletions"]}")

    if dry_run:
        console.print("\n[yellow]Dry run - skipping LLM call[/yellow]")
        return

    with console.status("[bold green]Analysing diff..."):
        summary = call_claude(config, pr_title=pull.title)

    if output == "terminal":
        deliver_terminal(summary)
    elif output == "github":
        console.print("\n[bold blue]Posting comment to GitHub...[/bold blue]")
        deliver_github(summary, config)
        console.print(f"\n[green]✓[/green] Comment posted to PR #{pr}")
    elif output == "email":
        email_to = typer.prompt("Recipient email address")
        console.print("\n[bold green]Sending email...[/bold green]")
        deliver_email(summary, config, recipient=email_to)
        console.print(f"[green]✓[/green] Email sent to {email_to}")
