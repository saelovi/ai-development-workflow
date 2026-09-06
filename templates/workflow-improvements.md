# Workflow improvement log

Read this during workflow maintenance, not on every coding task. Per-feature
retrospectives and repo lessons/landmines stay in their source repo or PR.
[workflow-runs.csv](workflow-runs.csv) is a compact index of those records.
The [delivery guide](../delivery.md#improvement-loop) contains the capture procedure.
Keep working logs private; public templates remain blank.

No runs or trials have been evaluated yet. Do not fill this log with speculative
proposals or create one entry per feature. The workflow owner examines roughly
ten comparable runs during normal maintenance, or investigates recurring friction
and serious escaped defects sooner. Observed incidents enter the normal lesson
path; there is no scheduled per-feature follow-up obligation.

## Read the ledger

`date, repo, run, outcome, review_rounds, confirmed_blockers, fallbacks,
workflow_revision, notes` are the only required columns. `run` is a PR/run id;
use a suffix for a replan. `review_rounds` counts completed spec/code/verification
passes; fallbacks count attempted alternate routes. Count confirmed actionable
blockers once, not repeated accusations of the same defect. Leave unknowns blank.
Link the retrospective in notes; update that row when later evidence appears.

Scope/risk, actual models, and optional measured time/tokens/cost stay in the
linked PR evidence when available. Do not invent missing metrics or spend model
calls collecting them. Keep older populated ledgers intact; read the useful
columns rather than discarding history to match this smaller template.

Use a known source commit only when it describes the installed content; for an
uncommitted or locally changed guide, record `sha256:<guide fingerprint>` and
relevant overrides. A source commit is useful for releases but is not required
for local capture. Compare each repo with its own baseline and workflow revision;
unequal tasks and unknown observation windows do not establish model quality or
cost savings. Include failed runs and observed escaped defects. Lack of an
incident report is not proof of no defects.

## Classify the cause

| Scope | Evidence to look for | Change location |
| ----- | -------------------- | --------------- |
| Repository | Product behavior, schema, architecture, conventions, or check commands | Repo code/tests, lessons/landmines, root guide or overrides |
| Stack/platform | Framework/runtime version, OS, or deployment constraint | Conditional repo override; reusable opt-in guidance when needed elsewhere |
| Operator/vendor | Allowance, availability, CLI behavior, or personal preferences | Vendor/operator settings, with applicability and verification date |
| Workflow | Shared routing, handoff, review/evidence rule, or bundled script defect | Reviewed change to the shared bundle |

Ask whether the mechanism would remain if product, stack, and account changed.
Similar symptoms in two repos sharing a faulty dependency may still be a stack
issue. Default uncertain findings to local/provisional. A shared policy needs
evidence from independent repos or a reproducible defect in the shared rule/script;
a stale-review acceptance bug need not harm another repo before being fixed.
Explain why a local/conditional override is insufficient and which repos benefit.

## Change only what evidence supports

Investigate the mechanism before adding process: product bug, weak test, missing
context, model limitation, or workflow rule. For an actionable shared proposal,
record the following compact entry (stable id such as W001):

```text
ID / status: proposed | trial | adopted | reverted | inconclusive | closed
Evidence and scope: linked runs, mechanism, affected/unaffected cases.
Smallest change: local fix or shared change, and why; implementation link.
Check: observed baseline → intended benefit, quality guardrail, owner/sample.
Decision: measured result and evidence; adopt/revert or next action.
```

Trial one material policy change at a time on comparable work; use independent
repos where available and keep one-repo results provisional. Review the trial at
the next maintenance pass after its stated sample. Keep inconclusive results
inconclusive; adopt or revert against the original benefit and quality guardrail.
Known shared correctness defects can be fixed with regression evidence immediately.
Use normal risk routing and independent review for changes; retrospectives do not
authorize changed permissions or weaker gates. Retire superseded rules.

Compare total delivery effort, including repair/review, rather than an isolated
cheap call. If choosing between reviewers requires causal evidence, run a small
explicitly budgeted paired comparison on frozen inputs; do not duplicate every
review by default. Expand metrics or automation only after a concrete analysis
needs them. Update installed copies during normal maintenance, preserving local
overrides; a shared default change does not prove every repo was updated.

## Decisions

No evidence-backed decisions recorded yet.
