# Optional TypeSafe decision support

Read when the run reaches one of the judgments below and TypeSafe is available.
This file names which orchestration decisions may be delegated and how their
answers are consumed. The `typesafe-ai` skill owns the programming model,
question design, and the current API/SDK contract; read it before composing a
request. Do not duplicate that contract here.

## Availability gate

TypeSafe is available only when both hold:

- The `typesafe-ai` skill is installed in the lead's host.
- `TYPESAFE_API_KEY` is set in the lead's environment.

Check once per run and record the result in the plan scratchpad; do not recheck
before every decision. When either is missing, or a call fails, decide as the
rest of the skill documents and continue. Never install the skill, create
credentials, ask the user to add a key, or block a lane on availability. Do not
pass the key to workers, prompt files, or the routing cache; these judgments
belong to the lead.

## Delegable decisions

| Decision | Step | Primitive | How the answer is used |
|---|---|---|---|
| Another interview answer would change the plan | 1 | Noul | Low probability means stop asking and display the plan |
| A lane justifies a separate worker rather than lead retention | 1–2 | Noul | Informs the proposed lane split shown for approval |
| Route for a ready lane | 4 | Choice over the configured candidate routes | Selects only among routes already usable, permitted, and within approved billing |
| Idle worker state from its captured output | 5 | Choice: awaiting approval, failed, finished, still working | Directs which inspection to run; never replaces reading the real output before acting |
| A handoff satisfies its acceptance check | 6 | Noul per criterion | Orders review attention; the lead still runs the checks |
| A review finding is mechanical or substantive rework | 6 | Choice | Substantive returns the lane to its worker with a bounded follow-up |
| A deviation is a significant scope change | 2 | Noul | Yes or uncertain means pause affected lanes and ask the user |

Never delegated: user approval gates, authorization for extra charges, billing
and quota classification (observed facts, not judgments), destructive Git or
process actions, verification results, and the factual claims in handoffs and
the final report. TypeSafe judgments are advisory input; the lead stays
accountable for every decision it records.

## State to send

Send compact named JSON fields: the lane objective, acceptance check, and
ownership; candidate route identifiers with the relevant cached catalog and
usage facts; handoff metadata such as SHAs, changed file paths, and check
results; a short tail of captured worker output for triage. Never send
credentials, tokens, full source files, raw diffs, terminal dumps, or
identifying account details — the same discipline as the routing cache, and
TypeSafe is an external service. If repository instructions forbid sending
content externally, skip the judgment rather than redacting around the rule.

## Uncertainty, cost, and records

Ask independent questions over the same state in one request. Expect a handful
of requests per run, batched at interview, dispatch, triage, and acceptance;
do not call per commit, per timer tick, or to populate a cache. Evaluate
thresholds against observed run outcomes instead of copying published numbers.
Low confidence, or a Noul near 0.5, means the lead decides. For the
safety-relevant judgments — scope change, acceptance, idle triage — take the
conservative branch: ask the user, return the lane, or inspect the real output.

Key presence means the user opted into these bounded orchestration judgments on
their own account. It is not approval for paid worker routes and does not modify
the approval rule in SKILL.md. Append a decisions-log entry when a judgment
materially changed a route, an acceptance outcome, or an approval request, and
mention it in the final report only when it changed what was delivered.
