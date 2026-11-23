"""Render self-contained SVG cards from cached GitHub contribution data.

Run with --refresh-data in GitHub Actions. STATIC=1 renders final frames.
An optional assets/portrait.png or assets/portrait.jpg appears in the hero.
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import date, timedelta
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "cards"
DATA = ROOT / "data/contributions.json"
FONT = ROOT / "fonts/geist-source.woff2"
STATIC = os.getenv("STATIC") == "1"
INK, MUTED, LINE = "#000", "#666", "#e5e5e5"
GLYPHS = ("Siddhi Joshi Creative developer building digital experiences "
          "I build thoughtful mobile and web experiences Build Explore Connect "
          "GitHub Portfolio LinkedIn Monthly activity A year of making things "
          "Contributions Active days Current streak Busiest day Featured project "
          "Tic Tac Toe Game Student Feedback System Employee Payroll System "
          "React Native Expo JavaScript HTML CSS MySQL Java OOP "
          "Made one day at a time Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec "
          "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz "
          "0123456789 /:,.+−→↗%·-'")

def esc(value):
    return escape(str(value), quote=True)

def font_data():
    if not FONT.exists():
        raise FileNotFoundError(FONT)
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "geist.woff"
        try:
            subprocess.run([sys.executable, "-m", "fontTools.subset", str(FONT), f"--output-file={output}",
                            "--flavor=woff", "--layout-features=*",
                            "--text=" + GLYPHS], check=True, capture_output=True, text=True)
        except FileNotFoundError as error:
            raise RuntimeError("Install fonttools and brotli: python -m pip install fonttools brotli") from error
        except subprocess.CalledProcessError as error:
            if "No module named brotli" in error.stderr:
                # Local preview fallback: Node's Brotli decoder lets fontTools read WOFF2.
                shim = Path(tmp) / "brotli.py"
                shim.write_text(
                    "import subprocess\n"
                    "def decompress(data):\n"
                    "    return subprocess.run(['node','-e',"
                    "'const z=require(\"zlib\");let b=[];process.stdin.on(\"data\",c=>b.push(c));"
                    "process.stdin.on(\"end\",()=>process.stdout.write(z.brotliDecompressSync(Buffer.concat(b))))'],"
                    "input=data,capture_output=True,check=True).stdout\n",
                    encoding="utf-8",
                )
                env = dict(os.environ, PYTHONPATH=str(shim.parent))
                retry = subprocess.run(
                    [sys.executable, "-m", "fontTools.subset", str(FONT),
                     f"--output-file={output}", "--flavor=woff",
                     "--layout-features=*", "--text=" + GLYPHS],
                    env=env, capture_output=True, text=True,
                )
                if retry.returncode:
                    raise RuntimeError(f"Font subsetting failed: {retry.stderr}") from error
            else:
                raise RuntimeError(f"Font subsetting failed: {error.stderr}") from error
        return base64.b64encode(output.read_bytes()).decode("ascii"), "woff"

def card(name, height, title, desc, body, font, motion="", width=1100):
    encoded, flavor = font
    css = (f"@font-face{{font-family:GeistCard;src:url(data:font/{flavor};base64," + encoded +
           f") format('{flavor}');font-weight:100 900}}text{{font-family:GeistCard,Arial,sans-serif}}")
    if not STATIC:
        css += motion + ("@media(prefers-reduced-motion:reduce){"
                         "*,*::before,*::after{animation:none!important;transition:none!important}}")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'role="img" aria-labelledby="title desc"><title id="title">{esc(title)}</title>'
           f'<desc id="desc">{esc(desc)}</desc><style>{css}</style>'
           f'<rect width="{width}" height="{height}" fill="white"/>{body}</svg>\n')
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(svg, encoding="utf-8")

def heading(text, x=42, y=44):
    return (f'<text x="{x}" y="{y}" font-size="13" font-weight="650" '
            f'letter-spacing="2.3" fill="{MUTED}">{esc(text.upper())}</text>')

def portrait():
    for filename, mime in (("portrait.png", "image/png"), ("portrait.jpg", "image/jpeg")):
        path = ROOT / "assets" / filename
        if path.exists():
            data = base64.b64encode(path.read_bytes()).decode("ascii")
            return ('<defs><clipPath id="crop"><rect x="793" y="57" width="262" height="286" rx="8"/>'
                    '</clipPath></defs><image x="793" y="57" width="262" height="286" '
                    f'preserveAspectRatio="xMidYMid slice" clip-path="url(#crop)" '
                    f'href="data:{mime};base64,{data}"/>')
    return ('<rect x="793" y="57" width="262" height="286" fill="#f5f5f5"/>'
            '<text x="813" y="105" font-size="26" font-weight="800">SJ</text>'
            '<path d="M813 284H1035" stroke="#ccc"/>'
            '<text x="813" y="314" font-size="12" fill="#666">DESIGN · CODE · CURIOSITY</text>')

def hero(font):
    body = (heading("Hello, I'm Siddhi") +
            '<text class="rise" x="40" y="180" font-size="100" font-weight="800" letter-spacing="-6">Siddhi</text>'
            '<text class="rise later" x="39" y="278" font-size="100" font-weight="800" letter-spacing="-6">Joshi</text>'
            '<text class="intro" x="43" y="330" font-size="21" fill="#555">I build thoughtful mobile and web experiences.</text>'
            '<path d="M42 365H1058" stroke="#e5e5e5"/>'
            '<text x="43" y="396" font-size="13" font-weight="650" letter-spacing="1.7">CREATIVE DEVELOPER</text>'
            '<text x="838" y="396" font-size="13" fill="#666">MEHKAR, INDIA</text>' + portrait())
    motion = (".rise{animation:up .75s both}.later{animation-delay:.18s}"
              ".intro{animation:up .7s .36s both}"
              "@keyframes up{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}")
    card("hero.svg", 420, "Siddhi Joshi", "Creative developer building mobile and web experiences.", body, font, motion)

def tile(name, number, title, detail, delay, font):
    body = (f'<rect x="1" y="1" width="348" height="208" fill="white" stroke="{LINE}"/>' +
            heading(f"0{number} / {title}", 25, 41) +
            f'<text class="tile" x="25" y="109" font-size="48" font-weight="760" '
            f'style="animation-delay:{delay}s">{esc(title)}</text>' +
            f'<text x="25" y="145" font-size="16" fill="#666">{esc(detail)}</text>' +
            '<path d="M25 170H325" stroke="#e5e5e5"/>'
            '<text x="25" y="197" font-size="13" font-weight="650">OPEN LINK</text>'
            '<path d="M286 185h36m0 0-11-11m11 11-11 11" fill="none" stroke="black" stroke-width="2"/>')
    motion = (".tile{animation:up .65s both}"
              "@keyframes up{from{opacity:0;transform:translateY(13px)}to{opacity:1;transform:translateY(0)}}")
    card(name, 210, title, detail, body, font, motion, width=350)

def fetch_calendar(token):
    query = ("query($login:String!){user(login:$login){contributionsCollection"
             "{contributionCalendar{totalContributions weeks{contributionDays"
             "{date contributionCount}}}}}}")
    request = Request("https://api.github.com/graphql",
                      data=json.dumps({"query": query, "variables": {"login": "siddhi-joshi"}}).encode(),
                      headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                               "User-Agent": "siddhi-profile-cards"})
    with urlopen(request, timeout=25) as response:
        payload = json.load(response)
    if payload.get("errors") or not payload.get("data", {}).get("user"):
        raise RuntimeError(f"GitHub contribution query failed: {payload.get('errors', 'user missing')}")
    calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    DATA.parent.mkdir(exist_ok=True)
    DATA.write_text(json.dumps(calendar, indent=2) + "\n", encoding="utf-8")
    return calendar

def days(calendar):
    return [day for week in calendar["weeks"] for day in week["contributionDays"]]

def streak(day_list):
    counts = {date.fromisoformat(day["date"]): day["contributionCount"] for day in day_list}
    last = max(counts)
    cursor = last if counts[last] else last - timedelta(days=1)
    result = 0
    while counts.get(cursor, 0):
        result += 1
        cursor -= timedelta(days=1)
    return result

def activity(calendar, font):
    day_list = days(calendar)
    monthly = defaultdict(int)
    for day in day_list:
        monthly[day["date"][:7]] += day["contributionCount"]
    keys = sorted(monthly)[-12:]
    maximum = max(monthly.values()) or 1
    active = sum(day["contributionCount"] > 0 for day in day_list)
    busiest = max(day_list, key=lambda day: day["contributionCount"])
    run = streak(day_list)
    body = (heading("Monthly activity") +
            '<text x="42" y="92" font-size="38" font-weight="750" letter-spacing="-1.6">A year of making things.</text>'
            '<path d="M42 304H1058" stroke="#e5e5e5"/>')
    for index, key in enumerate(keys):
        xpos = 48 + index * 84
        height = round(130 * monthly[key] / maximum)
        month = date.fromisoformat(key + "-01").strftime("%b").upper()
        body += (f'<rect class="bar" x="{xpos}" y="{298-height}" width="53" height="{height}" '
                 f'fill="black" style="animation-delay:{1.2+index*.055:.3f}s"/>'
                 f'<text x="{xpos}" y="327" font-size="13" fill="#666">{month}</text>'
                 f'<text x="{xpos}" y="{285-height}" font-size="12" fill="#666">{monthly[key]}</text>')
    body += '<path d="M42 348H1058" stroke="#e5e5e5"/>'
    for xpos, value, caption in ((42, calendar["totalContributions"], "CONTRIBUTIONS"),
                                  (290, active, "ACTIVE DAYS"), (526, run, "CURRENT STREAK"),
                                  (770, f'{busiest["contributionCount"]} · {busiest["date"][5:]}', "BUSIEST DAY")):
        body += (f'<text x="{xpos}" y="405" font-size="39" font-weight="760">{esc(value)}</text>'
                 f'<text x="{xpos}" y="431" font-size="12" letter-spacing="1.6" fill="#666">{caption}</text>')
    motion = (".bar{transform-box:fill-box;transform-origin:bottom;animation:grow .7s both}"
              "@keyframes grow{from{transform:scaleY(.02)}to{transform:scaleY(1)}}")
    card("activity.svg", 460, "Monthly GitHub activity",
         f'{active} active days, {run} day streak. Busiest day: {busiest["date"]}.', body, font, motion)

def repo(name, title, detail, tags, index, font):
    body = (f'<rect x="1" y="1" width="1098" height="186" fill="white" stroke="{LINE}"/>' +
            heading(f"Featured project / 0{index}", 34, 42) +
            f'<text class="repo" x="32" y="97" font-size="39" font-weight="750" '
            f'letter-spacing="-1.5" style="animation-delay:{2.05+index*.16:.2f}s">{esc(title)}</text>' +
            f'<text x="34" y="130" font-size="17" fill="#666">{esc(detail)}</text>' +
            f'<text x="34" y="165" font-size="12" letter-spacing="1.2">{esc(tags.upper())}</text>'
            '<path d="M1023 97h36m0 0-13-13m13 13-13 13" fill="none" stroke="black" stroke-width="2.5"/>')
    motion = (".repo{animation:up .65s both}"
              "@keyframes up{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}")
    card(name, 188, title, detail, body, font, motion)

def graph(calendar, font):
    weeks = calendar["weeks"][-52:]
    nonzero = sorted(day["contributionCount"] for week in weeks
                     for day in week["contributionDays"] if day["contributionCount"])
    thresholds = ([nonzero[int((len(nonzero)-1)*q)] for q in (.25, .5, .75)]
                  if nonzero else [1, 2, 3])
    colors = ["#f5f5f5", "#d4d4d4", "#a3a3a3", "#666666", "#000000"]
    body = (heading("Contribution graph") +
            '<text x="42" y="92" font-size="37" font-weight="750" letter-spacing="-1.4">Made one day at a time.</text>' +
            f'<text x="868" y="86" font-size="13" fill="#666">{calendar["totalContributions"]} IN THE PAST YEAR</text>')
    labels = {}
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            count = day["contributionCount"]
            level = 0 if not count else 1 + sum(count > t for t in thresholds)
            body += (f'<rect class="cell" x="{43+wi*19.5:.1f}" y="{122+di*19}" width="15" height="15" '
                     f'rx="2" fill="{colors[level]}" style="animation-delay:{2.65+wi*.012+di*.009:.3f}s"/>')
            labels.setdefault(day["date"][:7], wi)
    for key, wi in sorted(labels.items()):
        xpos = 43 + wi * 19.5
        if xpos < 1020:
            month = date.fromisoformat(key + "-01").strftime("%b").upper()
            body += f'<text x="{xpos:.1f}" y="275" font-size="12" fill="#666">{month}</text>'
    body += '<text x="42" y="304" font-size="12" fill="#666">LESS</text>'
    for index, color in enumerate(colors):
        body += f'<rect x="{88+index*22}" y="291" width="15" height="15" rx="2" fill="{color}"/>'
    body += '<text x="207" y="304" font-size="12" fill="#666">MORE</text>'
    motion = ".cell{animation:show .28s both}@keyframes show{from{opacity:0}to{opacity:1}}"
    card("graph.svg", 330, "GitHub contribution graph",
         "The past year of GitHub contributions in the site's monochrome palette.", body, font, motion)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-data", action="store_true")
    args = parser.parse_args()
    if args.refresh_data:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            parser.error("--refresh-data requires GITHUB_TOKEN")
        calendar = fetch_calendar(token)
    else:
        calendar = json.loads(DATA.read_text(encoding="utf-8"))
    font = font_data()
    hero(font)
    tile("build.svg", 1, "Build", "Explore my projects", .58, font)
    tile("explore.svg", 2, "Explore", "See the portfolio", .72, font)
    tile("connect.svg", 3, "Connect", "Let's talk on LinkedIn", .86, font)
    activity(calendar, font)
    repo("tic-tac-toe.svg", "Tic Tac Toe Game", "A cross-platform mobile game with smooth, responsive play.", "React Native · Expo · JavaScript", 1, font)
    repo("student-feedback.svg", "Student Feedback System", "Secure feedback collection and automated faculty reports.", "HTML · CSS · JavaScript · MySQL", 2, font)
    repo("employee-payroll.svg", "Employee Payroll System", "Modular Java payroll calculations for full-time and part-time staff.", "Java · OOP", 3, font)
    graph(calendar, font)

if __name__ == "__main__":
    main()
