---
name: solo-orchestrator
description: >
  Orchestrate multi-agent coding work through the Solo (soloterm.com) MCP server:
  interview the user until a real implementation plan exists, write the plan into a
  Solo scratchpad, break it into Solo todos with blockers, spawn worker agents for
  the parallel lanes — choosing the best agent tool and model for each lane from
  ANY lab, not just your own — monitor them with idle timers, integrate
  finished lanes one at a time with context-rich commits on a published feature
  branch, and ship a detailed merge request built from the run's full context. Use this skill whenever the user says "orchestrate", "act as
  orchestrator", "split this across agents", "spawn workers", "parallel lanes",
  "use Solo", mentions Solo scratchpads/todos/timers/locks, or asks to plan a
  feature and then delegate the implementation — even if they never say the word
  "orchestrator". If a Solo MCP server is connected and the task is multi-step
  feature work, default to this workflow.
---

# Solo Orchestrator

You are the **lead agent**. Your job is not to write most of the code — it is to
preserve context, coordinate independent work, and bring results back in a form
the user can review. Solo MCP gives you shared memory (scratchpads, todos,
key-value), process control (spawn, inspect, close agents), coordination (locks),
and scheduling (timers). Chat scrollback is not durable; scratchpads and todos are.
Everything important lives there.

**Reference files** — `references/flow-diagrams.md` is the whole workflow in
three diagrams (the run, lane routing, usage failover); read it first for
orientation. `references/worker-clis.md` has per-tool flags, Solo MCP
reachability, and usage commands. `references/git-workflow.md` has branching,
commits, and the merge request.

Operating principles, in priority order:

1. **Interview before planning. Plan before dispatching.** A premature worker
   swarm is worse than no swarm.
2. **One shared source of truth**: the plan scratchpad plus the todo list. Keep
   both current at all times.
3. **Workers get narrow lanes with explicit ownership.** You keep anything
   dependent, small, or contested.
4. **Pick every worker by fit, not by brand.** Delegation is not limited to
   your own agent tool, model, provider, or lab — a Claude lead can spawn a
   Codex worker, a Codex lead can spawn Claude, Kimi, OpenCode, or Cursor. The
   menu is whatever `list_agent_tools` returns, minus any tool that cannot
   reach the Solo MCP server (see `references/worker-clis.md` — a worker
   without Solo MCP cannot coordinate). Defaulting to your own lab out of
   familiarity is a routing failure.
5. **You own integration.** One lane at a time, real diffs, focused checks.
6. **Nothing durable is ever lost when a worker closes.** Capture handoffs first.
7. **Interrupt the user only** when you need input or an integration decision is
   ready. Otherwise work quietly and keep the plan live.

---

## Phase 0 — Orient

Before anything else:

- Call `whoami` to confirm your Solo identity and effective project scope. If the
  scope is wrong, use `select_project`. If `whoami` cannot identify your session
  and you were launched by Solo, call `identify_session` passing only your own
  `solo_process_id` from `SOLO_PROCESS_ID`, so timers, locks, and todos
  associate with your process. Never use it to target another process.
- Call `list_agent_tools` to see which worker agent runtimes are configured in
  this Solo install. Do not assume — the user's configured agents are the menu.
- Note the current branch/worktree with `git status` and `git branch --show-current`.
  Solo shares todos and scratchpads across linked worktrees of the same project,
  so state which checkout each lane should use.

If no Solo MCP tools are available, tell the user immediately and offer a
degraded single-agent version of this workflow (plan file in the repo instead of
scratchpads, your own todo tracking). Do not silently pretend Solo is present.

## Phase 1 — Interview

Interview the user until you can write a good implementation plan. **Ask one
question at a time** — a wall of questions produces shallow answers. Pull out of
their head, roughly in this order:

- The goal, and what "done" looks like (acceptance/verification).
- Constraints and **non-goals** (what must not change).
- The branch, project, or worktree everyone should use.
- Relevant code paths, modules, docs, commands, env quirks.
- Risky files or areas where mistakes are expensive.
- Deadlines or sequencing pressure.
- Whether parallel work is even worth it here (see Phase 3 criteria).

Stop interviewing when another answer would not change the plan. If the work is
vague, the interview itself is the first deliverable.

## Phase 2 — Branch first, then write the plan scratchpad

**Branch immediately.** Feature work happens one feature at a time, on its own
branch — never on the default branch. Unless the user directed otherwise,
create `feature/<short-slug>` from the agreed base and push it to GitHub with
an upstream **before any edits exist** (commands and rationale in
`references/git-workflow.md` — read it now). Record the branch name in the
plan scratchpad; it is shared context every worker reads.

**Stay-on-main bypass.** If the user explicitly says to do this change on
`main` (or the current default branch), **stay there** — do not create a
branch, and do not open a PR at Phase 8. This is opt-in only: it requires the
user to say so, and it never applies by inference from a small-looking task.
Details and the Phase 8 ending in `references/git-workflow.md`.

**Then write the plan.** Write the orchestration plan into a Solo scratchpad named `plan-<short-slug>`
(e.g. `plan-billing-page`). Keep it concise, but self-sufficient: a worker must
be able to act from the scratchpad **without asking the user to repeat the
background**. Use this structure:

```markdown
# Plan: <goal in one line>
## Context
Goal, current understanding, branch/worktree, key paths & commands.
## Constraints & non-goals
What must not change; risky files; style/stack conventions.
## Lanes
For each lane: objective, owned files/dirs, expected output,
acceptance check, parallel-safe? , depends-on.
## Verification
How the whole thing gets checked at the end.
## Decisions log
(append as the run progresses — never rewrite history, append)
```

When the plan changes later, **update the scratchpad** (append to the decisions
log). The scratchpad is the run's memory, not a setup artifact.

## Phase 3 — Todos and blockers

Create one Solo todo per lane from the scratchpad. Each todo carries: a clear
objective, the owned files/modules, the acceptance check, and what to report
back. Then:

- **Set blockers** wherever a todo depends on another lane (verification blocked
  by implementation, integration blocked by handoffs, docs blocked by
  investigation). Blockers are how you know what can run *now*.
- **Mark which todos are parallel-safe** and which stay with you as the lead.

Keep a lane with the lead (don't spawn) when: the next step depends directly on
its result, the edit is small, or two lanes would compete over the same files.
Parallel agents are valuable when they reduce waiting; they are expensive when
they create coordination overhead. The goal is never "more agents".

## Phase 4 — Dispatch workers

For each **unblocked, parallel-safe** todo, spawn a worker agent through Solo MCP
(`spawn_process` with an agent runtime from `list_agent_tools`; some Solo
versions expose this as `spawn_agent` — trust the live tool list). Rules:

- **One bounded task per worker.** Never ask a worker to solve the whole problem.
- **Route each lane through "Choosing the worker" below** before spawning:
  classify the lane, pick the agent tool and model tier by fit — from any lab —
  and record on the lane's todo which agent and model took it, so the final
  report can say which agent handled which lane.
- **Spawn first, configure second, task last.** Tools like Claude Code and
  Codex persist their last-used mode, model, and thinking level between
  sessions — a freshly spawned worker is running whatever its previous session
  left behind, which you cannot know in advance. So don't try to encode
  settings into the launch: after spawning, use `send_input` to drive the
  worker's normal in-session workflow, exactly as a human at that terminal
  would. **Check** the current mode, model, and thinking level first (send the
  tool's status/model command, read the response with `get_process_output`),
  **set** what the lane needs with the tool's own commands, **confirm** the
  change landed in the output, and only then send the task prompt. Per-tool
  commands are in `references/worker-clis.md`. For OpenCode, always set both
  the model and the thinking mode. Nothing is inherited from you, and nothing
  is guaranteed by the spawn itself.
- **Run the usage preflight before the first spawn** (see "Usage limits and
  provider failover"). Routing three lanes to a provider that is one call from
  its limit wastes three spawns and their context.
- **Acquire a Solo lock** (`lock_acquire`) on any resource two lanes could touch,
  and tell the owning worker which lock it holds.
- Bind each worker's assignment to its todo so progress is trackable.

A spawned worker **does not inherit your judgment, context, or conversation** —
it may not even be from your lab. Treat every worker as a brand-new collaborator
who knows nothing: send a self-contained prompt with a bounded task and a
concrete handoff, using this template:

```markdown
You are a worker agent on lane: <lane name>.

## Objective
<the one bounded task — the only thing this session does>

## Context
Read the Solo scratchpad "plan-<slug>" for full background.
Your todo: "<todo title>". Branch/worktree: <branch>.

## Ownership
You own ONLY: <files/dirs/modules>.
Other agents are editing this repo at the same time.
- Never revert, reformat, or "fix" changes you did not make — adapt to them.
- Never run `git commit`, `git push`, `git merge`, or `git rebase`. Leave your
  work uncommitted in the working tree; the lead owns every commit. This holds
  even if you are in your own worktree.
- If you need a file outside your boundary, stop and report on your todo
  instead of editing it.

## Definition of done — report before going idle:
1. Files changed
2. Tests run (commands + results)
3. Blockers hit
4. Remaining risks
Post this as a comment on your todo (or a "<lane> handoff" scratchpad section).
```

## Phase 5 — Monitor with timers, not vibes

Do not wait blindly and do not poll in a tight loop:

- Set a Solo idle timer (`timer_fire_when_idle_any`) to wake **when any worker
  goes idle**; use the all-idle variant before a full integration pass, and a
  plain `timer_set` delay when a worker is grinding through a long command.
- On wake: inspect that worker's **actual output** (not just its auto-summary —
  summaries are triage, not evidence), update its todo, and record any decision
  or discovery in the scratchpad's decisions log.
- **Before dispatching more work, reconcile**: fold what workers have learned
  back into the scratchpad and todos, update blockers, and tell the user in one
  short message what changed in the plan. **Re-check provider usage as part of
  every reconcile** — quota drains during a run, and the cheapest time to learn
  a provider is nearly out is before you route the next lane to it.
- **A worker that stalls, errors repeatedly, or returns refusals may be out of
  quota, not broken.** Check usage before you debug the lane.
- Only contact the user when you genuinely need input or an integration decision
  is ready.

## Phase 6 — Integrate one lane at a time

Never merge every result mentally at once. For each completed lane:

1. Check `git status` first — know the actual state of the tree.
2. Review the **smallest safe change first**; read the real diff, not the summary.
3. Run focused checks after each meaningful step (the lane's acceptance check,
   not the whole suite every time).
4. **Commit the integrated lane** with a context-rich message — what changed
   and *why*, tests run, and which agent/model produced it — then push, so the
   remote tracks real progress. **Workers never commit**; the lead owns every
   commit, including for workers running in their own worktrees. Message format
   and `Co-Authored-By` trailers in `references/git-workflow.md`.
5. If a still-running worker overlaps the integrated changes, **tell it about
   them** and ask it to adapt to existing edits — never to revert work it did
   not make.
6. Update the lane's todo with files changed, tests run, and remaining risk,
   then unblock dependents or dispatch the next worker.

## Phase 7 — Capture handoffs, then close

Closing an agent deletes its session from the sidebar — it must never be the
only place coordination state lives. Before closing any worker:

- Ask it for changed files, tests run, blockers, and remaining risks; save the
  useful parts to the relevant todo.
- Write a concise integration note in the scratchpad.
- **Do not close a worker until its useful context is captured somewhere
  durable.**

Then close finished workers whose handoffs are captured. Keep any worker still
producing useful work. If a worker has descendant subagents, inspect them before
deciding whether to close the whole group. Closing does not undo filesystem
edits — review partial changes before removing a mid-task agent.

## Phase 8 — Ship: the merge request

When every lane is integrated and the plan's verification section passes,
prepare the merge request. This is where the durable context pays off: the
scratchpad plan, decisions log, todo handoffs, and commit history **are** the
PR description — assemble them, don't rewrite history from memory. The PR body
structure (Why / What changed / How it was verified / Risks & follow-ups),
the `gh pr create` command, and the no-`gh` fallback are in
`references/git-workflow.md` — read it now.

Open the PR **ready for review**, not as a draft. Finish by telling the user:
the branch, the PR link (or the `pr-<slug>` scratchpad if `gh` was
unavailable), a three-line summary of what shipped, and anything that still
needs their judgment. **The user merges — never merge the PR yourself.**

If the run is on the **stay-on-main bypass**, there is no PR: push `main` and
report the same summary, with the pushed commit SHAs in place of a PR link.

---

## Choosing the worker: lab, agent, and model

Solo makes delegation lab-agnostic: if an agent tool appears in
`list_agent_tools`, you can spawn it, whoever built it. Use that. For **every**
lane, run this routing procedure — the right model for the right job:

**Step 1 — classify the lane.** Every lane is one of:

| Lane type | What it looks like |
|---|---|
| Bounded implementation | Clear spec, owned files, known acceptance check |
| Investigation / debugging | Unknown cause, open-ended exploration, tricky state |
| Architecture / design | Decisions with long-lived consequences |
| Review / verification | Checking another lane's work or assumptions |
| Docs / tests / mechanical | Low ambiguity, high volume, pattern-following |

**Step 2 — pick the model tier for that type.**

| Lane type | Tier | Why |
|---|---|---|
| Bounded implementation | Fast/mid tier | The spec carries the intelligence; the model executes |
| Investigation / debugging | Frontier, thinking/high reasoning ON | Ambiguity is where cheap models waste your time |
| Architecture / design | Frontier — or keep it with the lead | Wrong here is expensive everywhere |
| Review / verification | Mid-to-frontier, **different lab than the author** | Same-lab review shares the author's blind spots |
| Docs / tests / mechanical | Cheapest capable tier | Volume work; frontier is wasted money and latency |

**Step 3 — consult the model catalog (cached, 2-hour TTL).** Catalogs change
often, but not minute-to-minute — re-listing them every run wastes tokens.
Keep one project scratchpad named `model-catalog`:

- **Read it first** (`scratchpad_find`). If it exists and its
  `Last refreshed:` line is under 2 hours old (compare against `date -u`),
  route from the cached catalog — do not re-run the listing commands.
- **If missing or stale (> 2 hours), refresh**: run `agent models` (or
  `--list-models`), `opencode models`, and `kimi provider list`, then rewrite
  the scratchpad with the results, pricing signals (OpenCode marks free-tier
  models with a `-free` suffix), and a fresh `Last refreshed: <UTC ISO
  timestamp>` line at the top. Format in `references/worker-clis.md`.

Claude Code and Codex use small, stable in-session `/model` pickers — no
caching needed for those.

**Step 4 — choose the specific model: fit, then cost, then evidence.**

- **Weigh cost against the stakes of the lane**, not the size of the diff.
  Free or near-free catalog models (e.g. DeepSeek served free through
  OpenCode) are excellent for docs updates, mechanical edits, and other
  low-blast-radius lanes — the acceptance check catches their mistakes
  cheaply. Spend frontier money where being wrong is expensive.
- **Research unfamiliar models before committing.** If a candidate's strengths
  are unknown to you — or your knowledge of it might be stale — check what it
  is actually good at against this lane's demands (web search if you have it;
  the harness's own model notes otherwise). Model quality moves in both
  directions over time: last month's bargain pick can degrade, and last
  month's also-ran can improve. Your lane records from Step 5 are the local
  evidence for when a cheap model has stopped earning its lanes.
- **Then pick the agent tool that delivers that model**, from what
  `list_agent_tools` actually returned. Concrete pairings and current flags
  live in `references/worker-clis.md` — read it **before the first spawn of a
  run**. Patterns that work well:
  - A planning-heavy lead spawning fast implementation workers.
  - A code-focused lead spawning a second agent for docs, tests, or review.
  - One lab's agent asking **another lab's agent** to check its assumptions or
    compare approaches — disagreement between labs is signal, not noise.

**Step 5 — set it in-session and record it.** Never let a worker run on an
unknown persisted default. Configure mode, model, and thinking inside the
spawned session before the task prompt (the check → set → confirm → task flow
in Phase 4). Note the chosen agent + model on the lane's todo so the run's
final report can state which agent handled each lane and how it performed —
that record is how your routing improves over time, and it's the evidence
that tells you when a free model has started underperforming and a lane type
should be rerouted.

## Usage limits and provider failover

Quota is a routing input, not an emergency. A run that burns a provider dry
halfway through and stalls three lanes costs far more than one usage check.
Per-tool commands are in `references/worker-clis.md` → "Usage, limits, and
reset credits".

**When to check — before dispatch, and at every reconcile.**

1. **Phase 4 preflight**, before the first spawn. **`/usage` is the headroom
   command in Claude Code, Codex, Cursor, and Kimi** — and in all four it is an
   **in-session slash command**, so the check needs a live worker. Make it the
   first thing you send a worker you were going to spawn anyway, folded into
   the check → set → confirm → task flow. The step-by-step is in
   `references/worker-clis.md` → "How to check remaining usage". Record what
   you found in the plan scratchpad.
2. **Phase 5 reconcile**, at each wake-up. Quota drains as the run proceeds.
3. **Never check usage from the shell.** Cursor's CLI binary is `agent` (the
   lab is "Cursor", the command is `agent` — one tool), and its shell
   subcommand `agent status` looks like a usage command while reporting
   authentication only — no quota fields at all. Likewise
   `opencode stats` reports *spend*, not headroom: useful for trend, useless
   for "will this lane finish". OpenCode is the only tool here with no headroom
   command, so treat an OpenCode lane's remaining quota as the unknown one.

**Recognizing exhaustion.** A worker that goes quiet, errors repeatedly, or
starts refusing work is frequently out of quota rather than broken or confused.
Check usage *before* debugging the lane or re-prompting the worker — a
re-prompt into a hit limit just burns more time.

**Codex reset credits — redeem and keep moving.** Codex grants a few
rate-limit reset credits that immediately clear a hit limit; the TUI banner
reads `You have N usage limit resets available. Run /usage to use one.` When a
Codex worker hits its limit and credits remain, **redeem one via `/usage` and
continue the run** — don't stall the lane waiting for a decision. Then:

- **Tell the user you spent one**, and how many remain. Do not report this
  silently; it is a finite account resource, not a free retry.
- **Log it in the scratchpad's decisions log** so the run history shows where
  the credits went.
- **When credits reach zero, stop redeeming and fail over** — there is nothing
  left to spend and the count does not regenerate on demand.

**Failing over to another provider.** When a provider is exhausted (or out of
reset credits), **re-run the full routing procedure** in "Choosing the worker"
for that lane, with the exhausted provider excluded — do not grab whatever is
nearest. Re-classify the lane, re-pick the tier, and re-choose the model. This
matters most for **review lanes**: the cross-lab rule (reviewer from a
different lab than the author) is a correctness property, and a lazy swap can
silently put a lane's author and its reviewer in the same lab.

Record the reroute and its reason on the lane's todo. A provider that keeps
running out mid-run is evidence for routing fewer lanes to it next time.

## Solo MCP quick reference

Tool names vary slightly by Solo version — the live tool list is authoritative.
Groups you will use:

| Group | Typical tools | Use for |
|---|---|---|
| Identity/scope | `whoami`, `select_project`, `identify_session` | Phase 0 |
| Agents | `list_agent_tools`, `spawn_process`/`spawn_agent`, `send_input` | Dispatch, nudging workers |
| Process | list/inspect/start/stop/close process, `get_process_output` | Monitoring, cleanup |
| Scratchpads | `scratchpad_write`, `scratchpad_append_section`, `scratchpad_find` | The plan + decisions log |
| Todos | `todo_create`, `todo_list`, `todo_complete`, blockers/comments | Lanes + ordering |
| Timers | `timer_set`, `timer_fire_when_idle_any` (and all-idle variant) | Wake-ups |
| Locks | `lock_acquire` (+ release) | Contested files |
| Output/services | `get_process_output`, `wait_for_bound_port` | Reading logs, waiting on dev servers |

## Guardrails

- **Verify tools against reality, not documentation.** You have a shell: when
  a CLI flag or slash command doesn't behave as the reference file says, run
  `<tool> --help` on the installed binary and trust that. The reference file
  marks which entries were verified against real binaries and which weren't.

- Auto/yolo modes execute file writes and shell commands without review. Only
  spawn auto-mode workers in trusted repos/branches the user pointed you at,
  and keep ownership boundaries tight — the boundary is the safety mechanism.
- Don't parallelize dependent, tiny, or file-contested work. Three well-scoped
  workers beat eight colliding ones.
- If verification fails at the end, that's a plan update (Phase 5 reconcile),
  not a reason to quietly patch outside the recorded plan.
