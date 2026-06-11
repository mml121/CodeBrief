<div align="center">

# CodeBrief

**AI-powered pull request analysis for engineering teams**

[![CI](https://github.com/mml121/CodeBrief/actions/workflows/ci.yml/badge.svg)](https://github.com/mml121/CodeBrief/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

CodeBrief automatically analyses GitHub pull requests and generates structured, human-readable summaries covering what changed, what risks exist, and what reviewers should focus on.

</div>

---

## Overview

Code review is one of the most time-consuming parts of the software development lifecycle. Reviewers are expected to understand what a PR does, identify risks, and validate correctness, often across multiple files and hundreds of lines of diff.

CodeBrief automates the first pass. It fetches the diff, sends it to Claude, and returns a structured summary so reviewers can focus on what matters rather than piecing together context from scratch.

---

## Features

- **Structured summaries** - what changed, what risks exist, and where to focus the review
- **Risk scoring** - HIGH / MED / LOW severity with confidence scores backed by diff evidence
- **Smart diff handling** - file categorisation, token-aware chunking, and hierarchical summarisation for large PRs
- **Multiple delivery modes** - terminal, GitHub PR comment, email, Slack
- **Graceful error handling** - missing patches, binary files, and invalid LLM responses handled cleanly
- **Retry logic** - automatic retries with exponential backoff on API failures
- **Onboarding** - `code-brief init` guides first-time setup with connection validation
- **Observability** - per-run metrics table showing files processed, token usage, response times, and retries
- **CI/CD ready** - GitHub Actions workflow included

---

## Architecture

CodeBrief is structured as a Python pipeline with four logical layers:

```
+---------------------------------------------------------+
|                      CLI (Typer)                        |
+-------------------------+-------------------------------+
                          |
        +-----------------v-----------------+
        |        GitHub Integration         |
        |  Fetch PR metadata + unified diff |
        |  Filter binary, lock, generated   |
        +-----------------+-----------------+
                          |
        +-----------------v-----------------+
        |          Diff Processor           |
        |  Parse diff into file objects     |
        |  Categorise by token size         |
        |  Chunk + sub-chunk large files    |
        +-----------------+-----------------+
                          |
        +-----------------v-----------------+
        |            LLM Layer              |
        |  Build structured prompt          |
        |  Call Claude via httpx            |
        |  Validate + parse JSON response   |
        |  Hierarchical summarisation       |
        +-----------------+-----------------+
                          |
        +-----------------v-----------------+
        |          Delivery Layer           |
        |  Terminal, GitHub, Email, Slack   |
        +-----------------------------------+
```

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
pip install -e .
```

**4. Run first-time setup**
```bash
code-brief init
```

The `init` command walks you through setting up your API keys, validates each connection, and writes your `.env` file automatically. You can optionally configure email and Slack delivery during setup.

---

## Usage

**Basic review - output to terminal**
```bash
code-brief --pr <number> --repo <owner/repo>
```

**Verbose mode - see all files and skipped files**
```bash
code-brief --pr <number> --repo <owner/repo> --verbose
```

**Dry run - fetch diff without calling the LLM**
```bash
code-brief --pr <number> --repo <owner/repo> --dry-run
```

**Post as a GitHub PR comment**
```bash
code-brief --pr <number> --repo <owner/repo> --output github
```

**Send as an HTML email**
```bash
code-brief --pr <number> --repo <owner/repo> --output email
# You will be prompted for the recipient address at runtime
```

**Send to Slack** *(coming soon)*
```bash
code-brief --pr <number> --repo <owner/repo> --output slack
```

---

## Example output

```
+----------------------------------------------------------+
| CodeBrief - analysing PR #142 on moder/backend           |
+----------------------------------------------------------+
✓ Fetched PR: feat: add UserNotificationService
✓ 6 files changed
✓ +184 additions -42 deletions

Summary:
This PR adds a new UserNotificationService and wires it into the existing
auth flow. It introduces background job scheduling for email delivery and
updates the user schema to add a notifications_enabled flag.

Risks:
  HIGH (95%) Migration adds a non-nullable column with no default value.
             Will fail on existing databases without a data migration first.
  MED  (80%) Email task retries have no max-retry limit configured.
             A failed SMTP connection may cause an infinite retry loop.

Reviewer Focus Areas:
  1. Confirm default value strategy in migration before merging.
  2. Add max_retries cap to Celery retry config.
  3. Verify auth flow change does not break existing sessions.

+- Run Metrics ──────────────────────+
| Files processed      6             |
| Files skipped        0             |
| Input tokens         1,842         |
| Output tokens        312           |
| Total tokens         2,154         |
| Chunks               1             |
| LLM requests         1             |
| Retries              0             |
| Failed requests      0             |
| Avg response time    1.4s          |
| Total time           3.2s          |
+────────────────────────────────────+
```

---

## Large PR handling

CodeBrief handles PRs of any size without hitting token limits.

Files are categorised by token size and processed accordingly:

| Category | Token range | Strategy |
|---|---|---|
| Small | < 500 tokens | Grouped into shared chunks |
| Medium | 500 - 6,000 tokens | Sent as individual chunk |
| Large | 6,000 - 20,000 tokens | Split into sub-chunks, summarised per chunk |
| Extremely large | > 20,000 tokens | Truncated to most changed hunks with warning |

For very large PRs where the total diff exceeds 10x the chunk limit, CodeBrief uses hierarchical summarisation. Chunk summaries are synthesised into file summaries, which are then synthesised into a final PR summary.

The following file types are automatically filtered before processing:

- Binary files (images, fonts, compiled binaries)
- Lock files (`package-lock.json`, `poetry.lock`, `yarn.lock`)
- Minified files (`*.min.js`, `*.min.css`)
- Build artifacts (`*.pyc`, `dist/`, `build/`)

---

## Configuration

All configuration is managed via `.env`. Run `code-brief init` to generate this file automatically.

| Variable | Required | Default | Description |
|---|---|---|---|
| `GITHUB_TOKEN` | Yes | - | Fine-grained GitHub PAT |
| `ANTHROPIC_API_KEY` | Yes | - | Anthropic API key |
| `ANTHROPIC_ENDPOINT` | Yes | - | Anthropic API endpoint URL |
| `ANTHROPIC_MODEL` | No | `claude-3-haiku` | Model to use |
| `MAX_TOKENS_PER_CHUNK` | No | `6000` | Token limit per chunk |
| `LLM_MAX_TOKENS` | No | `1024` | Max tokens in LLM response |
| `API_TIMEOUT` | No | `60` | Request timeout in seconds |
| `MAX_RETRIES` | No | `3` | Max retry attempts on failure |
| `RETRY_WAIT_MIN` | No | `2` | Min retry wait in seconds |
| `RETRY_WAIT_MAX` | No | `10` | Max retry wait in seconds |
| `EMAIL_SENDER` | For email | - | Gmail address to send from |
| `EMAIL_PASSWORD` | For email | - | Gmail app password |
| `EMAIL_SMTP_HOST` | For email | - | SMTP host |
| `SLACK_WEBHOOK_URL` | For Slack | - | Slack incoming webhook URL |
| `SLACK_CHANNEL` | For Slack | - | Slack channel name |

---

## Output modes

| Mode | Description | Status |
|---|---|---|
| `terminal` | Rich-formatted output with colour-coded risks | Available |
| `github` | Markdown summary posted as a PR comment | Available |
| `email` | Styled HTML email sent to a recipient | Available |
| `slack` | Summary sent to a Slack channel | Coming soon |

---

## CLI flags

| Flag | Default | Description |
|---|---|---|
| `--pr` | required | PR number to review |
| `--repo` | required | Repository in `owner/repo` format |
| `--output` | `terminal` | Output mode: `terminal`, `github`, `email`, `slack` |
| `--dry-run` | `False` | Fetch diff without calling the LLM |
| `--verbose` | `False` | Show all files, skipped files, and debug output |

---

## Testing

Run the full test suite:

```bash
pytest tests/ -v
```

Run linting:

```bash
ruff check .
```

Tests cover diff parsing, file filtering, token counting, chunking logic, prompt generation, LLM response parsing, and connection validation. No real API calls are made during tests - all external dependencies are mocked.

---

## CI/CD

A GitHub Actions workflow runs on every push and pull request to `main`:

- `ruff check .` - linting
- `pytest tests/ -v` - full test suite

Pipeline configuration is at `.github/workflows/ci.yml`.

---

## Known limitations

- CodeBrief only has access to the diff - it cannot see the full file context, test suite, or CI results
- Risk confidence scores are based on LLM reasoning, not static analysis - false positives are possible on ambiguous diffs
- Very large PRs (500K+ tokens) are handled via hierarchical summarisation - detail is progressively compressed at each level
- Email delivery requires Gmail with 2-Step Verification and may be blocked on some corporate or institutional networks
- Slack integration is not yet implemented

---

## Contributing

This project was built during a 6-week internship at Moder. Contributions and feedback welcome.