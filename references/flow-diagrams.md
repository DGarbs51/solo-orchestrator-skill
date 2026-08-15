# Flow diagrams — the orchestrator at a glance

Visual companion to SKILL.md. The prose in SKILL.md is authoritative; these
diagrams are the shape of it. Read this when you want the whole run in one
view, or to orient before a long orchestration.

## 1. The run — Phase 0 → 8

```
                        ┌────────────────────────────┐
                        │    SOLO ORCHESTRATOR       │
                        │  you are the LEAD agent    │
                        │  coordinate, don't code    │
                        └─────────────┬──────────────┘
                                      ▼
  ┌── PHASE 0 · ORIENT ─────────────────────────────────────────────────┐
  │  whoami ──> select_project ──> identify_session                     │
  │  list_agent_tools  = the menu, MINUS any tool without Solo MCP      │
  │  git status · git branch --show-current                             │
  └──────────────────────────────┬──────────────────────────────────────┘
                                 │ no Solo MCP? ─> say so, offer degraded
                                 ▼
  ┌── PHASE 1 · INTERVIEW ──────────────────────────────────────────────┐
  │  ONE question at a time (a wall of them gets shallow answers)       │
  │  goal · "done" · constraints · NON-goals · risky files              │
  │  ...is parallel work even worth it here?                            │
  │  STOP when another answer wouldn't change the plan                  │
  └──────────────────────────────┬──────────────────────────────────────┘
                                 ▼
  ┌── PHASE 2 · BRANCH FIRST, THEN PLAN ────────────────────────────────┐
  │  git checkout -b feature/<slug> && git push -u   ← BEFORE any edits │
  │     └─ bypass: user explicitly says "on main" ─> stay, no PR        │
  │  scratchpad "plan-<slug>" =                                         │
  │     context · constraints · LANES · verification · decisions log    │
  └──────────────────────────────┬──────────────────────────────────────┘
                                 ▼
  ┌── PHASE 3 · TODOS + BLOCKERS ───────────────────────────────────────┐
  │  one todo per lane · set blockers · mark parallel-safe              │
  │  KEEP with lead: dependent · tiny · file-contested                  │
  │  (the goal is never "more agents")                                  │
  └──────────────────────────────┬──────────────────────────────────────┘
                                 ▼
  ┌── PHASE 4 · DISPATCH ───────────────────────────────────────────────┐
  │  usage preflight ─────────────────────────> [diagram 3]             │
  │  route each lane ─────────────────────────> [diagram 2]             │
  │  spawn ─> CHECK ─> SET ─> CONFIRM ─> TASK                           │
  │           └─ clear trust/approval gates or the worker stalls silent │
  │  lock_acquire on anything two lanes could touch                     │
  └──────────────────────────────┬──────────────────────────────────────┘
                                 ▼
  ┌── PHASE 5 · MONITOR (timers, not vibes) ────────────────────────────┐
  │  timer_fire_when_idle_any ──> wake when a worker goes idle          │
  │  read the REAL output — summaries are triage, not evidence          │
  │  reconcile: scratchpad + todos + blockers + RE-CHECK USAGE          │
  └──────────────────────────────┬──────────────────────────────────────┘
                                 ▼
  ┌── PHASE 6 · INTEGRATE — one lane at a time ─────────────────────────┐
  │  git status ─> smallest diff first ─> focused check ─> COMMIT       │
  │  lead commits ALWAYS · workers commit NEVER · push per lane         │
  │  Co-Authored-By: <worker model>  +  <lead model>                    │
  └──────────────────────────────┬──────────────────────────────────────┘
                                 ▼
                      ┌──────────────────────┐
                      │  lanes remaining?    │
                      └──────┬────────┬──────┘
                     yes ────┘        └──── no
        ┌────────────────┘                    │
        │                                     ▼
        │       ┌── PHASE 7 · CAPTURE, *THEN* CLOSE ──────────────┐
        │       │  handoff ─> todo / scratchpad                   │
        │       │  closing deletes the session — capture FIRST    │
        │       └────────────────────┬───────────────────────────-┘
        │                            ▼
        │       ┌── PHASE 8 · SHIP ───────────────────────────────┐
        │       │  gh pr create   (READY for review, not draft)   │
        │       │  body = plan + decisions log + handoffs + diffs │
        │       │  the USER merges — never you                    │
        │       │  on-main bypass ─> push main, report SHAs       │
        │       └────────────────────────────────────────────────-┘
        │
        └──────> back to PHASE 4 · dispatch next unblocked lane
```

## 2. Routing a lane — fit, not brand

```
                            ┌──────────┐
                            │  A LANE  │
                            └────┬─────┘
                                 ▼
  ┌── STEP 1 · CLASSIFY ────────────────────────────────────────────────┐
  └───┬───────────┬────────────┬────────────┬──────────────┬────────────┘
      ▼           ▼            ▼            ▼              ▼
  ┌────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐
  │Bounded │ │Investig-│ │Architect │ │  Review  │ │ Docs/tests │
  │  impl  │ │  ation  │ │  design  │ │  verify  │ │ mechanical │
  └───┬────┘ └────┬────┘ └────┬─────┘ └────┬─────┘ └─────┬──────┘
      ▼           ▼           ▼            ▼             ▼
  ┌────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐
  │fast /  │ │frontier │ │ frontier │ │ mid→front│ │  cheapest  │
  │mid tier│ │+thinking│ │ -or- KEEP│ │ DIFFERENT│ │  capable   │
  │        │ │  HIGH   │ │  w/ lead │ │   LAB ⚠  │ │ (free ok)  │
  └───┬────┘ └────┬────┘ └────┬─────┘ └────┬─────┘ └─────┬──────┘
      └───────────┴─────┬─────┴────────────┴─────────────┘
                        ▼
  ┌── STEP 3 · MODEL CATALOG ───────────────────────────────────────────┐
  │  scratchpad "model-catalog", 2-hour TTL                             │
  │  fresh? ──> route from cache      stale? ──> agent models /         │
  │                                     opencode models / kimi provider │
  └────────────────────────────┬────────────────────────────────────────┘
                               ▼
  ┌── STEP 4 · PICK: fit ─> cost ─> evidence ───────────────────────────┐
  │  cost weighed against STAKES, not diff size                         │
  │  unfamiliar model? research it — quality moves BOTH directions      │
  └────────────────────────────┬────────────────────────────────────────┘
                               ▼
  ┌── STEP 5 · SET IN-SESSION + RECORD ON THE TODO ─────────────────────┐
  │  never let a worker run on an unknown persisted default             │
  │  the record is how routing improves next run                        │
  └─────────────────────────────────────────────────────────────────────┘

  ⚠ review lanes: reviewer must be a DIFFERENT LAB than the author.
    same-lab review shares the author's blind spots.
```

## 3. Usage + failover loop

```
   PHASE 4 preflight ──┐                    ┌── PHASE 5 reconcile
                       ▼                    ▼
              ┌────────────────────────────────────┐
              │      CHECK PROVIDER HEADROOM       │
              └─────────────────┬──────────────────┘
                                ▼
        /usage  =  IN-SESSION slash command (needs a live worker)
   ┌────────────┬────────────┬────────────┬────────────┬──────────────┐
   ▼            ▼            ▼            ▼            ▼
┌──────────┐┌──────────┐┌──────────┐┌──────────┐  ┌──────────────┐
│  Claude  ││  Codex   ││  Cursor  ││   Kimi   │  │   OpenCode   │
│ `claude` ││ `codex`  ││ `agent`  ││  `kimi`  │  │  `opencode`  │
│          ││          ││          ││          │  │              │
│  /usage  ││  /usage  ││  /usage  ││  /usage  │  │    (none)    │
│    ✅    ││    ✅    ││    ✅    ││    ✅    │  │      ❌      │
│ headroom ││ headroom ││ headroom ││ headroom │  │ no headroom  │
└──────────┘└──────────┘└────┬─────┘└────┬─────┘  └──────────────┘
                             │           │         `opencode stats`
                             └─────┬─────┘          = SPEND only
                             time-to-reset shown
                             waiting may beat
                             rerouting the lane

   ⚠ lab vs command: "Cursor" is the lab, `agent` is its CLI binary —
     one tool, two names. Its SHELL subcommand `agent status` reports
     AUTH ONLY (no quota). Headroom lives in `agent`'s in-session /usage.
     Never substitute the shell check for the slash command.

   ── worker stalls / errors / refuses? ──> CHECK QUOTA before debugging
                                            (often out, not broken)
                                ▼
                      ┌───────────────────┐
                      │  provider is OUT  │
                      └─────────┬─────────┘
                                ▼
                   ┌────────────────────────┐
                   │ Codex + resets remain? │
                   └────┬──────────────┬────┘
                    yes │              │ no / not codex
                        ▼              ▼
       ┌────────────────────────┐  ┌──────────────────────────────┐
       │ /usage ─> REDEEM one   │  │  FAIL OVER:                  │
       │ keep the run moving    │  │  re-run FULL routing         │
       │  · tell user, + count  │  │  (diagram 2) with that       │
       │  · log in decisions    │  │  provider EXCLUDED           │
       │  · at zero ─> fail over│  │  ⚠ recheck cross-lab rule    │
       └───────────┬────────────┘  └──────────────┬───────────────┘
                   └───────────┬──────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ record on lane todo  │
                    │ (evidence for next   │
                    │  run's routing)      │
                    └──────────────────────┘
```

## The through-line

Chat scrollback is disposable, so everything durable lives in the scratchpad
and todos. The lead never mass-merges — one lane, one diff, one commit — and
every gate that could silently stall a run (trust prompts, unknown persisted
model defaults, exhausted quota) gets checked *before* work is sent, not after
it fails.

---
*Generated with /ascii*
