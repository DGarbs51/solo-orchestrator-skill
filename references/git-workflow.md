# Git workflow — branch, commits, and the merge request

Read this when Phase 2 starts (branching) and again at Phase 6/8
(commits and the PR). The rules live in SKILL.md; this file is the mechanics.

Conventions below match this user's actual history (Conventional Commits with
scopes, `feature/<slug>` branches, `Co-Authored-By` model trailers, PR-based
merges). Verified against `gh` 2.97.0 and git 2.50.1 on 2026-08-08.

## Branching (Phase 2)

Create or publish the implementation branch only after the user has approved
the displayed plan in SKILL.md Phase 2.

Feature work happens one feature at a time, on its own branch — never on the
default branch. Unless the user directed otherwise:

```bash
git checkout -b feature/<short-slug> <agreed-base>
git push -u origin feature/<short-slug>
```

Use `feature/<slug>` for features and `fix/<slug>` for bug work.

Publish after plan approval and before implementation. Record the integration
branch in the plan scratchpad. Pushing an empty branch establishes the remote
tracking branch; only later pushed commits preserve implementation work.

If the repo has no remote, `git push` will fail. Don't improvise a remote —
say so, keep the branch local, and note it in the plan scratchpad so Phase 8
takes the no-`gh` fallback.

### Bypass: stay on main

**When the user explicitly selects `main` as the integration branch, use it.**
Safely switch to the agreed branch if necessary without overwriting local work.
Do not create a feature branch or open a PR at Phase 8. Lane branches still
provide worker isolation.

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
| Phase 2 | `git checkout -b feature/<slug>` + `git push -u` | use agreed main; no feature branch |
| Plan scratchpad | records the feature branch | records `Branch: main (stay-on-main, user-directed)` |
| Phase 6 | commit + push to the feature branch | commit + `git push origin main` |
| Phase 8 | `gh pr create` | no PR — report pushed commit SHAs |

What does **not** change:
- Workers commit only on their lane branches; the lead integrates and pushes.
- Commit messages keep the same shape, scopes, and `Co-Authored-By` trailers.
- If the remote moved, fetch and inspect it, then merge compatible updates
  and reverify before pushing. Preserve reviewed lane history; never force-push
  to overcome a rejected push.
- Integration discipline is unchanged: smallest safe change first, real diffs,
  focused checks per step. On `main` there is no PR review to catch a mistake,
  so the acceptance checks matter more, not less.

Record the bypass in the plan scratchpad's branch line so every worker reads
the same thing and no worker tries to base off a branch that doesn't exist.

## Lane worktrees (Phase 4)

Use a separate Git worktree for each implementation worker. From the lead
checkout, after plan approval and any prerequisite integrations:

```bash
git worktree add -b lane/<run>-<lane> <lane-path> <integration-branch>
```

Choose unused paths and branch names. Record the absolute path, lane branch,
and base commit on the todo. Keep worktree directories outside tracked source
or under an ignored `.worktrees/` directory. Workers edit and run checks only
in their assigned checkout; the lead owns integration.

Git worktrees share the repository object database. To reduce dependency disk
usage further, compatible dependency directories can be copied into a new
worktree with copy-on-write support. On macOS, `cp -cR` uses cloning where
supported and falls back to copying. Both paths must be on the same supporting
filesystem to share storage. See `man cp` and `man clonefile` on the host.

Copy only dependencies matching the lane's lockfiles, platform, and runtime,
from a source that is not being modified. Check symlinks for references back
to the source checkout; rerun the package manager when compatibility is
uncertain. Install only what the lane needs. Do not copy `.git` metadata or
use hard links/shared writable dependency directories as lane isolation.

## Worker commits and handoff

Workers commit coherent changes on their assigned lane branch without asking
permission for each commit. Before committing, verify the checkout and branch,
stage explicit owned paths, and inspect the staged diff. Report unexpected
hook-generated or out-of-scope changes. Do not bypass repository hooks.
Workers do not push, merge, rebase, amend existing commits, change other
branches/worktrees, or alter shared repository settings. Worktrees isolate
checkouts, not all Git state; avoid shared stashes and repository-wide cleanup.

Use scoped Conventional Commit subjects and a concise body explaining why the
change exists and relevant validation. Credit the actual worker model with a
`Co-Authored-By` trailer. The lead records its integration/review attribution
on the integration commit; worker commits must not claim review that has not
happened yet.

At handoff, post the starting and final SHAs, changed files, check results,
blockers/risks, and any remaining local files on the todo. Report ready for
review and stop editing until reassigned. The lead alone completes todos.
If a worker exits before handoff, inspect its recorded branch and worktree;
recover committed and partial work without assuming it passed verification.

## Integration (Phase 6)

The lead owns the integration branch and serializes its updates. For each lane:

1. Confirm the recorded base belongs to the lane history and the branch tip
   matches the reported handoff SHA. Check the lane's staged, unstaged, and
   untracked files. Require intended deliverables to be committed.
2. Review `git diff <starting-sha> <handoff-sha>` and the lane commit history.
   A clean plain `git diff` says nothing about committed worker changes.
3. From the clean integration checkout, merge the exact reviewed SHA:

   ```bash
   git merge --no-ff --no-commit <handoff-sha>
   ```

   Both flags matter: `--no-commit` alone does not stop a fast-forward.
   Preserve lane history; do not squash or cherry-pick by default.
4. Inspect the resulting staged diff and run integration checks before the
   merge commit. Worker tests establish the lane's starting context; verify
   interactions with the current integration branch. Resolve straightforward
   conflicts; return substantive fixes as a bounded worker follow-up.
   On failure, keep the lane incomplete and unpublished; resolve or abort the
   pending merge before integrating another lane. Never reset away user work.
5. Commit the verified merge with the lane objective, handoff SHA, relevant
   checks, and lead attribution. Confirm checks/hooks left no unreviewed
   changes. Push when a remote is available. Record the integration SHA, verification,
   and publication status on the todo, then complete it and unblock dependents.
   A failed or unavailable push does not invalidate verified local integration;
   preserve commits, track the pending push, and report it in the final handoff.
   Ask only if resolving publication requires user input.

Workers freeze after handoff. If a follow-up changes the lane, require a new
SHA and updated verification; review the delta plus its effects on the earlier
review. Merge recorded SHAs, never a branch that can move during review.
If the reported SHA was already integrated, verify the recorded result instead
of manufacturing another merge commit.

### Cleanup after integration (Phase 7)

Clean up each finished lane promptly once its changes are integrated and
verified, its handoff is durable, and its worker and descendants have stopped.
Check the lane's status, including untracked and ignored files, before removal;
retain anything valuable that exists only there. Disposable lane dependencies
and build output can be removed with the worktree.

From the lead checkout, verify that the lane commit is reachable from the
integration branch, then remove the worktree and delete its local branch:

```bash
git merge-base --is-ancestor <lane-branch> <integration-branch>
git worktree remove <lane-path>
git branch -d <lane-branch>
```

Run each step only if the prior check succeeds. If removal refuses, inspect
why; do not force deletion to bypass unpreserved changes. Preserve failed or
interrupted lanes until integrated or explicitly discarded by the user. Keep
prompt files and durable handoffs outside the removed worktree. If dispatch
registered a temporary Solo project solely for this lane, preserve its needed
state in the coordination project first. Remove that registration only after
its processes stop and its Solo-owned state is no longer needed; never delete
the shared coordination project or a pre-existing registration. Never remove
pre-existing user worktrees or branches as part of lane cleanup.

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
