# Worker CLI reference

Read only the selected CLI's section. Routing, approval, failover, and cache
policy live in SKILL.md and routing-cache.md; this file holds mechanics.

## Verification scope

Installed help checked 2026-09-05: Claude Code **2.1.261**, Codex **0.153.4**,
Cursor Agent **2026.09.02-c22c1a3**, Kimi Code **0.41.0**, OpenCode **1.18.29**.
The Codex bundled catalog and Kimi provider JSON commands were also executed.
Help verifies advertised options, not account access or successful model/MCP
calls. Current read-only checks: Claude/OpenCode MCP health checks connected;
Cursor discovered Solo's `whoami` tool; Kimi TUI listed Solo connected with 101
tools and displayed plan usage and permission choices. Codex's server listing
shows Solo enabled; this audit's Codex host can call Solo, but that does not
prove a newly launched Codex CLI session. OpenCode resolved configuration
confirmed the explicit command and targeted skill deny in an isolated project.
Kimi automatically updated from 0.38.0 to 0.41.0 on TUI launch; its help was
rechecked. No model task was submitted by these diagnostics. Historical
five-CLI Solo task smoke checks were recorded on 2026-08-08; recheck connection
and effective settings in each new worker.

Use installed help when it differs from documentation. Do not test an unknown
flag by appending `--help`: help can short-circuit validation. Record the
version and actual evidence; do not claim a live check from a static catalog.

## Solo launch and startup

`list_agent_tools` supplies runtime IDs and saved commands. Current Solo
`spawn_agent`/`spawn_process(kind="agent")` accept an `extra_args` string array
appended to the saved command. Avoid contradictory saved/extra flags. A saved
`kimi --yolo`, for example, needs correction to normal mode before tasking.
Do not modify saved runtime/global CLI configuration for a single lane.

Solo starts a process in its registered project's directory. Ensure this is
the assigned worktree, or use an advertised CLI directory argument below.
For a CLI without a directory option, register/select the lane directory as a
Solo project and spawn with that project's ID. Keep the coordination project
ID explicit in the prompt for plan/todo access; do not assume a new registration
has the intended shared state. Do not create a second worktree via a CLI flag
when the lead already created one. `--add-dir` grants access; it does not set cwd.

Inspect output after spawn. Trust dialogs and MCP approvals are separate from
permission modes; read the live choices and approve only the intended scope.
Do not send blind Enter/"a"/"2" keystrokes based on an old screenshot. Supply
Solo's returned bootstrap information inside the prompt file, then send a short
absolute file pointer. Require `whoami` to confirm the worker's identity and
coordination scope before edits. A configured server is not a working connection.

## Claude Code — `claude`

- Launch: `--model <alias-or-id> --effort <level> --permission-mode auto`.
  Help advertises effort `low|medium|high|xhigh|max`; actual model support varies.
- Enable sandboxing with a per-launch `--settings <file-or-json>` containing
  `sandbox.enabled: true`; inspect `/sandbox` and effective permissions. If
  unavailable, retain normal approvals rather than enabling bypass.
- `/model` shows choices; the picker can apply a session-only selection (`s`).
  Typing `/model <name>` or selecting with Enter can save a user-global default.
  Prefer launch settings for parallel workers. Verify model and effort afterward.
- Catalog: the live picker and provider-specific aliases. Common aliases include
  `fable`, `opus`, `sonnet`, `haiku`; their actual resolution depends on version,
  provider and overrides. Do not assume aliases always select the newest model.
- `/usage` reports subscription limits; `/cost` is session spend. Inspect billing
  labels in the picker: some models can require usage credits even on a paid
  subscription. A print-mode invocation may bill credits without a consent UI.
- Noninteractive mode is `-p/--print`; use only after confirming billing and MCP
  behavior for the route. `--permission-mode plan` is available for review lanes.

Sources: [models/effort](https://code.claude.com/docs/en/model-config),
[permission modes](https://code.claude.com/docs/en/permission-modes),
[sandbox](https://code.claude.com/docs/en/sandboxing).

## Codex — `codex`

- Launch: `-C <worktree> -m <id> -c 'model_reasoning_effort="<effort>"'
  with `--approve-for-me -s workspace-write` for implementation. Check supported
  efforts in the actual catalog. Do not add `-a never` or full sandbox bypass.
- `/model` selects model/effort; `/permissions` is the current permission picker
  (`/approvals` is older guidance). `/status` shows effective settings; `/mcp`
  lists available servers/tools. Inspect account limit indicators separately
  from session tokens.
- `/usage` offers account token activity and earned reset redemption; activity
  totals are not remaining quota. Use actual rate-limit/window observations
  from the session. Only redeem when a reset is offered; verify the new count.
- `codex debug models` refreshes/renders JSON; `--bundled` skips remote refresh
  and is useful for schema inspection, not current account availability.
  Filter immediately: raw entries contain large prompt templates.

  ```bash
  codex debug models | jq '{models: [.models[] | {
    slug, visibility, default_reasoning_level, supported_reasoning_levels,
    upgrade, supported_in_api
  }]}'
  ```

  Record visibility, upgrade hints and auth constraints. `upgrade` is a
  migration hint, not by itself proof a model is unavailable. API support and
  ChatGPT-authenticated availability are different; do not reject a subscription
  route solely because `supported_in_api` is false. Confirm the selected route
  in the live session before dispatch.
- `-p` means **profile**, not print. Noninteractive commands are `codex exec`
  and `codex review`; their supported options differ, so read subcommand help.

Source: [Codex CLI commands](https://developers.openai.com/codex/cli/slash-commands)
plus installed help and bundled catalog schema.

## Cursor — `agent`

- Launch: `--workspace <worktree> --model <id> --auto-review --sandbox enabled`.
  Some operations still prompt. Do not add `--force`/`--yolo`.
- `agent models` or `agent --list-models` lists account choices. Some IDs encode
  reasoning effort; use exactly the advertised ID/parameters. `/model` changes
  the session model; verify the resulting setting.
- `--mode plan` and `--mode ask` are read-only modes. Normal agent mode is the
  default; `--mode agent` is not an advertised value.
- `/usage` was observed in prior installed sessions; inspect `/help` and the
  live panel for the current build. `agent status` reports authentication,
  not quota. Use remaining-limit/window rows rather than generic usage stats.
- `--trust` pre-trusts a workspace; `--approve-mcps` approves all MCP servers.
  Neither is a blanket worker default. Handle the actual required scope.
- Print mode: `-p --output-format text|json|stream-json`. Native `--worktree`
  creates another checkout; omit it for an existing lead-managed worktree.

Sources: [CLI parameters](https://cursor.com/docs/cli/reference/parameters),
[slash commands](https://cursor.com/docs/cli/reference/slash-commands), installed help.

## Kimi Code — `kimi`

- Launch model via `-m <alias>` from `kimi provider list --json`. This command
  reports `providers` and `models`. `kimi provider catalog` imports providers;
  it is a configuration mutation, not a read-only model refresh.
- Use normal/Always Ask mode, verified with `/permission`; saved runtime flags
  can override defaults. In 0.41.0, `--yolo` selects Ask When Needed (routine
  edits/commands proceed; risky actions still ask); `--auto` selects Never Ask
  and removes even dangerous-command blocking. Neither provides an OS sandbox.
  Keep scoped approvals as the default; do not infer safe review from a flag's name.
- `/model` selects the model. The installed help has no thinking/effort launch
  flag. Inspect the live model controls/status for supported session settings;
  do not edit global `config.toml` just to tune one worker. If a required effort
  cannot be set without changing global state, select another suitable route.
- `/usage` shows provider usage in supported sessions; inspect actual limit
  windows. Workspace trust and the first MCP approval can block startup.
- `-p/--prompt` runs one prompt; output formats are `text|stream-json`.
  A 2026-08-08 test found Solo unavailable in prompt mode. That historical
  result is not proof all future builds lack MCP: prefer TUI coordination
  until a current prompt-mode smoke test succeeds.
- `--skills-dir` overrides auto-discovered skill directories; normal discovery
  includes `~/.agents/skills` and `~/.kimi-code/skills`. `--plan` is available.

Sources: [CLI](https://moonshotai.github.io/kimi-code/en/reference/kimi-command.html),
[modes](https://moonshotai.github.io/kimi-code/en/guides/interaction.html),
[skills](https://moonshotai.github.io/kimi-code/en/customization/skills.html),
[0.41.0 changes](https://moonshotai.github.io/kimi-code/en/release-notes/changelog.html).

## OpenCode v1 — `opencode`

- Launch: `opencode <worktree> --model <provider/model> --agent <agent>`.
  Use scoped `permission` rules with narrow allows and prompts for other
  actions. Verify effective configuration: defaults can allow operations even
  without `--auto`. Do not enable `--auto` to suppress blocked requests.
- `/models` selects a model; verify its reasoning variant as well. The TUI's
  top-level help does not advertise `--variant`; `opencode run` does. Use live
  variant controls for the TUI. `--thinking` displays reasoning; it does not
  select effort. Tab switches the active agent (such as build/plan).
- `opencode models [provider]` lists models, not proof of authenticated access.
  Store relevant rows only. A free-looking name does not establish billing.
- `opencode stats` reports consumed tokens/cost, not remaining provider quota.
  No aggregate headroom command was verified. Treat unknown pools as unknown.
- `opencode run` supports `--variant`, `--format default|json`, `--file` and
  `--interactive`; confirm MCP and billing before using it for a lane.
- Explicit-only skill invocation requires an OpenCode-specific command/permission
  setup: the documented v1 skill format ignores `disable-model-invocation`.
  `install.sh --targets opencode` installs `/solo-orchestrator` and a targeted
  `permission.skill.solo-orchestrator: deny` for automatic skill loading. The
  command explicitly reads the installed skill. Existing custom agent rules
  may override global permissions; verify the effective configuration.

Sources: [CLI](https://opencode.ai/docs/cli/), [permissions](https://opencode.ai/docs/permissions/),
[skills](https://opencode.ai/docs/skills/), [commands](https://opencode.ai/docs/commands/).
OpenCode v2 has different permission keys; do not apply v1 snippets blindly.

## Other runtimes

Use the same checks for any additional configured CLI. Antigravity (`agy`) failed
Solo MCP connection tests on 2026-08-08; it was not configured in the 2026-09-05
runtime list. Retest a new version before routing it; do not make that historical
failure a permanent blacklist or reuse old flags from memory.
