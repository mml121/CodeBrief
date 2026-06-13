import httpx
from github import Github
from github.GithubException import GithubException
from rich.console import Console
from rich.panel import Panel
import typer
from code_brief.config import CONFIG_DIR, ENV_PATH

console = Console()


def validate_github_token(token: str) -> tuple[bool, str]:
    try:
        client = Github(token)
        user = client.get_user()
        return True, user.login
    except GithubException:
        return False, "Invalid token or insufficient permissions"
    except Exception as e:
        return False, str(e)


def validate_anthropic_connection(api_key: str, endpoint: str) -> tuple[bool, str]:
    try:
        response = httpx.post(
            endpoint,
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "model": "claude-3-haiku",
                "messages": [{"role": "user", "content": "Reply with the word OK and nothing else."}],
                "max_tokens": 10
            },
            timeout=15.0
        )
        response.raise_for_status()
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)


def ask_with_retry(prompt: str, test_fn, success_msg: str) -> str:
    hide = "key" in prompt.lower() or "password" in prompt.lower() or "token" in prompt.lower()
    while True:
        value = typer.prompt(prompt, hide_input=hide)
        if not value.strip():
            console.print("[red]✗ Value cannot be empty[/red]")
            continue

        with console.status("[bold green]Testing connection..."):
            ok, msg = test_fn(value.strip())

        if ok:
            console.print(f"[green]✓[/green] {success_msg}: [dim]{msg}[/dim]")
            return value.strip()
        else:
            console.print(f"[red]✗ {msg}[/red]")
            retry = typer.confirm("Would you like to try again?")
            if not retry:
                raise typer.Exit(1)


def run_init() -> None:
    console.print(Panel(
        "[bold]Welcome to CodeBrief![/bold]\n\nLet's get you set up. I'll need a few API keys.",
        border_style="cyan"
    ))

    # --- required keys ---
    console.print("\n[bold cyan]Required[/bold cyan]")

    github_token = ask_with_retry(
        "GitHub Personal Access Token",
        lambda t: validate_github_token(t),
        "GitHub connected"
    )

    endpoint = typer.prompt("Anthropic Endpoint URL")

    anthropic_key = ask_with_retry(
        "Anthropic API Key",
        lambda k: validate_anthropic_connection(k, endpoint),
        "Anthropic connected"
    )

    # --- optional: email ---
    console.print("\n[bold cyan]Optional[/bold cyan]")
    email_sender = ""
    email_password = ""
    email_smtp_host = ""
    email_smtp_port = "465"

    setup_email = typer.confirm("Would you like to set up email delivery?")
    if setup_email:
        email_sender = typer.prompt("Gmail address")
        email_password = typer.prompt("Gmail app password", hide_input=True)
        email_smtp_host = typer.prompt("SMTP host", default="smtp.gmail.com")
        email_smtp_port = typer.prompt("SMTP port", default="465")
        console.print("[green]✓[/green] Email settings saved")

    # --- write .env to ~/.codebrief/.env ---
    env_lines = [
        "# CodeBrief configuration",
        f"GITHUB_TOKEN={github_token}",
        f"ANTHROPIC_API_KEY={anthropic_key}",
        f"ANTHROPIC_ENDPOINT={endpoint}",
        "",
        "# LLM settings",
        "ANTHROPIC_MODEL=claude-3-haiku",
        "MAX_TOKENS_PER_CHUNK=6000",
        "LLM_MAX_TOKENS=1024",
        "API_TIMEOUT=60",
        "MAX_RETRIES=3",
        "RETRY_WAIT_MIN=2",
        "RETRY_WAIT_MAX=10",
    ]

    if setup_email:
        env_lines += [
            "",
            "# Email delivery",
            f"EMAIL_SENDER={email_sender}",
            f"EMAIL_PASSWORD={email_password}",
            f"EMAIL_SMTP_HOST={email_smtp_host}",
            f"EMAIL_SMTP_PORT={email_smtp_port}",
        ]

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(ENV_PATH, "w") as f:
        f.write("\n".join(env_lines))

    console.print(Panel(
        f"[bold green]You're all set![/bold green]\n\n"
        f"Config saved to [cyan]{ENV_PATH}[/cyan]\n\n"
        "Try running:\n"
        "  [cyan]code-brief --pr 1 --repo your-org/your-repo[/cyan]",
        border_style="green"
    ))
