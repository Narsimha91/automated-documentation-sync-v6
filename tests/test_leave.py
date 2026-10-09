import pytest

import store
from app import create_app
from github_pr import GitHubError, pull_request_body


class FakePullRequests:
    def __init__(self):
        self.opened = []
        self.closed = []
        self.deleted = []
        self.states = {}
        self.next_pr = 1
        self.fail_open = False
        self.fail_read = False
        self.fail_close = False

    def open(self, request_id, employee_name, start_date, end_date, reason):
        if self.fail_open:
            raise GitHubError("Could not open the pull request.")
        pr_number = self.next_pr
        self.next_pr += 1
        self.states[pr_number] = "open"
        self.opened.append(
            {
                "request_id": request_id,
                "pr_number": pr_number,
                "body": pull_request_body(
                    request_id, employee_name, start_date, end_date, reason
                ),
            }
        )
        return pr_number

    def read(self, pr_number):
        if self.fail_read:
            raise GitHubError("Could not read the pull request.")
        return self.states[pr_number]

    def close(self, pr_number):
        if self.fail_close:
            raise GitHubError("Could not close the pull request.")
        self.closed.append(pr_number)
        self.states[pr_number] = "closed"

    def delete_branch(self, request_id):
        self.deleted.append(request_id)


@pytest.fixture
def api(tmp_path):
    fake = FakePullRequests()
    db_path = tmp_path / "leave.db"
    flask_app = create_app(db_path=db_path, pr_client=fake)
    flask_app.config["TESTING"] = True
    return flask_app.test_client(), fake, db_path


def _create(client, **overrides):
    body = {
        "employee_name": "Ada Lovelace",
        "start_date": "2026-10-12",
        "end_date": "2026-10-14",
        "reason": "Conference",
    }
    body.update(overrides)
    return client.post("/leave-requests", json=body)


def test_create_list_and_view(api):
    client, fake, _db = api
    created = _create(client)
    assert created.status_code == 201
    row = created.get_json()
    assert row["status"] == "PENDING"
    assert row["pr_number"] == 1
    body = fake.opened[0]["body"]
    assert "Description" in body
    assert "Changelog" in body
    assert "Leave request 1 submitted for Ada Lovelace (2026-10-12 to 2026-10-14)." in body
    assert "Review checklist" in body

    listed = client.get("/leave-requests")
    assert listed.status_code == 200
    assert listed.get_json()[0]["id"] == row["id"]

    viewed = client.get(f"/leave-requests/{row['id']}")
    assert viewed.status_code == 200
    assert viewed.get_json()["employee_name"] == "Ada Lovelace"
    assert viewed.get_json()["status"] == "PENDING"


def test_cancel_pending_request(api):
    client, fake, _db = api
    row = _create(client).get_json()
    cancelled = client.post(f"/leave-requests/{row['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.get_json()["status"] == "CANCELLED"
    assert fake.closed == [row["pr_number"]]

    fake.states[row["pr_number"]] = "merged"
    viewed = client.get(f"/leave-requests/{row['id']}")
    assert viewed.get_json()["status"] == "CANCELLED"


def test_merged_pull_request_approves_and_stays_approved(api):
    client, fake, _db = api
    row = _create(client).get_json()
    fake.states[row["pr_number"]] = "merged"

    viewed = client.get(f"/leave-requests/{row['id']}")
    assert viewed.get_json()["status"] == "APPROVED"

    fake.states[row["pr_number"]] = "closed"
    again = client.get(f"/leave-requests/{row['id']}")
    assert again.get_json()["status"] == "APPROVED"

    cancelled = client.post(f"/leave-requests/{row['id']}/cancel")
    assert cancelled.status_code == 409
    assert fake.closed == []


def test_closed_pull_request_rejects(api):
    client, fake, _db = api
    row = _create(client).get_json()
    fake.states[row["pr_number"]] = "closed"
    listed = client.get("/leave-requests")
    assert listed.get_json()[0]["status"] == "REJECTED"


def test_bad_input(api):
    client, _fake, _db = api
    missing = _create(client, reason="  ")
    assert missing.status_code == 400
    bad_date = _create(client, start_date="12-10-2026")
    assert bad_date.status_code == 400
    order = _create(client, start_date="2026-10-20", end_date="2026-10-14")
    assert order.status_code == 400
    assert client.get("/leave-requests").get_json() == []


def test_unknown_id(api):
    client, fake, _db = api
    assert client.get("/leave-requests/9").status_code == 404
    cancelled = client.post("/leave-requests/9/cancel")
    assert cancelled.status_code == 404
    assert fake.closed == []


def test_failed_create_removes_the_row_and_branch(api):
    client, fake, _db = api
    fake.fail_open = True
    created = _create(client)
    assert created.status_code == 502
    assert fake.deleted == [1]
    assert client.get("/leave-requests").get_json() == []


def test_failed_read_leaves_the_row_pending(api):
    client, fake, _db = api
    row = _create(client).get_json()
    fake.fail_read = True
    viewed = client.get(f"/leave-requests/{row['id']}")
    assert viewed.status_code == 502
    fake.fail_read = False
    assert client.get(f"/leave-requests/{row['id']}").get_json()["status"] == "PENDING"


def test_cancel_close_failure_stays_cancelled(api):
    client, fake, _db = api
    row = _create(client).get_json()
    fake.fail_close = True
    cancelled = client.post(f"/leave-requests/{row['id']}/cancel")
    assert cancelled.status_code == 502
    fake.fail_close = False
    fake.fail_read = True
    viewed = client.get(f"/leave-requests/{row['id']}")
    assert viewed.status_code == 200
    assert viewed.get_json()["status"] == "CANCELLED"


def test_pending_without_pull_request_is_an_error(api):
    client, fake, db_path = api
    connection = store.connect(db_path)
    store.init_db(connection)
    request_id = store.insert_request(
        connection, "Grace Hopper", "2026-11-01", "2026-11-02", "Travel"
    )
    connection.close()

    viewed = client.get(f"/leave-requests/{request_id}")
    assert viewed.status_code == 409
    cancelled = client.post(f"/leave-requests/{request_id}/cancel")
    assert cancelled.status_code == 409
    assert fake.closed == []
    connection = store.connect(db_path)
    assert store.get_request(connection, request_id)["status"] == "PENDING"
    connection.close()
