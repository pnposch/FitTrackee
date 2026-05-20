# FitTrackee – Copilot Instructions

FitTrackee is a self-hosted outdoor workout/activity tracker. The repo is a monorepo with two separate apps:

- **`fittrackee/`** – Flask (Python) REST API + Dramatiq task queue
- **`fittrackee_client/`** – Vue 3 + TypeScript SPA (built output lands in `fittrackee/dist/`)

## Build, Test & Lint

All commands are driven by `make`. Variables are set in `Makefile.config`.

### Python (backend)

```bash
# Install
poetry install                        # dev deps

# Run single test
.venv/bin/py.test -c pyproject.toml -W ignore::DeprecationWarning fittrackee/tests/path/to/test_file.py::ClassName::test_method

# Full suite
make test-python

# With coverage
make test-python-cov

# Lint (ruff)
make lint-python          # check only
make lint-python-fix      # autofix

# Type check (mypy)
make type-check

# All checks combined
make check-python
```

### Client (frontend)

```bash
# Install
cd fittrackee_client && npm ci --ignore-scripts

# Run single test file
cd fittrackee_client && npm run test:unit -- run src/path/to/Component.spec.ts

# Full suite
make test-client

# Lint (oxlint + eslint + prettier)
make lint-client          # check only
make lint-client-fix      # autofix

# Type check (vue-tsc)
make type-check-client

# All checks combined
make check-client
```

### Everything at once

```bash
make check-all   # lint + type-check + tests for both sides
```

### Database migrations

```bash
make migrate-db                                      # generate migration from model changes
make revision MIGRATION_MESSAGE="description"       # empty migration (data migrations)
make upgrade-db                                      # apply migrations
make downgrade-db                                    # roll back one step
```

## Architecture

### Backend

- **App factory**: `fittrackee/__init__.py → create_app()`. All blueprints are registered here under `/api`.
- **Blueprints** correspond to domain modules: `users`, `workouts`, `comments`, `equipments`, `sports`, `reports`, `oauth2`, `feeds`, `geocode`, `media`, etc.
- **Models**: each domain module has its own `models.py` using SQLAlchemy 2.x declarative style with `Mapped`/`mapped_column`.
- **Responses**: all HTTP responses use typed helper classes from `fittrackee/responses.py` (`HttpResponse`, `InvalidPayloadErrorResponse`, `ForbiddenErrorResponse`, `DataNotFoundErrorResponse`, etc.). Never return raw dicts – use these classes.
- **Auth**: JWT-based (`pyjwt`) for the SPA; OAuth2 (`authlib`) for third-party clients. Route handlers call `require_auth` from `fittrackee/oauth2/server.py`.
- **Task queue**: Dramatiq + Redis. Background tasks live in `tasks.py` files within each domain module.
- **Visibility**: workouts, comments and equipment all share a `VisibilityLevel` enum (`public`, `followers_only`, `private`) defined in `fittrackee/visibility_levels.py`. Always use `can_view()` / `get_calculated_visibility()` helpers from that module.
- **Custom database types**: `TZDateTime` (always timezone-aware) and `PSQL_INTEGER_LIMIT` guard are in `fittrackee/database.py`. Use `aware_utc_now()` from `fittrackee/dates.py` instead of `datetime.utcnow()`.

### Frontend

- **State management**: Vuex 4 with typed modules under `fittrackee_client/src/store/modules/` (one module per domain: `authUser`, `workouts`, `sports`, `equipments`, `users`, `statistics`, `notifications`, `oauth2`, `reports`, `root`).
- **API layer**: `src/api/defaultApi.ts` (unauthenticated) and `src/api/authApi.ts` (adds Authorization header). Duplicate in-flight requests are automatically cancelled via `src/api/pending.ts`.
- **Routing**: Vue Router 5, routes defined in `src/router/`.
- **i18n**: Vue I18n 11; locale files are in `src/locales/`. Always add/update English strings when adding user-visible text.
- **Styling**: SCSS; global variables/mixins are in `src/scss/`.

## Key Conventions

### Python

- **All functions must be fully type-annotated** (`disallow_untyped_defs = true` in mypy config).
- Line length is **79 characters** (ruff).
- Use **double quotes** for strings (ruff `quote-style = "double"`).
- `TYPE_CHECKING` blocks are used to avoid circular imports – import types there and use string annotations in signatures.
- Test fixtures are defined in `fittrackee/tests/fixtures/` and declared in `fittrackee/tests/conftest.py`. Standard user fixtures are `user_1` (regular), `user_1_admin`, `user_1_moderator`, `user_1_owner`, `user_2`, etc.
- Tests use `time_machine.travel` (not `freezegun`) for datetime mocking.
- Custom assertions live in `fittrackee/tests/custom_asserts.py`; test mixins in `fittrackee/tests/mixins.py`.
- The `@check_workout` decorator in `fittrackee/workouts/decorators.py` handles workout lookup and ownership checks for route handlers.

### Client

- Tests use **Vitest** + `@vue/test-utils`; test files live alongside source in a `tests/unit/` tree.
- Linting: **oxlint** runs first, then **eslint**, then **prettier** (run in sequence via `run-s`).
- Strict TypeScript (`tsconfig.app.json`); no `any` unless unavoidable.
- PRs target the **`dev` branch**, not `main`.

### Translations

- **Client**: `fittrackee_client/src/locales/` (Vue I18n JSON files).
- **API** (emails & RSS): `fittrackee/translations/` managed with Babel (`make babel-extract / babel-update / babel-compile`).

## Contributing Policy

Per `CONTRIBUTING.md`: PRs or bug reports generated entirely by AI/LLM tools, or with commits co-authored by AI/LLM tools, are **not accepted** by the upstream project maintainers.
