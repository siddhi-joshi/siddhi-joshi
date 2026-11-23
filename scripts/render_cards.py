"""Render GitHub-safe SVG cards. No third-party dependencies required.

Run with GITHUB_TOKEN to refresh public contribution data. STATIC=1 renders
the final animation frame for local previews.
"""

import json
import os
from collections import defaultdict
from datetime import date
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
DATA = ROOT / "data" / "contributions.json"
STATIC = os.getenv("STATIC") == "1"
USER = "siddhi-joshi"


def write(name, body):
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / name).write_text(body + "\n", encoding="utf-8")


def svg(title, description, content, width, height, css=""):
    motion = "" if STATIC else css
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="title desc">'
        f'<title id="title">{escape(title)}</title>'
        f'<desc id="desc">{escape(description)}</desc>'
        f'<style>text{{font-family:Arial,Helvetica,sans-serif}}{motion}'
        '@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style>'
        f'{content}</svg>'
    )


def tile(filename, number, title, subtitle, note, background, ink, art):
    content = f'''
      <rect width="280" height="240" rx="18" fill="{background}"/>
      <rect x="1" y="1" width="278" height="238" rx="17" fill="none" stroke="{ink}" opacity=".25"/>
      <path d="M22 47H258M22 195H258" stroke="{ink}" opacity=".28"/>
      <text x="22" y="32" font-size="11" letter-spacing="2" font-weight="bold" fill="{ink}">0{number} / IN FOCUS</text>
      <text x="22" y="105" font-family="Georgia,serif" font-size="38" fill="{ink}">{title}</text>
      <text x="22" y="133" font-size="15" fill="{ink}">{subtitle}</text>
      <g class="art">{art}</g>
      <text x="22" y="220" font-size="11" letter-spacing="1" fill="{ink}">{note}</text>
      <text x="239" y="221" font-size="22" fill="{ink}">↗</text>'''
    css = (
        '.art{animation:appear .9s both,drift 4s 1s ease-in-out infinite}'
        '@keyframes appear{from{opacity:0;transform:translateY(14px) rotate(-4deg)}'
        'to{opacity:1;transform:translateY(0) rotate(0)}}'
        '@keyframes drift{50%{transform:translateY(-4px)}}'
    )
    write(filename, svg(title, subtitle, content, 280, 240, css))


def render_tiles():
    tile("build.svg", 1, "Build", "Ideas into interfaces", "WEB / TYPESCRIPT / REACT", "#d8e8dc", "#163c3c",
         '<rect x="190" y="74" width="61" height="55" rx="5" fill="none" stroke="#397e74" stroke-width="3"/>'
         '<path d="M190 86h61m-49 15-8 8 8 8m22-16 8 8-8 8" fill="none" stroke="#397e74" stroke-width="2"/>')
    tile("learn.svg", 2, "Learn", "Curiosity in code", "JAVA / SPRING BOOT", "#f5d9c9", "#763b39",
         '<path d="M211 75c-19 0-27 12-27 27s8 26 27 26h25v-53z" fill="none" stroke="#b36253" stroke-width="3"/>'
         '<path d="M202 91h25m-25 12h25m-25 12h18" stroke="#b36253" stroke-width="2"/>')
    tile("share.svg", 3, "Share", "Show the process", "PROJECTS / PORTFOLIO", "#e9e7cd", "#4d5c3b",
         '<circle cx="216" cy="100" r="28" fill="none" stroke="#839365" stroke-width="3"/>'
         '<path d="M204 100h24m-11-12 12 12-12 12" fill="none" stroke="#839365" stroke-width="3"/>')


def fetch_contributions(token):
    query = '''query($login: String!) {
      user(login: $login) { contributionsCollection {
        contributionCalendar { totalContributions weeks {
          contributionDays { date contributionCount }
        } }
      } }
    }'''
    body = json.dumps({"query": query, "variables": {"login": USER}}).encode()
    request = Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json",
        "User-Agent": "siddhi-profile-cards"})
    with urlopen(request, timeout=20) as response:
        payload = json.load(response)
    if payload.get("errors") or not payload.get("data", {}).get("user"):
        raise RuntimeError(f"GitHub contribution query failed: {payload.get('errors', 'user missing')}")
    calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    DATA.parent.mkdir(exist_ok=True)
    DATA.write_text(json.dumps(calendar, indent=2) + "\n", encoding="utf-8")
    return calendar


def render_activity(calendar):
    if calendar is None:
        content = '''
        <rect width="900" height="290" rx="18" fill="#122a34"/>
        <path d="M26 28H874M26 261H874" stroke="#64877d" opacity=".5"/>
        <text x="38" y="55" fill="#aad5c3" font-size="12" letter-spacing="2">GITHUB / ACTIVITY</text>
        <text x="38" y="117" fill="#f5f0e6" font-family="Georgia,serif" font-size="38">The work, in progress.</text>
        <text x="39" y="157" fill="#b9cfca" font-size="17">A year of building, learning, and showing up.</text>
        <text x="39" y="218" fill="#aad5c3" font-size="14">Live contribution chart appears after the first scheduled refresh.</text>
        <text x="844" y="231" fill="#aad5c3" font-size="25">↗</text>'''
        write("activity.svg", svg("GitHub activity", "Contribution chart refreshes after the first GitHub Actions run.", content, 900, 290))
        return

    weeks = calendar["weeks"]
    days = [day for week in weeks for day in week["contributionDays"]]
    active = sum(day["contributionCount"] > 0 for day in days)
    total = calendar["totalContributions"]
    months = defaultdict(int)
    for day in days:
        months[day["date"][:7]] += day["contributionCount"]
    month_keys = sorted(months)[-12:]
    max_month = max((months[m] for m in month_keys), default=1) or 1
    bars = []
    for i, month in enumerate(month_keys):
        x = 40 + i * 69
        height = round(55 * months[month] / max_month)
        bars.append(f'<rect class="bar" x="{x}" y="{205-height}" width="35" height="{height}" rx="3" fill="{("#eaa58b" if months[month] == max_month else "#76b4a2")}"/>')
        bars.append(f'<text x="{x}" y="222" font-size="10" fill="#b9cfca">{date.fromisoformat(month + "-01").strftime("%b")}</text>')
    cells = []
    palette = ["#26434a", "#39746f", "#5b9f8f", "#91c7a8", "#eaa58b"]
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            count = day["contributionCount"]
            level = 0 if not count else min(4, 1 + (count >= 2) + (count >= 4) + (count >= 8))
            cells.append(f'<rect class="cell" x="{39 + wi*15}" y="{245 + di*11}" width="9" height="9" rx="2" fill="{palette[level]}"/>')
    content = f'''
      <rect width="900" height="340" rx="18" fill="#122a34"/>
      <path d="M26 28H874M26 315H874" stroke="#64877d" opacity=".5"/>
      <text x="38" y="54" fill="#aad5c3" font-size="12" letter-spacing="2">GITHUB / LAST 12 MONTHS</text>
      <text x="38" y="99" fill="#f5f0e6" font-family="Georgia,serif" font-size="34">The work, in progress.</text>
      <text x="40" y="130" fill="#b9cfca" font-size="15">{total} contributions  ·  {active} active days</text>
      <text x="39" y="154" fill="#aad5c3" font-size="11" letter-spacing="1.5">MONTHLY ACTIVITY</text>
      <path d="M38 205H861" stroke="#64877d" opacity=".5"/>
      {''.join(bars)}
      {''.join(cells)}
      <text x="39" y="329" fill="#b9cfca" font-size="10">Updated from GitHub’s public contribution calendar</text>'''
    css = '.bar{transform-origin:center bottom;animation:grow .8s both}.cell{animation:pop .5s both}@keyframes grow{from{transform:scaleY(.05)}to{transform:scaleY(1)}}@keyframes pop{from{opacity:.2;transform:scale(.5)}to{opacity:1;transform:scale(1)}}'
    write("activity.svg", svg("GitHub activity", f"{total} contributions and {active} active days in the past year.", content, 900, 340, css))


def main():
    render_tiles()
    token = os.getenv("GITHUB_TOKEN")
    calendar = fetch_contributions(token) if token else (json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else None)
    render_activity(calendar)


if __name__ == "__main__":
    main()
