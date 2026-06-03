# CodeBrief

An AI-powered CLI tool that automatically analyses GitHub pull requests and generates structured, human-readable code review summaries.

---

## What it does

Point CodeBrief at any GitHub PR and it will:

- Fetch the PR metadata and unified diff from GitHub
- Send the diff to Claude via the Anthropic API
- Return a structured summary covering what changed, what risks exist, and what reviewers should focus on

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

---

## Example output

```
╭─────────────────────────────────────────────────────╮
│ CodeBrief — analysing PR #142 on moder/backend       │
╰─────────────────────────────────────────────────────╯
✓ Fetched PR: feat: add UserNotificationService
✓ 6 files changed

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

## Models

| Model | Value | Use case |
|---|---|---|
| Claude 3.5 Sonnet | `claude-3-5-sonnet` | Production — best quality summaries |
| Claude 3 Haiku | `claude-3-haiku` | Testing — faster and cheaper |

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
└── llm/
    ├── prompt.py       # System prompt and prompt builder
    ├── chunker.py      # Token counting and diff chunking
    └── anthropic.py    # API calls and response parsing
```

---

## Flags

| Flag | Default | Description |
|---|---|---|
| `--pr` | required | PR number to review |
| `--repo` | required | Repository in `owner/repo` format |
| `--output` | `terminal` | Output mode: `terminal`, `github`, `slack`, `email` |
| `--dry-run` | `False` | Fetch diff without calling the LLM |
| `--verbose` | `False` | Show all changed files before analysis |

---

## Notes

- CodeBrief uses `tiktoken` to count tokens before sending to the API. Diffs exceeding the token limit are automatically chunked per file.
- Retries are handled automatically using `tenacity` — up to 3 attempts with exponential backoff.
- Never commit your `.env` file. It is listed in `.gitignore` by default.