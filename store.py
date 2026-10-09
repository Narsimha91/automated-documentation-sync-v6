import sqlite3


def connect(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY,
            employee_name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL,
            pr_number INTEGER
        )
        """
    )
    connection.commit()


def insert_request(connection, employee_name, start_date, end_date, reason):
    cursor = connection.execute(
        """
        INSERT INTO leave_requests
            (employee_name, start_date, end_date, reason, status)
        VALUES (?, ?, ?, ?, 'PENDING')
        """,
        (employee_name, start_date, end_date, reason),
    )
    connection.commit()
    return cursor.lastrowid


def get_request(connection, request_id):
    row = connection.execute(
        "SELECT * FROM leave_requests WHERE id = ?",
        (request_id,),
    ).fetchone()
    if row is None:
        return None
    return dict(row)


def list_requests(connection):
    rows = connection.execute(
        "SELECT * FROM leave_requests ORDER BY id"
    ).fetchall()
    return [dict(row) for row in rows]


def set_pr_number(connection, request_id, pr_number):
    connection.execute(
        "UPDATE leave_requests SET pr_number = ? WHERE id = ?",
        (pr_number, request_id),
    )
    connection.commit()


def set_status(connection, request_id, status):
    connection.execute(
        "UPDATE leave_requests SET status = ? WHERE id = ?",
        (status, request_id),
    )
    connection.commit()


def delete_request(connection, request_id):
    connection.execute(
        "DELETE FROM leave_requests WHERE id = ?",
        (request_id,),
    )
    connection.commit()
