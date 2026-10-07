from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.getenv("GITHUB_USERNAME", "anshdeepofficial1").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()\nCONTRIBUTION_TOTAL_OFFSET = int(os.getenv("CONTRIBUTION_TOTAL_OFFSET", "0") or 0)
OUT = Path("data/contributions.json")
PUBLIC_URL = f"https://github.com/users/{USERNAME}/contributions"
GRAPHQL_URL = "https://api.github.com/graphql"


def _stats(days: list[dict], forced_total: int | None = None) -> dict:
    active_dates = {
        datetime.strptime(item["date"], "%Y-%m-%d").date()
        for item in days
        if int(item.get("count") or 0) > 0 or int(item.get("level") or 0) > 0
    }

    today = date.today()
    cursor = today
    if cursor not in active_dates and cursor - timedelta(days=1) in active_dates:
        cursor -= timedelta(days=1)

    current = 0
    while cursor in active_dates:
        current += 1
        cursor -= timedelta(days=1)

    longest = 0
    run = 0
    previous = None
    for d in sorted(active_dates):
        if previous and d == previous + timedelta(days=1):
            run += 1
        else:
            run = 1
        longest = max(longest, run)
        previous = d

    known = [item for item in days if item.get("count") is not None]
    total = forced_total if forced_total is not None else sum(int(item.get("count") or 0) for item in known)
    best = max(known, key=lambda item: int(item.get("count") or 0), default=None)

    monthly = defaultdict(int)
    for item in known:
        monthly[item["date"][:7]] += int(item.get("count") or 0)

    return {
        "total": int(total) if total is not None else None,
        "current_streak": current,
        "longest_streak": longest,
        "active_days": len(active_dates),
        "best_day": best,
        "monthly_totals": dict(sorted(monthly.items())),
    }


def fetch_graphql() -> dict | None:
    if not GITHUB_TOKEN:
        return None

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            colors
            weeks {
              firstDay
              contributionDays {
                contributionCount
                color
                date
                weekday
              }
            }
          }
        }
      }
    }
    """

    response = requests.post(
        GRAPHQL_URL,
        timeout=30,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "anshdeep-profile-readme/2.0",
        },
        json={"query": query, "variables": {"login": USERNAME}},
    )
    response.raise_for_status()
    body = response.json()
    if body.get("errors"):
        raise RuntimeError(f"GitHub GraphQL returned errors: {body['errors']}")

    calendar = body["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    colors = [str(c).lower() for c in calendar.get("colors", [])]\n    dark_palette = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    days = []
    for week in calendar.get("weeks", []):
        for day in week.get("contributionDays", []):
            color = str(day.get("color") or "#161b22")
            try:
                level = colors.index(color.lower()) + 1 if color.lower() in colors else (1 if int(day["contributionCount"]) > 0 else 0)
            except ValueError:
                level = 1 if int(day["contributionCount"]) > 0 else 0
            level = max(0, min(4, level))
            days.append({
                "date": day["date"],
                "count": int(day["contributionCount"]),
                "color": color,
                "level": level,
                "weekday": int(day.get("weekday", 0)),
            })

    return {
        "username": USERNAME,
        "source": "github-graphql",
        "public_url": PUBLIC_URL,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "days": sorted(days, key=lambda x: x["date"]),
        "stats": _stats(days, forced_total=int(calendar["totalContributions"]) + CONTRIBUTION_TOTAL_OFFSET),\n        "total_offset": CONTRIBUTION_TOTAL_OFFSET,
    }


def _parse_count(text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(r"([\d,]+)\s+contribution", text, flags=re.I)
    return int(match.group(1).replace(",", "")) if match else None


def fetch_html() -> dict:
    response = requests.get(
        PUBLIC_URL,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; anshdeep-profile-readme/2.0)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text(" ", strip=True)
    total_match = re.search(r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", page_text, flags=re.I)
    page_total = int(total_match.group(1).replace(",", "")) if total_match else None

    tooltips: dict[str, str] = {}
    for tip in soup.find_all(["tool-tip", "span"]):
        target = tip.get("for")
        if target:
            tooltips[target] = tip.get_text(" ", strip=True)

    days = []
    seen = set()
    palette = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    for node in soup.select("[data-date][data-level]"):
        day_date = node.get("data-date")
        if not day_date or day_date in seen:
            continue
        seen.add(day_date)
        try:
            level = max(0, min(4, int(node.get("data-level", "0"))))
        except ValueError:
            level = 0

        count = None
        for attr in ("data-count", "data-contribution-count"):
            raw = node.get(attr)
            if raw is not None and str(raw).isdigit():
                count = int(raw)
                break
        if count is None:
            count = _parse_count(node.get("aria-label"))
        if count is None and node.get("id"):
            count = _parse_count(tooltips.get(node.get("id")))
        if count is None:
            child = node.find("tool-tip")
            count = _parse_count(child.get_text(" ", strip=True) if child else None)

        days.append({
            "date": day_date,
            "count": count,
            "level": level,
            "color": palette[level],
        })

    if not days:
        raise RuntimeError("Could not parse GitHub contribution calendar")

    return {
        "username": USERNAME,
        "source": "github-public-html",
        "public_url": PUBLIC_URL,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "days": sorted(days, key=lambda x: x["date"]),
        "stats": _stats(days, forced_total=page_total),
    }


def main() -> None:
    try:
        payload = fetch_graphql()
    except Exception as exc:
        print(f"GraphQL fetch failed; falling back to public HTML: {exc}")
        payload = None

    if payload is None:
        payload = fetch_html()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT} via {payload['source']} with total={payload['stats'].get('total')}")


if __name__ == "__main__":
    main()
