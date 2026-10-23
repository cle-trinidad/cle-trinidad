"""Build a 'latest contributions' feed (newest first) from the public contribution calendar.

Counts include private contributions (if enabled in profile settings) without exposing repo names.
"""
import datetime as dt
import re
import sys
import urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "cle-trinidad"
README = "README.md"
START, END = "<!--START_SECTION:feed-->", "<!--END_SECTION:feed-->"


def fetch_calendar(user):
    req = urllib.request.Request(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "profile-feed"},
    )
    html = urllib.request.urlopen(req, timeout=30).read().decode()
    ids = {m[1]: m[0] for m in re.findall(r'<td[^>]*data-date="([0-9-]+)"[^>]*id="([^"]+)"', html)}
    days = {}
    for tid, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        if tid in ids:
            m = re.match(r"(\d+) contribution", text.strip())
            days[ids[tid]] = int(m[1]) if m else 0
    return dict(sorted(days.items()))


def streak(days):
    dates = sorted(days, reverse=True)
    if dates and days[dates[0]] == 0:  # today not started yet
        dates = dates[1:]
    n = 0
    for d in dates:
        if days[d] == 0:
            break
        n += 1
    return n


def vibe(c):
    if c >= 10:
        return "🚀 on fire"
    if c >= 5:
        return "🔥 big day"
    if c >= 3:
        return "⚡ solid"
    return "🌱 steady"


def build(days):
    total = sum(days.values())
    last7 = sum(list(days.values())[-7:])
    best_day, best = max(days.items(), key=lambda kv: kv[1])
    active = [(d, c) for d, c in days.items() if c > 0][::-1][:14]

    lines = [
        f"**{total}** contributions in the last year · **{last7}** in the last 7 days · "
        f"**{streak(days)}-day** current streak · best day: **{best}** on "
        f"{dt.date.fromisoformat(best_day):%b %d, %Y}",
        "",
        "| Date | | Contributions | |",
        "|:--|:--|:--|:--|",
    ]
    for d, c in active:
        day = dt.date.fromisoformat(d)
        bar = "🟩" * min(c, 10) + ("➕" if c > 10 else "")
        lines.append(f"| {day:%b %d} | {day:%a} | {bar} **{c}** | {vibe(c)} |")
    lines.append("")
    lines.append(f"<sub>Updated {dt.datetime.utcnow():%Y-%m-%d %H:%M} UTC</sub>")
    return "\n".join(lines)


def main():
    days = fetch_calendar(USER)
    if not days:
        sys.exit("No calendar data found")
    feed = build(days)
    text = open(README, encoding="utf-8").read()
    new = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        f"{START}\n{feed}\n{END}",
        text,
        flags=re.S,
    )
    open(README, "w", encoding="utf-8").write(new)


if __name__ == "__main__":
    main()
