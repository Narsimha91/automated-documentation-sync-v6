# Phase 1 Architecture — Leave Request Management

Source: `docs/sdlc/requirements.md`

One local Python process. A manager approves or rejects a leave request on a GitHub pull request. The API does not expose approve or reject.

## Stack

- Python 3
- Flask for the REST API
- `sqlite3` from the standard library
- Local database file `leave.db` in the project folder
- GitHub CLI (`gh`) for pull requests in `Narsimha91/automated-documentation-sync-v6`
- pytest, with GitHub calls replaced by a fake in tests

## Layout

- `app.py` — routes and input checks
- `store.py` — create the table and read or write rows
- `github_pr.py` — open, read, and close a pull request
- `tests/test_leave.py` — the main flow against a temporary database and a fake pull-request client
- `requirements.txt` — Flask and pytest
- `README.md` — how to run the API and the tests

## Data

One table, `leave_requests`:

| column | notes |
| --- | --- |
| id | integer primary key |
| employee_name | text |
| start_date | text, `YYYY-MM-DD` |
| end_date | text, `YYYY-MM-DD` |
| reason | text |
| status | `PENDING`, `APPROVED`, `REJECTED`, or `CANCELLED` |
| pr_number | integer, null only if create has not finished |

## Endpoints

- `POST /leave-requests` — create. Body: `employee_name`, `start_date`, `end_date`, `reason`.
- `GET /leave-requests` — list. Refreshes each `PENDING` row from its pull request.
- `GET /leave-requests/{id}` — view one. Refreshes that row when it is `PENDING`.
- `POST /leave-requests/{id}/cancel` — cancel a `PENDING` request.

There is no approve route and no reject route.

## Create

1. Reject the call when a field is missing or blank, a date is not `YYYY-MM-DD`, or `start_date` is after `end_date`.
2. Insert a `PENDING` row and take its id.
3. Create branch `leave/<id>` in a temporary worktree. Do not check that branch out in the project folder. Add one file, `leave-requests/<id>.md`, containing the employee name, dates, and reason. Push the branch, then remove the worktree.
4. Open a pull request into `main` and store `pr_number`. The pull request body has three parts:
   - **Description:** employee name, start date, end date, and reason. State that merging approves the request and closing it without merging rejects it.
   - **Changelog entry:** one line, such as `Leave request <id> submitted for <employee name> (<start date> to <end date>).`
   - **Review checklist:** a short tick-list for the manager — the name, dates, and reason look right; the start date is not after the end date; merge to approve, or close without merging to reject.
5. If the pull request cannot be opened, delete the new row, delete the `leave/<id>` branch, and return a clear error.

## Approve and reject

List and view call `gh` for a row that is still `PENDING` and has a `pr_number`:

- Pull request merged: set status to `APPROVED`. Merging also brings `leave-requests/<id>.md` into `main`.
- Pull request closed and not merged: set status to `REJECTED`.
- Pull request still open: leave status as `PENDING`.

If `gh` cannot read the pull request, or the row is `PENDING` and has no `pr_number`, return a clear error and leave the row unchanged.

Rows that are already `APPROVED`, `REJECTED`, or `CANCELLED` are not read from GitHub again.

## Cancel

1. If the row is missing or not `PENDING`, return a clear error and do not call GitHub.
2. Set status to `CANCELLED`.
3. Close the pull request without merging.

The status is saved before the pull request is closed, so a later list or view does not treat that close as a reject. If the close fails, return a clear error and leave the status as `CANCELLED`.

## Errors

Missing or blank fields, a date that is not `YYYY-MM-DD`, a start date after the end date, an unknown id, and a status change on a finished request return a clear error. A missing `gh` login returns a clear error on create. If `gh` cannot be read on list or view, return a clear error and leave the status unchanged. The process stays up.

## Tests

Tests use a temporary SQLite file and a fake pull-request client. They cover create, list, view, cancel, merged to `APPROVED`, closed to `REJECTED`, and a second change after the request is finished. Create checks that the pull request body includes a description, a changelog entry, and a review checklist. They do not open a real pull request.
