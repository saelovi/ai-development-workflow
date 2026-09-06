# Task: Bootstrap AI guide files for this repo

Read `INTEGRATE.md` first. Use a new task worktree. Adapt existing guidance; repo conventions win. This prompt installs guidance and its checker, not vendor automation, linters, or CI. Next prompts are `harness.md` (optional) and `tooling.md`.

Resolve `<py>` to an installed Python 3.8+ (`py -3`, `python3`, or `python`, verified by execution). Record the working command; do not assume Windows has the same interpreter as CI.

Copy `ai-state-check.py` and `ai-state-check-test.py` verbatim into `bin/`; copy `delivery.md` verbatim to `docs/ai/workflows.md`; for Claude Code, copy the three optional `agents/*.md` into `.claude/agents/` when those roles will be used. The implementer brief preloads two superpowers skills through its `skills:` field; entries for an uninstalled plugin are skipped without error, so keep or remove them as the repo prefers. These files are beside this prompt. Retire unchanged old template runners (`implement-runner`, `spec-verifier`, `review-runner`); reconcile custom definitions. Other agent hosts use these role briefs through their native dispatch mechanism.

Keep `.ai/` gitignored. Before capturing tests, add narrow ignores for actual generated caches/build output; `--test` rejects all untracked files too. Never ignore source changes just to pass the clean-tree check. Preserve any existing evidence-retention policy using a location outside the reviewed branch; record the mapping in overrides. Finish active old runs with their existing checker when practical. Update checker, tests, and delivery guide together; the new checker's `--archive` preserves older-schema or orphaned evidence before `--init`. Schema 3 does not silently resume older state. Run `<py> bin/ai-state-check-test.py` before trusting the copy.

From this task worktree root: `<py> bin/ai-state-check.py --init setup`. Steps: `audit → files → smoke → review → verify → pr`. Before each step run `<py> bin/ai-state-check.py <step>`; afterwards `--advance <step> --set key=value ...`. The next step's prerequisites must pass before advancing. Never hand-edit state. The schema-3 flag `claude_md=true` means root guidance exists; either `AGENTS.md` or `CLAUDE.md` satisfies it. The delivery guide defines evidence, test capture, and archiving.

## audit

Inspect stack/runtime, architecture, test/CI setup, conventions, existing guides, host/PR mechanism, developer OS, and CI OS. Prefer `rg`/reads; a code graph is optional when useful and current. Record observed differences in `docs/ai/overrides.md`: template default, repo choice, keep/override, and why.

Profile is a **tooling budget only**: small = solo/small internal or prototype repo; medium = a maintained production application/team; large = several teams or a substantial monorepo. Use observed needs to resolve overlapping signals. Delivery risk is evaluated per change; no automatic full workflow because contributor count grew.

Record actual stack/platform, host, interpreter, profile and reasoning; existing harness/guide files; evidence retention; commit conventions/history policy; and relevant tooling gaps. Do not install missing tools here.

`--advance audit --set profile=small|medium|large --set platform=<actual> --set stack=<actual>`; choose one profile, not the literal pipe-separated text.

## files

Preserve the repo's existing canonical root guide (`AGENTS.md` or `CLAUDE.md`); if neither exists, use `AGENTS.md`. Derive adapters only for active hosts, preserving one source of truth. Target ≤150 lines (200 maximum), each installed Cursor rule ≤50. Use pointers with a reason to read them. Avoid repeating manifests, formatter rules, vendor failure lore, or model ids in root guidance. Include:

- Architecture and navigation pointers; existing conventions; match patterns, YAGNI, and concrete repo-specific constraints.
- Routing: quick/standard work has no state ceremony; substantial features, architecture, and consequential risks use `docs/ai/workflows.md`. Risk wins over line count. A harmless wording/toggle change can be quick; security/data behavior changes cannot.
- Gate command with the resolved interpreter, **only for setup/gated work**, and the task worktree as its execution root.
- Short sections for actual targeted/full check commands (or their absence), commit conventions, and repo-specific review risks. Repo conventions win; otherwise use Conventional Commits and logical commits. Preserve reviewed commits until merge. Point to workflows, overrides, vendors, and nonempty learning files; tool commands only if present. Extract long details only when the root guide would exceed its budget.
- `spec-planner` is optional; `implementer` is a worker; `reviewer` is an independent fallback reviewer. The interactive session orchestrates and dispatches preferred vendor CLIs directly.
- Instruction/gate changes route by behavior: independent review for changed agent permissions, workflow rules, or evidence checks; quick for pure spelling/link fixes. Check affected guides, agents, and scripts for consistency. Do not generate a contract-glob test unless existing automation actually consumes those patterns.
- Explicit adopted-workflow precedence: “Use quick/standard/gated routing from docs/ai/workflows.md. For quick/standard work, omit plugin-mandated brainstorming interviews, design approval pauses, formal plans, and blanket TDD. Run proportionate checks and a regression check for non-trivial behavior. Use planning skills only when they help gated work; reuse its artifacts. Ask only for consequential missing decisions or actions outside existing authorization.”

Default to three supporting documents under `docs/ai/`; add the two learning files only when there is something useful to retain:

- **`workflows.md`**: the copied delivery guide is the single procedure, including feature retrospectives and the improvement loop. Keep repo-specific exceptions in **`overrides.md`**: private central run-ledger/improvement-log locations when available (initialize from `templates/` into an ignored `.local/` directory or another private workspace), installed workflow revision, and the durable retrospective location (existing PR/task notes by default). For each override, record its repo/stack/vendor applicability and reason; preserve it during bundle upgrades unless its cause is resolved. Capture the resolved source commit or installed guide fingerprint at setup; refresh it when updating the guide.
- **`vendors.md`**: merge operator preferences and available routes here, seeded from `model-preferences.md`, or `model-preferences.abi.md` only when explicitly selected. The generic profile supplies common identity/fallback rules; merge selected role choices into it. Adapt source-only links when installing. Keep personal choices out of the shared delivery procedure. Start with unresolved preferences; record actual ids and verification dates when used. Keep fallback order, interpreter/dispatch notes, and the independent-reviewer selection rule here. Do not probe unused fallbacks during bootstrap.
- **`LESSONS.md` / `LANDMINES.md`**: create only for useful repo-specific learning. Lessons explain what worked/failed, why, and prevention/reuse. Landmines describe active hazards: trigger, consequence, workaround/check, evidence link. Escaped defects include why existing review/checks missed them. Aim ≤100 lines each; deduplicate and retire hazards now prevented structurally. Read relevant entries before substantial planning. No mandatory append per round; the delivery guide defines capture and learning from observed defects.

When updating an existing repo, consolidate `operator.md` into vendors and short testing/commits/review-process notes into the root guide, update incoming links, then retire redundant files. Preserve substantial established docs by linking to them. File count is a budget, not a reason to delete useful content or inflate always-loaded instructions.

`--advance files --set claude_md=true --set state_check=true`.

## smoke

Check checker tests, derived-guide consistency, line budgets, Cursor activation rules, and that installed agent definitions load in Claude Code when used. Agent loading is not evidence that a model dispatch succeeded. No throwaway PR or successful commit needed solely to prove Git works.

Commit intended changes. Set `implementation_models` to all actual author ids. Run `<py> bin/ai-state-check.py --test -- <repo-check-command> <args>`; without an existing entry point, run the checker tests and record that they verify the workflow only, not application behavior. Then `--advance smoke --set smoke_ok=true`.

## review → verify → pr

Request the configured independent code reviewer to inspect `base_sha..HEAD`, using a model distinct from the authors; use an independent fallback if unavailable. The harness is optional. Write `.ai/reviews/round-1.md` using the delivery guide's six-field header and findings. `--advance review` before making fixes.

At verify, fix/commit findings, rerun checks if HEAD changes, and get focused round 2 when HEAD changed or round 1 had blockers. No-change, zero-blocker reviews need no second call. `--advance verify` checks fresh evidence; then open the PR via the detected host and `--advance pr`.

Hand-off: routing, profile/platform/stack/host/interpreter, guide sizes, overrides, smoke/review evidence, limitations, and the next optional setup prompt. Report measured effort briefly; do not manufacture metrics.
