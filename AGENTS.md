# Working on this workflow bundle

This repository distributes workflow documents, optional agent briefs, and stdlib Python scripts. It is not an application scaffold.

- Integrating into another project: start with `INTEGRATE.md` and resolve the target repository before making changes there.
- Maintaining this bundle: keep role policy in `delivery.md`, generic settings in `model-preferences.md`, and Abi's optional choices in `model-preferences.abi.md`. Avoid personal filesystem paths, account details, and machine inventories.
- Preserve quick/standard/gated routing. Changes to gates, review independence, or instruction behavior need appropriate independent review; do not manufacture review evidence.
- Keep the scripts dependency-free. Run `python3 ai-state-check-test.py` for gate changes and `python3 ai-review-run-test.py` for runner changes; update distributed scripts, tests, and docs together when their contracts change.
- Treat `templates/` as public blank examples. Real run records belong in a private workspace or ignored `.local/`. Keep source-repo details private unless deliberately supplied for publication.
- Use relevant context only. No requirement for a new agent, plugin, formal plan, or test suite for a simple editorial change.
