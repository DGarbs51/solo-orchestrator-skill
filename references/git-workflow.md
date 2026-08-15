# Git workflow — branch, commits, and the merge request

Read this when Phase 2 starts (branching) and again at Phase 6/8
(commits and the PR). The rules live in SKILL.md; this file is the mechanics.

Conventions below match this user's actual history (Conventional Commits with
scopes, `feature/<slug>` branches, `Co-Authored-By` model trailers, PR-based
merges). Verified against `gh` 2.97.0 and git 2.50.1 on 2026-08-08.

## Branching (Phase 2)

Feature work happens one feature at a time, on its own branch — never on the
default branch. Unless the user directed otherwise:

```bash
git checkout -b feature/<short-slug> <agreed-base>
git push -u origin feature/<short-slug>
```

Use `feature/<slug>` for features and `fix/<slug>` for bug work.

Publish to GitHub **before any edits exist**. An early remote branch gives the
run a durable anchor: workers and worktrees have something to base on, nothing
is lost to a local mishap, and the Phase 8 merge request has a home from
minute one. Record the branch name in the plan scratchpad — it is part of the
shared context every worker reads.

If the repo has no remote, `git push` will fail. Don't improvise a remote —
say so, keep the branch local, and note it in the plan scratchpad so Phase 8
takes the no-`gh` fallback.

### Bypass: stay on main

**When the user explicitly says to make this change directly on `main`, stay on
`main`.** Do not create a feature branch, do not move off the branch you are
on, and do not open a PR at Phase 8.

This triggers **only on an explicit instruction** — "do this on main", "just
commit to main", "no branch for this", "straight to main". It is never inferred
from a task looking small, urgent, or trivial. If the user hasn't said it,
branch. If you are unsure whether they said it, branch and mention it.

The instruction holds for the **whole run**, not just the next commit. Once
given, don't drift back to branching partway through, and don't ask again each
time you commit.

What changes:

| | Normal | Stay-on-main |
|---|---|---|
| Phase 2 | `git checkout -b feature/<slug>` + `git push -u` | stay put; no branch created |
| Plan scratchpad | records the feature branch | records `Branch: main (stay-on-main, user-directed)` |
| Phase 6 | commit + push to the feature branch | commit + `git push origin main` |
| Phase 8 | `gh pr create` | no PR — report pushed commit SHAs |

What does **not** change:
- The lead still makes every commit; workers still never commit.
- Commit messages keep the same shape, scopes, and `Co-Authored-By` trailers.
- Pull/rebase before pushing if the remote moved (`git pull --rebase origin
  main`); a rejected push means someone else pushed — never `--force` to win.
- Integration discipline is unchanged: smallest safe change first, real diffs,
  focused checks per step. On `main` there is no PR review to catch a mistake,
  so the acceptance checks matter more, not less.

Record the bypass in the plan scratchpad's branch line so every worker reads
the same thing and no worker tries to base off a branch that doesn't exist.

## Commits at integration (Phase 6)

**The lead makes every commit. Workers never commit — no exceptions**, not even
workers running in their own git worktree. Workers leave changes uncommitted in
the working tree and report on their todo; the lead reviews the real diff and
commits it. The worker prompt template in SKILL.md states this explicitly.

One commit per integrated lane (or meaningful step), containing: what changed
and *why* (from the lane's objective), tests run, and which agent/model
produced it.

Subject line: Conventional Commits with a scope — `feat(billing):`,
`fix(ui):`, `refactor(inertia):`, `chore(rules):`, `test:`.

**Attribution:** credit both the model that wrote the lane and the lead that
integrated it, as `Co-Authored-By` trailers at the end of the message. When the
lead wrote the lane itself, a single lead trailer is correct.

Example shape:

```
feat(billing): add usage-based invoice line items

Lane 2 of plan-billing-page. Adds InvoiceLineItem model + calculator
so invoices reflect metered usage (goal: bill overages, see PR).
Tests: php artisan test --filter=InvoiceLineItem (12 passing).
Implemented by Kimi K3 (--auto), integrated and reviewed by lead.

Co-Authored-By: Kimi K3 <noreply@moonshot.cn>
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

Trailers must be the last block, one per line, after a blank line. Use the
model's real product name — the trailer is the audit trail that makes lane
records readable from `git log` alone.

Push after each integrated lane so the remote branch tracks real progress.

## The merge request (Phase 8)

Assemble the PR body from the durable artifacts — scratchpad plan, decisions
log, todo handoffs, commit history — never from memory:

```markdown
## Why
The problem/goal, from the interview — what this changes for the user
and why it was worth doing. Include constraints and non-goals.

## What changed
Lane-by-lane: objective, key files, notable decisions (from the
decisions log), and which agent/model handled it.

## How it was verified
Acceptance checks per lane + the end-to-end verification, with actual
commands and results.

## Risks & follow-ups
Remaining risks from worker handoffs; anything deliberately deferred.
```

Open it **ready for review** (not a draft):

```bash
gh pr create --title "<type>(<scope>): <goal in one line>" --body-file <body> --base <base>
```

Pass `--base` explicitly rather than relying on the repo default, since the
run's agreed base is not always the default branch.

**Never merge the PR yourself** — opening it is where your authority ends. The
user reviews and merges.

If `gh` is unavailable or unauthenticated (check `gh auth status`), or the repo
has no GitHub remote, write the full PR body to a scratchpad named `pr-<slug>`
and give the user the branch name and body to paste.

**On the stay-on-main bypass there is no PR.** Push `main`, then report what
you would have put in the PR: the same Why / What changed / How it was verified
/ Risks & follow-ups summary, with the pushed commit SHAs in place of a PR
link. Don't skip the summary just because there's no PR to hold it — that
write-up is the only durable record of the run, and on `main` nothing else
will capture it.
