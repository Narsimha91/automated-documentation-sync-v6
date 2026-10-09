# Phase 1 Implementation Plan — Leave Request Management

Source: `docs/sdlc/architecture.md`

Six tasks, in dependency order. Keep each one small. Do not add layers beyond `app.py`, `store.py`, and `github_pr.py`.

## 1. Project setup

Add `requirements.txt` with Flask and pytest.

Blocked by: nothing.

## 2. Storage

Add `store.py`. Create `leave_requests` in a local SQLite file. Support insert as `PENDING`, get by id, list, save `pr_number`, set status, and delete a row.

Blocked by: nothing. Tasks 4 and 5 cannot start until this finishes.

## 3. Pull requests

Add `github_pr.py`. It opens, reads, closes, and deletes a pull request through `gh`.

Open creates branch `leave/<id>` in a temporary worktree, adds `leave-requests/<id>.md`, pushes the branch, and removes the worktree. The pull request body includes a description, a changelog entry, and a review checklist. Read reports merged, closed, or still open. Close closes without merging. Delete removes the branch when create fails.

The project folder stays on its current branch.

Blocked by: nothing. Task 4 cannot start until this finishes.

## 4. API

Add `app.py` with the four routes. There is no approve route and no reject route.

- `POST /leave-requests` validates the body, inserts the row, opens the pull request, and saves `pr_number`. A missing or blank field, a date that is not `YYYY-MM-DD`, or a start date after the end date returns a clear error. If the pull request cannot be opened, delete the row and the branch.
- `GET /leave-requests` lists rows and refreshes each `PENDING` row that has a `pr_number`.
- `GET /leave-requests/{id}` returns one row and refreshes it when it is `PENDING`.
- `POST /leave-requests/{id}/cancel` sets `CANCELLED`, then closes the pull request. If the close fails, the status stays `CANCELLED` and the API returns a clear error.

A missing row, a finished request, a `PENDING` row with no `pr_number`, or a failed `gh` read returns a clear error and does not change a finished or unreadable row. `APPROVED`, `REJECTED`, and `CANCELLED` are not read from GitHub again.

Blocked by: tasks 2 and 3.

## 5. Tests

Add `tests/test_leave.py`. Use a temporary SQLite file and a fake pull-request client. Do not call GitHub.

Cover create, list, view, cancel, merged to `APPROVED`, closed to `REJECTED`, and a second change after the request is finished. Create checks that the pull request body includes a description, a changelog entry, and a review checklist. Also cover bad input, an unknown id, a failed create cleanup, and a failed `gh` read that leaves the row unchanged.

Blocked by: task 4.

## 6. README

Update `README.md` with how to install dependencies, run the API from the project folder, and run the tests. Note that `gh` must be logged in for a real create, and that tests do not call GitHub.

Blocked by: task 4. Write it after the routes exist so the commands match the app.
