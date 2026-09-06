# AI workflow — setup index

Start with `INTEGRATE.md` to adapt this bundle to an existing repo. Use these focused setup prompts as needed:

| File | When |
| ---- | ---- |
| `bootstrap.md` | Install or update repo guidance first. |
| `harness.md` | Optional automation for repeated multi-vendor work, when the OS supports it. After bootstrap merges. |
| `tooling.md` | Audit/propose repo tooling after bootstrap; install only the approved items. Harness optional. |

Daily work is defined once in **[`delivery.md`](delivery.md)**; bootstrap copies it to `docs/ai/workflows.md`.

- **Quick:** update → relevant check → inspect diff → PR. No state file, formal plan, or automatic delegation.
- **Standard:** brief plan → implement/check → independent code review when warranted → PR.
- **Gated:** substantial features, architecture, or consequential risk → spec/plan → spec review → implementation → tests → code review → verification when needed → PR.

Risk determines depth, not line count or contributor count. A harmless toggle is quick; disabling a security control is gated. Choose model routes through `model-preferences.md`; Abi's optional example is alongside in `model-preferences.abi.md`. Preserve independent-model review for gated work.

After substantial features, use the delivery guide's improvement loop: short retrospective → repo lessons/landmines and a compact run row → periodic workflow maintenance → reuse in the next plan. Your private copy of `templates/workflow-improvements.md` retains shared decisions; this adds no checker step or recurring agent dispatch.

Files distributed by bootstrap:

| File | Installed as |
| ---- | ------------ |
| `delivery.md` | `docs/ai/workflows.md` (canonical delivery procedure) |
| `ai-state-check.py`, `ai-state-check-test.py` | `bin/`, copied verbatim |
| `agents/spec-planner.md`, `agents/implementer.md`, `agents/reviewer.md` | Optional role briefs; copy used roles into `.claude/agents/` for Claude Code |
| `model-preferences.md` | Starting preferences for operator setup; resolve live ids when needed |

The optional harness copies `ai-review-run.py` and `ai-review-run-test.py` into `bin/` beside the checker; it requires POSIX process groups. Supporting repo docs default to workflows, overrides, and vendors, with learning files only when useful.

The interactive session orchestrates. It dispatches preferred vendor CLIs directly, with one implementation writer; there is no agent just to relay another agent's CLI call. Other hosts use the same role briefs without depending on Claude-specific agent loading.

The gate is for setup and gated work only. It records test commands/results, checks revision-bound review artifacts, and keeps state in the task worktree. It does not authenticate human approvals or establish the quality of a review. Command reference and artifact format are in the delivery guide.

**Updating an installed copy:** finish active old runs with their existing checker when practical. Update checker/test/guide together and rerun tests; use the new checker's `--archive` to preserve older state and evidence before starting a new run. Schema 3 pins accepted reviews, the full-check command/log, and approved tooling scope; it does not resume older schemas. Quick work still has no state file. Retire the old `implement-runner`, `spec-verifier`, and `review-runner` definitions only if they are unchanged template copies; reconcile customized ones.

**Distribution:** bootstrap copies the checker and its tests; the review runner/tests and agent briefs are optional. Repo-local copies keep the selected version available to collaborators and CI. A user-level checkout can supply integration files, but a globally updated executable changes all consumers together and does not remove version/compatibility decisions. No global installer is needed until repeated upgrade work justifies one.
