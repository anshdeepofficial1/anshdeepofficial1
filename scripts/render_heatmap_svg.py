from __future__ import annotations

import html
import json
from datetime import datetime, timedelta
from pathlib import Path

DATA = Path("data/contributions.json")
OUT = Path("assets/contrib-heatmap.svg")
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

WIDTH, HEIGHT = 860, 180
CELL, GAP = 11, 4
X0, Y0 = 43, 40


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    username = payload.get("username", "anshdeepofficial1")
    raw_days = payload.get("days", [])
    day_map = {item["date"]: item for item in raw_days}

    parsed = [datetime.strptime(item["date"], "%Y-%m-%d").date() for item in raw_days]
    latest = max(parsed) if parsed else datetime.utcnow().date()
    current_week_start = latest - timedelta(days=(latest.weekday() + 1) % 7)
    start = current_week_start - timedelta(weeks=52)

    month_labels = []
    last_month = None
    for week in range(53):
        d = start + timedelta(weeks=week)
        key = (d.year, d.month)
        if key != last_month:
            month_labels.append((week, d.strftime("%b")))
            last_month = key

    cells = []
    for week in range(53):
        for row in range(7):
            d = start + timedelta(days=week * 7 + row)
            item = day_map.get(d.isoformat(), {})
            level = max(0, min(4, int(item.get("level", 0))))
            color = PALETTE[level]
            x = X0 + week * (CELL + GAP)
            y = Y0 + row * (CELL + GAP)
            begin = 0.10 + (week + row) * 0.012
            title_count = item.get("count")
            if title_count is None:
                title = d.isoformat()
            else:
                suffix = "contribution" if int(title_count) == 1 else "contributions"
                title = f"{title_count} {suffix} on {d.isoformat()}"
            cells.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}" opacity="0">'
                f'<title>{esc(title)}</title>'
                f'<animate attributeName="opacity" from="0" to="1" dur=".28s" begin="{begin:.3f}s" fill="freeze"/>'
                f'<animate attributeName="y" from="{y-5}" to="{y}" dur=".28s" begin="{begin:.3f}s" fill="freeze"/>'
                f'</rect>'
            )

    labels = "".join(
        f'<text x="{X0 + week * (CELL + GAP)}" y="31" class="muted" font-size="9">{esc(label)}</text>'
        for week, label in month_labels
        if X0 + week * (CELL + GAP) < 815
    )

    stats = payload.get("stats", {})
    total = stats.get("total")
    if total is None:
        left_footer = f'{stats.get("active_days", 0)} active days in the last year'
    else:
        left_footer = f'{int(total):,} contributions in the last year'
    right_footer = f'current {stats.get("current_streak", 0)}d · longest {stats.get("longest_streak", 0)}d'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <style>
    .mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
    .muted{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:#8b949e}}
  </style>
  <rect x=".5" y=".5" width="859" height="179" rx="16" fill="#0d1117" stroke="#30363d"/>
  <text x="24" y="24" class="mono" font-size="11" font-weight="700" fill="#39d353">LIVE CONTRIBUTIONS</text>
  <text x="836" y="24" class="muted" font-size="10" text-anchor="end">{esc(username)}</text>
  {labels}
  {''.join(cells)}
  <text x="24" y="164" class="muted" font-size="10">{esc(left_footer)}</text>
  <text x="836" y="164" class="muted" font-size="10" text-anchor="end">{esc(right_footer)}</text>
</svg>'''
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
