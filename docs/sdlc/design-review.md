# Phase 1 Design Review — Leave Request Management

Source: `docs/sdlc/architecture.md`

Reviewed against `docs/sdlc/requirements.md`. The stack, the four API actions, and approve or reject through a GitHub pull request stay as designed. These decisions were confirmed with the user.

## Agreed updates

1. Create branch `leave/<id>` in a temporary worktree. Do not check that branch out in the project folder. Push the branch, open the pull request, then remove the worktree.
2. If the pull request cannot be opened, delete the new database row and delete the `leave/<id>` branch.
3. A blank field, or a date that is not `YYYY-MM-DD`, is bad input and returns a clear error. The start date still cannot be after the end date.
4. If `gh` cannot be read on list or view, return a clear error and leave the row unchanged. The same applies to a `PENDING` row that has no `pr_number`.

These updates are now in `docs/sdlc/architecture.md`.

## Accepted for Phase 1

- Cancel saves `CANCELLED` before closing the pull request, so that close is not stored as `REJECTED`. If the close then fails, the API returns a clear error and the status stays `CANCELLED`.
- A crash after the insert and before `pr_number` is saved can leave a `PENDING` row with no pull request. List and view return a clear error for that row.
- An approved request merges `leave-requests/<id>.md` into `main`. That file is the approval record.

## Left as designed

- Python 3, Flask, a local SQLite file, and the GitHub CLI.
- `app.py`, `store.py`, and `github_pr.py`, plus a few tests that use a fake pull-request client.
- No approve endpoint, no reject endpoint, no login, and no webhooks.
