# Changelog

## 2.0.0 — 2026-09-05

### Changed

- Require execution inside Solo with a Solo-managed lead and timer delivery.
  External agents may review/maintain the skill and prepare a handoff prompt;
  the Solo lead verifies current state and gets plan approval before executing.
- Require explicit skill invocation and approval of the displayed plan before
  branches, implementation, or workers. Pause affected lanes for significant
  revisions; keep routine progress in Solo until input or final delivery.
- Isolate implementation workers in Git worktrees. Workers commit locally and
  freeze at handoff; the lead reviews fixed SHAs, preserves lane history during
  integration, verifies, and promptly removes accepted lanes and worktrees.
- Adapt concurrency to independent work, quota, resources, and review backlog.
  Prefer capable included subscription routes; support single-lab operation.
  Require scoped approval for extra charges and allow earned Codex reset credits.
- Update the five CLI references against installed help and official documentation,
  distinguishing historical smoke tests from current evidence.
- Reduce duplicated workflow documentation and load references only when needed.

### Added

- A machine-wide SQLite cache for model catalogs, quota observations, bounded
  usage history, and compact lane outcomes, with freshness and concurrency handling.
- Codex explicit-only invocation metadata and reversible OpenCode v1 command/
  permission setup. Copy installs include all runtime resources; uninstall
  preserves foreign installations and later user configuration changes.
- Automated helper and installer tests.

### Migration

Invoke the skill explicitly in a fresh session. OpenCode users must run
`./install.sh --targets opencode` or manually merge the documented configuration;
its v1 skill loader ignores the frontmatter invocation flag. Existing symlink
installs follow the checkout; reinstall copied or plugin-managed versions.
