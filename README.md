# Solo Orchestrator

An explicitly invoked coding workflow for [Solo](https://soloterm.com): interview,
approve a plan, assign bounded work to agent CLIs, review and integrate their
commits, clean up worktrees, and prepare a pull request. Works with one lab or
several. This is an independent community skill, not an official Solo product.

## Install and invoke

```bash
git clone https://github.com/DGarbs51/solo-orchestrator-skill.git
cd solo-orchestrator-skill
./install.sh
```

The default links this checkout into `~/.claude/skills` and `~/.agents/skills`.
Claude uses the first; Codex, Cursor, and Kimi discover the shared agents path.
Restart the host session after installation or updates.

| Host | Explicit invocation |
|---|---|
| Claude Code, Cursor | `/solo-orchestrator` |
| Codex | `$solo-orchestrator` or its skill selector |
| Kimi Code | `/skill:solo-orchestrator` |
| OpenCode v1 | `/solo-orchestrator`, after the configuration below |

Generic orchestration requests, a connected Solo server, and editing the skill
itself do not invoke it. Claude, Cursor, and Kimi support the frontmatter
`disable-model-invocation` setting; Codex uses `agents/openai.yaml`.
See the [CLI reference](references/worker-clis.md) for sources and version details.

```bash
./install.sh --targets all       # also Cursor native path and OpenCode setup
./install.sh --targets opencode  # OpenCode only, including explicit command
./install.sh --project           # selected targets in the current project
./install.sh --copy              # copy instead of linking
./install.sh --list
./install.sh --uninstall         # default targets only; add --targets all as needed
./install.sh --uninstall --force # also remove copies marked by this installer
```

Linked installations follow this checkout. Update it with a normal Git pull;
copy installations must be removed and recopied. Foreign links and unmarked
folders are preserved. Kimi's `--skills-dir` replaces automatic discovery, so
use it only when intentionally selecting a different skills root.

Manual installations need `SKILL.md`, `references/`, `agents/`, and `scripts/`.
The installer supports Bash on Unix-like systems; Windows users can install
manually using the host's documented skill directories.

### OpenCode v1 explicit-only configuration

OpenCode v1 ignores the frontmatter invocation flag and can also discover the
shared `.agents/skills` installation. **OpenCode users must run the OpenCode
target or configure the following entries manually**, even if another target
already exposes the skill.

The installer merges two entries into `opencode.json`: a targeted skill deny
that hides automatic skill loading, and an explicit command that reads this
skill's instructions. Other settings remain intact. It records previous entry
values in `.solo-orchestrator-install.json`; uninstall restores only unchanged
entries owned by this installer.

For JSONC, scalar permissions, or an existing custom command, the installer
stops and requests a manual merge. Preserve your existing configuration and
merge this fragment, replacing the absolute path:

```json
{
  "permission": { "skill": { "solo-orchestrator": "deny" } },
  "command": {
    "solo-orchestrator": {
      "description": "Explicitly run Solo orchestration",
      "template": "The user explicitly invoked solo-orchestrator. Read /absolute/path/to/solo-orchestrator/SKILL.md and resolve its references and scripts relative to that directory. Request: $ARGUMENTS"
    }
  }
}
```

User configuration is under `${XDG_CONFIG_HOME:-~/.config}/opencode`; project
configuration is `opencode.json` at the project root, following the
[OpenCode config locations](https://opencode.ai/docs/config/). Verify effective permissions in the
intended project: project and agent overrides can change global settings.
This recipe targets OpenCode v1; v2 has a different permission schema.

### Claude Code plugin

Alternatively, install the single-plugin marketplace:

```text
/plugin marketplace add DGarbs51/solo-orchestrator-skill
/plugin install solo-orchestrator@solo-orchestrator
/solo-orchestrator:solo-orchestrator
```

Use the plugin manager to update the installed release. Choose either plugin or
linked installation in a host to avoid duplicate skill entries.

## Requirements and flow

- The lead running **inside Solo**, connected to its
  [MCP server](https://soloterm.com/docs/integrations/mcp-server), with its own
  Solo process identity, timer delivery, and at least one usable worker CLI.
- Git; `gh` with repository access for opening GitHub pull requests.
- Python 3.9+ for cache and OpenCode configuration helpers.

An external agent may review or maintain this skill and prepare a handoff prompt
for a Solo-running orchestrator. It must not execute the orchestration workflow.
The Solo lead verifies the handoff against current state and obtains approval
of its concrete plan before execution.

The lead asks one question at a time, displays a concrete plan, and waits for
approval before implementation, branches, or workers. Significant changes
pause affected lanes until approved. Routine progress stays in Solo; the lead
contacts you for required input and the final report.

Workers use separate worktrees and commit on local lane branches. The lead
reviews fixed handoff SHAs, merges and tests serially, and cleans up each
accepted lane after its processes stop. Worktrees share Git objects; optional
copy-on-write dependency copies reduce additional disk use. They do not provide
a security sandbox.

Concurrency adapts to ready work, shared quota, machine capacity, and review
throughput. Routing prefers capable included subscription capacity. Another
model lab is preferred for review, but a single-lab run remains supported.
Extra charges require approval with a scope and limit; existing Codex earned
reset credits can be redeemed automatically and are reported at completion.

When the [typesafe-ai](https://docs.typesafe.ai) skill is installed and
`TYPESAFE_API_KEY` is set, the lead may delegate bounded orchestration
judgments — interview sufficiency, lane splits, route choice among configured
candidates, idle-worker triage, and acceptance triage — to TypeSafe on your
account. Approvals, spending authorization, and verification are never
delegated, and the run behaves as documented when either is absent.

The default result is a ready-for-review PR that **you merge**. Direct work on
main requires an explicit instruction. Without a usable remote or PR client,
the lead preserves local commits and supplies the remaining handoff.

## References and maintenance

| File | Responsibility |
|---|---|
| [SKILL.md](SKILL.md) | Approval, orchestration, routing, recovery, delivery |
| [Git workflow](references/git-workflow.md) | Branches, worker commits, integration, cleanup, PR conventions |
| [Worker CLIs](references/worker-clis.md) | Versioned launch settings, models, usage, permissions, MCP checks |
| [Routing cache](references/routing-cache.md) | Cross-project model/usage observations and lane outcomes |
| [TypeSafe decisions](references/typesafe-decisions.md) | Optional judgment support: gate, delegable decisions, limits |
| [Flow diagrams](references/flow-diagrams.md) | Compact optional overview |

The local SQLite cache lives at
`${XDG_CACHE_HOME:-$HOME/.cache}/solo-orchestrator/routing.sqlite3`. It contains
compact observations, not credentials or project prompts. Matching fresh
records are reused; only relevant stale or invalidated records are refreshed.
It does not reserve quota or authorize spending.

CLI references were checked against installed help and official documentation
on **2026-09-05**: Claude 2.1.261, Codex 0.153.4, Cursor agent
2026.09.02-c22c1a3, Kimi 0.41.0, and OpenCode 1.18.29. Historical Solo smoke
results are labeled separately; startup flags alone do not prove an authenticated
worker can reach MCP. Check effective settings and connectivity before each
new worker receives work.

To validate repository helpers:

```bash
python3 -m unittest discover -s tests -v
bash -n install.sh
git diff --check
claude plugin validate .claude-plugin/plugin.json --strict --json
```

[MIT](LICENSE). Customize the Git conventions for your team while preserving
the explicit invocation and approval controls.
