import json
import shutil
import subprocess
import tempfile
from pathlib import Path


REPO = "Narsimha91/automated-documentation-sync-v6"


class GitHubError(Exception):
    pass


def pull_request_body(request_id, employee_name, start_date, end_date, reason):
    return (
        "## Description\n\n"
        f"Employee: {employee_name}\n"
        f"Start date: {start_date}\n"
        f"End date: {end_date}\n"
        f"Reason: {reason}\n\n"
        "Merging this pull request approves the leave request. "
        "Closing it without merging rejects the leave request.\n\n"
        "## Changelog\n\n"
        f"- Leave request {request_id} submitted for {employee_name} "
        f"({start_date} to {end_date}).\n\n"
        "## Review checklist\n\n"
        "- [ ] The name, dates, and reason look right\n"
        "- [ ] The start date is not after the end date\n"
        "- [ ] Merge to approve, or close without merging to reject\n"
    )


class GitHubPullRequests:
    def __init__(self, repo_dir=None):
        self.repo_dir = Path(repo_dir or Path(__file__).resolve().parent)

    def open(self, request_id, employee_name, start_date, end_date, reason):
        branch = f"leave/{request_id}"
        worktree = Path(tempfile.mkdtemp(prefix=f"leave-{request_id}-"))
        worktree.rmdir()
        added = False
        try:
            self._run(["git", "fetch", "origin", "main"])
            self._run(
                ["git", "worktree", "add", "-b", branch, str(worktree), "origin/main"]
            )
            added = True
            note_dir = worktree / "leave-requests"
            note_dir.mkdir()
            (note_dir / f"{request_id}.md").write_text(
                "Employee: {name}\nStart date: {start}\nEnd date: {end}\nReason: {reason}\n".format(
                    name=employee_name,
                    start=start_date,
                    end=end_date,
                    reason=reason,
                ),
                encoding="utf-8",
            )
            self._run(["git", "add", f"leave-requests/{request_id}.md"], cwd=worktree)
            self._run(
                ["git", "commit", "-m", f"Add leave request {request_id}"],
                cwd=worktree,
            )
            self._run(["git", "push", "-u", "origin", branch], cwd=worktree)
            url = self._run(
                [
                    "gh",
                    "pr",
                    "create",
                    "--repo",
                    REPO,
                    "--base",
                    "main",
                    "--head",
                    branch,
                    "--title",
                    f"Leave request {request_id}: {employee_name}",
                    "--body",
                    pull_request_body(
                        request_id, employee_name, start_date, end_date, reason
                    ),
                ]
            )
            try:
                return int(url.rstrip("/").split("/")[-1])
            except ValueError as exc:
                raise GitHubError("Could not read the new pull request number.") from exc
        finally:
            if added:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree)],
                    cwd=self.repo_dir,
                    capture_output=True,
                    text=True,
                )
            if worktree.exists():
                shutil.rmtree(worktree, ignore_errors=True)

    def read(self, pr_number):
        raw = self._run(
            [
                "gh",
                "pr",
                "view",
                str(pr_number),
                "--repo",
                REPO,
                "--json",
                "state,mergedAt",
            ]
        )
        try:
            payload = json.loads(raw)
            state = payload["state"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise GitHubError("Could not read the pull request.") from exc
        if state == "MERGED" or payload.get("mergedAt"):
            return "merged"
        if state == "CLOSED":
            return "closed"
        return "open"

    def close(self, pr_number):
        self._run(
            ["gh", "pr", "close", str(pr_number), "--repo", REPO]
        )

    def delete_branch(self, request_id):
        branch = f"leave/{request_id}"
        remote = subprocess.run(
            ["git", "push", "origin", "--delete", branch],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
        )
        local = subprocess.run(
            ["git", "branch", "-D", branch],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
        )
        if remote.returncode != 0 and not _missing_branch(remote.stderr):
            raise GitHubError(remote.stderr.strip() or "Could not delete the remote branch.")
        if local.returncode != 0 and not _missing_branch(local.stderr):
            raise GitHubError(local.stderr.strip() or "Could not delete the local branch.")

    def _run(self, args, cwd=None):
        result = subprocess.run(
            args,
            cwd=cwd or self.repo_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            message = (result.stderr or result.stdout).strip()
            raise GitHubError(message or "GitHub command failed.")
        return result.stdout.strip()


def _missing_branch(message):
    text = (message or "").lower()
    return "remote ref does not exist" in text or "not found" in text
