"""Create or update the ArcGuard pull-request comment.

The workflow token is read from the environment. This file never stores a
token, and callers pass it only through GitHub Actions.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _request(method: str, url: str, bearer: str, payload: dict | None = None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("Authorization", "Bearer " + bearer)
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    request.add_header("User-Agent", "arcguard-action")
    if body is not None:
        request.add_header("Content-Type", "application/json")
    return request


def upsert_comment(
    *,
    repository: str,
    pr_number: str,
    markdown: str,
    bearer: str,
    api_url: str = "https://api.github.com",
    opener=urllib.request.urlopen,
) -> str:
    """Create the summary comment or replace the one with the same marker.

    Returns ``created`` or ``updated``.
    """

    marker = ""
    for line in markdown.splitlines():
        if line.startswith("<!-- arcguard-summary "):
            marker = line
            break
    if not marker:
        raise ValueError("summary marker is missing from the markdown")

    base = api_url.rstrip("/") + f"/repos/{repository}/issues"
    list_url = f"{base}/{pr_number}/comments?per_page=100"
    with opener(_request("GET", list_url, bearer), timeout=30) as response:
        existing = json.loads(response.read().decode("utf-8"))
    match_id = None
    if isinstance(existing, list):
        for item in existing:
            body = str(item.get("body", ""))
            if marker in body:
                match_id = item.get("id")
                break
    text = markdown if len(markdown) <= 60000 else markdown[:60000] + "\n\n… truncated.\n"
    if match_id is None:
        create_url = f"{base}/{pr_number}/comments"
        with opener(
            _request("POST", create_url, bearer, {"body": text}),
            timeout=30,
        ) as response:
            response.read()
        return "created"
    update_url = f"{base}/comments/{match_id}"
    with opener(
        _request("PATCH", update_url, bearer, {"body": text}),
        timeout=30,
    ) as response:
        response.read()
    return "updated"


def main() -> int:
    """Post ``ARCGUARD_MARKDOWN`` when the workflow token and PR number exist."""

    markdown_path = os.environ.get("ARCGUARD_MARKDOWN", "")
    pr_number = os.environ.get("INPUT_PR_NUMBER", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    bearer = os.environ.get("ARCGUARD_API_TOKEN", "")
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    if not markdown_path or not Path(markdown_path).is_file():
        print("arcguard: markdown summary is missing", file=sys.stderr)
        return 1
    if not pr_number or not repository or not bearer:
        print("arcguard: pull request comment needs repo, number, and token", file=sys.stderr)
        return 1
    markdown = Path(markdown_path).read_text(encoding="utf-8")
    try:
        result = upsert_comment(
            repository=repository,
            pr_number=pr_number,
            markdown=markdown,
            bearer=bearer,
            api_url=api_url,
        )
    except (urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
        print(f"arcguard: comment was not posted ({exc.__class__.__name__})", file=sys.stderr)
        return 1
    print(f"arcguard: comment {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
