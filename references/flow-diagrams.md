# Workflow overview

Optional orientation; SKILL.md owns policy and the references own mechanics.

```text
Explicit skill invocation
  → Confirm lead runs inside Solo with own identity, MCP, and timer delivery
    Outside Solo? review skill / prepare handoff prompt → hand over to Solo lead
  → Identify Solo project and inspect repository
  → Interview, one question at a time
  → Save and DISPLAY plan → WAIT for approval
  → Create/publish integration branch (or explicit stay-on-main)
  → Create lane todos and blockers
  → Read shared catalog/quota cache → route capable included models
  → Dispatch independent lanes in separate worktrees as capacity allows
  → Verify launch settings, checkout, permissions, and Solo access
  → Workers edit/check/commit locally → hand off fixed SHA → stop editing
  → Lead reviews and merges fixed SHA → checks combined result → pushes
  → Complete todo, unblock dependents, record outcome
  → Stop finished worker → remove verified worktree/branch → repeat
  → Whole-run checks → ready-for-review PR → final report → USER merges
```

```text
New evidence changes scope/approach?
  → Pause affected lanes and dependents; preserve partial work
  → DISPLAY revision → WAIT for approval → update assignments → resume
  → Unrelated approved work continues

Quota pressure?
  → Reuse fresh account-pool observations; refresh affected stale entries
  → Available existing Codex reset? redeem, verify, cache, log for final report
  → Otherwise reroute to capable included/free capacity
  → Extra charges needed? DISPLAY route + limit → WAIT for approval
  → No usable route? preserve work and report blocker/reset time
```

Concurrency has no fixed cap. Quota, machine contention, and integration backlog
control new dispatch. Cross-lab review is preferred; same-lab review is valid.
Routine updates stay in Solo. Only required input interrupts the user.
