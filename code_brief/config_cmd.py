import typer
from rich.console import Console
from rich.table import Table
from rich import box
from dotenv import set_key, dotenv_values
from code_brief.config import ENV_PATH

config_app = typer.Typer(help="View or update CodeBrief LLM settings")
console = Console()

LLM_SETTINGS = {
    "ANTHROPIC_MODEL": "claude-3-haiku",
    "MAX_TOKENS_PER_CHUNK": "6000",
    "LLM_MAX_TOKENS": "1024",
    "API_TIMEOUT": "60",
    "MAX_RETRIES": "3",
    "RETRY_WAIT_MIN": "2",
    "RETRY_WAIT_MAX": "10",
}

INTEGER_SETTINGS = {
    "MAX_TOKENS_PER_CHUNK",
    "LLM_MAX_TOKENS",
    "MAX_RETRIES",
    "RETRY_WAIT_MIN",
    "RETRY_WAIT_MAX",
}
FLOAT_SETTINGS = {"API_TIMEOUT"}


def validate_setting_value(key: str, value: str) -> str:
    if key in INTEGER_SETTINGS:
        try:
            parsed = int(value)
        except ValueError as exc:
            raise typer.BadParameter(f"{key} must be an integer") from exc
        if parsed <= 0:
            raise typer.BadParameter(f"{key} must be greater than 0")
        return str(parsed)

    if key in FLOAT_SETTINGS:
        try:
            parsed = float(value)
        except ValueError as exc:
            raise typer.BadParameter(f"{key} must be a number") from exc
        if parsed <= 0:
            raise typer.BadParameter(f"{key} must be greater than 0")
        return str(parsed)

    return value


@config_app.command("show")
def show():
    if not ENV_PATH.exists():
        console.print("[red]✗ No configuration found. Run 'code-brief init' first.[/red]")
        raise typer.Exit(1)

    values = dotenv_values(ENV_PATH)

    table = Table(title="LLM Settings", show_header=True, box=box.ROUNDED, border_style="cyan")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    for key, default in LLM_SETTINGS.items():
        current = values.get(key)
        if current:
            table.add_row(key, current)
        else:
            table.add_row(key, f"[dim]{default} (default)[/dim]")

    console.print(table)


@config_app.command("set")
def set_value(key: str, value: str):
    key = key.upper()

    if key not in LLM_SETTINGS:
        console.print(f"[red]✗ Unknown setting: {key}[/red]")
        console.print(f"[dim]Valid settings: {', '.join(LLM_SETTINGS.keys())}[/dim]")
        raise typer.Exit(1)

    if not ENV_PATH.exists():
        console.print("[red]✗ No configuration found. Run 'code-brief init' first.[/red]")
        raise typer.Exit(1)

    value = validate_setting_value(key, value)
    set_key(str(ENV_PATH), key, value)
    console.print(f"[green]✓[/green] {key} set to [bold]{value}[/bold]")


@config_app.command("reset")
def reset(key: str):
    key = key.upper()

    if key not in LLM_SETTINGS:
        console.print(f"[red]✗ Unknown setting: {key}[/red]")
        console.print(f"[dim]Valid settings: {', '.join(LLM_SETTINGS.keys())}[/dim]")
        raise typer.Exit(1)

    if not ENV_PATH.exists():
        console.print("[red]✗ No configuration found. Run 'code-brief init' first.[/red]")
        raise typer.Exit(1)

    set_key(str(ENV_PATH), key, LLM_SETTINGS[key])
    console.print(f"[green]✓[/green] {key} reset to default [bold]{LLM_SETTINGS[key]}[/bold]")
