"""
Midnight Aurora — GitHub profile generator.

Edit profile.json, then run:   python build.py
It writes every animated SVG into ./assets and regenerates README.md.
No third-party packages needed.
"""
import base64
import html
import json
import os
import random
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(ASSETS, exist_ok=True)

with open(os.path.join(ROOT, "profile.json"), encoding="utf-8") as f:
    C = json.load(f)

T = C["theme"]
SANS = "'Segoe UI', -apple-system, BlinkMacSystemFont, Inter, 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, 'Cascadia Code', 'JetBrains Mono', SFMono-Regular, Menlo, Consolas, monospace"
W = 1200
ACCENTS = [T["primary"], T["secondary"], T["tertiary"], T["accent"]]


def esc(s):
    return html.escape(str(s), quote=True)


def hx(c):
    return c.lstrip("#")


def wrap(text, limit):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) > limit:
            if cur:
                lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    if cur:
        lines.append(cur)
    return lines


def text_w(s, size, mono=False):
    """Rough rendered width of a string (good enough for chip sizing)."""
    return len(str(s)) * size * (0.61 if mono else 0.56)


def base_css(p):
    """Shared entrance animations, namespaced per file so nothing collides."""
    return f"""
    .{p}-sans {{ font-family: {SANS}; }}
    .{p}-mono {{ font-family: {MONO}; }}
    .{p}-in {{ animation: {p}-in 1.1s cubic-bezier(.16,1,.3,1) both; }}
    .{p}-pop {{ animation: {p}-pop .7s cubic-bezier(.34,1.56,.64,1) both; }}
    .{p}-draw {{ stroke-dasharray: 1400; stroke-dashoffset: 1400; animation: {p}-draw 2s cubic-bezier(.65,0,.35,1) .4s forwards; }}
    .{p}-pulse {{ animation: {p}-pulse 2s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
    .{p}-blink {{ animation: {p}-blink 1s steps(1) infinite; }}
    @keyframes {p}-in {{ from {{ opacity: 0; transform: translateY(14px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes {p}-pop {{ from {{ opacity: 0; transform: translateY(8px) scale(.96); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes {p}-draw {{ to {{ stroke-dashoffset: 0; }} }}
    @keyframes {p}-pulse {{ 0%,100% {{ transform: scale(1); opacity: 1; }} 50% {{ transform: scale(1.8); opacity: .25; }} }}
    @keyframes {p}-blink {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .{p}-in, .{p}-pop, .{p}-pulse, .{p}-blink {{ animation: none !important; }}
      .{p}-draw {{ animation: none; stroke-dashoffset: 0; }}
    }}"""


def delay(p, i, step=0.08, start=0.0):
    return f'style="animation-delay:{start + i * step:.2f}s"'


def svg_open(p, h, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{esc(label)}">\n'
            f'<title>{esc(label)}</title>\n')


def card_bg(p, h, glow_x="80%", glow_color=None, rx=22):
    g = glow_color or T["secondary"]
    return f"""
  <defs>
    <linearGradient id="{p}-bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{T['bg1']}"/><stop offset="1" stop-color="{T['bg0']}"/>
    </linearGradient>
    <radialGradient id="{p}-glow" cx="{glow_x}" cy="20%" r="60%">
      <stop offset="0" stop-color="{g}" stop-opacity=".28"/><stop offset="1" stop-color="{g}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="{p}-grid" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M32 0H0V32" fill="none" stroke="{T['primary']}" stroke-opacity=".06"/>
    </pattern>
    <clipPath id="{p}-clip"><rect width="{W}" height="{h}" rx="{rx}"/></clipPath>
  </defs>
  <g clip-path="url(#{p}-clip)">
    <rect width="{W}" height="{h}" fill="url(#{p}-bg)"/>
    <rect width="{W}" height="{h}" fill="url(#{p}-grid)"/>
    <rect width="{W}" height="{h}" fill="url(#{p}-glow)"/>
  </g>
  <rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="{rx}" fill="none" stroke="{T['line']}"/>"""


def trace_border(p, h, color, rx=22, dur=8):
    per = 2 * (W + h)
    seg = per * 0.16
    return f"""
  <style>.{p}-trace {{ stroke-dasharray: {seg:.0f} {per - seg:.0f}; animation: {p}-trace {dur}s linear infinite; }}
  @keyframes {p}-trace {{ from {{ stroke-dashoffset: {per:.0f}; }} to {{ stroke-dashoffset: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{ .{p}-trace {{ display: none; }} }}</style>
  <rect class="{p}-trace" x="1" y="1" width="{W - 2}" height="{h - 2}" rx="{rx}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" opacity=".9"/>"""


def chip(p, x, y, label, color, i=0, start=0.6, size=13):
    w = text_w(label, size, mono=True) + 28
    return (f'<g class="{p}-pop" {delay(p, i, 0.07, start)}>'
            f'<rect x="{x}" y="{y}" width="{w:.0f}" height="32" rx="16" fill="{color}" fill-opacity=".1" stroke="{color}" stroke-opacity=".45"/>'
            f'<text class="{p}-mono" x="{x + w / 2:.0f}" y="{y + 21}" font-size="{size}" text-anchor="middle" fill="{T["text"]}">{esc(label)}</text></g>'), w


def write(name, svg):
    with open(os.path.join(ASSETS, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)


# ---------------------------------------------------------------- avatar
def avatar_data():
    """Embed the GitHub avatar (SVGs shown as <img> cannot load external files)."""
    src = C.get("avatar", "auto")
    user = C["username"]
    try:
        if src == "auto":
            if user.startswith("your-"):
                return None
            req = urllib.request.Request(f"https://github.com/{user}.png?size=360",
                                         headers={"User-Agent": "profile-builder"})
            data = urllib.request.urlopen(req, timeout=20).read()
            return "data:image/png;base64," + base64.b64encode(data).decode()
        if src:
            path = os.path.join(ROOT, src)
            ext = os.path.splitext(path)[1].lower().lstrip(".")
            mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "png")
            with open(path, "rb") as fh:
                return f"data:image/{mime};base64," + base64.b64encode(fh.read()).decode()
    except Exception as e:  # network hiccup → monogram fallback
        print(f"  ! avatar not embedded ({e}); using monogram", file=sys.stderr)
    return None


# ---------------------------------------------------------------- hero
def hero():
    p, h = "hr", 520
    name = C["name"]
    fs = min(78, int(620 / max(1, len(name) * 0.6)))
    roles = C["roles"]
    n = len(roles)
    slot = 3.2
    total = n * slot
    a = 100 / n
    rnd = random.Random(7)

    css = base_css(p) + f"""
    .{p}-blob {{ animation: {p}-drift 16s ease-in-out infinite alternate; transform-box: fill-box; transform-origin: center; }}
    .{p}-blob.b2 {{ animation-duration: 21s; animation-direction: alternate-reverse; }}
    .{p}-blob.b3 {{ animation-duration: 26s; }}
    @keyframes {p}-drift {{ 0% {{ transform: translate(0,0) scale(1); }} 50% {{ transform: translate(60px,-30px) scale(1.15); }} 100% {{ transform: translate(-40px,30px) scale(.95); }} }}
    .{p}-role {{ opacity: 0; animation: {p}-role {total}s infinite; }}
    @keyframes {p}-role {{
      0% {{ opacity: 0; transform: translateY(16px); }}
      {a * 0.12:.2f}% {{ opacity: 1; transform: none; }}
      {a * 0.86:.2f}% {{ opacity: 1; transform: none; }}
      {a:.2f}% {{ opacity: 0; transform: translateY(-16px); }}
      100% {{ opacity: 0; }} }}
    .{p}-float {{ animation: {p}-float 5s ease-in-out infinite; }}
    @keyframes {p}-float {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-12px); }} }}
    .{p}-tw {{ animation: {p}-tw 3s ease-in-out infinite; }}
    @keyframes {p}-tw {{ 0%,100% {{ opacity: .15; }} 50% {{ opacity: .9; }} }}
    .{p}-bounce {{ animation: {p}-bounce 1.8s ease-in-out infinite; }}
    @keyframes {p}-bounce {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(5px); }} }}
    @media (prefers-reduced-motion: reduce) {{
      .{p}-blob, .{p}-float, .{p}-tw, .{p}-bounce {{ animation: none; }}
      .{p}-role {{ animation: none; }} .{p}-role.r0 {{ opacity: 1; }}
    }}"""

    stars = "".join(
        f'<circle class="{p}-tw" cx="{rnd.randint(20, 1180)}" cy="{rnd.randint(20, 500)}" r="{rnd.choice([0.8, 1, 1.2, 1.6])}" '
        f'fill="{T["primary_light"]}" style="animation-delay:{rnd.random() * 3:.2f}s"/>'
        for _ in range(46))

    role_svgs = "".join(
        f'<text class="{p}-role {p}-sans r{i}" x="104" y="282" font-size="28" font-weight="600" fill="{T["text"]}" '
        f'style="animation-delay:{i * slot:.1f}s">{esc(r)}</text>' for i, r in enumerate(roles))

    tag_lines = wrap(C["tagline"], 62)[:2]
    tagline = "".join(
        f'<text class="{p}-sans" x="72" y="{330 + i * 28}" font-size="18" fill="{T["muted"]}">{esc(l)}</text>'
        for i, l in enumerate(tag_lines))

    chips, cx = "", 72
    for i, (label, dot) in enumerate([(C.get("status"), T["primary"]), (C.get("location"), T["secondary"])]):
        if not label:
            continue
        w = text_w(label, 13, True) + 52
        chips += (f'<g class="{p}-pop" {delay(p, i, .15, 1.2)}>'
                  f'<rect x="{cx}" y="402" width="{w:.0f}" height="36" rx="18" fill="{dot}" fill-opacity=".08" stroke="{dot}" stroke-opacity=".5"/>'
                  f'<circle class="{p}-pulse" cx="{cx + 20}" cy="420" r="4" fill="{dot}"/><circle cx="{cx + 20}" cy="420" r="4" fill="{dot}"/>'
                  f'<text class="{p}-mono" x="{cx + 34}" y="425" font-size="13" fill="{T["text"]}">{esc(label)}</text></g>')
        cx += w + 12

    # avatar
    ax, ay, r = 930, 258, 128
    av = avatar_data()
    if av:
        avatar = f'<image href="{av}" xlink:href="{av}" x="{ax - r}" y="{ay - r}" width="{2 * r}" height="{2 * r}" clip-path="url(#{p}-avclip)" preserveAspectRatio="xMidYMid slice"/>'
    else:
        initials = "".join(w[0] for w in name.split()[:2]).upper()
        avatar = (f'<circle cx="{ax}" cy="{ay}" r="{r}" fill="url(#{p}-avbg)"/>'
                  f'<text class="{p}-sans" x="{ax}" y="{ay + 30}" font-size="92" font-weight="800" text-anchor="middle" fill="url(#{p}-name)">{esc(initials)}</text>')

    planets = "".join(
        f'<circle cx="{ax + 196}" cy="{ay}" r="{rr}" fill="{c}" transform="rotate({ang} {ax} {ay})"/>'
        for ang, rr, c in [(0, 6, T["primary"]), (120, 4.5, T["secondary"]), (240, 5, T["tertiary"])])

    badges = ""
    spots = [(ax - 210, ay - 150), (ax + 150, ay - 175), (ax + 170, ay + 150), (ax - 230, ay + 120)]
    for i, b in enumerate(C.get("floating_badges", [])[:4]):
        bx, by = spots[i]
        bw = text_w(b, 15, True) + 30
        col = ACCENTS[i % len(ACCENTS)]
        badges += (f'<g class="{p}-float" style="animation-delay:{i * 1.1:.1f}s">'
                   f'<rect x="{bx}" y="{by}" width="{bw:.0f}" height="38" rx="11" fill="{T["bg1"]}" fill-opacity=".85" stroke="{col}" stroke-opacity=".7"/>'
                   f'<text class="{p}-mono" x="{bx + bw / 2:.0f}" y="{by + 25}" font-size="15" font-weight="700" text-anchor="middle" fill="{col}">{esc(b)}</text></g>')

    svg = svg_open(p, h, f"{name} — {', '.join(roles)}. {C['tagline']}") + f"""<style>{css}</style>
  <defs>
    <radialGradient id="{p}-bg" cx="70%" cy="35%" r="85%">
      <stop offset="0" stop-color="{T['bg2']}"/><stop offset=".55" stop-color="{T['bg1']}"/><stop offset="1" stop-color="{T['bg0']}"/>
    </radialGradient>
    <filter id="{p}-blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="60"/></filter>
    <filter id="{p}-glowf" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <linearGradient id="{p}-name" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{T['text']}"/><stop offset=".45" stop-color="{T['primary_light']}"/><stop offset=".8" stop-color="{T['primary']}"/><stop offset="1" stop-color="{T['secondary']}"/>
    </linearGradient>
    <linearGradient id="{p}-sheen" gradientUnits="userSpaceOnUse" x1="-300" y1="0" x2="-60" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="0 0;1000 0;1000 0" keyTimes="0;.35;1" dur="7s" begin="2s" repeatCount="indefinite"/>
    </linearGradient>
    <linearGradient id="{p}-ring" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{T['primary']}"/><stop offset=".5" stop-color="{T['secondary']}"/><stop offset="1" stop-color="{T['tertiary']}" stop-opacity=".2"/>
    </linearGradient>
    <radialGradient id="{p}-avbg"><stop offset="0" stop-color="{T['bg2']}"/><stop offset="1" stop-color="{T['bg0']}"/></radialGradient>
    <radialGradient id="{p}-halo"><stop offset="0" stop-color="{T['primary']}" stop-opacity=".45"/><stop offset="1" stop-color="{T['primary']}" stop-opacity="0"/></radialGradient>
    <pattern id="{p}-grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="{T['primary']}" stroke-opacity=".07"/></pattern>
    <radialGradient id="{p}-fade" cx="75%" cy="45%" r="55%"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
    <mask id="{p}-mask"><rect width="{W}" height="{h}" fill="url(#{p}-fade)"/></mask>
    <clipPath id="{p}-clip"><rect width="{W}" height="{h}" rx="24"/></clipPath>
    <clipPath id="{p}-avclip"><circle cx="{ax}" cy="{ay}" r="{r}"/></clipPath>
  </defs>
  <g clip-path="url(#{p}-clip)">
    <rect width="{W}" height="{h}" fill="url(#{p}-bg)"/>
    <g filter="url(#{p}-blur)">
      <ellipse class="{p}-blob" cx="880" cy="160" rx="260" ry="150" fill="{T['primary']}" opacity=".32"/>
      <ellipse class="{p}-blob b2" cx="1050" cy="420" rx="220" ry="140" fill="{T['secondary']}" opacity=".3"/>
      <ellipse class="{p}-blob b3" cx="240" cy="460" rx="300" ry="120" fill="{T['tertiary']}" opacity=".16"/>
    </g>
    <rect width="{W}" height="{h}" fill="url(#{p}-grid)" mask="url(#{p}-mask)"/>
    {stars}

    <g class="{p}-in" {delay(p, 0, 0, .1)}>
      <text class="{p}-mono" x="72" y="122" font-size="13" letter-spacing="4" fill="{T['primary']}">◆  {esc(C.get('kicker', 'HELLO, WORLD — I AM'))}</text>
    </g>
    <g class="{p}-in" {delay(p, 0, 0, .3)}>
      <text class="{p}-sans" x="68" y="{172 + fs * 0.55:.0f}" font-size="{fs}" font-weight="800" letter-spacing="-2" fill="url(#{p}-name)">{esc(name)}</text>
      <text class="{p}-sans" x="68" y="{172 + fs * 0.55:.0f}" font-size="{fs}" font-weight="800" letter-spacing="-2" fill="url(#{p}-sheen)" opacity=".55">{esc(name)}</text>
    </g>
    <g class="{p}-in" {delay(p, 0, 0, .55)}>
      <text class="{p}-mono" x="72" y="282" font-size="26" font-weight="700" fill="{T['primary']}">&gt;_</text>
      {role_svgs}
    </g>
    <g class="{p}-in" {delay(p, 0, 0, .8)}>{tagline}</g>
    {chips}
    <g class="{p}-in" {delay(p, 0, 0, 1.6)}>
      <path class="{p}-draw" d="M72 470 H520" stroke="url(#{p}-ring)" stroke-width="1.5"/>
      <g class="{p}-bounce"><text class="{p}-mono" x="72" y="496" font-size="11" letter-spacing="3" fill="{T['muted']}">SCROLL TO EXPLORE  ↓</text></g>
    </g>

    <g class="{p}-in" {delay(p, 0, 0, .4)}>
      <circle cx="{ax}" cy="{ay}" r="240" fill="url(#{p}-halo)"/>
      <circle cx="{ax}" cy="{ay}" r="196" fill="none" stroke="{T['secondary']}" stroke-opacity=".35" stroke-dasharray="2 9" stroke-linecap="round">
        <animateTransform attributeName="transform" type="rotate" from="360 {ax} {ay}" to="0 {ax} {ay}" dur="60s" repeatCount="indefinite"/>
      </circle>
      <g><animateTransform attributeName="transform" type="rotate" from="0 {ax} {ay}" to="360 {ax} {ay}" dur="24s" repeatCount="indefinite"/>{planets}</g>
      <circle cx="{ax}" cy="{ay}" r="162" fill="none" stroke="{T['primary']}" stroke-opacity=".5" stroke-dasharray="60 24 8 24" stroke-width="1.5">
        <animateTransform attributeName="transform" type="rotate" from="0 {ax} {ay}" to="360 {ax} {ay}" dur="30s" repeatCount="indefinite"/>
      </circle>
      <circle cx="{ax}" cy="{ay}" r="{r + 9}" fill="none" stroke="url(#{p}-ring)" stroke-width="4" filter="url(#{p}-glowf)">
        <animateTransform attributeName="transform" type="rotate" from="0 {ax} {ay}" to="360 {ax} {ay}" dur="8s" repeatCount="indefinite"/>
      </circle>
      {avatar}
      <circle cx="{ax}" cy="{ay}" r="{r}" fill="none" stroke="{T['bg0']}" stroke-width="3"/>
    </g>
    {badges}
  </g>
  <rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="24" fill="none" stroke="{T['line']}"/>
</svg>"""
    write("hero.svg", svg)


# ---------------------------------------------------------------- section titles
def title(idx, key, label, heading, tag):
    p, h = f"t{idx}", 120
    words = heading.split()
    head = " ".join(words[:-1])
    last = words[-1]
    css = base_css(p) + f"""
    .{p}-hex {{ animation: {p}-spin 14s linear infinite; transform-box: fill-box; transform-origin: center; }}
    @keyframes {p}-spin {{ to {{ transform: rotate(360deg); }} }}
    @media (prefers-reduced-motion: reduce) {{ .{p}-hex {{ animation: none; }} }}"""
    svg = svg_open(p, h, f"{idx:02d} {label} — {heading}") + f"""<style>{css}</style>
  <defs>
    <linearGradient id="{p}-g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{T['primary']}"/><stop offset="1" stop-color="{T['secondary']}"/></linearGradient>
    <linearGradient id="{p}-line" gradientUnits="userSpaceOnUse" x1="40" y1="0" x2="1160" y2="0">
      <stop offset="0" stop-color="{T['primary']}"/><stop offset=".5" stop-color="{T['secondary']}"/><stop offset="1" stop-color="{T['secondary']}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="{p}-sheen" gradientUnits="userSpaceOnUse" x1="-300" y1="0" x2="0" y2="0">
      <stop offset="0" stop-color="{T['primary']}"/><stop offset=".5" stop-color="{T['primary_light']}"/><stop offset="1" stop-color="{T['secondary']}"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="0 0;1400 0;1400 0" keyTimes="0;.45;1" dur="6s" begin="1s" repeatCount="indefinite"/>
    </linearGradient>
    <radialGradient id="{p}-dot"><stop offset="0" stop-color="#fff"/><stop offset=".4" stop-color="{T['primary_light']}" stop-opacity=".8"/><stop offset="1" stop-color="{T['primary']}" stop-opacity="0"/></radialGradient>
  </defs>
  <g class="{p}-in">
    <polygon class="{p}-hex" points="70,22 96,37 96,67 70,82 44,67 44,37" fill="none" stroke="url(#{p}-g)" stroke-width="1.5" stroke-dasharray="6 5"/>
    <polygon points="70,30 89,41 89,63 70,74 51,63 51,41" fill="{T['primary']}" fill-opacity=".1" stroke="url(#{p}-g)" stroke-width="1.5"/>
    <text class="{p}-mono" x="70" y="58" font-size="16" font-weight="700" text-anchor="middle" fill="{T['primary_light']}">{idx:02d}</text>
  </g>
  <g class="{p}-in" {delay(p, 0, 0, .15)}>
    <text class="{p}-mono" x="122" y="40" font-size="12" letter-spacing="3.5" fill="{T['primary']}">// {esc(label.upper())}</text>
    <text class="{p}-sans" x="120" y="80" font-size="38" font-weight="800" letter-spacing="-1" fill="{T['text']}">{esc(head)} <tspan fill="url(#{p}-sheen)">{esc(last)}</tspan></text>
  </g>
  <g class="{p}-in" {delay(p, 0, 0, .3)}>
    <text class="{p}-mono" x="1160" y="40" text-anchor="end" font-size="11" letter-spacing="2.5" fill="{T['muted']}">{esc(tag.upper())}</text>
  </g>
  <path class="{p}-draw" d="M40 106 H1160" stroke="url(#{p}-line)" stroke-width="1.2"/>
  <circle cx="40" cy="106" r="7" fill="url(#{p}-dot)" opacity="0">
    <animate attributeName="cx" values="40;1160" dur="5s" begin="2s" repeatCount="indefinite" calcMode="spline" keyTimes="0;1" keySplines=".45 0 .55 1"/>
    <animate attributeName="opacity" values="0;1;0" keyTimes="0;.2;1" dur="5s" begin="2s" repeatCount="indefinite"/>
  </circle>
</svg>"""
    write(f"title-{key}.svg", svg)


# ---------------------------------------------------------------- about (terminal)
def about():
    p = "ab"
    A = C["about"]
    bio = wrap(A["bio"], 64)
    facts = A["facts"]
    user = C["username"]
    lines = []  # (kind, payload)
    lines.append(("cmd", "whoami"))
    lines.append(("out", f'{C["name"]} — {C["roles"][0]}'))
    lines.append(("cmd", "cat about.md"))
    for l in bio:
        lines.append(("muted", l))
    lines.append(("cmd", "cat me.json"))
    lines.append(("brace", "{"))
    for i, (k, v) in enumerate(facts):
        lines.append(("kv", (k, v, i == len(facts) - 1)))
    lines.append(("brace", "}"))
    lines.append(("caret", ""))

    lh = 26
    top = 88
    h = top + len(lines) * lh + 40
    h = max(h, 420)

    out = []
    for i, (kind, pay) in enumerate(lines):
        y = top + i * lh
        d = f'style="animation-delay:{0.5 + i * 0.16:.2f}s"'
        if kind == "cmd":
            out.append(f'<text class="{p}-mono {p}-in" {d} x="40" y="{y}" font-size="15"><tspan fill="{T["primary"]}">❯</tspan> <tspan fill="{T["secondary"]}">~/{esc(user)}</tspan> <tspan fill="{T["text"]}">{esc(pay)}</tspan></text>')
        elif kind == "out":
            out.append(f'<text class="{p}-sans {p}-in" {d} x="40" y="{y}" font-size="17" font-weight="700" fill="{T["primary_light"]}">{esc(pay)}</text>')
        elif kind == "muted":
            out.append(f'<text class="{p}-sans {p}-in" {d} x="40" y="{y}" font-size="15.5" fill="{T["muted"]}">{esc(pay)}</text>')
        elif kind == "brace":
            out.append(f'<text class="{p}-mono {p}-in" {d} x="40" y="{y}" font-size="15" fill="{T["text"]}">{pay}</text>')
        elif kind == "kv":
            k, v, last = pay
            if isinstance(v, list):
                val = (f'<tspan fill="{T["text"]}">[</tspan>' +
                       f'<tspan fill="{T["text"]}">, </tspan>'.join(f'<tspan fill="{T["accent"]}">"{esc(x)}"</tspan>' for x in v) +
                       f'<tspan fill="{T["text"]}">]</tspan>')
            else:
                val = f'<tspan fill="{T["accent"]}">"{esc(v)}"</tspan>'
            comma = "" if last else f'<tspan fill="{T["text"]}">,</tspan>'
            out.append(f'<text class="{p}-mono {p}-in" {d} x="64" y="{y}" font-size="15"><tspan fill="{T["tertiary"]}">"{esc(k)}"</tspan><tspan fill="{T["text"]}">: </tspan>{val}{comma}</text>')
        elif kind == "caret":
            out.append(f'<g class="{p}-in" {d}><text class="{p}-mono" x="40" y="{y}" font-size="15"><tspan fill="{T["primary"]}">❯</tspan></text>'
                       f'<rect class="{p}-blink" x="58" y="{y - 14}" width="9" height="18" fill="{T["primary"]}"/></g>')

    # right panel: NOW
    nx = 800
    now = "".join(
        f'<g class="{p}-in" {delay(p, i, .15, 1.0)}>'
        f'<circle class="{p}-pulse" cx="{nx + 34}" cy="{150 + i * 52}" r="5" fill="{ACCENTS[i % 4]}" style="animation-delay:{i * .4:.1f}s"/>'
        f'<circle cx="{nx + 34}" cy="{150 + i * 52}" r="5" fill="{ACCENTS[i % 4]}"/>'
        + "".join(f'<text class="{p}-sans" x="{nx + 54}" y="{155 + i * 52 + j * 19}" font-size="15" fill="{T["text"]}">{esc(l)}</text>'
                  for j, l in enumerate(wrap(item, 34)[:2]))
        + '</g>'
        for i, item in enumerate(A["now"][:5]))

    svg = svg_open(p, h, f"About {C['name']}: {A['bio']} Currently: {'; '.join(A['now'])}") + f"<style>{base_css(p)}</style>" + card_bg(p, h, "90%", T["primary"]) + f"""
  <rect x="0" y="0" width="{W}" height="46" rx="22" fill="{T['bg2']}" fill-opacity=".6" clip-path="url(#{p}-clip)"/>
  <rect x="0" y="23" width="{W}" height="23" fill="{T['bg2']}" fill-opacity=".6" clip-path="url(#{p}-clip)"/>
  <circle cx="30" cy="23" r="6.5" fill="#FF5F57"/><circle cx="52" cy="23" r="6.5" fill="#FEBC2E"/><circle cx="74" cy="23" r="6.5" fill="#28C840"/>
  <text class="{p}-mono" x="600" y="28" font-size="12.5" text-anchor="middle" fill="{T['muted']}">{esc(user)}@github: ~ — zsh</text>
  <path d="M0 46 H{W}" stroke="{T['line']}"/>
  {''.join(out)}
  <path d="M{nx - 10} 70 V{h - 30}" stroke="{T['line']}" stroke-dasharray="3 6"/>
  <g class="{p}-in" {delay(p, 0, 0, .8)}>
    <text class="{p}-mono" x="{nx + 20}" y="100" font-size="12" letter-spacing="3.5" fill="{T['primary']}">◉ RIGHT NOW</text>
  </g>
  {now}
</svg>"""
    write("about.svg", svg)


# ---------------------------------------------------------------- highlights
def highlights():
    p, h = "hl", 210
    items = C["highlights"][:4]
    n = len(items)
    gap = 20
    cw = (W - 2 * 0 - gap * (n - 1)) / n
    cards = []
    for i, it in enumerate(items):
        x = i * (cw + gap)
        col = ACCENTS[i % 4]
        cards.append(f"""
  <g class="{p}-pop" {delay(p, i, .15, .2)}>
    <rect x="{x + .5:.1f}" y=".5" width="{cw - 1:.1f}" height="{h - 1}" rx="20" fill="url(#{p}-bg)" stroke="{T['line']}"/>
    <rect x="{x + .5:.1f}" y=".5" width="{cw - 1:.1f}" height="{h - 1}" rx="20" fill="url(#{p}-g{i})"/>
    <text class="{p}-sans" x="{x + 30:.1f}" y="92" font-size="52" font-weight="800" letter-spacing="-2" fill="{col}">{esc(it['value'])}</text>
    <text class="{p}-sans" x="{x + 32:.1f}" y="128" font-size="17" font-weight="600" fill="{T['text']}">{esc(it['label'])}</text>
    <text class="{p}-mono" x="{x + 32:.1f}" y="152" font-size="12" letter-spacing="1" fill="{T['muted']}">{esc(it.get('sub', ''))}</text>
    <rect x="{x + 32:.1f}" y="176" width="{cw - 64:.1f}" height="4" rx="2" fill="{T['line']}"/>
    <rect x="{x + 32:.1f}" y="176" width="{cw - 64:.1f}" height="4" rx="2" fill="{col}" class="{p}-bar" style="animation-delay:{.6 + i * .2:.1f}s"/>
  </g>""")
    grads = "".join(
        f'<radialGradient id="{p}-g{i}" cx="85%" cy="10%" r="80%"><stop offset="0" stop-color="{ACCENTS[i % 4]}" stop-opacity=".22"/><stop offset="1" stop-color="{ACCENTS[i % 4]}" stop-opacity="0"/></radialGradient>'
        for i in range(n))
    css = base_css(p) + f"""
    .{p}-bar {{ transform-box: fill-box; transform-origin: left; animation: {p}-bar 2.4s cubic-bezier(.65,0,.35,1) both, {p}-shine 3s ease-in-out 3s infinite; }}
    @keyframes {p}-bar {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
    @keyframes {p}-shine {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: .45; }} }}
    @media (prefers-reduced-motion: reduce) {{ .{p}-bar {{ animation: none; }} }}"""
    label = "; ".join(f"{i['value']} {i['label']}" for i in items)
    svg = svg_open(p, h, f"Highlights: {label}") + f"""<style>{css}</style>
  <defs><linearGradient id="{p}-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{T['bg1']}"/><stop offset="1" stop-color="{T['bg0']}"/></linearGradient>{grads}</defs>
  {''.join(cards)}
</svg>"""
    write("highlights.svg", svg)


# ---------------------------------------------------------------- projects
def project(i, pr):
    p, h = f"p{i}", 390
    col = ACCENTS[i % 4]
    summary = wrap(pr["summary"], 60)
    built = wrap(pr["built"], 74)
    if len(summary) > 2 or len(built) > 3:
        print(f"  ! project '{pr['title']}': shorten summary (max ~120 chars) or built (max ~220 chars)", file=sys.stderr)
    summary, built = summary[:2], built[:3]
    y0 = 186
    body = "".join(f'<text class="{p}-sans" x="56" y="{y0 + k * 26}" font-size="18" fill="{T["text"]}" fill-opacity=".86">{esc(l)}</text>' for k, l in enumerate(summary))
    yb = y0 + len(summary) * 26 + 18
    body += "".join(
        f'<text class="{p}-mono" x="{56 if k == 0 else 122}" y="{yb + k * 22}" font-size="13.5" fill="{T["muted"]}">'
        + (f'<tspan fill="{col}">BUILT ›</tspan> ' if k == 0 else '')
        + f'{esc(l)}</text>' for k, l in enumerate(built))
    chips, cx = "", 56
    for k, s in enumerate(pr["stack"][:6]):
        c, w = chip(p, cx, 322, s, col, k, .7)
        if cx + w > 760:
            break
        chips += c
        cx += w + 10
    metrics = ""
    for k, (v, l) in enumerate(pr.get("metrics", [])[:3]):
        my = 55 + k * 96
        metrics += (f'<g class="{p}-pop" {delay(p, k, .15, .5)}>'
                    f'<rect x="820" y="{my}" width="330" height="82" rx="16" fill="{col}" fill-opacity=".06" stroke="{col}" stroke-opacity=".3"/>'
                    f'<rect x="820" y="{my + 18}" width="4" height="46" rx="2" fill="{col}"/>'
                    f'<text class="{p}-sans" x="846" y="{my + 46}" font-size="32" font-weight="800" letter-spacing="-1" fill="{col}">{esc(v)}</text>'
                    f'<text class="{p}-mono" x="848" y="{my + 67}" font-size="11.5" letter-spacing="2" fill="{T["muted"]}">{esc(l.upper())}</text></g>')
    label = f"{pr['title']}: {pr['summary']} {pr['built']} Stack: {', '.join(pr['stack'])}."
    svg = svg_open(p, h, label) + f"<style>{base_css(p)}</style>" + card_bg(p, h, "85%", col) + trace_border(p, h, col) + f"""
  <text class="{p}-sans" x="1180" y="120" font-size="200" font-weight="900" text-anchor="end" fill="{col}" fill-opacity=".04">{i + 1:02d}</text>
  <g class="{p}-in" {delay(p, 0, 0, .1)}>
    <text class="{p}-mono" x="56" y="62" font-size="12.5" letter-spacing="3" fill="{col}">{i + 1:02d} · {esc(pr['kicker'])}</text>
    <text class="{p}-sans" x="53" y="130" font-size="50" font-weight="800" letter-spacing="-1.5" fill="{T['text']}">{esc(pr['title'])}</text>
    <path class="{p}-draw" d="M56 150 H220" stroke="{col}" stroke-width="3" stroke-linecap="round"/>
  </g>
  <g class="{p}-in" {delay(p, 0, 0, .3)}>{body}</g>
  {chips}
  {metrics}
</svg>"""
    write(f"project-{i + 1}.svg", svg)


# ---------------------------------------------------------------- tech stack
def stack():
    p = "sk"
    groups = C["skills"]
    rows = []
    y = 56
    maxw = W - 300 - 40
    for gi, (g, items) in enumerate(groups):
        col = ACCENTS[gi % 4]
        line, cx, row_y = [], 0, y
        parts = []
        for k, s in enumerate(items):
            w = text_w(s, 13, True) + 28
            if cx + w > maxw:
                cx = 0
                row_y += 44
            c, _ = chip(p, 300 + cx, row_y, s, col, gi * 3 + k, .3)
            parts.append(c)
            cx += w + 10
        rows.append(f"""
  <g class="{p}-in" {delay(p, gi, .12, .2)}>
    <circle cx="64" cy="{y + 16}" r="7" fill="{T['bg0']}" stroke="{col}" stroke-width="2"/>
    <circle class="{p}-pulse" cx="64" cy="{y + 16}" r="3" fill="{col}" style="animation-delay:{gi * .3:.1f}s"/>
    <text class="{p}-sans" x="88" y="{y + 22}" font-size="18" font-weight="700" fill="{T['text']}">{esc(g)}</text>
    <text class="{p}-mono" x="88" y="{y + 42}" font-size="11" letter-spacing="1.5" fill="{T['muted']}">{len(items):02d} TOOLS</text>
  </g>{''.join(parts)}""")
        y = row_y + 44 + 30
    h = y + 10
    css = base_css(p)
    label = "Tech stack. " + " ".join(f"{g}: {', '.join(i)}." for g, i in groups)
    svg = svg_open(p, h, label) + f"<style>{css}</style>" + card_bg(p, h, "95%", T["secondary"]) + f"""
  <defs><linearGradient id="{p}-spine" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{T['primary']}"/><stop offset="1" stop-color="{T['tertiary']}" stop-opacity=".2"/></linearGradient>
  <radialGradient id="{p}-dot"><stop offset="0" stop-color="#fff"/><stop offset=".4" stop-color="{T['primary_light']}"/><stop offset="1" stop-color="{T['primary']}" stop-opacity="0"/></radialGradient></defs>
  <path class="{p}-draw" d="M64 40 V{h - 40}" stroke="url(#{p}-spine)" stroke-width="1.5"/>
  <circle cx="64" cy="40" r="8" fill="url(#{p}-dot)">
    <animate attributeName="cy" values="40;{h - 40}" dur="5s" repeatCount="indefinite" calcMode="spline" keyTimes="0;1" keySplines=".45 0 .55 1"/>
    <animate attributeName="opacity" values="0;1;0" dur="5s" repeatCount="indefinite"/>
  </circle>
  {''.join(rows)}
</svg>"""
    write("stack.svg", svg)


# ---------------------------------------------------------------- certifications
def certs():
    p = "ce"
    items = C.get("certifications", [])
    if not items:
        return False
    h = 40 + len(items) * 60 + 28
    out = []
    for k, it in enumerate(items):
        name, issuer = it[0], it[1]
        year = it[2] if len(it) > 2 else ""
        x, y = 40, 40 + k * 60
        col = ACCENTS[k % 4]
        out.append(f"""<g class="{p}-in" {delay(p, k, .1, .2)}>
    <rect x="{x}" y="{y}" width="1120" height="48" rx="12" fill="{col}" fill-opacity=".05" stroke="{T['line']}"/>
    <text class="{p}-mono" x="{x + 22}" y="{y + 30}" font-size="13" fill="{col}">{k + 1:02d}</text>
    <circle cx="{x + 70}" cy="{y + 24}" r="11" fill="{col}" fill-opacity=".15" stroke="{col}"/>
    <path d="M{x + 65} {y + 24} l4 4 l7 -8" fill="none" stroke="{col}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <text class="{p}-sans" x="{x + 96}" y="{y + 30}" font-size="16" font-weight="600" fill="{T['text']}">{esc(name)}</text>
    <text class="{p}-mono" x="{x + 1030}" y="{y + 29}" font-size="11.5" text-anchor="end" letter-spacing="1.2" fill="{T['muted']}">{esc(issuer.upper())}</text>
    <rect x="{x + 1046}" y="{y + 12}" width="56" height="24" rx="12" fill="{col}" fill-opacity=".12"/>
    <text class="{p}-mono" x="{x + 1074}" y="{y + 28}" font-size="12" text-anchor="middle" fill="{col}">{esc(year)}</text>
  </g>""")
    label = "Certifications: " + "; ".join(f"{it[0]} ({it[1]})" for it in items)
    svg = svg_open(p, h, label) + f"<style>{base_css(p)}</style>" + card_bg(p, h, "10%", T["tertiary"]) + "".join(out) + "\n</svg>"
    write("certifications.svg", svg)
    return True


# ---------------------------------------------------------------- marquee
def marquee():
    p, h = "mq", 64
    orgs = C.get("orgs", [])
    if not orgs:
        return False
    fs, ls = 13, 2.5
    items, x = [], 0
    for o in orgs:
        label = o.upper()
        items.append((x, label))
        x += len(label) * (fs * 0.61 + ls) + 34
        items.append((x, "✦"))
        x += 34
    L = x
    def copy(off):
        return "".join(
            f'<text class="{p}-mono" x="{off + ix:.0f}" y="38" font-size="{fs}" letter-spacing="{ls}" '
            f'fill="{T["accent"] if t == "✦" else T["muted"]}">{esc(t)}</text>' for ix, t in items)
    reps = int(W // L) + 2
    css = base_css(p) + f"""
    .{p}-run {{ animation: {p}-run {L / 45:.1f}s linear infinite; }}
    @keyframes {p}-run {{ to {{ transform: translateX(-{L:.0f}px); }} }}
    @media (prefers-reduced-motion: reduce) {{ .{p}-run {{ animation: none; }} }}"""
    svg = svg_open(p, h, "Worked and competed with: " + ", ".join(orgs)) + f"""<style>{css}</style>
  <defs>
    <linearGradient id="{p}-fade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#000"/><stop offset=".12" stop-color="#fff"/><stop offset=".88" stop-color="#fff"/><stop offset="1" stop-color="#000"/>
    </linearGradient>
    <mask id="{p}-mask"><rect width="{W}" height="{h}" fill="url(#{p}-fade)"/></mask>
    <clipPath id="{p}-clip"><rect width="{W}" height="{h}" rx="16"/></clipPath>
  </defs>
  <rect width="{W}" height="{h}" rx="16" fill="{T['bg1']}"/>
  <g clip-path="url(#{p}-clip)" mask="url(#{p}-mask)">
    <g class="{p}-run">{''.join(copy(r * L + 20) for r in range(reps))}</g>
  </g>
  <rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="16" fill="none" stroke="{T['line']}"/>
</svg>"""
    write("marquee.svg", svg)
    return True


# ---------------------------------------------------------------- journey timeline
def journey():
    p = "jr"
    items = C.get("journey", [])
    if not items:
        return False
    kinds = {"achievement": T["accent"], "hackathon": T["primary"], "work": T["secondary"],
             "research": T["tertiary"], "project": T["primary_light"], "education": T["secondary"]}
    rh = 72
    h = 48 + len(items) * rh + 16
    spine = 250
    rows = []
    for k, (date, kind, ttl, org) in enumerate(items):
        y = 40 + k * rh
        col = kinds.get(kind.lower(), T["primary"])
        cw = text_w(kind.upper(), 11, True) + 26
        rows.append(f"""<g class="{p}-in" {delay(p, k, .11, .3)}>
    <text class="{p}-mono" x="{spine - 28}" y="{y + 34}" font-size="12.5" text-anchor="end" letter-spacing="1.5" fill="{T['muted']}">{esc(date)}</text>
    <circle cx="{spine}" cy="{y + 30}" r="9" fill="{T['bg0']}" stroke="{col}" stroke-width="2"/>
    <circle class="{p}-pulse" cx="{spine}" cy="{y + 30}" r="3.5" fill="{col}" style="animation-delay:{k * .25:.2f}s"/>
    <rect x="{spine + 30}" y="{y + 2}" width="{1160 - spine - 30}" height="56" rx="14" fill="{col}" fill-opacity=".05" stroke="{T['line']}"/>
    <rect x="{spine + 48}" y="{y + 18}" width="{cw:.0f}" height="24" rx="12" fill="{col}" fill-opacity=".14"/>
    <text class="{p}-mono" x="{spine + 48 + cw / 2:.0f}" y="{y + 34}" font-size="11" text-anchor="middle" letter-spacing="1" fill="{col}">{esc(kind.upper())}</text>
    <text class="{p}-sans" x="{spine + 62 + cw:.0f}" y="{y + 36}" font-size="17" font-weight="700" fill="{T['text']}">{esc(ttl)}</text>
    <text class="{p}-mono" x="1140" y="{y + 35}" font-size="11.5" text-anchor="end" letter-spacing="1.2" fill="{T['muted']}">{esc(org.upper())}</text>
  </g>""")
    label = "Journey: " + "; ".join(f"{d} — {t}, {o}" for d, _, t, o in items)
    svg = svg_open(p, h, label) + f"<style>{base_css(p)}</style>" + card_bg(p, h, "100%", T["tertiary"]) + f"""
  <defs><linearGradient id="{p}-spine" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{T['primary']}"/><stop offset=".5" stop-color="{T['secondary']}"/><stop offset="1" stop-color="{T['tertiary']}" stop-opacity=".2"/></linearGradient>
  <radialGradient id="{p}-dot"><stop offset="0" stop-color="#fff"/><stop offset=".4" stop-color="{T['primary_light']}"/><stop offset="1" stop-color="{T['primary']}" stop-opacity="0"/></radialGradient></defs>
  <path class="{p}-draw" d="M{spine} 40 V{h - 30}" stroke="url(#{p}-spine)" stroke-width="2"/>
  <circle cx="{spine}" cy="40" r="9" fill="url(#{p}-dot)">
    <animate attributeName="cy" values="40;{h - 30}" dur="7s" repeatCount="indefinite" calcMode="spline" keyTimes="0;1" keySplines=".45 0 .55 1"/>
    <animate attributeName="opacity" values="0;1;0" dur="7s" repeatCount="indefinite"/>
  </circle>
  {''.join(rows)}
</svg>"""
    write("journey.svg", svg)
    return True


# ---------------------------------------------------------------- footer
def footer():
    p, h = "ft", 260
    def wave(amp, length, y):
        d = f"M0 {y}"
        for x in range(0, W * 2 + length, length):
            d += f" Q{x + length / 4} {y - amp} {x + length / 2} {y} T{x + length} {y}"
        return d
    css = base_css(p) + f"""
    .{p}-w {{ animation: {p}-w 12s linear infinite; }} .{p}-w.w2 {{ animation-duration: 18s; animation-direction: reverse; }} .{p}-w.w3 {{ animation-duration: 26s; }}
    @keyframes {p}-w {{ to {{ transform: translateX(-{W}px); }} }}
    @media (prefers-reduced-motion: reduce) {{ .{p}-w {{ animation: none; }} }}"""
    svg = svg_open(p, h, f"{C['name']} — {C['footer_quote']} Thanks for visiting.") + f"<style>{css}</style>" + card_bg(p, h, "50%", T["primary"]) + f"""
  <defs><linearGradient id="{p}-name" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{T['primary_light']}"/><stop offset=".5" stop-color="{T['primary']}"/><stop offset="1" stop-color="{T['secondary']}"/></linearGradient></defs>
  <g clip-path="url(#{p}-clip)">
    <path class="{p}-w" d="{wave(18, 300, 200)} V{h} H0 Z" fill="{T['primary']}" fill-opacity=".10"/>
    <path class="{p}-w w2" d="{wave(14, 240, 214)} V{h} H0 Z" fill="{T['secondary']}" fill-opacity=".10"/>
    <path class="{p}-w w3" d="{wave(10, 400, 228)} V{h} H0 Z" fill="{T['tertiary']}" fill-opacity=".10"/>
  </g>
  <g class="{p}-in">
    <text class="{p}-mono" x="600" y="56" font-size="12" letter-spacing="4" text-anchor="middle" fill="{T['primary']}">✦  THANKS FOR SCROLLING  ✦</text>
  </g>
  <g class="{p}-in" {delay(p, 0, 0, .25)}>
    <text class="{p}-sans" x="600" y="116" font-size="46" font-weight="800" letter-spacing="-1.5" text-anchor="middle" fill="url(#{p}-name)">{esc(C['name'])}</text>
  </g>
  <g class="{p}-in" {delay(p, 0, 0, .5)}>
    <text class="{p}-sans" x="600" y="152" font-size="18" font-style="italic" text-anchor="middle" fill="{T['muted']}">{esc(C['footer_quote'])}</text>
  </g>
</svg>"""
    write("footer.svg", svg)


# ---------------------------------------------------------------- README
def badge(label, msg, logo, href, color=None):
    color = hx(color or T["primary_deep"])
    m = urllib.parse.quote(msg.replace("-", "--").replace("_", "__").replace(" ", "_"))
    l = urllib.parse.quote(label.replace("-", "--").replace("_", "__").replace(" ", "_"))
    src = (f"https://img.shields.io/badge/{l}-{m}-{color}?style=for-the-badge&labelColor={hx(T['bg1'])}"
           f"&logo={logo}&logoColor={hx(T['primary_light'])}")
    return f'  <a href="{esc(href)}"><img src="{src}" alt="{esc(label)}: {esc(msg)}"></a>'


def link_badges():
    L, out = C["links"], []
    if L.get("portfolio"):
        out.append(badge("Portfolio", "Visit live site", "googlechrome", L["portfolio"]))
    if L.get("linkedin"):
        # Simple Icons dropped the LinkedIn logo, so ship our own as a data URI.
        li = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{T["primary_light"]}" d="M20.45 20.45h-3.56v-5.57'
              'c0-1.33-.02-3.04-1.85-3.04-1.86 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 '
              '5.46v6.28ZM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13ZM7.12 20.45H3.56V9h3.56v11.45ZM22.22 0H1.77C.79 0 0 .77 0 '
              '1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0Z"/></svg>')
        logo = "data:image/svg%2bxml;base64," + base64.b64encode(li.encode()).decode()
        out.append(badge("LinkedIn", L["linkedin"], logo, f"https://www.linkedin.com/in/{L['linkedin']}/"))
    if L.get("email"):
        out.append(badge("Email", L["email"], "gmail", f"mailto:{L['email']}"))
    if L.get("leetcode"):
        out.append(badge("LeetCode", L["leetcode"], "leetcode", f"https://leetcode.com/u/{L['leetcode']}/"))
    if L.get("twitter"):
        out.append(badge("X", "@" + L["twitter"], "x", f"https://x.com/{L['twitter']}"))
    if L.get("resume"):
        out.append(badge("Resume", "Download", "readthedocs", L["resume"], T["secondary"]))
    return "\n".join(out)


SECTIONS = [  # key, label, heading, right-hand tag
    ("about", "About", None, "who I am"),
    ("highlights", "Highlights", "Numbers that speak.", "at a glance"),
    ("work", "Featured work", "Built, shipped, measured.", "selected projects"),
    ("journey", "Journey", "Milestones so far.", "timeline"),
    ("stack", "Toolkit", "What I build with.", "tech stack"),
    ("activity", "Activity", "Always shipping.", "github pulse"),
    ("certs", "Certifications", "Certified, still curious.", "credentials"),
    ("connect", "Connect", "Let's build something great.", "say hello"),
]


def readme(active):
    u = C["username"]
    nm = C["name"]
    bg, tc, tx, ic = hx(T["bg1"]), hx(T["primary_light"]), hx(T["muted"]), hx(T["secondary"])
    stats = (f"https://github-readme-stats.vercel.app/api?username={u}&show_icons=true&hide_border=true&border_radius=16"
             f"&bg_color={bg}&title_color={tc}&text_color={tx}&icon_color={ic}&ring_color={hx(T['primary'])}&include_all_commits=true&count_private=true&rank_icon=github")
    langs = (f"https://github-readme-stats.vercel.app/api/top-langs/?username={u}&layout=compact&hide_border=true&border_radius=16"
             f"&bg_color={bg}&title_color={tc}&text_color={tx}&langs_count=8")
    streak = (f"https://streak-stats.demolab.com/?user={u}&hide_border=true&border_radius=16&background={bg}"
              f"&ring={hx(T['primary'])}&fire={hx(T['tertiary'])}&currStreakNum={hx(T['text'])}&sideNums={hx(T['text'])}"
              f"&currStreakLabel={tc}&sideLabels={tx}&dates={tx}&stroke={hx(T['line'])}")
    views = f"https://komarev.com/ghpvc/?username={u}&label=PROFILE%20VIEWS&color={hx(T['primary_deep'])}&style=for-the-badge"
    link0 = C["links"].get("portfolio") or f"https://github.com/{u}"

    def title_img(key):
        idx, label, heading = active[key]
        return f'<img src="assets/title-{key}.svg" width="100%" alt="{idx:02d} {esc(label)} — {esc(heading)}">'

    sec = [f'<a href="{esc(link0)}">\n  <img src="assets/hero.svg" width="100%" alt="{esc(nm)} — {esc(", ".join(C["roles"]))}. {esc(C["tagline"])}">\n</a>',
           f'<p align="center">\n{link_badges()}\n  <img src="{views}" alt="Profile views">\n</p>']
    if os.path.exists(os.path.join(ASSETS, "marquee.svg")) and C.get("orgs"):
        sec.append(f'<img src="assets/marquee.svg" width="100%" alt="Worked and competed with: {esc(", ".join(C["orgs"]))}">')

    for key in active:
        sec.append(title_img(key))
        if key == "about":
            sec.append(f'<img src="assets/about.svg" width="100%" alt="{esc(C["about"]["bio"])}">')
        elif key == "highlights":
            sec.append(f'<img src="assets/highlights.svg" width="100%" alt="{esc("; ".join(h["value"] + " " + h["label"] for h in C["highlights"]))}">')
        elif key == "work":
            for i, pr in enumerate(C["projects"]):
                target = pr.get("case_study") or pr.get("repo") or pr.get("demo")
                img = f'<img src="assets/project-{i + 1}.svg" width="100%" alt="{esc(pr["title"])}: {esc(pr["summary"])}">'
                sec.append(f'<a href="{esc(target)}">{img}</a>' if target else img)
                btns = []
                if pr.get("case_study"):
                    btns.append(badge("Case study", pr["title"], "readthedocs", pr["case_study"], T["secondary"]))
                if pr.get("demo"):
                    btns.append(badge("Live demo", "Open app", "streamlit" if "streamlit" in pr["demo"] else "render", pr["demo"], T["secondary"]))
                if pr.get("repo"):
                    btns.append(badge("Source", "GitHub", "github", pr["repo"], T["secondary"]))
                if btns:
                    sec.append('<p align="center">\n' + "\n".join(btns) + "\n</p>")
        elif key == "journey":
            sec.append('<img src="assets/journey.svg" width="100%" alt="Journey timeline">')
        elif key == "stack":
            sec.append('<img src="assets/stack.svg" width="100%" alt="Tech stack">')
        elif key == "activity":
            sec.append(f"""<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/{u}/{u}/output/snake-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/{u}/{u}/output/snake-light.svg">
  <img src="https://raw.githubusercontent.com/{u}/{u}/output/snake-dark.svg" width="100%" alt="Snake eating my GitHub contribution graph">
</picture>""")
            sec.append(f"""<p align="center">
  <img src="{stats}" height="175" alt="GitHub stats for {esc(u)}">
  <img src="{langs}" height="175" alt="Most used languages">
</p>
<p align="center">
  <img src="{streak}" height="175" alt="Contribution streak">
</p>""")
        elif key == "certs":
            sec.append('<img src="assets/certifications.svg" width="100%" alt="Certifications">')
        elif key == "connect":
            sec.append(f'<p align="center">\n{link_badges()}\n</p>')

    sec.append(f'<a href="{esc(link0)}">\n  <img src="assets/footer.svg" width="100%" alt="{esc(nm)} — {esc(C["footer_quote"])}">\n</a>')
    body = "\n\n".join(sec) + "\n"
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    return body


# ---------------------------------------------------------------- build
def main():
    for old in os.listdir(ASSETS):  # start clean so removed sections don't linger
        if old.endswith(".svg"):
            os.remove(os.path.join(ASSETS, old))
    hero()
    about()
    highlights()
    for i, pr in enumerate(C["projects"]):
        project(i, pr)
    stack()
    marquee()
    footer()
    present = {"journey": journey(), "certs": certs()}

    active, idx = {}, 0
    for key, label, heading, tag in SECTIONS:
        if not present.get(key, True):
            continue
        idx += 1
        heading = heading or f"Hello, I'm {C['first_name']}."
        title(idx, key, label, heading, tag)
        active[key] = (idx, label, heading)
    body = readme(active)

    # preview page that mimics GitHub's dark profile column
    with open(os.path.join(ROOT, "preview.html"), "w", encoding="utf-8") as f:
        f.write(f"""<!doctype html><meta charset="utf-8"><title>Profile preview</title>
<style>body{{margin:0;background:#0d1117;color:#e6edf3;font-family:-apple-system,Segoe UI,sans-serif}}
.col{{max-width:896px;margin:32px auto;padding:24px;border:1px solid #30363d;border-radius:6px}}
img{{max-width:100%}} p{{margin:8px 0 16px}} a img{{vertical-align:middle}} p img{{margin:2px}}
</style><div class="col">{body}</div>""")

    leftovers = [k for k, v in [("username", C["username"]), ("name", C["name"]), ("email", C["links"].get("email", ""))]
                 if v.lower().startswith("your") or "example.com" in v]
    print(f"✓ built {len(os.listdir(ASSETS))} SVGs + README.md + preview.html")
    if leftovers:
        print("! still placeholders in profile.json:", ", ".join(leftovers))


if __name__ == "__main__":
    main()
