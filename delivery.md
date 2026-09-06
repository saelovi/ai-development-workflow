# Delivery workflow

Use the lightest path that fits. Repo conventions and explicit human instructions win. Tooling profile (small/medium/large) does not determine delivery risk. Model/backend choices come from the repo's `docs/ai/vendors.md`, seeded from the selected model-preferences profile; roles below do not require a particular vendor. Read the chosen path and relevant reference sections; do not load every setup guide into every task.

## Choose a path

| Path | Use for | Process |
| ---- | ------- | ------- |
| Quick | Clear, local, reversible wording, correction, or harmless toggle | Update → relevant check → inspect diff → PR. Independent review only if uncertainty remains. |
| Standard | Bounded fix/enhancement using established patterns | Brief conversational plan → implement → targeted tests → independent code review when logic/integration uncertainty warrants it → fixes → PR. |
| Gated | Whole feature, architecture, migration, public contract, new dependency, security/payment/data-loss risk, or behavioral changes to agent instructions/gates | Spec/plan → spec review → implement → tests → code review → focused verification when needed → PR. |

Risk wins over line count: disabling authorization or backups is gated even in one line. Trace callers and the user path when consequences are unclear. Pure spelling/link fixes in guides may be quick; changed agent permissions or evidence rules need independent review.

For a narrow risky fix with an obvious established solution, a short combined plan and `--skip spec_review` suffice; record why no architectural decision needs cross-checking. Whole features, architecture, migrations, and new public contracts get spec review. Urgency can reduce scope, not essential verification.

The adopted routing explicitly replaces plugin-mandated brainstorming interviews, design-approval pauses, formal plans, and blanket TDD for quick/standard work. Keep proportionate checks and regression coverage for changed non-trivial behavior. On gated work, invoke relevant planning skills only within the plan step and reuse its artifacts. Existing authorization remains valid; ask only for consequential missing decisions or actions outside it.

## Quick and standard work

- Follow the existing repo; installing this bundle is not a prerequisite. Use a suitable task branch or create one, preserving unrelated work.
- No state file, formal spec, agent delegation, or interview checklist. Read relevant conventions and landmines; inspect shared callers and match existing patterns.
- Run the relevant existing check. Harmless text/config changes may need only a diff/config/manual check. Keep a runnable regression check for changed non-trivial behavior.
- Inspect the final diff; request independent code review when meaningful logic, edge cases, or integration warrant it. Fix useful findings, rerun affected checks, commit, and open the PR. Existing required CI applies; no extra full local suite solely because a PR exists.

If scope grows into gated work, preserve changes on the task branch, continue in a linked worktree, and initialize against the original PR target. Treat existing implementation as draft input for planning and review.

## Gated work

Use one authoritative **task worktree**, based on the intended PR target. Run the orchestrator, gate, implementation, and reviews from its root. Keep durable plans in the repo and `.ai/` gitignored. Preserve evidence in PR attachments or the repo's external evidence location; committing a report containing its own HEAD creates a circular reference.

Resolve `<py>` from the root guide. In this section, `gate` is shorthand for `<py> bin/ai-state-check.py`, not an installed executable. Initialize once:

```
<py> bin/ai-state-check.py --init implement-with-review-gate --base <PR-target-ref>
```

Only the narrow-fix exception adds `--skip spec_review`; set `spec_review_skip_reason` before advancing plan. The base is the merge-base with the target at initialization; reviews cover `base_sha..HEAD`. Integrating newer target commits requires fresh tests/review.

| Step | Check before starting | Artifact / completion evidence | Advance after completion |
| ---- | --------------------- | ------------------------------ | ------------------------ |
| Plan | `gate plan` | Committed spec/plan, actual `plan_models`, optional narrow-fix reason | `gate --advance plan --set spec_path=… --set plan_path=… --set 'plan_models=["actual-id"]'` |
| Spec review | `gate spec_review` | Independent spec report at current HEAD, zero blockers | `gate --advance spec_review` |
| Implement | `gate implement` | Logical commits, targeted checks, cumulative author ids | `gate --advance implement --set 'implementation_models=["actual-id"]'` |
| Test | `gate test` | `gate --test -- <repo-check-command> <args>` | `gate --advance test` |
| Review | `gate review` | Independent `.ai/reviews/round-1.md` at current HEAD | `gate --advance review` |
| Verify | `gate verify` | Dispositions, required fixes/tests/round 2, product check | `gate --advance verify --set product_check="<result or specific applicability reason>"` |
| PR | `gate pr` | Push/open PR using repo host mechanism | `gate --advance pr` |

The orchestrator alone writes state through the checker. `--print-next` reports order only; the named check validates prerequisites. An advance checks the current and next step before saving; failure writes nothing. `--template implement-with-review-gate` lists inputs. Examples use POSIX quoting; preserve each `key=value` argument and JSON on other shells.

### Plan and spec review

The orchestrator normally plans. Delegate to `spec-planner` only for useful independent exploration or context isolation. Infer answers from the request/repo before asking about consequential unknowns.

Before planning a substantial feature, read relevant `LESSONS.md` / `LANDMINES.md` entries and the most recent comparable retrospective. Search the run ledger by repo/area when available; load only relevant evidence. Carry applicable prevention checks into the plan and call out assumptions that no longer hold.

Write one combined spec/plan or reuse existing spec locations. State the user outcome, non-goals, behavior/edge cases, acceptance checks, and ordered tasks. Each task names its files, the change, its targeted check with the expected result, anything out of scope, and its **implementer lane** from `docs/ai/vendors.md`: the default lane when the task is mechanical and the check is decisive; a stronger available lane, chosen by the planner with a one-line reason, when the task carries design judgment, cross-cutting change, or auth/payment/data/migration risk. Flag the riskiest task. Assigned lanes are authors-to-be: reserve an independent code reviewer against them now. For consequential decisions, explain the simplest viable alternative and chosen tradeoff; cover compatibility, security/privacy, data changes, rollback, and operational checks where relevant. Use a small exploratory spike for a material unknown before freezing a speculative design.

Record every actual plan author in `plan_models` and commit before review. Use the configured **spec reviewer**, in a fresh context distinct from all plan authors. Resolve canonical ids in `docs/ai/vendors.md` when needed. Dispatch directly or through the optional harness; use an independent session if no harness is available.

Review behavior, architecture, security, compatibility, and acceptance gaps. Findings need evidence and impact. Accept useful findings; decline incorrect premises or disproportionate complexity with a concrete reason. Commit revised plans and obtain focused confirmation on the delta. Aim for one discovery and, if needed, one focused confirmation; unresolved material disagreement then needs human triage before more review calls.

The accepted `.ai/reviews/spec-review.md` names the final plan commit with zero blockers. Advancing spec review pins both report and spec/plan; a skipped review pins the plan at plan completion. Keep accepted files unchanged. Later progress goes in notes; changed scope/design starts a new run after archiving evidence, retaining the original PR base and existing work as draft input.

### Implement and test

Dispatch each task to the lane the accepted plan assigns, one coherent task/batch per fresh dispatch; the configured default implementer takes any unassigned task. Use `implementer` as a fallback worker in the same worktree. Reserve an independent reviewer before choosing author models; use the selection rules in `docs/ai/vendors.md`. Record all actual authors, including the orchestrator when it edits and every fallback. Lists are cumulative; the gate rejects author removal and normalizes whitespace/case.

One writer at a time. Supply worktree, starting HEAD, spec/plan pointers, scope, and acceptance checks. Review fixes use the same implementation route when practical; no extra relay agent. Commit logical changes. Verify returned HEAD here, scope, and check results; inspect and deliberately integrate any commits made elsewhere before continuing. State remains in the authoritative worktree.

Use parallel agents only for independently useful research or disjoint work with an integration owner and verifiable outputs. Default to sequential implementation. Share relevant file pointers, decisions, and acceptance criteria; avoid copying the entire conversation or repeatedly retrieving unchanged context.

If a helper takes more review/repair effort than the feature, reconsider it before another fix loop: remove, inline, or use existing facilities while preserving required validation. If the same substantive error survives one focused repair, investigate and consider a stronger implementer instead of repeated vendor ping-pong.

Commit intended changes, then record the full repo check entry point with `gate --test -- <command> <args>`. The gate runs an argument list without a shell, captures exit status/HEAD/log, and rejects dirty work or a command that changes HEAD/work. Narrowly ignore generated caches before capture; never ignore source to pass. Targeted development checks run separately.

The first successful capture pins the command; subsequent captures use the same argument list. The log is fingerprinted too. Rerun after HEAD changes or a failed check, not after unchanged review prose. A changed verification plan needs a new run. If there is no suite, record the actual available smoke/manual verification command and its limits. The gate proves that command succeeded, not coverage quality; unavailable required checks leave a draft.

### Code review and verification

Use the configured **code reviewer**, in a fresh context and on a model distinct from all implementation authors. Give base/HEAD, spec/plan, relevant guidance, and test log. Review the whole branch and trace assembled behavior: correctness, security, compatibility, spec deviations, then repo fit. Let tools handle mechanical checks. Instruction changes also need cross-file consistency and an old-wording sweep. Exercise the user/API path where applicable.

Write `.ai/reviews/round-1.md` on current HEAD. Advancing review fingerprints its contents. Reviewers never edit implementation or state. Triage findings with evidence; fix blockers and explain declines/non-blocking follow-ups. Ask only for decisions changing requirements or accepting material risk.

**Unchanged HEAD and zero blockers: no second LLM call.** Otherwise commit fixes, rerun the full check if HEAD changed (reuse a current passing capture otherwise), and obtain focused verification of the unchanged round-1 report, dispositions, and `round-1.sha..HEAD`. Reuse reviewer context when available. Round 2 accounts for every prior Blocking/Should finding by stable id, with fix evidence, justified decline, or non-blocking follow-up/owner. Check regressions from fixes; avoid another whole-branch discovery pass.

Write `.ai/reviews/round-2.md` at current HEAD, zero blockers, with `previous: <state.review_hash>`. Automatic code review is bounded to one discovery and one verification. If blockers remain, keep a draft and present remaining issues/proposed fixes for human triage before another LLM review. Continue useful authorized fixes/checks meanwhile. Preserve attempts before any explicitly authorized additional focused verification. Never relabel blockers to pass.

Record a product check result (or specific applicability reason). Advancing verify requires fresh tests, clean work, and a final zero-blocker report, then pins the final report. Later edits invalidate acceptance. Open the PR and complete `pr`; preserve reviewed commits until merge. Report behavior, checks, dispositions, fallbacks, and limitations. Required CI and repo merge policy govern merge; the local gate does not authorize automatic merge.

For deployed features, include the expected production signal, rollback trigger, and responsible person in the PR when relevant. Deploy only within existing authorization. Use actual post-deploy failures to improve checks and lessons; a green local gate is not production validation.

## Review artifact contract

Each spec/code report begins with these lines, a blank line, and findings/dispositions with file:line evidence, or a concrete account of what was examined when clean:

```
model: <actual canonical model id>
effort: <actual setting or default>
backend: <actual CLI/session>
base: <full state.base_sha>
sha: <full reviewed commit id>
blocking: <non-negative integer>

<findings, dispositions, verification notes>
```

Round 2 adds `previous: <state.review_hash>` before the blank line. This is the accepted round-1 file hash, not its commit id. Accepted spec/round-1/final reports are immutable. Restore accidental edits from preserved originals; deliberate replacement needs a fresh run, not a hand-edited state hash.

Use canonical ids consistently across vendors. Follow the reviewer-selection rules in `docs/ai/vendors.md` before dispatch. The gate cannot detect aliases, prove which model ran, or judge review quality. The optional runner validates revision/output metadata but cannot attest provider identity. Inspect actual session/provider metadata; never label a silent model substitution as the requested model. If independence cannot be established, leave review pending/draft.

## Resume and setup

- `--set` accepts template inputs only. Step/base/worktree/skips, fingerprints, and test evidence are managed. Completed runs reject writes/captures. Approval flags are assertions, not authenticated human decisions.
- `--archive` preserves state, reports/logs, test log, and tooling proposal in `.ai/runs/<timestamp>/`, including orphaned artifacts. Use after completion or intentional replanning; do not restart to evade failed checks.
- Setup/harness/tooling keep their one-time named orders and shared `review → verify → pr` checks. Commit, set all author ids, and capture appropriate repo checks before review. Round 2 remains conditional. Tooling approval pins the actual proposal; a spec-review skip is not installation approval.
- Keep lessons only for surprises or escaped defects. Promote stable rules into existing guidance/checks and remove obsolete entries.

## Improvement loop

For substantial features (including failed/abandoned runs), keep a short retrospective in the existing PR/task record; use `docs/ai/retrospectives/<date>-<feature>.md` only if no durable record exists. Quick work needs no reporting ceremony.

```
Outcome: intended behavior → checked result; PR and code revision.
Review: useful findings, false positives, or missed issues; evidence links.
Friction: repair rounds, fallbacks, or avoidable human effort.
Lesson: what to reuse or change next time, and why; or none.
Landmine: active hazard, consequence, and prevention check; or none.
Next: one useful action with an owner, or none.
```

Append one row to the private run ledger (date, repo, run/PR, outcome, review rounds, confirmed blockers, fallbacks, workflow revision, notes). Link the retrospective; leave unknown counts blank. Ledger unavailable: retain the row in that record for later collection. Use the source commit for an unchanged bundle, otherwise the installed guide's SHA-256 fingerprint. Detailed optional measurements belong in existing evidence, not mandatory columns.

Keep reusable lessons and active landmines in the source repo; read relevant entries before the next plan and retire warnings now prevented by checks. Record escaped defects when normal usage or incident work reveals them, updating the original retrospective; do not create a scheduled revisit or assume silence proves success. Preserve useful notes before deleting worktrees. Learning edits after accepted code evidence use the normal follow-up path with appropriate fresh checks; accepted reports stay immutable.

The workflow owner reads roughly ten comparable runs during normal maintenance, or investigates sooner after repeated friction or a serious defect. Scope classification and experiment guidance live in the central improvement log, read only when maintaining the workflow. Local lessons stay local; promote shared rules only with evidence and normal independent review. No automatic reporting agent or extra delivery gate.
