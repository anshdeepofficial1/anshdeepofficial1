from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

DATA = Path("data/projects.json")
PROJECT_OUT = Path("assets/project-dashboard.svg")
ACTIVITY_OUT = Path("assets/recent-activity.svg")


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def fmt_date(value: str | None) -> str:
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%b %d")
    except ValueError:
        return "—"


def host(value: str | None) -> str:
    if not value:
        return "github.com"
    try:
        return urlparse(value).netloc.replace("www.", "") or "github.com"
    except Exception:
        return "github.com"


def truncate(value: str, limit: int) -> str:
    value = (value or "").strip()
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def panel(height: int, title: str, meta: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{height}" viewBox="0 0 860 {height}"><style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}.title{{fill:#39d353;font-size:12px;font-weight:700;letter-spacing:.8px}}.muted{{fill:#8b949e;font-size:11px}}.value{{fill:#f0f6fc;font-size:28px;font-weight:700}}.label{{fill:#c9d1d9;font-size:11px}}.bright{{fill:#f0f6fc;font-size:13px;font-weight:700}}</style><rect x=".5" y=".5" width="859" height="{height-1}" rx="18" fill="#0d1117" stroke="#30363d"/><text x="24" y="27" class="title">{esc(title)}</text><text x="836" y="27" class="muted" text-anchor="end">{esc(meta)}</text><line x1="24" y1="43" x2="836" y2="43" stroke="#21262d"/>{body}</svg>''' + "\n"


def metric_cards(metrics, height=81):
    out = []
    for i, (label, value) in enumerate(metrics):
        x = 24 + i * 206
        shown = f"{value:,}" if isinstance(value, int) else value
        out.append(f'<rect x="{x}" y="58" width="194" height="{height}" rx="11" fill="#161b22" stroke="#30363d"/><text x="{x+13}" y="80" class="muted">{esc(label)}</text><text x="{x+13}" y="{112 if height==72 else 115}" class="value">{esc(shown)}</text>')
    return "".join(out)


def render_projects(payload: dict) -> None:
    projects = payload.get("projects", [])
    body = metric_cards([("TRACKED PROJECTS", len(projects)), ("STARS", sum(int(p.get("stars") or 0) for p in projects)), ("FORKS", sum(int(p.get("forks") or 0) for p in projects)), ("OPEN ISSUES", sum(int(p.get("issues") or 0) for p in projects))], 72)
    body += '<text x="32" y="158" class="title">REPOSITORY</text><text x="292" y="158" class="muted">LANGUAGE</text><text x="455" y="158" class="muted">STARS</text><text x="527" y="158" class="muted">FORKS</text><text x="615" y="158" class="muted">RELEASE</text><text x="824" y="158" class="muted" text-anchor="end">UPDATED</text>'
    for i, p in enumerate(projects):
        y = 187 + i * 30
        fill = "#161b22" if i % 2 == 0 else "#0d1117"
        release = truncate((p.get("release") or {}).get("tag") or "—", 20)
        body += f'<rect x="24" y="{y-18}" width="812" height="27" rx="5" fill="{fill}"/><text x="32" y="{y}" class="bright">{esc(truncate(p.get("label") or "repo", 28))}</text><text x="292" y="{y}" class="label">{esc(truncate(p.get("language") or "—", 18))}</text><text x="455" y="{y}" class="label">{int(p.get("stars") or 0)}</text><text x="527" y="{y}" class="label">{int(p.get("forks") or 0)}</text><text x="615" y="{y}" class="label">{esc(release)}</text><text x="824" y="{y}" text-anchor="end" class="muted">{esc(fmt_date(p.get("pushed_at")))}</text>'
    height = 203 + len(projects)*30
    body += f'<text x="24" y="{height-15}" class="muted">Source: GitHub repository metadata · releases and default-branch activity</text>'
    PROJECT_OUT.write_text(panel(height, "REPOSITORY OVERVIEW", "daily refresh", body), encoding="utf-8")


def render_activity(payload: dict) -> None:
    items = payload.get("recent_activity", [])[:6]
    rows = []

    for i, item in enumerate(items):
        y = 72 + i * 34
        begin = .16 + i * .11
        project = truncate(item.get("project") or "repo", 12)
        message = truncate(item.get("message") or "update", 72)
        sha = item.get("sha") or "-------"
        stamp = fmt_date(item.get("date"))
        rows.append(f'''
        <g opacity="0">
          <animate attributeName="opacity" from="0" to="1" dur=".3s" begin="{begin:.2f}s" fill="freeze"/>
          <circle cx="34" cy="{y-3}" r="4" fill="#39d353"/>
          <text x="52" y="{y}" class="repo" font-size="9">{esc(project)}</text>
          <text x="145" y="{y}" class="bright" font-size="10">{esc(message)}</text>
          <text x="808" y="{y}" text-anchor="end" class="muted" font-size="8">{esc(sha)} · {esc(stamp)}</text>
        </g>''')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="292" viewBox="0 0 860 292">
<style>
.repo,.bright,.muted{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.repo{{fill:#39d353;font-weight:700}}
.bright{{fill:#c9d1d9}}
.muted{{fill:#8b949e}}
</style>
<rect x=".5" y=".5" width="859" height="291" rx="18" fill="#0d1117" stroke="#30363d"/>
<circle cx="18" cy="18" r="4" fill="#ff5f56"/><circle cx="32" cy="18" r="4" fill="#ffbd2e"/><circle cx="46" cy="18" r="4" fill="#27c93f"/>
<text x="64" y="22" class="muted" font-size="10">anshdeep@github ~ $ git log --recent --projects</text>
<text x="836" y="22" text-anchor="end" class="muted" font-size="9">latest development activity</text>
<line x1="20" y1="42" x2="840" y2="42" stroke="#21262d"/>
<line x1="34" y1="62" x2="34" y2="248" stroke="#21262d" stroke-width="2"/>
{''.join(rows)}
<text x="24" y="272" class="muted" font-size="9">showing a mixed timeline across the featured repositories</text>
<rect x="808" y="260" width="8" height="14" rx="1" fill="#39d353"><animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect>
</svg>'''
    ACTIVITY_OUT.write_text(svg + "\n", encoding="utf-8")


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    PROJECT_OUT.parent.mkdir(parents=True, exist_ok=True)
    render_projects(payload)
    render_activity(payload)
    print(f"wrote {PROJECT_OUT} and {ACTIVITY_OUT}")


if __name__ == "__main__":
    main()
