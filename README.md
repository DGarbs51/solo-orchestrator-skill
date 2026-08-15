# Solo Orchestrator

**One lead agent. Workers from five different labs. One reviewable pull request at the end.**

An agent skill that turns [Solo](https://soloterm.com) into a real orchestration layer: your lead agent interviews you, writes a plan into a Solo scratchpad, splits it into todos with blockers, spawns workers — Claude, Codex, Cursor, Kimi, or OpenCode, whichever fits the lane — watches them with idle timers, integrates one lane at a time, and opens the PR.

Works in Claude Code, Codex CLI, and Cursor from the same checkout.

---

## The problem this solves

You already run more than one coding agent. Claude Code in one tab, Codex in another, something cheap for the mechanical work. And you are the thing holding it together: re-explaining the goal to each one, remembering which agent touched which file, reconstructing what happened when a session scrolls away.

That coordination work is real work, and it is the part you are worst at, because chat scrollback is not memory. Close a worker and its context is gone. Compact a session and the plan goes with it. Two agents edit the same file and you find out at merge time.

Solo already ships the primitives that fix this — [shared scratchpads](https://soloterm.com/docs/scratchpads), [todos with blockers](https://soloterm.com/docs/todos), timers, locks, and a key-value store, all exposed to every connected agent over [MCP](https://soloterm.com/docs/integrations/mcp-server). What was missing was a procedure that makes an agent actually use them. That's this skill.

Aaron Francis, who builds Solo, [describes the layer this way](https://soloterm.com/blog/the-agentic-metaharness):

> A harness turns a model into a coding agent. A metaharness gives all of your harnesses a place to live.

This skill is one opinionated way to live there.

---

## Install

Clone it, read it, link it. No `curl | bash` — this skill spawns agents in auto-approve modes and rewrites your git workflow, so it's worth thirty seconds of reading first.

```bash
git clone https://github.com/DGarbs51/solo-orchestrator-skill.git
cd solo-orchestrator-skill
./install.sh
```

That symlinks the checkout into two directories, which covers all three major CLIs:

| Directory | Read by |
|---|---|
| `~/.claude/skills/solo-orchestrator` | [Claude Code](https://code.claude.com/docs/en/skills) |
| `~/.agents/skills/solo-orchestrator` | [Codex CLI](https://learn.chatgpt.com/docs/build-skills) and [Cursor](https://cursor.com/docs/skills) |

Because they're symlinks to one checkout, `git pull` updates every tool at once.

**Other options:**

```bash
./install.sh --targets all     # also OpenCode + Cursor's own ~/.cursor/skills
./install.sh --copy            # vendor a copy instead (no auto-updates)
./install.sh --project         # install into ./.claude, ./.agents, ./.cursor for this repo only
./install.sh --list            # show where it's currently installed
./install.sh --uninstall       # remove it
```

**Kimi Code** has no fixed skills directory — point it at whichever one you installed to:

```bash
kimi --skills-dir ~/.agents/skills
```

**Manual install**, if you'd rather not run a script: copy or symlink this directory to `<tool-skills-dir>/solo-orchestrator/`. The skill is just `SKILL.md` plus `references/`.

### Claude Code plugin

If you only use Claude Code, the repo doubles as a single-plugin marketplace:

```
/plugin marketplace add DGarbs51/solo-orchestrator-skill
/plugin install solo-orchestrator@solo-orchestrator
```

`claude plugin update solo-orchestrator` pulls new versions, and `/plugin` manages it in the UI. The tradeoff versus `install.sh`: this route is Claude-only and pins you to a released version, where the symlink route covers Claude, Codex, and Cursor from one checkout you can edit in place. Since the whole point of the git-workflow section below is that you'll want to edit it, most people should prefer `install.sh`.

**Verify it loaded** by starting a fresh session and typing `/solo-orchestrator`, or just asking your agent to "orchestrate" something. The skill also triggers on "split this across agents", "spawn workers", "parallel lanes", and any mention of Solo scratchpads or todos.

### Requirements

- **[Solo](https://soloterm.com)** running, with its MCP server connected to your agent ([setup](https://soloterm.com/docs/integrations/mcp-server)). Solo ships for macOS and Windows; `install.sh` assumes a Unix-style home directory.
- **At least one worker CLI** configured in Solo's Settings → Agents. More labs means better routing, but the skill works with one.
- **`git`**, and **`gh`** if you want the pull request opened for you. Without `gh`, the skill writes the PR body to a scratchpad instead.

If Solo's MCP tools aren't reachable, the skill says so up front and offers a single-agent fallback rather than pretending to coordinate.

---

## What a run actually looks like

Nine phases. The lead agent stays in the driver's seat the whole way.

| Phase | What happens |
|---|---|
| **0 · Orient** | `whoami`, `select_project`, `list_agent_tools`, `git status`. The configured agents are the menu — nothing is assumed. |
| **1 · Interview** | One question at a time until another answer wouldn't change the plan. Goal, "done", constraints, **non-goals**, risky files. |
| **2 · Branch, then plan** | `feature/<slug>` created and pushed **before any edits exist**. Then the plan goes into a `plan-<slug>` scratchpad. |
| **3 · Todos + blockers** | One todo per lane. Blockers encode dependencies. Dependent, tiny, or file-contested lanes stay with the lead. |
| **4 · Dispatch** | Usage preflight, then route each lane by fit. Spawn → check → set → confirm → task. Locks on anything two lanes could touch. |
| **5 · Monitor** | Idle timers, not polling. Read the worker's real output — summaries are triage, not evidence. Reconcile the plan on every wake. |
| **6 · Integrate** | One lane at a time. Smallest diff first, focused check, then a commit that records what changed, why, tests run, and which model wrote it. |
| **7 · Capture, then close** | Closing a worker deletes its session. Handoffs land in todos and the scratchpad *first*. |
| **8 · Ship** | The PR body is assembled from the plan, decisions log, handoffs, and commits — not from memory. Opened ready for review. **You merge.** |

`references/flow-diagrams.md` has all of this as three ASCII diagrams: the run, lane routing, and the usage/failover loop.

### The rules that make it work

- **The lead never mass-merges.** One lane, one diff, one commit.
- **Workers never commit.** They leave changes in the working tree and report on their todo. The lead reviews the real diff and owns every commit — even for workers in their own worktrees.
- **Workers never edit outside their lane.** If they need a file they don't own, they stop and report.
- **Nothing durable dies with a session.** Handoffs are captured before any worker is closed.
- **More agents is not the goal.** Three well-scoped workers beat eight colliding ones.

---

## The Solo features it leans on

This skill is built around [Solo's orchestration workflow](https://soloterm.com/docs/workflows/agent-orchestration) and uses these [MCP tool groups](https://soloterm.com/docs/mcp-tools):

**[Scratchpads](https://soloterm.com/docs/scratchpads)** — project-scoped Markdown, shared across every agent on the project. The skill keeps two:

- `plan-<slug>` — context, constraints, non-goals, the lanes, the verification plan, and an append-only **decisions log**. Solo's docs call the scratchpad "the shared memory for the run," and that's exactly the job: a worker should be able to act from it without you repeating the background. When the plan changes, the lead appends rather than rewrites, so the history survives to become the PR description.
- `model-catalog` — a cached list of available models across tools with a 2-hour TTL, so routing doesn't re-run `opencode models` and friends on every run.

**[Todos](https://soloterm.com/docs/todos)** — one per lane, carrying the objective, owned files, acceptance check, and what to report back. **Blockers** are how the lead knows what can run *now* — verification blocked by implementation, docs blocked by investigation. **Comments** carry the handoff: files changed, tests run, blockers hit, risks remaining. Each todo also records which agent and model took the lane, which is the evidence that improves routing next time.

**[Agents](https://soloterm.com/docs/agents)** — `list_agent_tools` enumerates what's configured, `spawn_agent` launches a worker, `send_input` drives it, `get_process_output` reads the actual pane.

**Timers** — `timer_fire_when_idle_any` wakes the lead when a worker goes idle; the all-idle variant gates a full integration pass. This replaces polling loops and blind waiting.

**Locks** — `lock_acquire` on any resource two lanes could touch, with the owning worker told which lock it holds.

**Key-value store** — available for small shared run state.

---

## Cross-lab routing

The single most useful thing Solo unlocks: **a Claude lead can spawn a Codex worker.** A Codex lead can spawn Kimi, Cursor, or OpenCode. If it's in `list_agent_tools`, it's on the menu. Defaulting to your own lab out of familiarity is treated as a routing failure.

Every lane gets classified, then matched to a tier:

| Lane type | Tier | Why |
|---|---|---|
| Bounded implementation | Fast/mid tier | The spec carries the intelligence |
| Investigation / debugging | Frontier, thinking on | Ambiguity is where cheap models waste your time |
| Architecture / design | Frontier — or keep it with the lead | Wrong here is expensive everywhere |
| Review / verification | Mid-to-frontier, **different lab than the author** | Same-lab review shares the author's blind spots |
| Docs / tests / mechanical | Cheapest capable tier | Free-tier models are fine when the acceptance check is cheap |

That cross-lab review rule is the sharpest edge in here. Disagreement between labs is signal, not noise.

### The five labs, verified

`references/worker-clis.md` is a field guide to the CLIs this was built against, re-verified 2026-08-08 against the `--help` output of the installed binaries — not against documentation:

| Lab | CLI | Solo MCP | Headroom check |
|---|---|---|---|
| Claude Code | `claude` | ✅ | `/usage` |
| Codex | `codex` | ✅ | `/usage` (+ reset credits) |
| Cursor | `agent` | ✅ | `/usage` |
| Kimi Code | `kimi` | ✅ TUI only | `/usage` |
| OpenCode | `opencode` | ✅ | none — `opencode stats` is spend, not headroom |

It also documents the things that quietly kill a run:

- **Startup gates.** Codex, Kimi, and Cursor all open trust dialogs on spawn. A worker parked at a modal looks alive and does nothing. Each gate's exact keystroke is listed.
- **Persisted defaults.** These CLIs remember their last-used model, mode, and thinking level. A freshly spawned worker is running whatever the previous session left behind — hence the **spawn → check → set → confirm → task** flow instead of trusting launch flags.
- **Quota as a routing input.** `/usage` is an in-session slash command in four of the five tools, so a headroom check costs a spawn and gets folded into a worker you were launching anyway. A worker that stalls or starts refusing work is often out of quota, not broken.
- **A tool that couldn't reach Solo MCP.** Antigravity (`agy`) was removed from the routing menu, with the evidence recorded so nobody re-adds it without re-testing.

**These are the five labs I subscribe to.** Nothing about the skill depends on that set. To add a lab: configure the CLI in Solo's Settings → Agents so it shows up in `list_agent_tools`, then add a section to `references/worker-clis.md` covering its model/mode/thinking commands, its startup gates, its usage command, and whether it can reach Solo MCP. That last one is the gate — a worker that can't call `whoami` or claim a todo can't coordinate, and becomes a black box you have to babysit.

---

## ⚠️ The git workflow is opinionated. Audit it.

`references/git-workflow.md` encodes **my** conventions, matched to my commit history. It is the file you should read before your first real run, and the file most likely to be wrong for your team.

What it currently insists on:

| Convention | Current default |
|---|---|
| Branching | `feature/<slug>` and `fix/<slug>`, created **and pushed** before any edits exist |
| Never on the default branch | Unless you explicitly say "do this on main" — an opt-in bypass, never inferred |
| Who commits | The lead, always. Workers never run `git commit`, `push`, `merge`, or `rebase` |
| Commit style | Conventional Commits with scopes: `feat(billing):`, `fix(ui):`, `chore(rules):` |
| Attribution | `Co-Authored-By:` trailers for both the worker model and the lead |
| Commit body | What changed and why, tests run with results, which agent produced it |
| PR | `gh pr create`, opened **ready for review**, explicit `--base` |
| Merging | Never by the agent. You merge. |

If your team squashes, uses `ticket/JIRA-123` branches, doesn't want model trailers in `git log`, protects `main` differently, or uses GitLab instead of `gh` — **edit that file before you run this.** The skill follows it faithfully, which is exactly the problem if it's describing someone else's workflow.

Two rules I'd keep even if you change everything else: the lead owning every commit (it's what makes "review the real diff" enforceable), and never merging the PR (the human stays the last gate).

---

## Customizing

Everything is Markdown. Fork it and edit.

| File | What to change |
|---|---|
| `SKILL.md` | The phases, the operating principles, the worker prompt template, the routing procedure |
| `references/git-workflow.md` | **Start here.** Branching, commits, attribution, PR format |
| `references/worker-clis.md` | Add or remove labs, update flags, adjust the default tiering table |
| `references/flow-diagrams.md` | The ASCII overview — regenerate after structural changes |

The frontmatter `description` in `SKILL.md` is what makes the skill trigger automatically. If it's firing too eagerly or not at all, that's the field to tune.

**A note on CLI drift:** these tools ship weekly. The skill tells the lead agent to run `<tool> --help` on the installed binary and trust that over the reference file whenever they disagree. Treat `references/worker-clis.md` as a good starting map, not scripture.

---

## Safety

The unattended-worker modes this skill uses (`--auto`, `--dangerously-skip-permissions`, `-a never -s workspace-write`, `--yolo`) execute file writes and shell commands without review. The skill only calls for them in repos you've pointed it at, and keeps ownership boundaries tight — **the lane boundary is the safety mechanism.** Read `SKILL.md` → Guardrails before running this on anything you'd hate to lose, and keep the first run small.

---

## Layout

```
SKILL.md                        the orchestrator: phases 0-8, routing, guardrails
references/
  flow-diagrams.md              the whole run in three ASCII diagrams
  worker-clis.md                per-lab flags, MCP reachability, usage commands
  git-workflow.md               branching, commits, the merge request  ← audit this
install.sh                      symlink or copy into your agents' skill dirs
.claude-plugin/
  plugin.json                   Claude Code plugin manifest
  marketplace.json              self-referential marketplace, so the repo installs itself
LICENSE                         MIT
```

## License

[MIT](LICENSE). Fork it, edit the git workflow, swap the labs, ship your own version.

## Links

- [Solo](https://soloterm.com) · [Docs](https://soloterm.com/docs) · [Solo for agents](https://soloterm.com/agents)
- [Agent orchestration workflow](https://soloterm.com/docs/workflows/agent-orchestration) — the pattern this skill implements
- [Scratchpads](https://soloterm.com/docs/scratchpads) · [Todos](https://soloterm.com/docs/todos) · [MCP tools](https://soloterm.com/docs/mcp-tools) · [MCP server setup](https://soloterm.com/docs/integrations/mcp-server)
- [The agentic metaharness](https://soloterm.com/blog/the-agentic-metaharness) — Aaron Francis on why this layer exists
- Skill formats: [Claude Code](https://code.claude.com/docs/en/skills) · [Codex](https://learn.chatgpt.com/docs/build-skills) · [Cursor](https://cursor.com/docs/skills)

Solo is built by [Aaron Francis](https://aaronfrancis.com). This skill is an independent community workflow, not an official Solo project.
