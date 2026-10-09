# Phase 1 Verification — Leave Request Management

Checked against `docs/sdlc/requirements.md`. Tests do not call GitHub.

## Test run

Command:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
python -m pytest -v
```

Python 3.14.6, pytest 9.1.1. Plugin autoload was turned off because a global Allure plugin fails to import (`No module named 'namedlist'`). The project tests do not use Allure.

Result: **10 passed in 0.54s**.

- `test_create_list_and_view`
- `test_cancel_pending_request`
- `test_merged_pull_request_approves_and_stays_approved`
- `test_closed_pull_request_rejects`
- `test_bad_input`
- `test_unknown_id`
- `test_failed_create_removes_the_row_and_branch`
- `test_failed_read_leaves_the_row_pending`
- `test_cancel_close_failure_stays_cancelled`
- `test_pending_without_pull_request_is_an_error`

The first run failed during collection because the `pytest` import had been removed. That import is restored. It is required for the test fixture.

## Content check

A create through the test client returned:

`id`, `employee_name`, `start_date`, `end_date`, `reason`, `status` `PENDING`, and `pr_number`.

List and view returned the same fields. A start date after the end date returned `400` and `{"error": "start_date must not be after end_date."}`. `POST /leave-requests/1/approve` and `POST /leave-requests/1/reject` returned `404`. Opening a new app on the same SQLite file still returned the saved request. The pull request body included a description, a changelog entry, and a review checklist.

## Requirements

- FR1–FR8: covered by the tests and the content check.
- NFR4: the main flow is covered, and the run did not call GitHub.
- Definition of done: create, list, view, and cancel work; merge maps to `APPROVED`; close maps to `REJECTED`; data survived a new process on the same database file; the tests passed.
