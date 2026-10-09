from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request

import store
from github_pr import GitHubError, GitHubPullRequests


class ApiError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status


def create_app(db_path=None, pr_client=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = str(
        db_path or Path(__file__).resolve().parent / "leave.db"
    )
    app.config["PR_CLIENT"] = pr_client or GitHubPullRequests()

    def connection():
        db = store.connect(app.config["DB_PATH"])
        store.init_db(db)
        return db

    def refresh(db, row):
        if row["status"] != "PENDING":
            return row
        if row["pr_number"] is None:
            raise ApiError(
                f"Leave request {row['id']} is pending and has no pull request.",
                409,
            )
        try:
            state = app.config["PR_CLIENT"].read(row["pr_number"])
        except GitHubError as exc:
            raise ApiError(str(exc), 502) from exc
        if state == "merged":
            store.set_status(db, row["id"], "APPROVED")
            row["status"] = "APPROVED"
        elif state == "closed":
            store.set_status(db, row["id"], "REJECTED")
            row["status"] = "REJECTED"
        return row

    @app.post("/leave-requests")
    def create_leave_request():
        body = request.get_json(silent=True)
        error = _validate(body)
        if error:
            return jsonify(error=error), 400
        employee_name = body["employee_name"].strip()
        start_date = body["start_date"].strip()
        end_date = body["end_date"].strip()
        reason = body["reason"].strip()
        db = connection()
        try:
            request_id = store.insert_request(
                db, employee_name, start_date, end_date, reason
            )
            try:
                pr_number = app.config["PR_CLIENT"].open(
                    request_id, employee_name, start_date, end_date, reason
                )
            except GitHubError as exc:
                store.delete_request(db, request_id)
                cleanup = _delete_branch(app, request_id)
                message = str(exc)
                if cleanup:
                    message = f"{message} {cleanup}"
                return jsonify(error=message), 502
            store.set_pr_number(db, request_id, pr_number)
            return jsonify(store.get_request(db, request_id)), 201
        finally:
            db.close()

    @app.get("/leave-requests")
    def list_leave_requests():
        db = connection()
        try:
            rows = []
            for row in store.list_requests(db):
                rows.append(refresh(db, row))
            return jsonify(rows)
        except ApiError as exc:
            return jsonify(error=exc.message), exc.status
        finally:
            db.close()

    @app.get("/leave-requests/<int:request_id>")
    def view_leave_request(request_id):
        db = connection()
        try:
            row = store.get_request(db, request_id)
            if row is None:
                return jsonify(error="Leave request not found."), 404
            return jsonify(refresh(db, row))
        except ApiError as exc:
            return jsonify(error=exc.message), exc.status
        finally:
            db.close()

    @app.post("/leave-requests/<int:request_id>/cancel")
    def cancel_leave_request(request_id):
        db = connection()
        try:
            row = store.get_request(db, request_id)
            if row is None:
                return jsonify(error="Leave request not found."), 404
            if row["status"] != "PENDING":
                return jsonify(error="Leave request can no longer be changed."), 409
            if row["pr_number"] is None:
                return jsonify(
                    error=f"Leave request {request_id} is pending and has no pull request."
                ), 409
            # Save CANCELLED before closing so a later read does not store this close as REJECTED.
            store.set_status(db, request_id, "CANCELLED")
            try:
                app.config["PR_CLIENT"].close(row["pr_number"])
            except GitHubError as exc:
                return jsonify(error=str(exc)), 502
            return jsonify(store.get_request(db, request_id))
        finally:
            db.close()

    return app


def _validate(body):
    if not isinstance(body, dict):
        return "Request body must be a JSON object."
    for field in ("employee_name", "start_date", "end_date", "reason"):
        value = body.get(field)
        if not isinstance(value, str) or not value.strip():
            return f"{field} is required."
    for field in ("start_date", "end_date"):
        try:
            datetime.strptime(body[field].strip(), "%Y-%m-%d")
        except ValueError:
            return f"{field} must be YYYY-MM-DD."
    if body["start_date"].strip() > body["end_date"].strip():
        return "start_date must not be after end_date."
    return None


def _delete_branch(app, request_id):
    try:
        app.config["PR_CLIENT"].delete_branch(request_id)
    except GitHubError as exc:
        return str(exc)
    return None


app = create_app()


if __name__ == "__main__":
    app.run(port=5000)
