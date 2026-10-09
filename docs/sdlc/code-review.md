# Phase 1 Code Review — Leave Request Management

Reviewed `app.py`, `store.py`, `github_pr.py`, and `tests/test_leave.py` against `docs/sdlc/requirements.md`.

## Checklist

**Correctness.** Create, list, view, and cancel match the requirements. Approve and reject stay on the pull request. A finished request is not changed again. One gap is fixed below: a merged pull request could have been stored as `REJECTED` when `gh` reports it as closed and also sets `mergedAt`.

**Security.** SQL uses parameters. Git and `gh` run as argument lists, so request text is not a shell command. Input is checked for blank fields, `YYYY-MM-DD` dates, and date order. No secrets are written into responses.

**Error handling.** Bad input, an unknown id, a finished request, a missing pull request number, and a failed `gh` call return a JSON error. The process stays up. A pull request response that is not a URL or not JSON now becomes that same clear error, and create still deletes the new row and branch.

**Test coverage.** Tests cover create, list, view, cancel, merged to `APPROVED`, closed to `REJECTED`, a second change after the request is finished, bad input, an unknown id, failed create cleanup, a failed read, a failed close, and a pending row with no pull request. They use a fake client and do not call GitHub.

**Clarity.** The three modules match the architecture. Names describe the actions. The cancel comment explains why the status is saved before the pull request is closed.

**DRY.** Create stripped the same four fields twice. It now strips them once.

**Dependencies.** `requirements.txt` has Flask and pytest only. They are unpinned so a new install gets the current releases. No extra packages.

## Fixes applied

1. `github_pr.read` treats a pull request as merged when `state` is `MERGED` or `mergedAt` is set.
2. A pull request URL that has no number, or a `gh` view response that is not JSON, raises `GitHubError` so the API returns a clear error.
3. Create strips `employee_name`, `start_date`, `end_date`, and `reason` once.
4. The `pytest` import stays. The tests use it for the fixture.

## Left as designed

- No login, no approve route, and no reject route.
- Cancel saves `CANCELLED` before closing. If the close fails, the status stays `CANCELLED`.
- Tests do not run the real worktree or `gh` commands.
- A successful create can leave the local `leave/<id>` branch in this clone after the worktree is removed. The branch is already on the remote.
