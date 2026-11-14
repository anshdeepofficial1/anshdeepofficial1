from __future__ import annotations

import html
import json
from datetime import datetime, timedelta
from pathlib import Path

DATA = Path("data/contributions.json")
HEATMAP = Path("assets/contrib-heatmap.svg")
INFO = Path("assets/info-card.svg")

WIDTH, HEIGHT = 860, 180
CELL, GAP = 11, 4
X0, Y0 = 43, 40
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_heatmap(payload: dict) -> None:
    username = payload.get("username", "anshdeepofficial1")
    raw_days = payload.get("days", [])
    day_map = {item["date"]: item for item in raw_days}

    parsed = [datetime.strptime(item["date"], "%Y-%m-%d").date() for item in raw_days]
    latest = max(parsed) if parsed else datetime.utcnow().date()
    current_week_start = latest - timedelta(days=(latest.weekday() + 1) % 7)
    start = current_week_start - timedelta(weeks=52)

    labels = []
    last_month = None
    for week in range(53):
        d = start + timedelta(weeks=week)
        key = (d.year, d.month)
        if key != last_month:
            labels.append((week, d.strftime("%b")))
            last_month = key

    cells = []
    for week in range(53):
        for row in range(7):
            d = start + timedelta(days=week * 7 + row)
            item = day_map.get(d.isoformat(), {})
            level = max(0, min(4, int(item.get("level", 0))))
            color = item.get("color") or PALETTE[level]
            x = X0 + week * (CELL + GAP)
            y = Y0 + row * (CELL + GAP)
            begin = 0.08 + (week + row) * 0.011
            count = item.get("count")
            title = (
                d.isoformat()
                if count is None
                else f"{int(count)} {'contribution' if int(count) == 1 else 'contributions'} on {d.isoformat()}"
            )
            cells.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{esc(color)}" opacity="0">'
                f'<title>{esc(title)}</title>'
                f'<animate attributeName="opacity" from="0" to="1" dur=".24s" begin="{begin:.3f}s" fill="freeze"/>'
                f'<animate attributeName="y" from="{y-4}" to="{y}" dur=".24s" begin="{begin:.3f}s" fill="freeze"/>'
                f'</rect>'
            )

    month_text = "".join(
        f'<text x="{X0 + week * (CELL + GAP)}" y="31" class="muted" font-size="9">{esc(label)}</text>'
        for week, label in labels
        if X0 + week * (CELL + GAP) < 815
    )

    legend = []
    for i, color in enumerate(PALETTE):
        legend.append(f'<rect x="{712 + i * 15}" y="155" width="10" height="10" rx="2" fill="{color}"/>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
<style>
.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.muted{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:#8b949e}}
</style>
<rect x=".5" y=".5" width="859" height="179" rx="18" fill="#0d1117" stroke="#30363d"/>
<text x="24" y="24" class="mono" font-size="11" font-weight="700" fill="#39d353">LIVE CONTRIBUTIONS</text>
<text x="836" y="24" class="muted" font-size="10" text-anchor="end">{esc(username)} · auto refresh</text>
{month_text}
{''.join(cells)}
<text x="24" y="164" class="muted" font-size="10">365-day activity · refreshed daily</text>
<text x="680" y="164" class="muted" font-size="9">Less</text>
{''.join(legend)}
<text x="792" y="164" class="muted" font-size="9">More</text>
</svg>'''
    HEATMAP.write_text(svg + "\n", encoding="utf-8")


def panel(height: int, title: str, meta: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{height}" viewBox="0 0 860 {height}"><style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}.title{{fill:#39d353;font-size:12px;font-weight:700;letter-spacing:.8px}}.muted{{fill:#8b949e;font-size:11px}}.value{{fill:#f0f6fc;font-size:28px;font-weight:700}}.label{{fill:#c9d1d9;font-size:11px}}.bright{{fill:#f0f6fc;font-size:13px;font-weight:700}}</style><rect x=".5" y=".5" width="859" height="{height-1}" rx="18" fill="#0d1117" stroke="#30363d"/><text x="24" y="27" class="title">{esc(title)}</text><text x="836" y="27" class="muted" text-anchor="end">{esc(meta)}</text><line x1="24" y1="43" x2="836" y2="43" stroke="#21262d"/>{body}</svg>''' + "\n"


def metric_cards(metrics, height=81):
    out = []
    for i, (label, value) in enumerate(metrics):
        x = 24 + i * 206
        shown = f"{value:,}" if isinstance(value, int) else value
        out.append(f'<rect x="{x}" y="58" width="194" height="{height}" rx="11" fill="#161b22" stroke="#30363d"/><text x="{x+13}" y="80" class="muted">{esc(label)}</text><text x="{x+13}" y="{112 if height==72 else 115}" class="value">{esc(shown)}</text>')
    return "".join(out)


def render_info(payload: dict) -> None:
    stats = payload.get("stats", {})
    total = payload.get("raw_total")
    if total is None:
        total = sum(int(d.get("count", 0)) for d in payload.get("days", []))
    body = metric_cards([("CONTRIBUTIONS", int(total)), ("ACTIVE DAYS", int(stats.get("active_days", 0))), ("CURRENT STREAK", f'{stats.get("current_streak", 0)}d'), ("LONGEST STREAK", f'{stats.get("longest_streak", 0)}d')])
    monthly = sorted((stats.get("monthly_totals") or {}).items())[-12:]
    maximum = max(1, *(int(v) for _, v in monthly)) if monthly else 1
    body += '<text x="24" y="166" class="title">MONTHLY CONTRIBUTIONS</text><text x="836" y="166" class="muted" text-anchor="end">12-month activity · current month to date</text><line x1="24" y1="294" x2="836" y2="294" stroke="#30363d"/>'
    for i, (month, value) in enumerate(monthly):
        value = int(value)
        x = 35 + i * 67
        h = max(2, round(92 * value / maximum)) if value else 0
        color = "#39d353" if i == len(monthly)-1 else "#238636"
        label = datetime.strptime(month, "%Y-%m").strftime("%b")
        body += f'<rect x="{x}" y="{294-h}" width="42" height="{h}" rx="4" fill="{color}"/><text x="{x+21}" y="{max(190,287-h)}" class="muted" text-anchor="middle">{value}</text><text x="{x+21}" y="314" class="muted" text-anchor="middle">{label}</text>'
    best = stats.get("best_day") or {}
    body += f'<text x="24" y="347" class="muted">Best day: {esc(best.get("count", 0))} contributions · {esc(best.get("date", "—"))}</text><text x="836" y="347" class="muted" text-anchor="end">Source: GitHub contribution calendar</text>'
    INFO.write_text(panel(365, "CONTRIBUTION INSIGHTS", "daily refresh", body), encoding="utf-8")


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    HEATMAP.parent.mkdir(parents=True, exist_ok=True)
    render_heatmap(payload)
    render_info(payload)
    print(f"wrote {HEATMAP} and {INFO}")


if __name__ == "__main__":
    main()
