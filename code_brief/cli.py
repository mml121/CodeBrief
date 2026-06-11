import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from code_brief.config import load_config
from code_brief.github.client import get_pr
from code_brief.github.diff import get_changed_files
from code_brief.llm.anthropic import call_claude
from code_brief.delivery.terminal import deliver_terminal
from code_brief.delivery.github import deliver_github
from code_brief.delivery.email import deliver_email
from code_brief.logger import set_log_level
from code_brief.metrics import Metrics
from code_brief.init import run_init

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    pr: int = typer.Option(None, "--pr", help="PR number to review"),
    repo: str = typer.Option(None, "--repo", help="Repository in format owner/repo"),
    output: str = typer.Option("terminal", "--output", help="Output mode: terminal, github, slack, email"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Fetch diff without calling LLM"),
    verbose: bool = typer.Option(False, "--verbose", help="Show detailed output"),
):
    if ctx.invoked_subcommand is not None:
        return

    if pr is None or repo is None:
        console.print("[red]✗ --pr and --repo are required[/red]")
        console.print("[dim]Run 'code-brief init' to set up CodeBrief for the first time[/dim]")
        raise typer.Exit(1)

    set_log_level(verbose)
    metrics = Metrics()

    console.print(Panel(f"[bold]CodeBrief[/bold] — analysing PR [cyan]#{pr}[/cyan] on [cyan]{repo}[/cyan]"))

    config = load_config(repo=repo, pr_number=pr)

    with console.status("[bold green]Fetching PR from GitHub..."):
        pull = get_pr(config)
        files, skipped = get_changed_files(pull)

    metrics.files_processed = len(files)
    metrics.files_skipped = len(skipped)
    metrics.skip_reasons = [s["reason"] for s in skipped]

    console.print(f"[green]✓[/green] Fetched PR: [bold]{pull.title}[/bold]")
    console.print(f"[green]✓[/green] {len(files)} files changed")
    console.print(f"[green]✓[/green] [green]+{pull.additions}[/green] additions [red]-{pull.deletions}[/red] deletions")

    if skipped:
        console.print(f"[yellow]⚠ {len(skipped)} files skipped[/yellow]")
        if verbose:
            for s in skipped:
                console.print(f"  [dim]{s['filename']} — {s['reason']}[/dim]")

    if verbose:
        for f in files:
            console.print(f"  [dim]{f['filename']}[/dim] +{f['additions']} -{f['deletions']}")

    if dry_run:
        console.print("\n[yellow]Dry run — skipping LLM call[/yellow]")
        return

    with console.status("[bold green]Analysing diff with Claude..."):
        summary = call_claude(config, files=files, pr_title=pull.title, metrics=metrics)

    if output == "terminal":
        deliver_terminal(summary)
    elif output == "github":
        console.print("\n[bold green]Posting comment to GitHub...[/bold green]")
        deliver_github(summary, config)
        console.print(f"[green]✓[/green] Comment posted to PR #{pr}")
    elif output == "email":
        email_to = typer.prompt("Recipient email address")
        console.print("\n[bold green]Sending email...[/bold green]")
        deliver_email(summary, config, recipient=email_to)
        console.print(f"[green]✓[/green] Email sent to {email_to}")
    elif output == "slack":
        console.print("[yellow]Slack integration coming soon![/yellow]")

    table = Table(
        title="Run Metrics",
        box=box.ROUNDED,
        show_header=False,
        padding=(0, 2),
        title_style="bold cyan",
        border_style="cyan"
    )
    table.add_column(style="dim white", min_width=20)
    table.add_column(justify="right", style="bold white")

    table.add_row("Files processed", f"[green]{metrics.files_processed}[/green]")
    table.add_row("Files skipped", f"[yellow]{metrics.files_skipped}[/yellow]")
    table.add_row("Total tokens", str(metrics.total_tokens))
    table.add_row("Chunks", str(metrics.chunk_count))
    table.add_row("LLM requests", str(metrics.llm_request_count))
    table.add_row("Retries", f"[{'yellow' if metrics.retry_count > 0 else 'green'}]{metrics.retry_count}[/{'yellow' if metrics.retry_count > 0 else 'green'}]")
    table.add_row("Failed requests", f"[{'red' if metrics.failed_requests > 0 else 'green'}]{metrics.failed_requests}[/{'red' if metrics.failed_requests > 0 else 'green'}]")
    table.add_row("Avg response time", f"{metrics.avg_response_time()}s")
    table.add_row("Total time", f"[cyan]{metrics.elapsed()}s[/cyan]")

    console.print("\n")
    console.print(table, justify="center")


@app.command()
def init():
    run_init()
