# Leave Request Management

A small local API for submitting a leave request. A manager approves it by merging the GitHub pull request, and rejects it by closing that pull request without merging.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`gh` must be installed and logged in (`gh auth login`) before a real create. The API stores requests in `leave.db` in this folder.

## Run

```powershell
python app.py
```

The API listens on http://127.0.0.1:5000.

- `POST /leave-requests` with `employee_name`, `start_date`, `end_date`, and `reason`
- `GET /leave-requests`
- `GET /leave-requests/{id}`
- `POST /leave-requests/{id}/cancel`

There is no approve route and no reject route.

## Tests

```powershell
pytest
```

Tests use a temporary database and a fake pull-request client. They do not call GitHub.
