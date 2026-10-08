from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

USERNAME = os.getenv("GITHUB_USERNAME", "anshdeepofficial1").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
OUT = Path("data/projects.json")

PROJECTS = [
    {"repo": "AniDash", "label": "AniDash"},
    {"repo": "VYBE", "label": "VYBE"},
    {"repo": "Copy-Cloud", "label": "Copy Cloud"},
]


def headers() -> dict[str, str]:
    value = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "anshdeep-profile-readme/4.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        value["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return value


def get_json(url: str):
    response = requests.get(url, headers=headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def one_project(item: dict) -> dict:
    repo = item["repo"]
    base = f"https://api.github.com/repos/{USERNAME}/{repo}"
    meta = get_json(base)
    commits = get_json(f"{base}/commits?per_page=4")
    releases = get_json(f"{base}/releases?per_page=1")

    release = None
    if releases:
        latest = releases[0]
        release = {
            "tag": latest.get("tag_name") or "—",
            "name": latest.get("name") or latest.get("tag_name") or "Release",
            "published_at": latest.get("published_at"),
            "downloads": sum(int(asset.get("download_count") or 0) for asset in latest.get("assets", [])),
            "url": latest.get("html_url"),
        }

    compact_commits = []
    for commit in commits:
        inner = commit.get("commit", {})
        author = inner.get("author") or {}
        committer = inner.get("committer") or {}
        message = (inner.get("message") or "").splitlines()[0].strip()
        compact_commits.append(
            {
                "sha": (commit.get("sha") or "")[:7],
                "message": message,
                "date": author.get("date") or committer.get("date"),
                "url": commit.get("html_url"),
            }
        )

    return {
        "repo": repo,
        "label": item["label"],
        "url": meta.get("html_url"),
        "homepage": meta.get("homepage"),
        "description": meta.get("description"),
        "language": meta.get("language") or "—",
        "stars": int(meta.get("stargazers_count") or 0),
        "forks": int(meta.get("forks_count") or 0),
        "issues": int(meta.get("open_issues_count") or 0),
        "pushed_at": meta.get("pushed_at"),
        "release": release,
        "commits": compact_commits,
    }


def build_recent(projects: list[dict], limit: int = 6) -> list[dict]:
    selected = []

    for project in projects:
        for commit in (project.get("commits") or [])[:2]:
            item = dict(commit)
            item["project"] = project["label"]
            item["repo"] = project["repo"]
            selected.append(item)

    selected.sort(key=lambda x: x.get("date") or "", reverse=True)
    return selected[:limit]

def main() -> None:
    projects = [one_project(item) for item in PROJECTS]
    active = max(projects, key=lambda p: p.get("pushed_at") or "")["repo"]

    payload = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "active_project": active,
        "projects": projects,
        "recent_activity": build_recent(projects),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT}; active={active}")


if __name__ == "__main__":
    main()
