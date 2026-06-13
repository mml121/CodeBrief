# Changelog

## [1.0.1] - 2026-06-13
### Added
- Added `code-brief config` commands for viewing, setting, and resetting LLM settings.
- Added regression tests for CLI validation, config parsing, delivery formatting, and LLM response parsing.

### Fixed
- Hardened CLI output validation, config parsing, logging, LLM response handling, and delivery rendering.
- Escaped untrusted content in terminal, GitHub, and email delivery.
- Skipped LLM calls when PRs have no reviewable diff content.

### Removed
- Removed unfinished Slack delivery from the CLI, setup flow, configuration, and documentation.

## [1.0.0] - 2026-06-13
### Added
- Initial release with PR diff analysis, token-aware chunking, Claude review generation, terminal/GitHub/email delivery, onboarding, metrics, and CI.
