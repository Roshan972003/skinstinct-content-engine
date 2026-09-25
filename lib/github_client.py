"""
Minimal GitHub Contents API client — commits one markdown file per approved
draft to a private archive repo. This is the ONLY permanent record this app
keeps of a finished piece; everything else (scores, drafts still pending a
decision) lives only in Supabase's `pending_items` table until resolved.
"""
from __future__ import annotations

import base64
import os

import requests

TIMEOUT_SECONDS = 15
API_BASE = "https://api.github.com"


class GitHubError(RuntimeError):
    pass


def _headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise GitHubError("GITHUB_TOKEN not configured")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }


def _owner_repo() -> tuple[str, str]:
    owner = os.environ.get("GITHUB_OWNER", "")
    repo = os.environ.get("GITHUB_ARCHIVE_REPO", "")
    if not owner or not repo:
        raise GitHubError("GITHUB_OWNER / GITHUB_ARCHIVE_REPO not configured")
    return owner, repo


def ensure_repo_exists() -> None:
    """Create the archive repo (private) if it doesn't already exist."""
    owner, repo = _owner_repo()
    resp = requests.get(f"{API_BASE}/repos/{owner}/{repo}", headers=_headers(), timeout=TIMEOUT_SECONDS)
    if resp.status_code == 200:
        return
    if resp.status_code != 404:
        raise GitHubError(f"repo lookup failed: {resp.status_code} {resp.text}")

    create_resp = requests.post(
        f"{API_BASE}/user/repos",
        headers=_headers(),
        json={"name": repo, "private": True, "description": "Approved Skinstinct content archive", "auto_init": True},
        timeout=TIMEOUT_SECONDS,
    )
    if not create_resp.ok:
        raise GitHubError(f"repo create failed: {create_resp.status_code} {create_resp.text}")


def commit_markdown_file(path: str, content: str, message: str) -> str:
    """Creates (or overwrites) a file in the archive repo. Returns the file's URL."""
    owner, repo = _owner_repo()
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")

    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    existing = requests.get(url, headers=_headers(), timeout=TIMEOUT_SECONDS)
    body = {"message": message, "content": encoded}
    if existing.status_code == 200:
        body["sha"] = existing.json()["sha"]

    resp = requests.put(url, headers=_headers(), json=body, timeout=TIMEOUT_SECONDS)
    if not resp.ok:
        raise GitHubError(f"commit file failed: {resp.status_code} {resp.text}")
    return resp.json()["content"]["html_url"]
