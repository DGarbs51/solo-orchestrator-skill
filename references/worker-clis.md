# Worker CLI cheat sheet — configuring mode, model, and thinking

**Verification status:** re-verified 2026-08-08 against the `--help` output of
the installed binaries, at these versions:

| Tool | Command | Version verified | Solo MCP |
|---|---|---|---|
| Claude Code | `claude` | 2.1.226 | ✅ verified |
| OpenCode | `opencode` | 1.18.15 | ✅ verified |
| Codex CLI | `codex` | codex-cli 0.147.0 | ✅ verified |
| Cursor Agent | `agent` | 2026.08.04-aaa8809 | ✅ verified |
| Kimi Code CLI | `kimi` | 0.34.0 | ✅ verified (TUI only) |

**Standing rule for the lead:** you have a shell. When a flag or command below
doesn't behave as documented, run `<tool> --help` yourself and trust that over
this file. CLIs ship weekly; `--help` on the installed binary is the only
source that cannot be stale. Note that `--help` short-circuits argument parsing
in most of these tools, so `tool --someflag --help` printing help does **not**
prove `--someflag` exists — test the flag against a real subcommand instead.

---

## Solo MCP reachability — check this before routing a lane

**A worker that cannot reach the Solo MCP server cannot coordinate.** It can't
call `whoami`, claim todos, take locks, read the plan scratchpad, or report
completion. It becomes a black box you have to babysit through
`get_process_output`, which defeats the point of the swarm.

All five tools above were verified on 2026-08-08 by spawning a real Solo agent
in each and calling `whoami()` end-to-end — not by reading config files. Each
returned its own `process_name` and `project_id=12`. Solo exposes **95 tools**
to clients.

Tool-name spelling differs per client — don't assume the `mcp__solo__` form:

| Tool | How the Solo tool appeared |
|---|---|
| Claude Code | `mcp__solo__whoami` |
| OpenCode | `solo_whoami` |
| Codex | `solo.whoami` |
| Cursor | `solo whoami` |
| Kimi | `mcp__solo__whoami` |

**If a lane's worker comes back with no Solo tools, check these before assuming
the CLI can't do it:**

1. **Was the folder trusted?** Kimi loads project MCP servers *only in trusted
   folders*, and Codex/Cursor gate config loading behind their own trust
   prompts. An untrusted session silently has no MCP.
2. **Was it print mode?** `kimi -p` loads **no MCP servers at all** — its tool
   list comes back with zero MCP entries even though the TUI connects fine.
   Treat headless/`--print` runs as MCP-less unless you've proven otherwise for
   that tool.
3. **Is the config non-empty?** Verify the actual file, not your memory of it.

### Startup gates that stall a worker silently

A worker sitting at a modal prompt looks alive and produces no output. This is
the single most common way a lane dies quietly. Observed on spawn:

| Tool | Gate on spawn | Clear it with |
|---|---|---|
| Codex | workspace trust dialog | `send_input` bytes `[13]` (Enter, "Yes, continue") |
| Kimi | "Trust this folder?" dialog | `send_input` bytes `[13]` (Enter) |
| Cursor | "Workspace Trust Required" | `send_input` `"a"` with `submit: false` |
| Kimi | **second** gate: per-tool approval on the first MCP call | `"2"` (approve for session), or launch with `--auto` |
| Claude Code | none observed | — |
| OpenCode | none observed | — |

This is exactly what the **spawn → check → set → confirm → task** flow below is
for. Always read output after spawning; never send the lane prompt blind.

---

## Usage, limits, and reset credits

Verified 2026-08-08. Policy for *when* to check and what to do when a provider
runs dry is in SKILL.md → "Usage limits and provider failover"; this is the
mechanics.

**Distinguish two different questions.** *Headroom* ("how much quota is left
before I'm cut off") is what routing decisions need. *Spend* ("what have I
consumed") is a cost report and says nothing about when you'll be throttled.

**`/usage` is the headroom command in four of the five tools** — and in every
case it is an **in-session slash command**, not a shell subcommand. Checking
the shell CLI is not a substitute and will tell you the wrong thing.

Lab name vs CLI command — these are the same tool under two names, and the
tables below use `binary` to keep it unambiguous:

| Lab / product | CLI binary |
|---|---|
| Claude Code | `claude` |
| Codex | `codex` |
| **Cursor** | **`agent`** (not `cursor`; the `cursor-agent` name is stale) |
| Kimi Code | `kimi` |
| OpenCode | `opencode` |

| Lab (`binary`) | Command | Where | Headroom? | What you get |
|---|---|---|---|---|
| Claude Code (`claude`) | `/usage` | in-session | ✅ yes | 5-hour session window + 7-day weekly window, with usage against each |
| Codex (`codex`) | `/usage` | in-session | ✅ yes | Rate-limit status **and** the reset-credit redemption flow |
| Cursor (`agent`) | `/usage` | in-session | ✅ yes | Plan tier + reset date, % bars for Included / Auto / API, on-demand state, dashboard link |
| Kimi (`kimi`) | `/usage` | in-session | ✅ yes | % bars for the weekly limit and the 5-hour limit, each with time-to-reset, plus context-window fill |
| Claude Code (`claude`) | `/cost` | in-session | ❌ spend | Spend for the current session |
| OpenCode (`opencode`) | `opencode stats [--days N] [--models] [--project ""]` | **shell** | ❌ spend | Local history: sessions, cost, tokens, tool usage |

Sample shapes, so you know what to read out of the pane:

```
Cursor /usage              Kimi /usage
 Usage • Pro                Plan usage
   Resets Aug 30              Weekly limit  ░░░░  2% used  resets in 5d 23h
 Included   1% used  █░░░     5h limit      ██░░  9% used  resets in 3h 22m
   Auto     0% used  ░░░░   Context window
   API      1% used  █░░░     ░░░░  0%  (0 / 256k)
 On-Demand  Disabled
```

Consequences for the preflight:

- **Every real headroom check needs a live session**, so it costs a spawn. Fold
  it into a worker you were going to spawn anyway rather than spawning one just
  to ask.
- **Don't check usage from the shell.** Cursor's binary is `agent`, and its
  shell subcommand `agent status --format json` reports *authentication only* —
  `status`, `isAuthenticated`, token flags, `userInfo`, and no quota fields
  whatsoever. Same tool, wrong surface: Cursor's real numbers are behind
  `agent`'s **in-session** `/usage`. It looks like a usage check and is not one.
- **`opencode stats` is not a quota check either.** It runs free from the shell
  and is worth reading for consumption trend, but it reports what you *spent*,
  not what remains. OpenCode also routes across many providers (including free
  tiers), so "remaining quota" there is per-provider and not something the CLI
  aggregates. OpenCode is the one tool with no headroom command.
- **Kimi and Cursor both expose time-to-reset.** When a limit is close, that
  tells you whether waiting is cheaper than rerouting the lane.

### How to check remaining usage (the procedure)

`/usage` is a slash command inside a running session, so you need a live worker
to ask. Never spawn a throwaway agent just to check — fold the check into a
worker you were already going to spawn, as the first thing you send it.

```
1. spawn_agent(agent_tool_id=<tool>)          → note the process_id
2. get_process_output(process_id)             → clear any trust/approval gate
                                                 (see "Startup gates" above)
3. send_input(process_id, "/usage", wait_ms=9000)
4. read the returned pane: % used, limit window, time-to-reset
5. send_input(process_id, bytes=[27])         → Esc, close the usage pane
                                                 (Cursor shows "Esc to close")
6. …then continue with check → set → confirm → task for the real lane
```

Notes that will save you a confused loop:

- **Step 2 is not optional.** A worker parked at a trust dialog will swallow
  `/usage` and return its splash screen instead of a usage pane. If the output
  doesn't contain percentages, you probably skipped a gate.
- **`wait_ms` around 9000 is about right.** These panes render after a round
  trip to the provider; a 250 ms wait returns an empty frame and looks like the
  command failed.
- **Dismiss the pane before tasking.** It's a modal overlay in Cursor and Kimi;
  sending a lane prompt into it wastes a turn.
- **Fresh sessions show near-zero session usage.** That's the *session* line,
  not your plan. Read the plan/weekly/5-hour rows for headroom — a brand-new
  worker always looks idle.
- **For OpenCode**, skip all of this and run `opencode stats` from the shell —
  but remember it answers "what did I spend", not "what is left".

### Codex reset credits

Codex grants a small number of **rate-limit reset credits** that immediately
clear a hit usage limit. When any are available, the Codex TUI prints a banner
on startup:

```
• You have 2 usage limit resets available. Run /usage to use one.
```

To redeem: send `/usage` in-session, then follow the prompt to consume one.
Redemption is a real account mutation (it calls the
`rate-limit-reset-credits/consume` endpoint), and the count does not
regenerate on demand — treat each credit as spent for good.

Read the remaining count from that banner or from `/usage` and **record it in
the plan scratchpad's decisions log** whenever you consume one, so the run
history shows where the credits went.

**The flow: spawn → check → set → confirm → task.** These tools persist their
last-used mode, model, and thinking level between sessions, so a freshly
spawned worker is running whatever its previous session left behind. Drive each
worker's normal in-session workflow via `send_input`, the way a human would:

1. **Check** — clear any trust/approval gate first (see above), then send the
   tool's model/status command; read the reply with `get_process_output`
   (current model and mode usually show in the status line).
2. **Set** — mode, model, and thinking level, using the commands below.
3. **Confirm** — read the output again; a settings command that didn't land is
   worse than one never sent.
4. **Task** — only now send the lane's worker prompt.

Launch flags are listed as a fallback, mainly for pre-configuring agent
variants in Solo's Settings → Agents. Which tools exist at all comes from
`list_agent_tools`.

## Discovering the live model catalog

Multi-model harnesses re-shuffle their lineups often — but not minute-to-minute,
so **cache the catalog in a Solo scratchpad named `model-catalog` with a 2-hour
TTL** instead of re-listing on every run. Protocol:

1. `scratchpad_find` → read `model-catalog`. If its `Last refreshed:` line is
   under 2 hours old (compare with `date -u`), route from it. Done.
2. Otherwise refresh — run the catalog commands below, then rewrite the
   scratchpad in this shape:

```markdown
# Model Catalog
Last refreshed: 2026-08-08T14:32:00Z

## OpenCode (`opencode models`)
opencode/deepseek-v4-flash-free   ← free tier
anthropic/claude-sonnet-4-5
...

## Cursor (`agent models`)
...

## Kimi (`kimi provider list`)
...
```

Catalog commands (all verified on installed binaries):

| Tool | Catalog command | Notes |
|---|---|---|
| OpenCode | `opencode models [provider]` | Works even unauthenticated; ~87 models. Free-tier models carry a `-free` suffix — currently `opencode/deepseek-v4-flash-free`, `laguna-s-2.1-free`, `ling-3.0-flash-free`, `mimo-v2.5-free`, `nemotron-3-ultra-free`, `north-mini-code-free` — prime candidates for docs/mechanical lanes |
| Cursor | `agent models` or `agent --list-models` | Shows what your subscription routes. **Effort is baked into the model name** (`-low`/`-medium`/`-high`/`-xhigh`, plus `-fast` variants), e.g. `claude-opus-5-thinking-xhigh`. `auto` is the default |
| Kimi | `kimi provider list [--json]` | Lists configured providers and model aliases; `kimi provider catalog` imports more from models.dev. Current aliases: `kimi-code/k3` (default), `k3-256k`, `kimi-for-coding` (K2.7), `kimi-for-coding-highspeed` |
| Claude Code | in-session `/model` picker | Small stable alias set (`fable`/`opus`/`sonnet`) — no caching needed |
| Codex | in-session `/model` picker | Model + reasoning effort chosen together — no caching needed |

Cost is part of routing: a free model on a low-blast-radius lane (docs,
mechanical edits) where the acceptance check catches mistakes cheaply is
usually the right call — but re-earn that trust from lane records, since
catalog models change quality in both directions.

---

## Claude Code (`claude`) — verified 2.1.226

**Fit:** strongest all-rounder. First pick for investigation/debugging lanes
(frontier model + high effort) and a reliable Sonnet-tier
bounded-implementation workhorse. Natural cross-lab reviewer for
OpenAI-authored lanes. **Solo MCP: verified.** No startup gate observed.

**In-session (preferred):**
- Model — `/model` shows current and opens the picker; aliases: `fable`,
  `opus`, `sonnet`, or a full model name (e.g. `claude-fable-5`).
- Mode — status line shows the permission mode; Shift+Tab cycles, or manage via
  `/permissions`.
- Thinking — effort level per session; "think hard"/"ultrathink" in the prompt
  also raises it for a turn.

**Launch fallback (verified flags):**
- `--model <alias-or-full-name>`
- `--permission-mode <acceptEdits|auto|bypassPermissions|manual|dontAsk|plan>`
  — there is a literal `auto` mode (classifier-driven; inspect or reset it with
  `claude auto-mode`); `plan` for read-only lanes
- `--effort <low|medium|high|xhigh|max>` — thinking level
- `--dangerously-skip-permissions` (bounded lanes in trusted repos only);
  `--allow-dangerously-skip-permissions` merely makes it *available* without
  enabling it
- `-p/--print` one-shots (`--output-format text|json|stream-json`); `--bg`
  background agents (manage with `claude agents`); `--agent <name>`
- `-w/--worktree [name]` — isolated git worktree, same idea as Cursor's;
  `--tmux` pairs with it. `--add-dir <dirs...>` widens tool access
- `--fallback-model <a,b>` — retry chain when the primary is overloaded
  (`--print` only); `--max-budget-usd` caps spend on a `--print` lane

## OpenCode (`opencode`) — verified 1.18.15

**Fit:** the flexible model router — one CLI, many providers, including local
models for near-free mechanical lanes. Reach for it when the routing table
names a model no other configured tool serves. **Solo MCP: verified** (tool
appears as `solo_whoami`; the TUI's right-hand panel shows `• solo Connected`,
a fast visual confirmation). No startup gate observed.

**In-session (preferred):**
- Model — `/models` opens the picker. List from outside with
  `opencode models [provider]`.
- **Always set BOTH the model and the reasoning variant** — OpenCode's
  effective default depends on which config files it discovered, so an
  unchecked default is a real hazard here. This matters more than it used to:
  see the `--variant` caveat below.
- Mode/agent — Tab switches agents (e.g. build vs plan); permissions come from
  `opencode.json`.

**Launch fallback (verified flags):**
- Top-level (TUI launch): `-m/--model provider/model` (e.g.
  `anthropic/claude-sonnet-4-5`), `--agent <name>`, `--auto` (auto-approve
  permissions not explicitly denied — the tool itself labels this dangerous;
  trusted repos only), `-c/--continue`, `-s/--session <id>`, `--prompt`,
  `--mini` (minimal interactive UI)
- ⚠️ **`--variant` is NOT a top-level flag** — it exists only on
  `opencode run`. A TUI worker spawned by Solo therefore cannot have its
  reasoning effort set at launch; you **must** set it in-session. This is a
  change from earlier builds, and it's the single easiest way to silently ship
  a lane at the wrong effort.
- `opencode run "<msg>"` one-shots carry the extras: `--variant <high|max|
  minimal|…>` (provider-specific reasoning effort), `--format default|json`,
  `--thinking` (show thinking blocks — display only, not an effort control),
  `-f/--file`, `--share`, `-i/--interactive`

## Codex CLI (`codex`) — verified 0.147.0

**Fit:** high-reasoning implementation and review from the OpenAI side. The
default cross-lab reviewer for Claude-authored lanes. **Solo MCP: verified**
(reports the full 95-tool count back from `whoami`).

⚠️ **Startup gate:** opens a workspace-trust dialog ("Do you trust the contents
of this directory?"). Send Enter (`[13]`) to accept before doing anything else.

**In-session (preferred):**
- Model + reasoning — `/model` selects both together in one picker.
- Mode — `/approvals` sets the approval policy.
- Persists in `~/.codex/config.toml` — whatever the last session chose is live.

**Launch fallback (verified flags):**
- `-m/--model <name>`; reasoning via `-c model_reasoning_effort="high"`
  (config key confirmed present in the 0.147.0 binary)
- `-a/--ask-for-approval <untrusted|on-request|never>` — **`--full-auto` and
  the `on-failure` policy still do not exist** (`--full-auto` errors with
  "unexpected argument"); for unattended workers use `-a never` (failures
  return to the model instead of stalling)
- `--approve-for-me` — newer middle ground: routes approval requests through
  automatic review using the workspace-write sandbox
- `-s/--sandbox <read-only|workspace-write|danger-full-access>` — unattended
  recipe: `-a never -s workspace-write`
- `--dangerously-bypass-approvals-and-sandbox` only in externally-sandboxed
  environments
- ⚠️ **`-p` is `--profile` here, not `--print`** — unlike every other CLI on
  this page. Use `codex exec "<prompt>"` for one-shots; `codex review` for
  review lanes. Getting this wrong silently layers a config profile instead of
  going non-interactive.
- `--search` enables the native web-search tool; `--add-dir` widens the
  writable workspace; `codex doctor` diagnoses install/auth/config health

## Cursor Agent (`agent`) — verified 2026.08.04

**Launch command is just `agent`** — older docs say `cursor-agent`, which is
stale (the `cursor-agent` binary still exists and `agent` symlinks to it, but
Solo is configured with `agent`). If Solo's agent tool for Cursor fails to
start, fix the command in Settings → Agents.

**Fit:** multi-provider access through one subscription; good mid-tier
implementation lanes and quick second opinions when you want a model your
other tools don't carry. Native git-worktree isolation makes it the easiest
tool for physically separating parallel lanes. **Solo MCP: verified.**

⚠️ **Startup gate:** "⚠ Workspace Trust Required" panel. Send `"a"` with
`submit: false` (it's a hotkey, not a line of input).

**In-session (preferred):** `/model` to check and switch. No flag exists for
"agent mode" — it's the default; `--mode` only takes `plan` or `ask`
(both read-only), so use those for investigation lanes.

**Launch fallback (verified flags):**
- `--model <name>`; list with `--list-models` or `agent models`. **Effort is
  primarily part of the model name now** — `claude-opus-5-thinking-xhigh`,
  `gpt-5.3-codex-high`, `cursor-grok-4.5-low`, with `-fast` variants. Bracket
  overrides are still supported for parameterized models:
  `--model 'claude-opus-4-8[context=1m,effort=high,fast=false]'`
- `--mode <plan|ask>` (both read-only); `--plan` is shorthand for `--mode=plan`
- `-f/--force` (alias `--yolo`) — allow commands unless explicitly denied;
  `--auto-review` is the middle ground (a server classifier auto-runs safe
  calls, prompts for the rest)
- `--approve-mcps` to auto-approve MCP servers; `--sandbox <enabled|disabled>`
- `--trust` pre-trusts the workspace without prompting. (Earlier builds
  restricted this to `--print`/headless; the 2026.08.04 help no longer says so.
  Confirm behavior before relying on it for an interactive worker.)
- `-w/--worktree [name]` spawns in an isolated git worktree
  (`~/.cursor/worktrees/<repo>/<name>`, `--worktree-base <ref>`,
  `--skip-worktree-setup`) — a strong option for parallel lanes that might
  contest files; Solo shares todos and scratchpads across linked worktrees of
  the same project
- `--workspace <path-or-name>`, `--add-dir <path>` (repeatable),
  `--plugin-dir <path>` (repeatable)
- `-p/--print` with `--output-format text|json|stream-json` for one-shots
  (`--stream-partial-output` for text deltas)

## Kimi Code CLI (`kimi`) — verified 0.34.0

⚠️ **This section was substantially wrong before 2026-08-08.** The prior note
claimed "v1.48" and listed `--afk`, `--thinking`, `--no-thinking`, `--print`,
and `--agent <default|okabe>` — none of those exist in 0.34.0 (each was
confirmed removed by testing against a real subcommand, with a bogus-flag
control producing the identical `unknown option` error).

**Fit:** cheap, fast K3-class lanes — the go-to for docs/tests/mechanical
volume work and well-specced bounded implementation. Auto mode makes it the
most reliably unattended worker of the bunch.

⚠️ **Solo MCP: verified in the TUI, but Kimi has TWO gates and one hard
limitation:**
1. **Trust dialog on spawn** — Kimi loads project MCP servers *only in trusted
   folders*. Send Enter (`[13]`).
2. **Per-tool approval on the first MCP call** — a menu appears; send `"2"`
   (approve for this session) or launch with `--auto`. A worker left here
   looks busy and is doing nothing.
3. **`kimi -p` loads no MCP servers at all.** Verified: its full tool list in
   print mode contains zero MCP entries, while the same install connects solo
   with 95 tools in the TUI. **Never route a coordination-dependent lane
   through Kimi print mode.**

Once trusted, the banner reads `MCP: 1 connected` and
`MCP server "solo" connected · 95 tools (stdio)` — check for that line.

**In-session (preferred):**
- Model — `/model` to check and switch (slash command confirmed in the bundle).
- Mode — `/yolo` toggles auto-approval; status bar shows a YOLO badge — confirm
  the badge before tasking.
- Thinking — **no longer a Tab toggle or CLI flag.** It is configuration:
  `[thinking] enabled = true` / `effort = "high"` in `~/.kimi-code/config.toml`
  (the enum accepts `minimal|low|medium|high|max`, though this install shows a
  recorded `thinking-effort-max-to-high` migration, so treat `max` as retired
  for the managed provider). Validate edits with `kimi doctor`. The TUI status
  bar shows e.g. `K3 thinking: high`.

**Launch fallback (verified flags):**
- `-m/--model <name>` — alias from `kimi provider list`, e.g. `kimi-code/k3`
  (the current default), `kimi-code/k3-256k`
- Two distinct autonomy levels, which the old note conflated:
  - `-y/--yolo` — auto-approve regular tool calls; **the agent may still ask
    questions** (so it can still stall an unattended lane)
  - `--auto` — fully autonomous permission mode; the agent will not ask
    questions. **This is the correct flag for an unattended worker**, and it
    also clears the MCP tool-approval gate.
- `--plan` for read-only investigation
- `--agent <name>` — profiles discovered from agent directories; the old
  `default|okabe` enum is gone. `--agent-file <path>` loads one from Markdown.
  Neither can be combined with `--session`/`--continue`.
- `--skills-dir <dir>` (repeatable) — point at `~/.claude/skills` so workers
  can read this very skill
- `-p/--prompt "<text>"` for one-shots with
  `--output-format <text|stream-json>` (note: **no `json`**, and **no
  `--print`**) — but see the MCP limitation above
- `--add-dir <dir>` (repeatable), `-S/--session [id]`, `-c/--continue`

---

## Removed: Antigravity (`agy`)

**Antigravity was removed from the routing menu on 2026-08-08 because it cannot
reach the Solo MCP server**, which makes it unusable as an orchestrated worker.

Evidence, so nobody re-adds it without re-testing:
- `~/.gemini/config/mcp_config.json` is the correct global location (confirmed
  against Antigravity's own docs embedded in the 1.1.11 binary), and the solo
  entry matched the documented stdio schema.
- `/mcp` in the CLI *sees* the entry and shows `solo initializing...` — but it
  never leaves that state. Two fresh sessions, ~2 minutes each.
- The agent's enumerated tool list contained only built-ins (`run_command`,
  `view_file`, `grep_search`, …) — zero MCP tools — and `whoami` was
  unreachable. Every other CLI connected within seconds.
- Separately, the global `mcp_config.json` was observed being emptied to
  `{"mcpServers": {}}` during testing. Cause unconfirmed, but treat that file
  as something Antigravity may rewrite.

**Re-test before restoring it**: spawn it via Solo, run `/mcp`, and confirm
solo reaches a *connected* state — then have it actually call `whoami`. If a
future build fixes this, its old fit was Gemini-suited lanes (long-context
reading, multimodal inputs) with `--effort <low|medium|high>` and
`--mode <accept-edits|plan>`; it also spawned nested subagents freely and burned
quota in parallel, so it wanted tightly bounded lanes.

Note that Solo's `list_agent_tools` may still return Antigravity as a
registered agent tool. **Registered is not the same as usable** — skip it when
routing regardless of what the list returns.

---

## Suggested tiering (edit to taste)

| Lane type | Good defaults |
|---|---|
| Orchestrator | Frontier model (stay put) |
| Bounded implementation | Claude Sonnet via Claude Code · Kimi K3 via `--auto` · mid-tier via OpenCode |
| Investigation / debugging | Claude Code `--effort xhigh`+ frontier model, or Codex with high reasoning |
| Cross-lab review | A different provider than the lane's author (`codex review` fits here) |
| Docs / mechanical edits | Free-tier catalog models via OpenCode (the `-free` suffix set), Haiku-class, flash-class, or a local model — verified against lane records |

## Unattended-worker quick reference

The one flag per tool that actually stops a lane from stalling on a prompt:

| Tool | Unattended launch | Notes |
|---|---|---|
| `claude` | `--permission-mode bypassPermissions` or `--dangerously-skip-permissions` | trusted repos only |
| `opencode` | `--auto` | tool labels it dangerous |
| `codex` | `-a never -s workspace-write` | failures return to the model; still clear the trust dialog |
| `agent` | `-f/--force` (`--yolo`) | `--auto-review` is the safer middle; still clear the trust panel |
| `kimi` | `--auto` | **not** `-y/--yolo` — that one still asks questions. Also clears the MCP approval gate |

Note that none of these flags dismiss the **workspace-trust** dialogs, which
are a separate gate — always read output after spawning.
