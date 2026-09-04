## SDLC and Code Quality Checks

This app seems heavily vibe-coded and in a state of partial implementation. I want to add some rigor to the application and structure to this. 

## Toolchain
- build/run/package management: [uv](https://github.com/astral-sh/uv)
- linting/flakes/etc: [ruff](https://astral.sh/ruff)
- testing: pytest
- project tasks: [Task](https://taskfile.dev)
- pre-commit validation: pre-commit

## Improvements
### Local Development
- Anything that is run in a pre-commit hook or CI job should be executable locally - full stop
- Use Task tasks as to run checks and tests locally and in CI
- Task tasks should use uv to run tools/tests

#### Pre-Commit Validation
- All ruff checks should run on precommit hook
- Checks should run in "fix" mode so that code is automatically fixed/cleaned if possible and exit non-zero RC if not possible (and block commit)

### GitHub CI
- Github CI stages:
  - Quality
  - Testing
- Run Ruff checks
  - Keep each rough check in its own CI job that runs in the Quality stage so it's clear what's failing and why
  - Only needs to run on a single Python version (3.10)
- Run full pytest suite
  - Should include a test report on PR
  - Should include a coverage report on PR
    - Coverage should include only code owned by this package
    - Coverage should include branch coverage
  - Should run with python3.10 but set it up so I can execute tests against multiple python versions easily

## Notes
- I've restructured to src layout and tests might not work as a result - ignore failures like ImportErrors. That's fine for now
