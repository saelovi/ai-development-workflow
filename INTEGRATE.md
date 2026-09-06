# Integrate this workflow into an existing project

This is the entry point for a coding AI. The workflow source and the target project are separate repositories. Modify the target project; do not bootstrap the workflow bundle into itself unless that is explicitly the task.

## 1. Establish scope

Resolve the target path and workflow source from the user's request/context. If the target is missing, ask for that path before writing into a repo. Read the target's existing instructions and inspect its current guidance, checks, Git state, and relevant architecture. Preserve unrelated changes and existing conventions.

Read this file and `workflow.md` first, then the relevant setup prompt. Retrieve files from the selected source revision as needed, preserving relative paths; do not rely on a rendered directory listing or assume files from different revisions form a valid bundle. Prefer a local checkout outside the target for a consistent source. Do not copy this entire repository into an application.

An integration request authorizes adapting repo guidance and copying the checker. It does not by itself authorize new paid accounts, plugin installation, optional tooling, publishing private data, deployment, or changes outside the target. Existing explicit authorization still applies. Resolve routine implementation choices without an interview.

## 2. Choose preferences

Use `model-preferences.md` by default. Use `model-preferences.abi.md` only when the user selects Abi's example. Existing explicit user preferences win over both. Keep the generic profile's common identity/fallback rules and merge in the selected role choices. Write the effective roles and resolved routes into the target's `docs/ai/vendors.md`; keep model choices out of the common delivery procedure. Rewrite source-only relative profile links to the pinned source URL, or omit them from the installed copy so they do not become broken links.

Use already available tools/accounts. Leave unknown model ids or availability clearly unresolved until needed; do not fabricate verification. Before dispatch, resolve the actual author/reviewer identities and preserve independent review. If a required independent model is unavailable, prepare the work and report the pending review honestly.

## 3. Apply the smallest useful setup

Follow `bootstrap.md` for the concrete setup and evidence order. If an equivalent integration already exists, reconcile the differences and update its installed revision; avoid duplicate guides, runners, or rules. Finish active runs with their current checker before upgrading when practical.

Default installation:

- Copy `delivery.md` to `docs/ai/workflows.md` and both `ai-state-check*.py` files to `bin/`.
- Update the existing canonical root guide with routing, actual check commands, and pointers. Keep it short. Use `AGENTS.md` or `CLAUDE.md`; maintain host adapters only when they are used.
- Create/adapt `docs/ai/overrides.md` and `docs/ai/vendors.md`. Record the source revision, local exceptions, selected preferences, and private evidence/retrospective locations.
- Keep `.ai/` ignored. Create lessons/landmines only for useful observed knowledge.
- Install the optional agent briefs only for roles that will actually be used. On Claude they live in `.claude/agents/`; other hosts use their native mechanism.

Use `harness.md` only when repeated external dispatches justify automation and the platform supports it. Use `tooling.md` only for an actual tooling audit/install request. Neither is a prerequisite for ordinary daily use. Existing instructions and risk routing govern subsequent work.

## 4. Validate and hand off

Run the copied checker tests, inspect guide consistency and active host adapters, and run the relevant target checks. Follow bootstrap's independent review requirements; distinguish passed checks from pending reviews or unavailable tools. Do not mark evidence gates complete based on assumptions.

Hand off the changed files, selected model roles, source revision, checks, unresolved limitations, and where feature retrospectives/lessons will live. Show how the target handles a quick edit and a substantial feature. Do not publish, merge, or deploy beyond existing authorization.

The public files in `templates/` remain blank examples. Initialize working ledgers privately, such as under an ignored `.local/` directory in a separate workflow checkout. No metrics upload, telemetry service, or scheduled analysis is part of this integration.
