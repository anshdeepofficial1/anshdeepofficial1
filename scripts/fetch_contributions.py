from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.getenv("GITHUB_USERNAME", "anshdeepofficial1").strip()
OUT = Path("data/contributions.json")
URL = f"https://github.com/users/{USERNAME}/contributions"


def _parse_count(text: str | None) -> int | None:
    if not text:
        return None
    m = re.search(r"([\d,]+)\s+contribution", text, flags=re.I)
    return int(m.group(1).replace(",", "")) if m else None


def fetch() -> list[dict]:
    response = requests.get(
        URL,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; profile-readme-bot/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    tooltip_text: dict[str, str] = {}
    for tip in soup.find_all(["tool-tip", "span"]):
        target = tip.get("for")
        if target:
            tooltip_text[target] = tip.get_text(" ", strip=True)

    days: list[dict] = []
    seen: set[str] = set()
    for node in soup.select("[data-date][data-level]"):
        day = node.get("data-date")
        if not day or day in seen:
            continue
        seen.add(day)

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
            count = _parse_count(tooltip_text.get(node.get("id")))
        if count is None:
            child_tip = node.find("tool-tip")
            count = _parse_count(child_tip.get_text(" ", strip=True) if child_tip else None)

        days.append({"date": day, "count": count, "level": level})

    if not days:
        raise RuntimeError("Could not find GitHub contribution day cells in public HTML")
    return sorted(days, key=lambda item: item["date"])


def build_stats(days: list[dict]) -> dict:
    active_dates = {
        datetime.strptime(item["date"], "%Y-%m-%d").date()
        for item in days
        if (item.get("count") or 0) > 0 or item.get("level", 0) > 0
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

    known_counts = [item for item in days if item.get("count") is not None]
    total = sum(int(item["count"]) for item in known_counts)
    best = max(known_counts, key=lambda item: int(item["count"]), default=None)

    monthly = defaultdict(int)
    for item in known_counts:
        monthly[item["date"][:7]] += int(item["count"])

    return {
        "total": total if known_counts else None,
        "current_streak": current,
        "longest_streak": longest,
        "active_days": len(active_dates),
        "best_day": best,
        "monthly_totals": dict(sorted(monthly.items())),
    }


def main() -> None:
    days = fetch()
    payload = {
        "username": USERNAME,
        "source": URL,
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "days": days,
        "stats": build_stats(days),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT} with {len(days)} days")


if __name__ == "__main__":
    main()
