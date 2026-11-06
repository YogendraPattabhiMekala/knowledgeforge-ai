# Contributing
Use Python 3.12+ and Node 22 LTS. `make demo` starts a safe no-key local demo; README explains the full Docker stack.

Use `apps/api/requirements.lock` for installation. `requirements.txt` declares direct dependencies; regenerate the Python 3.12 resolution after changes, review it, rerun `pip-audit`, and verify both local and PostgreSQL suites. npm uses `npm ci` and a committed lock file.

Add negative tenant/role tests to every scoped endpoint. HTTP composition belongs in domain routers; shared business/integration logic should not depend on HTTP handlers. Prefer small typed screens and shared primitives over growing the shell/controller.

Run backend tests, typecheck, frontend tests/build and browser checks before a PR. Changes to DB schemas need reviewed Alembic revisions. Integration fixtures are destructive and require a dedicated `_test` database.

Never commit credentials, user documents, databases, raw logs, test reports or archives. Curated synthetic documentation screenshots are allowed. Run `python scripts/release.py --check` and review `git diff --cached` yourself. Do not seed production or run paid models in CI. Report real test results and environmental failures honestly.
