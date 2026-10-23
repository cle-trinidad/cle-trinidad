"""Build the profile's 'recent activity' card and 'latest contributions' feed.

Data comes from the public contribution calendar, so counts include private
contributions (if enabled in profile settings) without exposing repo names.
"""
import datetime as dt
import os
import re
import sys
import urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "cle-trinidad"
README = "README.md"
SVG = "assets/recent.svg"
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


def vibe(c):
    if c >= 10:
        return "🚀 on fire"
    if c >= 5:
        return "🔥 big day"
    if c >= 3:
        return "⚡ solid"
    return "🌱 steady"


def recent_svg(days, n=30):
    items = list(days.items())[-n:]
    total = sum(c for _, c in items)
    active = sum(1 for _, c in items if c)
    peak = max([c for _, c in items] + [1])
    w, h, pad, top, chart_h = 495, 195, 25, 70, 90
    bw = (w - 2 * pad) / n
    bars = []
    for i, (d, c) in enumerate(items):
        bh = max(2, chart_h * c / peak) if c else 2
        x = pad + i * bw + 1.5
        y = top + chart_h - bh
        color = "#39d353" if c >= 5 else "#26a641" if c >= 3 else "#006d32" if c else "#2a2e3a"
        delay = i * 0.03
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw - 3:.1f}" height="{bh:.1f}" rx="2" fill="{color}">'
            f'<title>{d}: {c}</title>'
            f'<animate attributeName="height" from="0" to="{bh:.1f}" dur="0.6s" begin="{delay:.2f}s" fill="freeze"/>'
            f'<animate attributeName="y" from="{top + chart_h}" to="{y:.1f}" dur="0.6s" begin="{delay:.2f}s" fill="freeze"/>'
            f"</rect>"
        )
    first = dt.date.fromisoformat(items[0][0])
    last = dt.date.fromisoformat(items[-1][0])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="Segoe UI, Ubuntu, sans-serif">
  <rect width="{w}" height="{h}" rx="6" fill="#1a1b27"/>
  <text x="{pad}" y="32" fill="#70a5fd" font-size="17" font-weight="600">⚡ Last {n} days</text>
  <text x="{pad}" y="54" fill="#a9b1d6" font-size="13">{total} contributions · {active} active days · peak {peak}/day</text>
  {''.join(bars)}
  <text x="{pad}" y="{h - 12}" fill="#565f89" font-size="11">{first:%b %d}</text>
  <text x="{w - pad}" y="{h - 12}" fill="#565f89" font-size="11" text-anchor="end">{last:%b %d}</text>
</svg>
"""


def build_feed(days):
    vals = list(days.values())
    last30, last7 = sum(vals[-30:]), sum(vals[-7:])
    active = [(d, c) for d, c in days.items() if c > 0][::-1][:14]
    lines = [
        f"**{last30}** contributions in the last 30 days · **{last7}** in the last 7 days",
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
    os.makedirs(os.path.dirname(SVG), exist_ok=True)
    open(SVG, "w", encoding="utf-8").write(recent_svg(days))
    text = open(README, encoding="utf-8").read()
    new = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        f"{START}\n{build_feed(days)}\n{END}",
        text,
        flags=re.S,
    )
    open(README, "w", encoding="utf-8").write(new)


if __name__ == "__main__":
    main()
