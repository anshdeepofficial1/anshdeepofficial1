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


def render_projects(payload: dict) -> None:
    projects = payload.get("projects", [])
    active = payload.get("active_project")

    cards = []
    starts = [24, 299, 574]
    for i, project in enumerate(projects[:3]):
        x = starts[i]
        is_active = project.get("repo") == active
        release = project.get("release")
        release_text = release.get("tag") if release else "web"
        release_label = "LATEST RELEASE" if release else "DELIVERY"
        update = fmt_date(project.get("pushed_at"))
        homepage = host(project.get("homepage"))
        badge = (
            f'<rect x="{x+171}" y="61" width="70" height="20" rx="10" fill="#0e4429" stroke="#238636"/>'
            f'<text x="{x+206}" y="75" text-anchor="middle" class="mono green" font-size="8" font-weight="700">ACTIVE</text>'
            if is_active else
            f'<text x="{x+241}" y="74" text-anchor="end" class="muted" font-size="8">updated {update}</text>'
        )
        begin = .18 + i * .18
        cards.append(f'''
        <g opacity="0">
          <animate attributeName="opacity" from="0" to="1" dur=".35s" begin="{begin:.2f}s" fill="freeze"/>
          <animateTransform attributeName="transform" type="translate" from="0 6" to="0 0" dur=".35s" begin="{begin:.2f}s" fill="freeze"/>
          <rect x="{x}" y="54" width="262" height="190" rx="14" fill="#0d1117" stroke="#30363d"/>
          <text x="{x+16}" y="77" class="bright" font-size="14" font-weight="800">{esc(project.get("label"))}</text>
          {badge}
          <text x="{x+16}" y="100" class="muted" font-size="9">{esc(project.get("language"))} · {esc(homepage)}</text>
          <line x1="{x+16}" y1="112" x2="{x+246}" y2="112" stroke="#21262d"/>

          <text x="{x+16}" y="137" class="key">STARS</text>
          <text x="{x+16}" y="161" class="metric">{int(project.get("stars") or 0)}</text>
          <text x="{x+85}" y="137" class="key">FORKS</text>
          <text x="{x+85}" y="161" class="metric">{int(project.get("forks") or 0)}</text>
          <text x="{x+154}" y="137" class="key">ISSUES</text>
          <text x="{x+154}" y="161" class="metric">{int(project.get("issues") or 0)}</text>

          <line x1="{x+16}" y1="178" x2="{x+246}" y2="178" stroke="#21262d"/>
          <text x="{x+16}" y="199" class="key">{release_label}</text>
          <text x="{x+16}" y="222" class="bright" font-size="12" font-weight="700">{esc(release_text)}</text>
          <text x="{x+246}" y="222" text-anchor="end" class="muted" font-size="8">{esc(update)}</text>
        </g>''')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="270" viewBox="0 0 860 270">
<style>
.mono,.key,.metric,.bright,.muted{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.key{{fill:#39d353;font-size:8px;font-weight:700;letter-spacing:.8px}}
.metric{{fill:#f0f6fc;font-size:18px;font-weight:800}}
.bright{{fill:#f0f6fc;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.muted{{fill:#8b949e;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.green{{fill:#39d353}}
</style>
<rect x=".5" y=".5" width="859" height="269" rx="18" fill="#0d1117" stroke="#30363d"/>
<circle cx="18" cy="18" r="4" fill="#ff5f56"/><circle cx="32" cy="18" r="4" fill="#ffbd2e"/><circle cx="46" cy="18" r="4" fill="#27c93f"/>
<text x="64" y="22" class="muted" font-size="10">anshdeep@github ~ $ projects --live</text>
<text x="836" y="22" text-anchor="end" class="muted" font-size="9">repo metrics · daily refresh</text>
<line x1="20" y1="42" x2="840" y2="42" stroke="#21262d"/>
{''.join(cards)}
</svg>'''
    PROJECT_OUT.write_text(svg + "\n", encoding="utf-8")


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
