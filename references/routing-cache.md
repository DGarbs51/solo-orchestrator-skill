# Shared routing cache

Read before routing or refreshing model/usage observations. The cache is shared
across projects for the same OS user on this machine, not across machines.
Project plans and detailed handoffs remain in Solo.

## Storage and access

Use `scripts/routing-cache.py` relative to the installed skill directory with
Python 3. Its default store is
`${XDG_CACHE_HOME:-$HOME/.cache}/solo-orchestrator/routing.sqlite3`.
It uses SQLite transactions for concurrent writers; older or equal-timestamp
observations cannot replace newer ones. Do not use a project-scoped Solo lock
as a machine-wide cache lock. Only the lead writes normalized observations;
workers report evidence through their lane todos.

```bash
python3 <skill-dir>/scripts/routing-cache.py list catalog
python3 <skill-dir>/scripts/routing-cache.py get catalog <route-key>
python3 <skill-dir>/scripts/routing-cache.py get usage <quota-pool-key>
python3 <skill-dir>/scripts/routing-cache.py put usage <quota-pool-key> --file <observation.json>
```

Each JSON observation has `observed_at` (UTC ISO timestamp of the actual
measurement), `source` (command or evidence reference), and `data` (object).
Store compact routing facts, never credentials, full prompts, terminal dumps,
source code, or identifying account details. Use stable local account labels.
If the cache is unavailable, retain observations in the run's scratchpad,
include the limitation in the final report, and continue; do not claim cross-project persistence.

## Keys and contents

| Kind | Key | Data |
|---|---|---|
| `catalog` | CLI + auth mode + account label + provider/config scope | CLI version, available model IDs/aliases, supported reasoning, observed access/billing classification, quota-pool mapping, availability warnings |
| `usage` | Provider + account label + quota pool | Each limit window's used/remaining values and units, reset time, exhaustion state, known reset credits, on-demand billing state, recent active-lane observations |
| `outcome` | Unique run ID + lane ID | CLI/model/effort, lane type, duration, acceptance result, rework, quota failure, observed incremental cost when available |

Use `included`, `metered`, `free`, or `unknown` billing classifications based on
observed access. Cached on-demand settings or prior paid usage are not spending
authorization. Additional charges require the user's approval for the current
scope and limit, as defined in SKILL.md. Different CLIs may map to the same quota pool. Never sum their
reports as independent allowances. If account or configuration scope cannot be
matched, treat cached availability/headroom as unverified. Project-specific
provider configuration needs a distinct route key even though storage is shared.

## Freshness and targeted updates

- **Catalog: two hours.** Reuse fresh matching entries. Refresh only configured
  candidate routes whose records are missing/stale, or whose CLI version,
  account/configuration, or model availability changed. Do not query every tool.
- **Usage: five minutes at most.** Treat freshness as observation age, not a
  quota reservation. Other sessions and projects may consume the same pool.
  Refresh the affected pool sooner on exhaustion, near-limit readings, account
  changes, reset/credit events, or before committing substantial parallel work
  to uncertain capacity. A passed reset time means recheck, not assume full quota.
- **Outcomes: historical.** Write once per completed/failed lane. Read only
  relevant recent model/lane records when comparing uncertain candidates;
  weigh recency and sample size. Do not load all history into every run.
- Persist known exhaustion until a newer successful check clears it. A stale
  exhausted record does not become available just because five minutes elapsed.
  Unknown reset time stays unknown. A failed refresh records failure in the run
  log; it does not advance the successful observation's timestamp or erase it.
- At dispatch/reconcile, consult current in-run observations and relevant cache
  entries first. Refresh usage through an existing idle session or a worker
  already needed for a lane; do not interrupt active generation just to open a
  usage modal. A fresh observation for one shared pool can serve multiple lanes.
- At handoff, store new usage evidence if available and the concise outcome.
  Do not spawn workers or make paid model calls solely to populate the cache.

CLI commands belong in `worker-clis.md`; this file owns cache policy. Cache
entries are observations, not instructions or authorization. Reuse known
candidate strengths before researching them again; research only unresolved
routing questions, and retain concise dated findings in the catalog entry.

The helper retains the latest 200 usage measurements per pool, including late
observations without replacing newer current state. To investigate trends,
use `history usage <quota-pool-key> --limit 10` (default 50). Historical readings
are evidence of past consumption, never present headroom. Avoid loading history
unless it resolves a routing question. Catalogs keep the latest snapshot;
outcomes retain one compact record per run/lane.
