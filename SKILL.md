---
name: solo-orchestrator
description: >
  Run inside Solo to coordinate coding workers through its MCP server: interview,
  plan, delegate bounded
  lanes across agent CLIs, monitor, integrate, and prepare a pull request.
  Use only when the user explicitly invokes the solo-orchestrator skill by
  name, skill selector, or command.
disable-model-invocation: true
---

# Solo Orchestrator

Run only when the user invokes this skill. Auditing or editing its files is not
an invocation. You are the lead: own the plan, routing, integration, and final
report. Keep routine progress in Solo; contact the user only for required input
and the final report. User instructions and existing approvals govern the run.

Read references when needed, not all at startup:

- [Git workflow](references/git-workflow.md): branching, lane worktrees,
  worker commits, integration, and cleanup. Read after plan approval.
- [Worker CLIs](references/worker-clis.md): read only the selected tools'
  configuration, model/usage commands, and startup checks before dispatch.
- [Routing cache](references/routing-cache.md): read before selecting models
  or refreshing usage; shared across projects on this machine.
- [Flow diagrams](references/flow-diagrams.md): optional visual overview.

## 0. Orient

Execution requires a lead running inside Solo, connected to its MCP server,
with its own Solo process identity and timer delivery available. Call `whoami`
to confirm the lead process and effective project. Resolve a missing/wrong
project with `list_projects` and `select_project`, or explicit `project_id`
arguments. If your Solo-launched session is unidentified, use `identify_session`
with your own `SOLO_PROCESS_ID`; never impersonate another process. An external
actor identity or MCP connectivity alone does not satisfy this requirement.

Outside Solo, limit work to reviewing/maintaining the skill and preparing a
handoff prompt for a Solo-running orchestrator. Include the user's objective,
known constraints/decisions, relevant repository paths, and unresolved questions.
Label it as preparation, not an approved execution plan: the Solo lead must
verify current state, display its concrete plan, and obtain approval before
execution. Do not create run state, branches, or workers from the external
session, or substitute external monitoring or a local orchestration fallback.
Skill maintenance itself remains outside this execution workflow.

If the Solo execution requirements cannot be confirmed, explain what needs to
be restored or moved into Solo before proceeding. Once confirmed, read repository
instructions, Git status, branch, worktrees, and configured runtimes from
`list_agent_tools`. Preserve existing edits. Use live MCP schemas;
`spawn_agent` currently accepts `extra_args` for per-launch settings.

## 1. Interview

Ask one question at a time until another answer would not change the plan.
Reuse context already supplied. Establish the goal, acceptance checks,
constraints/non-goals, branch/base, relevant paths, and expensive risks.
Inspect code to resolve questions the repository can answer. Determine whether
independent lanes justify delegation; keep tiny, dependent, or contested steps
with the lead rather than spawning unnecessary workers.

## 2. Display the plan and wait for approval

Create a `plan-<run>` scratchpad marked `awaiting approval`. Include:

- Goal, constraints, non-goals, and key paths/commands.
- Proposed base/integration branch and lane checkout arrangement.
- Each lane's objective, owned files, dependencies, and acceptance check.
- Whole-run verification and an append-only decisions log.

Display the concrete plan to the user, not just a scratchpad link. Wait for
explicit approval; revise and redisplay if requested. Before approval, perform
inspection/planning only: no implementation edits, branch publication, or workers.
Record approval, then create/push the agreed branch using the Git reference.
The explicit stay-on-main choice is supported; never infer it from task size.

For significant changes to approved scope or approach, pause affected lanes
and dependents, including running workers. Preserve partial work and show the
proposed revision, reason, and impact. Wait for approval; unrelated approved
work continues. Keep pending revisions distinct from the approved plan. After
approval, update plan/todos/worker instructions and append the decision. Routine
implementation choices within the plan do not need renewed approval.

## 3. Track lanes

Create one Solo todo per lane with objective, ownership, acceptance, and handoff
requirements. Set dependency blockers. Record plan/todo IDs so workers can read
directly; `scratchpad_list(query=...)` locates a plan, while `scratchpad_find`
searches within a known scratchpad. Use the current revision when editing a
scratchpad; on a revision conflict, reread and preserve the other changes.

Workers report ready for review. Only the lead completes implementation todos
and releases their dependency blockers after accepted integration and checks.
For investigation/review lanes without code, acceptance means reviewing their
findings/evidence. Use advisory locks only for genuinely shared resources;
record the holder, renew when needed, and release when the protected work ends.

## 4. Route and dispatch

Use adaptive concurrency with no fixed worker cap. Dispatch independent ready
lanes when shared quota, machine capacity, and integration throughput support
them. Slow new dispatch on throttling, build contention, memory pressure, or a
backlog of unreviewed handoffs. Do not repeatedly probe every worker or stop
useful work to meet an arbitrary count.

Choose among configured, usable runtimes, regardless of model lab:

| Lane | Selection guidance |
|---|---|
| Clear bounded implementation | Efficient capable model; the spec should resolve ambiguity |
| Investigation/architecture | Stronger reasoning when uncertainty or consequences warrant it; lead may retain it |
| Docs/mechanical work | Efficient model with cheap acceptance checks |
| Review/verification | Prefer another model lab; capable same-lab review is valid |

Read relevant shared cache entries first. Prefer capable models covered by
existing subscriptions with available quota before extra paid usage. Different
CLIs may consume the same account pool; do not count it twice. Model listings
alone prove neither included billing nor headroom. Compare known quality,
latency, quota pressure, and recent lane outcomes; research only unresolved
routing questions and retain concise dated findings.

Cross-lab review is a preference, not a prerequisite. If needed, use a fresh
same-lab reviewer; give it requirements, diff, and evidence without seeding the
author's conclusions. Different CLIs serving the same lab are still same-lab.
If only the lead is available, it reviews. Do not abandon single-lab runs.

**Extra charges require approval.** Show the proposed paid route and spending
limit, then wait. Existing explicit approval applies only within its scope and
limit. Skill invocation, plan approval, cached billing, or previous paid runs
are not authorization. Do not enable overages or metered fallback implicitly.

Give each implementation worker a separate lane branch/worktree from the
current integrated base. Record its absolute path, starting SHA, process ID,
model/effort, and account route on the todo. Follow the Git and CLI references
for launch directory and permissions; confirm the real checkout before tasking.

Supply supported model/effort/permission settings at launch through `extra_args`,
then verify effective settings, checkout, and Solo MCP access in the session.
Inspect saved runtime arguments for conflicting bypass flags. Use in-session
controls for corrections or unsupported launch settings; avoid global changes.
Prefer automatic approval review and sandboxing where supported; otherwise
retain scoped approvals. A denial is not permission to switch to bypass mode.
The lead may handle narrow, already-authorized actions when host policy permits;
broader authority needs user input. Keep unrelated work moving.

Put the self-contained assignment in a prompt file outside the disposable lane
checkout, such as the lead's ignored `.worktrees/prompts/<run>-<lane>.md`.
Include useful bootstrap instructions returned by Solo in that file. Send a
short pointer via `send_input`, with the absolute file path at the end; large
TUI pastes have been truncated in prior runs. Include this contract in the file:

```text
Task: <one objective and acceptance check>
Plan/todo: <IDs, coordination project ID, relevant context>
Checkout: <absolute path>; branch: <lane branch>; starting SHA: <sha>
Ownership: <paths>; dependencies: <accepted prerequisites>
Settings: <model/effort and permission mode>

Confirm cwd/branch and call Solo whoami before edits. Work only in this checkout
and owned paths. Report needed scope changes rather than editing outside them.
Commit coherent changes locally on your lane branch, staging explicit paths.
Do not push, merge, rebase, amend commits, alter shared Git settings, or modify
other worktrees. Do not spawn additional workers without lead coordination.

Run checks and commit the deliverable. Post one todo handoff: starting/final
SHA, files changed, check commands/results, blockers/risks, and remaining local
files. Report ready for review; stop editing until reassigned. Do not complete
the todo. Report blockers/material discoveries promptly, not every commit.
```

## 5. Monitor and recover

Use Solo idle timers for running workers, with a maximum-wait guard and a body
containing process/plan/todo IDs and the next inspection. Deliver to the lead's
actual Solo process; never re-identify to redirect a timer. If scheduling says
`already_satisfied`, inspect now; no future wake-up was scheduled. Exclude
already-reviewed idle workers when rearming. Idle can mean an approval prompt,
a failure, or completion: inspect real output and the handoff before deciding.
Cancel run timers when done. If Solo identity, connectivity, or timer delivery
fails mid-run, stop new dispatch and preserve the run state and lane handoffs.
Pause affected workers when reachable; if they cannot be reached, explicitly
report that their state is unconfirmed. Restore supervision inside Solo before
resuming; do not replace it with an external monitoring loop.

At reconciliation update todos, blockers, and the plan. Consult cached quota
and in-run observations; refresh only affected stale/invalidated pools under
the cache rules. Check actual errors before diagnosing silence as exhaustion.
Keep routine progress in Solo and ask only for required input.

On quota exhaustion, preserve committed and partial work, stop the old worker
before giving another worker its checkout, and reroute from the current lane
state. Prefer another capable included/free route; paid fallback needs approval.
If none is usable, retain the lane and report the blocker/known reset time.
Do not repeatedly spawn into an exhausted pool or duplicate the lane from scratch.

Existing Codex rate-limit reset credits may be redeemed automatically when
needed. Confirm redemption and the remaining count, update the quota cache,
and log the event for the final report. Inspect uncertain results before retrying
to avoid spending another credit. Buying credits/paid overages still needs approval.

## 6. Accept and integrate

Follow the Git reference one ready lane at a time. Freeze and review the
reported SHA from its recorded base, inspect remaining files, merge that exact
SHA with lane history preserved, and verify the combined result before pushing.
Resolve straightforward conflicts; return substantive fixes to the worker with
a bounded follow-up and require a new handoff SHA. Significant scope changes
return to the approval step. Reuse applicable worker tests while checking
interactions and assumptions changed by integration.

Record acceptance, integration SHA, and checks; then complete the todo and
unblock dependents. Notify only workers affected by integrated changes. Store
a compact outcome and any fresh usage evidence in the shared cache.

## 7. Clean up promptly

Reuse the saved handoff; ask only for missing information. Once accepted and
verified, close the worker and confirm descendants/still-running commands have
stopped. Remove its worktree and lane branch using the Git reference's checks.
Do this per finished lane rather than retaining everything until run end.
Preserve failed/interrupted lanes until integrated or explicitly discarded by
the user. Release owned locks and cancel obsolete timers. Never remove unrelated
user worktrees, processes, or branches.

## 8. Deliver

After all accepted lanes and whole-run verification, open a ready-for-review PR
using the Git reference. Assemble its description from the final plan, decisions,
handoffs, and commits; omit superseded proposals. The user merges the final PR.
On explicit stay-on-main runs, report pushed commits instead. Without a working
remote/PR client, preserve local work and prepare the PR body, clearly identifying
what remains unpublished.

Give one final report: branch, PR link or local fallback, outcome, verification,
remaining decisions/risks, and any reset credits used/remaining. Keep detail
proportional to the change; do not reproduce every lane transcript.
