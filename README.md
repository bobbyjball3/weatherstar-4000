# WeatherStar 4000

A recreation of The Weather Channel's iconic 1990s WeatherStar 4000 local
forecast presentation.

> **Note:** the original README (features, controls, packaging, Raspberry Pi
> setup, etc.) has been preserved as [`README.old.md`](./README.old.md). This
> README focuses on the development toolchain, local checks, and CI.

## Overview

This project is managed end-to-end with modern Python tooling:

| Tool | Purpose | Invoked via |
| --- | --- | --- |
| [uv](https://docs.astral.sh/uv/) | Build / run / package / dependency management | `uv …` |
| [ruff](https://docs.astral.sh/ruff/) | Linting and formatting | `uv run ruff …` |
| [pytest](https://docs.pytest.org/) | Testing (with coverage via pytest-cov) | `uv run pytest …` |
| [Task](https://taskfile.dev) | Project task runner (checks, tests, CI) | `task …` |
| [pre-commit](https://pre-commit.com) | Git hook framework for commit-time checks | `uv run pre-commit …` |

Everything that runs in CI also runs locally through the same `task` commands,
so results are reproducible between your machine and GitHub Actions.

## Quick start

Prerequisites: Python 3.10 and [uv](https://docs.astral.sh/uv/) installed.

```sh
# Install task (taskfile.dev runner)
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b "$HOME/bin"
export PATH="$HOME/bin:$PATH"

# Create the environment (project + dev dependencies), pinned by uv.lock
uv sync

# Install the git pre-commit hooks
task install-hooks
```

The Python version is pinned in `.python-version` (`3.10`). `uv sync` reads it
so your local environment matches CI.

## Everyday workflow

```sh
task check        # ruff lint + ruff format --check
task fix          # auto-fix what ruff can (mirrors the pre-commit hooks)
task coverage     # full pytest suite with branch coverage + reports
```

### Available tasks

Run `task --list` or see [`Taskfile.yml`](./Taskfile.yml). All tasks execute
their tools through `uv run`, so they work on any machine with uv installed.

| Task | Command | Description |
| --- | --- | --- |
| `install` | `uv sync` | Sync project and dev dependencies |
| `lint` | `uv run ruff check src tests` | Lint the package and tests |
| `lint-fix` | `uv run ruff check --fix src tests` | Auto-fix lint issues |
| `format` | `uv run ruff format src tests` | Format code |
| `format-check` | `uv run ruff format --check src tests` | Verify formatting |
| `check` | `lint` + `format-check` | All quality gates |
| `fix` | `lint-fix` + `format` | Auto-fix everything possible |
| `test` | `uv run pytest` | Run the test suite |
| `coverage` | `uv run pytest --cov …` | Run tests with coverage + XML report |
| `install-hooks` | `uv run pre-commit install` | Install pre-commit hooks |

## Configuration

All tool configuration lives in [`pyproject.toml`](./pyproject.toml):

- **ruff** — `[tool.ruff]`, targets Python 3.10, 100-column lines, `src`
  layout. Lint rules enabled (`[tool.ruff.lint]`): `E4`, `E7`, `E9`, `F`,
  `I`, `UP`, `W`; everything fixable is auto-fixed.
- **pytest** — `[tool.pytest.ini_options]`; discovers tests in `tests/`, always
  writes a JUnit report to `reports/junit.xml`, and runs with
  `--continue-on-collection-errors` so one broken test module does not abort
  the whole suite.
- **coverage** — `[tool.coverage.run]` measures only code owned by this package
  (`source = ["src/weatherstar_4000"]`) with branch coverage enabled.

### pre-commit

[`.pre-commit-config.yaml`](./.pre-commit-config.yaml) runs ruff in **fix mode**
on every commit: safe lint fixes and formatting are applied automatically, and
the commit is blocked if anything could not be fixed. The hook ruff version is
pinned to match the version uv locked in the dev group.

## CI

GitHub Actions is defined in
[`.github/workflows/ci.yml`](./.github/workflows/ci.yml). It runs on push to
`main`/`master` and on pull requests, and is split into two stages:

### Quality stage

Each ruff check runs in its **own job** so failures are easy to isolate:

| Job | Runs | Tool |
| --- | --- | --- |
| `ruff-check` | `task lint` | ruff lint |
| `ruff-format` | `task format-check` | ruff format |

Both run on a single Python version (3.10).

### Testing stage

| Job | Runs | Notes |
| --- | --- | --- |
| `test` | `task coverage` | Python 3.10 by default; see matrix below |

The test job then:

1. **Publishes a test report** to the PR/commit checks
   (`EnricoMi/publish-unit-test-result-action`), generated from
   `reports/junit.xml`.
2. **Posts a coverage comment** on the PR
   (`MishaKav/pytest-coverage-comment`), generated from `coverage.xml`. The
   report is limited to package-owned code in `src/weatherstar_4000` and
   includes branch coverage.
3. Uploads `reports/junit.xml` and `coverage.xml` as a downloadable artifact.

Reports are only published when the token has write access (same-repo branches
and pushes). On pull requests from external forks the token is read-only, so the
publishing steps are skipped — the artifact is still uploaded.

### Running tests on more Python versions

The `test` job uses a strategy matrix that defaults to a single version:

```yaml
matrix:
  python-version: ['3.10']
```

Add versions to that list (e.g. `['3.10', '3.11']`) to run the suite across
them. Each matrix cell is pinned by overwriting `.python-version`, so CI never
drifts from the committed lockfile.

## Repository layout

```
pyproject.toml            uv / ruff / pytest / coverage configuration
Taskfile.yml              task runner commands
.pre-commit-config.yaml   commit-time ruff (fix mode) hooks
.github/workflows/ci.yml  Quality + Testing CI pipeline
.github/actions/setup     reusable CI step: uv + task + dependency sync
src/weatherstar_4000/     the package (src layout)
  __main__.py             application entrypoint (`python -m weatherstar_4000`)
tests/                    pytest suite
reports/                  JUnit output (gitignored, generated)
coverage.xml              coverage output (gitignored, generated)
README.old.md             original project README (features, packaging)
```

## Running the app

The installed command is `weatherstar4000` (equivalent to
`python -m weatherstar_4000`):

```sh
uv run weatherstar4000 --lat 40.7128 --lon -74.0060 --log-level INFO
```

Run `weatherstar4000 --help` for available options.

## Current status

- The project recently moved to a **src layout** (`src/weatherstar_4000/`).
  The test suite and several modules still import the legacy
  `weatherstar_modules` package, so most tests currently error on import, and
  the `weatherstar4000` entrypoint cannot start yet. This is a known, tracked
  issue — pytest tolerates it and still produces reports.
- The lint/format backlog in existing code is also not yet cleared, so the CI
  Quality stage is expected to be red until a cleanup pass lands. Run
  `task fix` to auto-apply the safe fixes, then address the rest manually.
- The former standalone launcher `run_weatherstar.py` has been moved into the
  package as `src/weatherstar_4000/__main__.py` and exposed as the
  `weatherstar4000` entrypoint. A stale copy still exists under
  `docs/alternative_launchers/` for reference.

