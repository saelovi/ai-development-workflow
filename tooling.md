# Task: Audit and propose developer tooling for this repo

Work on a **new git worktree**. Do not touch the current working branch.

**Prerequisite:** `AGENTS.md` or `CLAUDE.md`, `docs/ai/overrides.md`, `bin/ai-state-check.py`, `bin/ai-state-check-test.py`. If any is missing, **stop**. Run `bootstrap.md` first. Do not invent a parallel contract.

Follow `docs/ai/workflows.md` for state and review evidence. The orchestrator dispatches the configured code reviewer directly when available, with an independent-model fallback; the harness is optional. Run everything from this task worktree root.

**This task changes tooling behavior and agent guidance, so it uses the gated `tooling` order below.** The proposal supplies the plan; there is no separate interview or mandatory architecture spec. Independent code/config review is required. **Install only the items the human has approved**; existing explicit authorization counts.

**Gate.** `<py>` is whatever the canonical root guide's gate line names. `<py> bin/ai-state-check.py --init tooling`. Before every step: `<py> bin/ai-state-check.py <step>`. Exit 1 → stop. After a step: `--advance <step> --set key=value ...`; it refuses until the next step's keys pass. Never hand-edit `.ai/state.json`. `install` will not start until `proposal_approved` is JSON `true`; the strings `"yes"` / `"true"` and the number `1` are refused.

Steps: `detect` → `audit` → `propose` → `install` → `guides` → `review` → `verify` → `pr`.

## detect

Reuse `docs/ai/overrides.md`; fill only gaps. Profile determines tooling budget, not delivery/review depth. Reassess it when observed needs change, not at the start of every code task.

- **Language / framework** from manifests. Mixed repo: primary = application language.
- **Runtime actually in use** (`.php-version`, composer `platform`, `.nvmrc`/`engines`, `.python-version`, `go.mod`, `rust-toolchain`, CI images). These bound tool versions.
- **Platform** (developers + CI). Do not assume bash. **Never propose a hooks manager developers cannot install.**
- **Host / CI** from remote + `bitbucket-pipelines.yml` / `.github/workflows/` / `.gitlab-ci.yml` / `Jenkinsfile` / none.
- **Frontend:** meaningful if ~10+ app-authored JS/TS files under the frontend dir, or any component/framework code. Else incidental.
- **Profile:** small (solo/small internal or prototype), medium (maintained production application/team), large (several teams or substantial monorepo). Resolve overlapping signals using actual tooling needs and record why.

State those at the top of the proposal. `--advance detect --set profile=small|medium|large --set platform=… --set stack=…` (real values; `n/a` is refused).

## audit

Config files first. Code graph only if installed and not stale; say once if missing, then `rg`. Per category: present / absent / misconfigured, where, version.

Categories: formatter; linter; static analysis / types + strictness; refactor/upgrade tooling; tests (runner, coverage, parallel); commit-msg enforcement; hooks manager; staged-file runner; `.editorconfig`; single task entry (`composer|npm|make|just check`); CI (checks, triggers, image); dep/vuln audit; `.gitattributes` / `.gitignore` (including `.ai/`).

Stack defaults: **PHP/Laravel** — Pint or PHP-CS-Fixer; PHPStan/Larastan + level; Rector = upgrade not daily; PHPUnit/Pest; `composer audit`; GrumPHP/CaptainHook or Node hooks if Node exists. **JS/TS** — ESLint (flat vs legacy); Prettier; Stylelint only for hand-written CSS; `tsc`; Vitest/Jest; `npm audit`; Husky + lint-staged + commitlint; Vite lint if applicable. **Python** — Ruff; mypy/pyright; pytest; `pip-audit`; `pre-commit`. **Go** — gofmt/goimports; golangci-lint (do not also propose staticcheck); `go test`; govulncheck; lefthook or pre-commit. **Else** — same categories, name that stack's standard tools.

`--advance audit --set audit_done=true`.

## propose

Write `.ai/tooling-proposal.md`. Per item: tool + what it enforces; **pinned version compatible with detected runtime** (older runtime → newest compatible tool, and list the runtime upgrade separately; never install what cannot run); status add/upgrade/reconfigure/remove; **why tied to an observed problem** (no problem → drop a tier; if that lands optional, omit); friction (seconds, false positives, learning); OS/install catch; default config + one or two deviations; tier essential/recommended/optional.

Present a concise, concrete proposal. If the requested items are not already authorized, wait for approval before installation. Keep the approved scope in `.ai/tooling-proposal.md`, then `--advance propose --set proposal_approved=true`. The checker fingerprints this file and requires it unchanged before install and subsequent steps. Put progress/results in separate notes. Revised scope needs approval in a new run that preserves the original PR base and archives prior evidence. This boolean records approval; its type does not authenticate the human decision.

Defaults (medium), then scale:

- Essential: formatter; static analysis or types; `.editorconfig`; single lint+analyse+test entry; CI running all three.
- Recommended: commitlint + hooks manager; staged-file lint; frontend lint/format if meaningful.
- Optional: refactor dry-run; style lint; dep audit in CI; coverage threshold.
- **Small:** essential = formatter + entry + `.editorconfig`. Static analysis only if nearly free. No hooks, no commitlint (convention in the canonical root guide + review). CI only if it exists or the repo deploys. No Rector/Stylelint/coverage/dep-audit.
- **Large:** defaults + coverage threshold, dep audit in CI, staged-file lint as essential.
- No observed problem in a category → propose nothing for it.
- Laravel: Pint `laravel` preset; Larastan from level 5 unless already cleaner. TS: `strict` only if close to passing; else incremental flags + follow-up.
- **No CI, when this profile/deployment needs it:** its own essential item. Minimal: install deps, run the entry, services the tests need, image matching runtime. Say that a pipeline is bigger than a config file.
- **Hooks:** (1) portable on developer OS; (2) Node already installed (`package.json` that people `npm install`, including Vite-only) → Husky + lint-staged + commitlint, and say so if Node is only the build tool; else language-native (PHP GrumPHP / `grumphp-shim`, CaptainHook only if GrumPHP stash/boot is a problem; Python `pre-commit`; else lefthook or `pre-commit`). **Never add `package.json` just for Husky.**
- Pre-commit: formatter + linter on staged files, a few seconds, **not** analysis or tests (pre-push or CI). Over ~10s → move or drop.

State which profile branch, and why, at the top.

## install

One tier at a time, essential first, own commits. Pin, config, task script, hooks/CI if approved. Wire hook install into dependency install (`prepare` / `post-install-cmd` / setup task); else put the manual command in the hand-off.

Run each tool once. **Do not auto-fix the whole repo.** Baseline counts go in `docs/ai/tooling.md`, not `.ai/`. Existing violations: baseline/exclude **or** a cleanup follow-up — never a mass-reformat commit.

Commit per tool (`build(tooling): …`, `ci: …`). Throwaway failing commit to prove the hook, then discard — on this worktree. If the hook cannot fire on this OS, record unverified.

`--advance install --set installed_tiers=["essential","recommended"]` (only tiers actually installed; values must be `essential` / `recommended` / `optional`).

## guides

Canonical root guidance: one line per pre-commit command + the single entry. No config prose. `docs/ai/tooling.md`: what/how/baseline exception/bypass flag (almost never); approved proposal (tool, version, tier, why, deviations, OS catch); baseline counts. Root review notes (or existing detailed review docs): what tools do not own. LANDMINES: remove entries now enforced structurally; list meaningful removals in the PR. `overrides.md`: deviations, including hooks skipped for OS. `LESSONS.md`: non-obvious audit finds. Regenerate installed host adapters from the canonical root guide. Check changed instructions for consistency; retain existing checks that enforce actual behavior.

Commit intended changes. Record all actual author ids with `--set 'implementation_models=["<actual-author-id>"]'` (adapt quoting to the shell). Run the repo check entry point via `<py> bin/ai-state-check.py --test -- <command> <args>`. Then `--advance guides --set guides_updated=true`; this refuses until the review prerequisites, including recorded tests, pass.

## review → verify → pr

The test result from guides is tied to its exact HEAD. Reuse it if HEAD is unchanged; no hand-entered suite pass.

Request independent review using the configured code reviewer, including config behavior, guide consistency, and old-wording sweep. Write `.ai/reviews/round-1.md` with the six-field header from `workflows.md`; `--advance review`. Fix and commit findings during verify. If HEAD changes or round 1 has blockers, rerun the repo checks and obtain focused round 2 with zero remaining blockers. Otherwise no second review call. `--advance verify` requires fresh tests, final review evidence, and clean work. Then open the PR and `--advance pr`.

**Hand-off:** detected profile and observed needs; approved/installed items and versions; runtime/OS deferrals; baselines and cleanup follow-ups; unverified hooks; first-pull command. Existing required CI still applies. Do not mark unavailable checks as passing.
