# Phase 1 Requirements — Leave Request Management

Source: [Leave Request Management](https://narasing81.atlassian.net/wiki/spaces/~712020d5927c33f2e5433cbea73c335a08e134/pages/26345473/Leave+Request+Management)

Phase 1 is a small Python REST API that shows the basic leave request workflow and the Agentic SDLC process. Keep it simple. Do not over-engineer.

Confirmed with the user:

- Python REST API and a few tests
- Request fields are employee name, start date, end date, and reason
- No login in this phase
- Create, list, view, and cancel are API actions
- Approve and reject happen on a GitHub pull request
- Storage is a local SQLite file

The Confluence page names SQLite. The API replaces the “Python web framework” line in that section.

## User story

As an employee, I want to submit and manage my leave requests, so that my manager can approve or reject them.

## In scope

1. An employee can create a leave request with:
   - employee name
   - start date
   - end date
   - reason
2. A new request starts as `PENDING`.
3. Creating a request opens a GitHub pull request in this repository. The pull request is how a manager approves or rejects it.
4. Merging that pull request sets the status to `APPROVED`.
5. Closing that pull request without merging sets the status to `REJECTED`.
6. An employee can cancel a pending request through the API. Status becomes `CANCELLED`, and the pull request is closed.
7. An employee can view the current status of a request.
8. Anyone using the API can list requests. List and view refresh a `PENDING` request from its pull request.
9. `APPROVED`, `REJECTED`, and `CANCELLED` cannot change again.
10. The app is a local Python REST API.
11. Requests are stored in a local SQLite file.
12. A few automated tests cover the main flow.

## Out of scope (Phase 1)

- Login, passwords, roles, or permissions
- Email or other notifications
- Leave balances, holidays, or calendar views
- A web UI, cloud hosting, or a database other than local SQLite
- Webhooks
- Multiple leave types, attachments, comments, or edit after submit
- Team hierarchy or “only my manager can approve”

## Functional requirements

- FR1: Create a leave request with employee name, start date, end date, and reason. Reject create if any field is missing or the start date is after the end date.
- FR2: Store each request with a simple id, status `PENDING`, and the pull request number.
- FR3: Opening the pull request is part of create. The API has no approve endpoint and no reject endpoint.
- FR4: On list and on view, if the request is `PENDING`, read the pull request. Merged becomes `APPROVED`. Closed and not merged becomes `REJECTED`.
- FR5: Cancel a pending request by id. Set status to `CANCELLED`, then close the pull request.
- FR6: Do not change a request unless it exists and is `PENDING`.
- FR7: Get one request by id, including its status.
- FR8: List requests with id, employee name, dates, reason, status, and pull request number.

## Non-functional requirements

- NFR1: Python 3 REST API. Prefer the standard library plus one small web framework, a local SQLite file, and the GitHub CLI for pull requests.
- NFR2: Runs locally from the project folder with a short README.
- NFR3: Bad input returns a clear error. The API does not crash.
- NFR4: A few tests cover create, list, view, cancel, pull-request approve, pull-request reject, and the rule that a finished request cannot change. Tests do not call GitHub.
- NFR5: Keep the code small and easy to read. No extra layers.

## Phase 1 definition of done

- A caller can create, list, view, and cancel leave requests through the REST API.
- A manager approves by merging the pull request and rejects by closing it without merging.
- Data survives a restart in a local SQLite file.
- A few tests pass for the main flow.
- This requirements file is the source of truth for later SDLC steps.
