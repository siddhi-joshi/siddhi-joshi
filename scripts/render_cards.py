"""Render Siddhi's self-contained GitHub profile SVGs.

Run locally with cached data, or set GITHUB_TOKEN to refresh GitHub's
contribution calendar. Set STATIC=1 to render the final animation frame.
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
PAPER = "#f5f5f3"
INK = "#151515"
BLUE = "#3158f4"
RED = "#d94842"
YELLOW = "#f0c558"


def e(value):
    return escape(str(value), quote=True)


def svg(name, width, height, title, description, body, animation=""):
    css = "" if STATIC else animation
    content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{e(title)}</title><desc id="desc">{e(description)}</desc>
<style>text{{font-family:Arial,Helvetica,sans-serif}}.serif,.count{{font-family:Georgia,'Times New Roman',serif}}.mono,.ascii{{font-family:Consolas,monospace}}.ascii{{font-size:8.5px;fill:#333}}{css}@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>
{body}
</svg>'''
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / name).write_text(content + "\n", encoding="utf-8")


def background(width, height, color=PAPER):
    return f'<rect width="{width}" height="{height}" rx="18" fill="{color}"/>'


def ascii_illustration():
    """A generic character illustration, not an invented likeness of Siddhi."""
    lines = []
    for row in range(44):
        chars = []
        y = (row - 21) / 21
        for col in range(58):
            x = (col - 29) / 29
            hair = (x / .54) ** 2 + ((y + .18) / .65) ** 2 < 1
            face = (x / .40) ** 2 + ((y + .08) / .52) ** 2 < 1
            shoulders = y > .43 and abs(x) < .82 - .34 * (y - .43)
            if face:
                value = ":" if (row + col) % 3 else "."
                if abs(y + .06) < .04 and .12 < abs(x) < .25:
                    value = "o"
                if abs(y - .28) < .035 and abs(x) < .17:
                    value = "-"
            elif hair:
                value = "#" if (row + col) % 3 else "+"
            elif shoulders:
                value = "=" if (row + col) % 3 else "+"
            else:
                value = " "
            chars.append(value)
        line = "".join(chars).rstrip()
        delay = .55 + row * .016
        lines.append(f'<text class="ascii" style="animation-delay:{delay:.3f}s" x="650" y="{73+row*9.1:.1f}" xml:space="preserve">{e(line)}</text>')
    return "".join(lines)


def render_hero():
    body = f'''{background(1100, 525)}
    <rect x="60" y="62" width="9" height="9" rx="2" fill="#9baaff"/>
    <text class="mono" x="83" y="72" font-size="14" letter-spacing="2" fill="#6b6b70">SOFTWARE DEVELOPER</text>
    <text class="serif enter" x="55" y="238" font-size="140" fill="{INK}">Siddhi</text>
    <text class="serif enter later" x="53" y="363" font-size="140" font-style="italic" fill="{INK}">Joshi</text>
    <text x="59" y="424" font-size="22" fill="#45454a">I turn ideas into useful, approachable software.</text>
    <text x="59" y="461" font-size="22" fill="#45454a">Building across the web, one project at a time.</text>
    <text class="mono" x="60" y="497" font-size="14" fill="{INK}">portfolio</text>
    <text x="147" y="497" font-size="18" fill="{BLUE}">↗</text>
    {ascii_illustration()}'''
    animation = '''.enter{animation:rise .8s both}.later{animation-delay:.22s}.ascii{animation:print .2s both}@keyframes rise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}@keyframes print{from{opacity:0}to{opacity:1}}'''
    svg("hero.svg", 1100, 525, "Siddhi Joshi", "Software developer with an animated ASCII-style illustration.", body, animation)


def fetch_calendar(token):
    query = '''query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}'''
    request = Request("https://api.github.com/graphql", data=json.dumps({
        "query": query, "variables": {"login": USER}}).encode(), headers={
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


def days(calendar):
    return [day for week in calendar["weeks"] for day in week["contributionDays"]]


def render_heatmap(calendar):
    body = background(1100, 306)
    body += f'''<text class="serif" x="54" y="78" font-size="47" fill="{INK}">Every day,</text>
    <text class="serif" x="254" y="78" font-size="47" font-style="italic" fill="{BLUE}">in blue</text>
    <text class="mono" x="899" y="75" font-size="13" letter-spacing="1.4" fill="#77777d">REFRESHED DAILY</text>'''
    colors = ["#e6e6e6", "#d2dcff", "#a8bcff", "#7896ff", "#4e73ff", BLUE, "#173bd1"]
    if calendar:
        for wi, week in enumerate(calendar["weeks"]):
            for di, day in enumerate(week["contributionDays"]):
                count = day["contributionCount"]
                level = 0 if count == 0 else min(6, 1 + (count >= 2) + (count >= 4) + (count >= 8) + (count >= 16) + (count >= 24))
                delay = .45 + wi * .012 + di * .025
                body += f'<rect class="cell" style="animation-delay:{delay:.3f}s" x="{54+wi*18.8:.1f}" y="{120+di*18}" width="15" height="15" rx="3" fill="{colors[level]}"/>'
        month_positions = {}
        for wi, week in enumerate(calendar["weeks"]):
            for day in week["contributionDays"]:
                key = day["date"][:7]
                month_positions.setdefault(key, wi)
        for key, wi in sorted(month_positions.items())[1:]:
            x = 57 + wi*18.8
            if x < 800:
                body += f'<text x="{x:.1f}" y="274" font-size="12" fill="#71717a">{date.fromisoformat(key+"-01").strftime("%b")}</text>'
    else:
        body += '<text x="56" y="183" font-size="18" fill="#666">Contribution calendar will appear after the first refresh.</text>'
    body += '<text class="mono" x="850" y="279" font-size="12" fill="#777">less</text>'
    for i, color in enumerate(colors[::1]):
        body += f'<rect x="{892+i*18}" y="266" width="14" height="14" rx="3" fill="{color}"/>'
    body += '<text class="mono" x="1034" y="279" font-size="12" fill="#777">more</text>'
    animation = '.cell{animation:pop .35s both}@keyframes pop{from{opacity:0;transform:scale(.45)}to{opacity:1;transform:scale(1)}}'
    svg("graph.svg", 1100, 306, "Every day, in blue", "Siddhi's GitHub contributions, refreshed daily.", body, animation)


def current_streak(day_list):
    counts = {date.fromisoformat(day["date"]): day["contributionCount"] for day in day_list}
    if not counts:
        return 0
    latest = max(counts)
    cursor = latest if counts[latest] else latest - timedelta(days=1)
    result = 0
    while counts.get(cursor, 0):
        result += 1
        cursor -= timedelta(days=1)
    return result


def render_activity(calendar):
    body = background(1100, 400)
    if calendar is None:
        body += '<text class="serif" x="55" y="91" font-size="44">A year in the making.</text><text x="55" y="160" font-size="20">Real monthly activity appears after the first refresh.</text>'
        svg("activity.svg", 1100, 400, "Monthly activity", "Waiting for GitHub data.", body)
        return
    day_list = days(calendar)
    total = calendar["totalContributions"]
    active = sum(day["contributionCount"] > 0 for day in day_list)
    streak = current_streak(day_list)
    monthly = defaultdict(int)
    for day in day_list:
        monthly[day["date"][:7]] += day["contributionCount"]
    keys = sorted(monthly)[-12:]
    best = max(keys, key=lambda key: monthly[key])
    top = max(monthly.values()) or 1
    body += f'''<text class="serif" x="55" y="91" font-size="44" fill="{INK}">A year in the making.</text>
    <text class="mono" x="866" y="77" font-size="13" letter-spacing="1.4" fill="#777">LAST 12 MONTHS</text>
    <text class="serif" x="55" y="174" font-size="71" fill="{BLUE}">{total}</text>
    <text x="{70+len(str(total))*38}" y="172" font-size="19" fill="#555">contributions</text>
    <path d="M57 315H1044" stroke="#bbb"/>'''
    for i, key in enumerate(keys):
        x = 59 + i*84
        height = max(3, round(109*monthly[key]/top)) if monthly[key] else 3
        color = BLUE if key == best else "#9baeff"
        body += f'<rect class="bar" style="animation-delay:{.9+i*.06:.2f}s" x="{x}" y="{315-height}" width="45" height="{height}" rx="3" fill="{color}"/>'
        body += f'<text x="{x}" y="337" font-size="12" fill="#71717a">{date.fromisoformat(key+"-01").strftime("%b")}</text>'
    body += f'''<text class="mono" x="57" y="378" font-size="13" fill="#666">{active} ACTIVE DAYS</text>
    <text class="mono" x="419" y="378" font-size="13" fill="#666">{streak} DAY STREAK</text>
    <text class="mono" x="781" y="378" font-size="13" fill="#666">BEST MONTH: {date.fromisoformat(best+"-01").strftime("%b").upper()}</text>'''
    animation = '.bar{transform-box:fill-box;transform-origin:bottom;animation:grow .85s both}@keyframes grow{from{transform:scaleY(.03)}to{transform:scaleY(1)}}'
    svg("activity.svg", 1100, 400, "Activity in the last year", f"{total} contributions, {active} active days, {streak} day streak.", body, animation)


def render_tile(filename, title, number, unit, detail, fill, ink, delay):
    body = f'''{background(350, 270, fill)}
    <text class="mono" x="30" y="48" font-size="13" letter-spacing="2" fill="{ink}">{e(title.upper())} / 0{delay}</text>
    <text class="serif" x="30" y="118" font-size="43" fill="{ink}">{e(title)}</text>
    <text class="count" x="29" y="200" font-family="Georgia,serif" font-size="76" fill="{ink}">{e(number)}</text>
    <text x="{38+len(str(number))*45}" y="195" font-size="20" fill="{ink}">{e(unit)}</text>
    <path d="M30 218H320" stroke="{ink}" opacity=".35"/>
    <text x="30" y="244" font-size="13" fill="{ink}">{e(detail)}</text>
    <text class="arrow" x="307" y="247" font-size="22" fill="{ink}">↗</text>'''
    animation = f'.count{{animation:rise .75s {1.1+delay*.15:.2f}s both}}.arrow{{animation:nudge 2.8s infinite}}@keyframes rise{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}@keyframes nudge{{50%{{transform:translate(3px,-3px)}}}}'
    svg(filename, 350, 270, title, f"{number} {unit}. {detail}", body, animation)


def render_tiles():
    render_tile("build.svg", "Build", 3, "projects", "Web projects, built by hand", "#c8d7ff", "#173aa0", 1)
    render_tile("learn.svg", "Learn", 4, "tools", "Java · Spring Boot · TS · React", "#f8c7c2", "#913d3a", 2)
    render_tile("share.svg", "Share", 1, "portfolio", "Ideas, projects and process", "#f7e5af", "#735c12", 3)


def render_title(name, dark):
    color = "#f5f5f3" if dark else INK
    body = f'<text class="serif" x="8" y="62" font-size="52" fill="{color}">What I’m coding</text><path d="M394 43H1090" stroke="{color}" opacity=".28"/>'
    svg(name, 1100, 82, "What I'm coding", "Selected repositories.", body)


def render_repo(filename, title, line1, line2, tag, fill, accent):
    body = f'''{background(350, 224, fill)}
    <text class="mono" x="26" y="43" font-size="12" letter-spacing="1.5" fill="{accent}">SELECTED WORK</text>
    <text class="serif" x="25" y="96" font-size="34" fill="{INK}">{e(title)}</text>
    <text x="27" y="138" font-size="15" fill="#444">{e(line1)}</text>
    <text x="27" y="162" font-size="15" fill="#444">{e(line2)}</text>
    <path d="M26 185H324" stroke="{INK}" opacity=".2"/>
    <text class="mono" x="27" y="209" font-size="12" fill="{accent}">{e(tag)}</text>
    <text class="arrow" x="306" y="209" font-size="20" fill="{accent}">↗</text>'''
    animation = '.arrow{animation:nudge 2.8s infinite}@keyframes nudge{50%{transform:translate(3px,-3px)}}'
    svg(filename, 350, 224, title, f"{line1} {line2}", body, animation)


def render_repos():
    render_repo("portfolio.svg", "Portfolio", "A home for my projects", "and ideas.", "TYPESCRIPT / WEB", "#dbe6ff", BLUE)
    render_repo("feedback.svg", "Student feedback", "Collect and review", "student feedback.", "WEB / FORMS", "#f9ddd8", RED)
    render_repo("grades.svg", "Grade calculator", "A small Java project", "for working with grades.", "JAVA / LOGIC", "#f4e9c6", "#876714")


def main():
    calendar = fetch_calendar(os.environ["GITHUB_TOKEN"]) if os.getenv("GITHUB_TOKEN") else (json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else None)
    render_hero()
    render_heatmap(calendar)
    render_activity(calendar)
    render_tiles()
    render_title("title-coding-light.svg", False)
    render_title("title-coding-dark.svg", True)
    render_repos()


if __name__ == "__main__":
    main()
