# CodeBrief

An AI-powered CLI tool that automatically analyses GitHub pull requests and generates structured, human-readable code review summaries.

---

## What it does

Point CodeBrief at any GitHub PR and it will:

- Fetch the PR metadata and unified diff from GitHub
- Send the diff to Claude via the Anthropic API
- Return a structured summary covering what changed, what risks exist, and what reviewers should focus on
- Deliver the summary via terminal, GitHub comment, email, or Slack

---

## Requirements

- Python 3.12+
- A GitHub Personal Access Token (fine-grained)
- An Anthropic API key

---

## Installation

**1. Clone the repository**
```bash
git clone https://github.com/your-username/CodeBrief.git
cd CodeBrief
```

**2. Create and activate a virtual environment**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Install the package**
```bash
pip install -e .
```

**5. Set up your `.env` file**

Create a `.env` file in the root of the project:
```env
GITHUB_TOKEN=github_pat_xxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=your-api-key-here
ANTHROPIC_ENDPOINT=https://your-endpoint-here

# Email delivery (optional)
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password-here
EMAIL_SMTP_HOST=smtp.gmail.com
```

---

## Usage

**Basic review — output to terminal**
```bash
code-brief --pr <number> --repo <owner/repo>
```

**Verbose mode — see all files changed**
```bash
code-brief --pr <number> --repo <owner/repo> --verbose
```

**Dry run — fetch diff without calling the LLM**
```bash
code-brief --pr <number> --repo <owner/repo> --dry-run
```

**Post as a GitHub PR comment**
```bash
code-brief --pr <number> --repo <owner/repo> --output github
```

**Send as an email**
```bash
code-brief --pr <number> --repo <owner/repo> --output email
```
You will be prompted to enter the recipient email address at runtime:
```
Recipient email address: reviewer@company.com
```

**Send to Slack** *(coming soon)*
```bash
code-brief --pr <number> --repo <owner/repo> --output slack
```

---

## Example output

```
╭─────────────────────────────────────────────────────╮
│ CodeBrief — analysing PR #142 on moder/backend       │
╰─────────────────────────────────────────────────────╯
✓ Fetched PR: feat: add UserNotificationService
✓ 6 files changed
✓ +184 additions -42 deletions

Summary:
This PR adds a new UserNotificationService and wires it into the existing
auth flow. It introduces background job scheduling for email delivery and
updates the user schema to add a notifications_enabled flag with a
corresponding migration.

Risks:
  HIGH (95%) Migration adds a non-nullable column with no default value.
             Will fail on existing databases without a data migration first.
  MED  (80%) Email task retries have no max-retry limit configured.
             A failed SMTP connection may cause an infinite retry loop.

Reviewer Focus Areas:
  1. Confirm default value strategy in migration before merging.
  2. Add max_retries cap to Celery retry config.
  3. Verify auth flow change doesn't break existing sessions.
```

---

## Configuration

| Variable | Required | Description |
|---|---|---|
| `GITHUB_TOKEN` | Yes | Fine-grained GitHub PAT with `pull requests: read/write` and `contents: read` permissions |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key |
| `ANTHROPIC_ENDPOINT` | Yes | Anthropic API endpoint URL |
| `EMAIL_SENDER` | For email | Gmail address to send from |
| `EMAIL_PASSWORD` | For email | Gmail app password |
| `EMAIL_SMTP_HOST` | For email | SMTP host (e.g. `smtp.gmail.com`) |

---

## GitHub PAT Setup

1. Go to `GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens`
2. Click **Generate new token**
3. Under **Repository access**, select the repos you want CodeBrief to analyse
4. Under **Permissions**, set:
   - `Pull requests` → Read and write
   - `Contents` → Read only
5. Generate and copy the token into your `.env` file

---

## Gmail App Password Setup

Required if you plan to use `--output email` with Gmail.

1. Enable 2-Step Verification on your Google account at `myaccount.google.com → Security`
2. Go to `myaccount.google.com → Security → 2-Step Verification → App Passwords`
3. Click **Create a new app password** and name it `code-brief`
4. Copy the 16 character password into your `.env` as `EMAIL_PASSWORD` with no spaces

---

## Output modes

| Mode | Description | Status |
|---|---|---|
| `terminal` | Rich-formatted output printed to the CLI | ✅ Available |
| `github` | Summary posted as a comment on the PR | ✅ Available |
| `email` | HTML summary emailed to a recipient | ✅ Available |
| `slack` | Summary sent to a Slack channel | ⏳ Coming soon |

---

## Models

**Claude 3.5 Sonnet** — best quality summaries

**Claude 3 Haiku** — faster and cheaper, recommended for testing

CodeBrief defaults to `claude-3-haiku`. The model can be changed in `config.py`.

---

## Project Structure

```
code_brief/
├── cli.py              # Entry point — Typer CLI
├── config.py           # Loads .env into a Config dataclass
├── models.py           # PRSummary and Risk dataclasses
├── github/
│   ├── client.py       # GitHub authentication and PR fetching
│   └── diff.py         # Diff fetching and parsing
├── llm/
│   ├── prompt.py       # System prompt and prompt builder
│   ├── chunker.py      # Token counting and diff chunking
│   └── anthropic.py    # API calls and response parsing
└── delivery/
    ├── terminal.py     # Rich formatted CLI output
    ├── github.py       # Posts summary as a PR comment
    ├── email.py        # Sends HTML email via Gmail
    └── slack.py        # Slack integration (coming soon)
```

---

## Flags

| Flag | Default | Description |
|---|---|---|
| `--pr` | required | PR number to review |
| `--repo` | required | Repository in `owner/repo` format |
| `--output` | `terminal` | Output mode: `terminal`, `github`, `email`, `slack` |
| `--dry-run` | `False` | Fetch diff without calling the LLM |
| `--verbose` | `False` | Show all changed files before analysis |

---

## Notes

- CodeBrief uses `tiktoken` to count tokens before sending to the API. Diffs exceeding the token limit are automatically chunked per file.
- Retries are handled automatically using `tenacity` — up to 3 attempts with exponential backoff.
- Never commit your `.env` file. It is listed in `.gitignore` by default.
- API usage is limited to 1200 requests per month. Use `claude-3-haiku` for testing to conserve quota.