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


def render_info(payload: dict) -> None:
    stats = payload.get("stats", {})
    total = int(stats.get("total") or 0)
    active = int(stats.get("active_days") or 0)
    current = int(stats.get("current_streak") or 0)
    longest = int(stats.get("longest_streak") or 0)
    best = stats.get("best_day") or {}
    best_count = int(best.get("count") or 0)
    best_date = best.get("date") or "—"

    monthly = list((stats.get("monthly_totals") or {}).items())[-6:]
    max_value = max([v for _, v in monthly], default=1)
    bars = []
    for i, (month, value) in enumerate(monthly):
        x = 274 + i * 31
        h = max(4, int(72 * value / max_value))
        y = 346 - h
        begin = 1.15 + i * 0.08
        bars.append(
            f'<rect x="{x}" y="{y}" width="17" height="{h}" rx="4" fill="#238636" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" dur=".35s" begin="{begin:.2f}s" fill="freeze"/>'
            f'<animate attributeName="height" from="0" to="{h}" dur=".45s" begin="{begin:.2f}s" fill="freeze"/>'
            f'<animate attributeName="y" from="346" to="{y}" dur=".45s" begin="{begin:.2f}s" fill="freeze"/>'
            f'</rect><text x="{x+8.5}" y="364" text-anchor="middle" class="muted" font-size="7">{esc(month[5:])}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="490" height="390" viewBox="0 0 490 390">
<style>
.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.key{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:9px;font-weight:700;fill:#39d353;letter-spacing:1px}}
.val{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:11px;fill:#c9d1d9}}
.big{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:21px;font-weight:800;fill:#f0f6fc}}
.muted{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:#8b949e}}
</style>
<rect x=".5" y=".5" width="489" height="389" rx="18" fill="#0d1117" stroke="#30363d"/>
<circle cx="18" cy="18" r="4" fill="#ff5f56"/><circle cx="32" cy="18" r="4" fill="#ffbd2e"/><circle cx="46" cy="18" r="4" fill="#27c93f"/>
<text x="64" y="22" class="muted" font-size="10">anshdeep@github ~ $ neofetch --stats</text>
<line x1="20" y1="42" x2="470" y2="42" stroke="#21262d"/>

<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".35s" begin=".2s" fill="freeze"/>
<text x="26" y="68" class="key">ANSHDEEP SINGH</text>
<text x="26" y="88" class="val">Developer · Data Science · Android · Web · AI</text>
</g>

<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".35s" begin=".4s" fill="freeze"/>
<rect x="24" y="105" width="102" height="78" rx="11" fill="#161b22" stroke="#30363d"/>
<text x="36" y="126" class="key">CONTRIB</text><text x="36" y="157" class="big">{total:,}</text>
<rect x="134" y="105" width="102" height="78" rx="11" fill="#161b22" stroke="#30363d"/>
<text x="146" y="126" class="key">ACTIVE DAYS</text><text x="146" y="157" class="big">{active}</text>
<rect x="244" y="105" width="102" height="78" rx="11" fill="#161b22" stroke="#30363d"/>
<text x="256" y="126" class="key">CURRENT</text><text x="256" y="157" class="big">{current}d</text>
<rect x="354" y="105" width="112" height="78" rx="11" fill="#161b22" stroke="#30363d"/>
<text x="366" y="126" class="key">LONGEST</text><text x="366" y="157" class="big">{longest}d</text>
</g>

<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".35s" begin=".72s" fill="freeze"/>
<rect x="24" y="194" width="206" height="78" rx="11" fill="#161b22" stroke="#30363d"/>
<text x="36" y="216" class="key">BEST DAY</text>
<text x="36" y="244" class="big">{best_count}</text>
<text x="91" y="244" class="muted" font-size="9">{esc(best_date)}</text>

<rect x="238" y="194" width="228" height="78" rx="11" fill="#161b22" stroke="#30363d"/>
<text x="250" y="216" class="key">BUILD MODE</text>
<text x="250" y="242" class="val">ship → measure → refine</text>
<text x="250" y="260" class="muted" font-size="9">product-minded · UI-focused · iterative</text>
</g>

<text x="24" y="302" class="key">LAST 6 MONTHS</text>
<line x1="24" y1="346" x2="248" y2="346" stroke="#21262d"/>
<text x="24" y="326" class="muted" font-size="9">activity volume</text>
{''.join(bars)}
<line x1="262" y1="346" x2="468" y2="346" stroke="#21262d"/>
<circle cx="28" cy="371" r="4" fill="#39d353"><animate attributeName="opacity" values="1;.35;1" dur="1.6s" repeatCount="indefinite"/></circle>
<text x="42" y="375" class="muted" font-size="9">status: shipping · data refreshes daily</text>
<text x="462" y="375" text-anchor="end" class="mono" font-size="9" fill="#39d353">ONLINE</text>
</svg>'''
    INFO.write_text(svg + "\n", encoding="utf-8")


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    HEATMAP.parent.mkdir(parents=True, exist_ok=True)
    render_heatmap(payload)
    render_info(payload)
    print(f"wrote {HEATMAP} and {INFO}")


if __name__ == "__main__":
    main()
