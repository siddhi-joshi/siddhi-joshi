"""Generate the profile's animated, self-contained SVG cards.

GITHUB_TOKEN refreshes real public contributions through GitHub GraphQL.
STATIC=1 writes the final animation frame for visual inspection.
"""

import json
import os
from collections import defaultdict
from datetime import date, timedelta
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
DATA = ROOT / "data" / "contributions.json"
STATIC = os.getenv("STATIC") == "1"
USER = "siddhi-joshi"
PAPER = "#f4efe5"
INK = "#172b34"
BLUE = "#4267c7"
RED = "#c9584e"


def xml(value):
    return escape(str(value), quote=True)


def card(name, title, description, height, body, css=""):
    motion = "" if STATIC else css
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 {height}" role="img" aria-labelledby="title desc">
<title id="title">{xml(title)}</title><desc id="desc">{xml(description)}</desc>
<style>text{{font-family:Arial,Helvetica,sans-serif}}text[font-family^="Georgia"]{{font-family:Georgia,serif}}text[font-family^="Consolas"]{{font-family:Consolas,monospace}}{motion}@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>
{body}
</svg>'''
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / name).write_text(svg + "\n", encoding="utf-8")


def base(height, fill=PAPER):
    return f'<rect width="900" height="{height}" rx="20" fill="{fill}"/><rect x="1" y="1" width="898" height="{height-2}" rx="19" fill="none" stroke="{INK}" opacity=".16"/>'


def line(y, color=INK):
    return f'<path d="M28 {y}H872" stroke="{color}" opacity=".22"/>'


def heading(command, y=47, color=INK):
    return f'<text x="34" y="{y}" font-family="Consolas,monospace" font-size="14" fill="{color}" opacity=".72">siddhi@github ~ $ {xml(command)}</text>'


def hero():
    # A text mark, not a likeness or a portrait attributed to Siddhi.
    rows = [
        "  SSSSS   JJJJJ  ", " SS         JJ    ", " SS         JJ    ",
        "  SSSS      JJ    ", "     SS     JJ    ", "     SS  J  JJ    ",
        " SSSSS    JJJ     ",
    ]
    art = "".join(
        f'<text class="print" style="animation-delay:{.22 + i*.12:.2f}s" x="69" y="{126+i*20}" font-family="Consolas,monospace" font-size="22" font-weight="bold" xml:space="preserve" fill="{BLUE}">{xml(row)}</text>'
        for i, row in enumerate(rows)
    )
    body = f'''{base(330)}{line(66)}{line(302)}
    {heading('whoami')}
    <path d="M360 66V302" stroke="{INK}" opacity=".22"/>
    <rect x="52" y="90" width="282" height="193" rx="12" fill="#e4e9e8"/>
    <circle class="ring" cx="193" cy="187" r="100" fill="none" stroke="{BLUE}" opacity=".18"/>
    {art}
    <text x="391" y="130" fill="{INK}" font-family="Georgia,serif" font-size="67" class="rise">Siddhi</text>
    <text x="391" y="201" fill="{INK}" font-family="Georgia,serif" font-size="67" class="rise late">Joshi<tspan fill="{RED}">.</tspan></text>
    <text x="395" y="244" fill="#425b5f" font-size="19" class="rise later">I turn ideas into useful software.</text>
    <text x="395" y="275" fill="#617777" font-size="14" class="rise later">BUILDING  /  LEARNING  /  SHARING</text>
    <text x="33" y="320" fill="#627879" font-size="11" letter-spacing="2">SOFTWARE DEVELOPER</text>'''
    css = '''.print{animation:print .12s both}.rise{animation:rise .75s both}.late{animation-delay:.28s}.later{animation-delay:.55s}.ring{animation:pulse 4s ease-in-out infinite}@keyframes print{from{opacity:0}to{opacity:1}}@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}@keyframes pulse{50%{opacity:.55;transform:scale(1.06)}}'''
    card("hero.svg", "Siddhi Joshi", "Software developer building, learning and sharing. Animated SJ text mark.", 330, body, css)


def fetch(token):
    query = '''query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}'''
    request = Request("https://api.github.com/graphql", data=json.dumps({
        "query": query, "variables": {"login": USER}}).encode(), headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json",
        "User-Agent": "siddhi-profile-readme"})
    with urlopen(request, timeout=20) as response:
        payload = json.load(response)
    if payload.get("errors") or not payload.get("data", {}).get("user"):
        raise RuntimeError(f"GitHub contribution query failed: {payload.get('errors', 'user missing')}")
    calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    DATA.parent.mkdir(exist_ok=True)
    DATA.write_text(json.dumps(calendar, indent=2) + "\n", encoding="utf-8")
    return calendar


def days_in(calendar):
    return [day for week in calendar["weeks"] for day in week["contributionDays"]]


def graph(calendar):
    body = base(218, "#e5edf8") + line(66) + heading("./contributions.sh")
    if calendar is None:
        body += f'''<text x="38" y="115" fill="{INK}" font-family="Georgia,serif" font-size="30">Every little commit counts.</text>
        <text x="39" y="160" fill="#465e7d" font-size="16">The live contribution graph appears after the first workflow run.</text>
        <text x="39" y="194" fill="#5873a0" font-size="12">VIEW THE LIVE ACTIVITY ON GITHUB ↗</text>'''
        card("graph.svg", "GitHub contributions", "Live graph appears after the first workflow run.", 218, body)
        return
    palette = ["#d2dced", "#afc4eb", "#789de0", BLUE, "#254aa8"]
    cells = []
    for wi, week in enumerate(calendar["weeks"]):
        for di, day in enumerate(week["contributionDays"]):
            count = day["contributionCount"]
            level = min(4, 1 + (count >= 2) + (count >= 4) + (count >= 8)) if count else 0
            delay = .12 + wi*.012 + di*.025
            cells.append(f'<rect class="cell" style="animation-delay:{delay:.2f}s" x="{39+wi*15}" y="{90+di*15}" width="11" height="11" rx="2" fill="{palette[level]}"/>')
    body += ''.join(cells)
    body += f'<text x="39" y="207" fill="#465e7d" font-size="11">LAST 12 MONTHS  ·  UPDATED DAILY</text><text x="835" y="207" fill="{BLUE}" font-size="15">↗</text>'
    css = '.cell{animation:pop .3s both}@keyframes pop{from{opacity:0;transform:scale(.3)}to{opacity:1;transform:scale(1)}}'
    card("graph.svg", "GitHub contribution graph", "Real daily contributions over the last year.", 218, body, css)


def streak(days):
    counts = {date.fromisoformat(d["date"]): d["contributionCount"] for d in days}
    if not counts:
        return 0
    latest = max(counts)
    cursor = latest if counts[latest] else latest - timedelta(days=1)
    length = 0
    while counts.get(cursor, 0) > 0:
        length += 1
        cursor -= timedelta(days=1)
    return length


def activity(calendar):
    body = base(266) + line(66) + heading("./activity.sh")
    if calendar is None:
        body += f'''<text x="38" y="121" fill="{INK}" font-family="Georgia,serif" font-size="31">A year of building.</text>
        <text x="39" y="164" fill="#526667" font-size="16">Monthly bars and real stats appear after the first workflow run.</text>
        <text x="39" y="228" fill="{BLUE}" font-size="12">ACTIVITY REFRESHES DAILY</text>'''
        card("activity.svg", "Monthly GitHub activity", "Monthly chart appears after the first workflow run.", 266, body)
        return
    days = days_in(calendar)
    total = calendar["totalContributions"]
    active = sum(d["contributionCount"] > 0 for d in days)
    current_streak = streak(days)
    months = defaultdict(int)
    for day in days:
        months[day["date"][:7]] += day["contributionCount"]
    # The calendar spans parts of 13 months; show the most recent 12.
    keys = sorted(months)[-12:]
    max_value = max((months[key] for key in keys), default=1) or 1
    best = max(keys, key=lambda key: months[key]) if keys else None
    bars = []
    for i, key in enumerate(keys):
        x = 39 + i*70
        h = max(2, round(65*months[key]/max_value)) if months[key] else 2
        color = BLUE if key == best else "#84a9a2"
        bars.append(f'<rect class="bar" style="animation-delay:{.6+i*.055:.2f}s" x="{x}" y="{218-h}" width="34" height="{h}" rx="3" fill="{color}"/>')
        bars.append(f'<text x="{x}" y="239" fill="#5b7071" font-size="11">{date.fromisoformat(key+"-01").strftime("%b")}</text>')
    body += f'''<text x="39" y="105" fill="{INK}" font-family="Georgia,serif" font-size="32">A year of building.</text>
    <text x="40" y="139" fill="#526667" font-size="16">{total} contributions  ·  {active} active days  ·  {current_streak} day streak</text>
    <path d="M39 218H867" stroke="{INK}" opacity=".28"/>{''.join(bars)}
    <text x="39" y="255" fill="#6a7a78" font-size="10">BEST MONTH IN BLUE  /  REAL GITHUB DATA</text>'''
    css = '.bar{transform-box:fill-box;transform-origin:bottom;animation:grow .75s both}@keyframes grow{from{transform:scaleY(.04)}to{transform:scaleY(1)}}'
    card("activity.svg", "Monthly GitHub activity", f"{total} contributions, {active} active days, {current_streak} day streak.", 266, body, css)


def tile(filename, number, title, subtitle, footer, fill, accent, icon):
    body = f'''<rect width="280" height="246" rx="18" fill="{fill}"/>
    <rect x="1" y="1" width="278" height="244" rx="17" fill="none" stroke="{INK}" opacity=".18"/>
    <path d="M20 46H260M20 199H260" stroke="{INK}" opacity=".22"/>
    <text x="21" y="31" fill="{INK}" font-family="Consolas,monospace" font-size="11">0{number} / {xml(title.upper())}</text>
    <text x="20" y="111" fill="{INK}" font-family="Georgia,serif" font-size="46">{xml(title)}</text>
    <text x="22" y="143" fill="{INK}" font-size="15">{xml(subtitle)}</text>
    <g class="icon">{icon}</g>
    <text x="21" y="226" fill="{INK}" font-size="11" letter-spacing="1">{xml(footer)}</text>
    <text class="arrow" x="239" y="229" fill="{accent}" font-size="24">↗</text>'''
    css = '.icon{animation:hover 4s ease-in-out infinite}.arrow{animation:nudge 3s infinite}@keyframes hover{50%{transform:translateY(-5px)}}@keyframes nudge{50%{transform:translate(3px,-3px)}}'
    # Tile viewBox is deliberately 280px so the three images form a row.
    markup = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 246" role="img" aria-labelledby="title desc"><title id="title">{xml(title)}</title><desc id="desc">{xml(subtitle)}</desc><style>text{{font-family:Arial,Helvetica,sans-serif}}text[font-family^="Georgia"]{{font-family:Georgia,serif}}text[font-family^="Consolas"]{{font-family:Consolas,monospace}}{'' if STATIC else css}@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>{body}</svg>'''
    (ASSETS / filename).write_text(markup + "\n", encoding="utf-8")


def tiles():
    tile("build.svg", 1, "Build", "Ideas into interfaces", "TYPESCRIPT / REACT", "#d8e9e2", "#326d72",
         '<rect x="191" y="79" width="63" height="53" rx="6" fill="none" stroke="#326d72" stroke-width="3"/><path d="M191 92h63m-48 12-7 7 7 7m24-14 7 7-7 7" fill="none" stroke="#326d72" stroke-width="2"/>')
    tile("learn.svg", 2, "Learn", "Curiosity in code", "JAVA / SPRING BOOT", "#f6d9cf", RED,
         '<path d="M203 82h43v51h-43c-10 0-17-8-17-17V99c0-9 7-17 17-17z" fill="none" stroke="#bb6459" stroke-width="3"/><path d="M201 98h32m-32 12h32m-32 12h19" stroke="#bb6459" stroke-width="2"/>')
    tile("share.svg", 3, "Share", "Projects and process", "PORTFOLIO / IDEAS", "#efe8c7", "#7b8050",
         '<circle cx="219" cy="106" r="30" fill="none" stroke="#7b8050" stroke-width="3"/><path d="M204 106h29m-12-12 12 12-12 12" fill="none" stroke="#7b8050" stroke-width="3"/>')


def project(filename, index, title, subtitle, tags, fill, accent, motif):
    body = f'''{base(166, fill)}{line(47)}
    <text x="35" y="31" fill="{accent}" font-family="Consolas,monospace" font-size="12">0{index} / WHAT I’M CODING</text>
    <text x="36" y="96" fill="{INK}" font-family="Georgia,serif" font-size="38">{xml(title)}</text>
    <text x="37" y="123" fill="#4d6266" font-size="15">{xml(subtitle)}</text>
    <text x="37" y="151" fill="{accent}" font-size="11" letter-spacing="1">{xml(tags)}</text>
    <g class="motif">{motif}</g><text x="846" y="98" fill="{accent}" font-size="25">↗</text>'''
    css = '.motif{animation:drift 4s ease-in-out infinite}@keyframes drift{50%{transform:translateY(-4px)}}'
    card(filename, title, subtitle, 166, body, css)


def projects():
    project("portfolio.svg", 1, "Portfolio", "A home for my projects and ideas.", "TYPESCRIPT / WEB", "#e2ede8", "#317879",
            '<rect x="709" y="63" width="107" height="67" rx="7" fill="none" stroke="#317879" stroke-width="3"/><path d="M709 77h107m-92 18h34m-34 12h63" stroke="#317879" stroke-width="3"/>')
    project("feedback.svg", 2, "Student feedback system", "A simple way to collect and review feedback.", "WEB / FORMS", "#f5ddd4", "#ad5b53",
            '<path d="M712 66h104v62h-53l-18 12v-12h-33z" fill="none" stroke="#ad5b53" stroke-width="3"/><path d="M729 86h68m-68 15h46" stroke="#ad5b53" stroke-width="3"/>')
    project("grades.svg", 3, "Grade calculator", "A small Java project for working with grades.", "JAVA / LOGIC", "#e9ebcf", "#697b4b",
            '<path d="M709 129h107" stroke="#697b4b" stroke-width="3"/><rect x="724" y="93" width="17" height="36" fill="#aab485"/><rect x="753" y="77" width="17" height="52" fill="#839661"/><rect x="782" y="61" width="17" height="68" fill="#697b4b"/>')


def main():
    hero()
    calendar = fetch(os.environ["GITHUB_TOKEN"]) if os.getenv("GITHUB_TOKEN") else (json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else None)
    graph(calendar)
    activity(calendar)
    tiles()
    projects()


if __name__ == "__main__":
    main()
