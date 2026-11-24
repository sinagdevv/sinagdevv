"""Generates the dark-fantasy monochrome README assets (static + SMIL-animated SVG).

Run: python scripts/build-codex.py
All text is converted to outlines so rendering never depends on viewer fonts.
Live-data panels (chronicle, footprints) are produced by scripts/sync-profile.mjs.
"""
import json, math, random, re
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / 'assets'
BLACK, OBS, CHAR, ASH, SIL, OFF = '#000000', '#080808', '#141414', '#666666', '#BFBFBF', '#E5E5E5'


class Face:
    def __init__(self, path, tag):
        self.tag = tag
        self.f = TTFont(path)
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f['head'].unitsPerEm

    def _adv(self, ch):
        return self.gs[self.cmap.get(ord(ch), '.notdef')].width

    def width(self, text, size, ls=0):
        return sum(self._adv(c) for c in text) * size / self.upm + ls * (len(text) - 1)

    def path(self, text, size, x, y, anchor='middle', ls=0, fill=OFF, extra=''):
        w = self.width(text, size, ls)
        cx = x - (w / 2 if anchor == 'middle' else w if anchor == 'end' else 0)
        s = size / self.upm
        uses, pen_x = [], 0.0
        for ch in text:
            name = self.cmap.get(ord(ch), '.notdef')
            gid = f'{self.tag}{self.f.getGlyphID(name)}'
            if gid not in DEFS and ch != ' ':
                pen = SVGPathPen(self.gs, ntos=lambda v: f'{v:.0f}')
                self.gs[name].draw(pen)
                if pen.getCommands():
                    DEFS[gid] = pen.getCommands()
            if gid in DEFS:
                uses.append(f'<use href="#{gid}" x="{pen_x:.0f}"/>')
            pen_x += self.gs[name].width + ls / s
        return f'<g transform="translate({cx:.1f} {y}) scale({s:.5f} {-s:.5f})" fill="{fill}" {extra}>{"".join(uses)}</g>'

    def wrap(self, text, size, maxw, ls=0):
        lines, cur = [], ''
        for word in text.split():
            t = f'{cur} {word}'.strip()
            if self.width(t, size, ls) > maxw and cur:
                lines.append(cur); cur = word
            else:
                cur = t
        return lines + [cur]


DEFS = {}
BLACKLETTER = Face(ROOT / 'scripts/fonts/UnifrakturCook-Bold.ttf', 'b')
ROMAN = Face(ROOT / 'scripts/fonts/Cinzel.ttf', 'r')


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;')


def svg(w, h, body, title, desc=''):
    title, desc = esc(title), esc(desc)
    d = f'<desc id="d">{desc}</desc>' if desc else ''
    defs = '<defs>' + ''.join(f'<path id="{k}" d="{v}"/>' for k, v in DEFS.items()) + '</defs>'
    DEFS.clear()
    body = defs + body
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-labelledby="t{" d" if desc else ""}"><title id="t">{title}</title>{d}{body}</svg>')


def write(rel, content):
    p = A / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')
    print(f'{rel}: {len(content) / 1024:.1f} KB')


def anim(attr, values, dur, key=None, extra=''):
    k = f' keyTimes="{key}"' if key else ''
    return f'<animate attributeName="{attr}" values="{values}"{k} dur="{dur}s" repeatCount="indefinite" {extra}/>'


def spin(dur, cx=0, cy=0, rev=False):
    a, b = (360, 0) if rev else (0, 360)
    return (f'<animateTransform attributeName="transform" type="rotate" from="{a} {cx} {cy}" to="{b} {cx} {cy}" '
            f'dur="{dur}s" repeatCount="indefinite"/>')


def rune(rng, s):
    """A procedurally drawn rune-like glyph: stave plus a few branches."""
    d = f'M0 {-s}V{s}'
    for _ in range(rng.randint(1, 3)):
        y0 = rng.uniform(-s, s * .6)
        side = rng.choice((-1, 1))
        d += f'M0 {y0:.1f}L{side * s * .7:.1f} {y0 + rng.choice((-1, 1)) * s * .55:.1f}'
    return d


def sigil(r, seed, runes=24, spin_dur=140, op=.5):
    """Concentric ring of ticks and runes plus counter-rotating triangles."""
    rng = random.Random(seed)
    ticks = ''.join(f'M{r * math.cos(a):.1f} {r * math.sin(a):.1f}L{(r - (9 if i % 6 == 0 else 4)) * math.cos(a):.1f} '
                    f'{(r - (9 if i % 6 == 0 else 4)) * math.sin(a):.1f}'
                    for i in range(96) for a in [i * math.tau / 96])
    glyphs = ''
    for i in range(runes):
        a = i * 360 / runes
        glyphs += f'<path transform="rotate({a:.1f}) translate(0 {-(r - 24)}) " d="{rune(rng, 7)}"/>'
    tri = ''.join(f'<path d="M0 {-(r - 60)}L{(r - 60) * .866:.1f} {(r - 60) * .5:.1f}L{-(r - 60) * .866:.1f} {(r - 60) * .5:.1f}Z" '
                  f'transform="rotate({rot})"/>' for rot in (0, 180))
    return (f'<g fill="none" stroke="{SIL}" stroke-width=".8" stroke-linecap="round" opacity="{op}">'
            f'<g>{spin(spin_dur)}<circle r="{r}"/><circle r="{r - 14}" opacity=".6"/><path d="{ticks}" opacity=".7"/>{glyphs}</g>'
            f'<g>{spin(spin_dur * .6, rev=True)}{tri}<circle r="{r - 60}" opacity=".5"/><circle r="{r - 96}" stroke-dasharray="2 7"/></g></g>')


def catmull(pts):
    d = ''
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f'C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}'
    return d


def knight():
    """Hooded wanderer leaning on a planted greatsword. Origin at feet; up is negative y."""
    right = [(0, -262), (15, -259), (25, -246), (27, -230), (22, -216), (20, -207), (38, -199), (53, -184),
             (60, -158), (68, -120), (80, -78), (92, -38), (101, -4)]
    hem = [(101, -4), (90, -12), (80, -2), (68, -11), (56, -1), (44, -9), (32, 0), (18, -8), (6, -1), (-8, -9),
           (-22, 0), (-36, -10), (-50, -1), (-64, -11), (-76, -3), (-92, -14), (-106, -2)]
    left = [(-106, -2), (-96, -44), (-84, -84), (-70, -122), (-61, -158), (-54, -184), (-39, -199), (-21, -207),
            (-23, -216), (-28, -230), (-26, -246), (-15, -259), (0, -262)]
    d = f'M0 -262{catmull(right)}' + ''.join(f'L{x} {y}' for x, y in hem[1:]) + catmull(left) + 'Z'
    folds = ('M-34 -196C-44 -150 -50 -90 -58 -20M34 -196C44 -150 50 -90 58 -20M-8 -180C-12 -120 -10 -60 -14 -10'
             'M16 -170C22 -110 28 -60 30 -8')
    sword = (f'<path d="M-4.5 -152H4.5L2.4 3H-2.4Z M-30 -152C-14 -158 14 -158 30 -152L30 -147C14 -152 -14 -152 -30 -147Z '
             f'M-2.6 -152V-190H2.6V-152Z" fill="{BLACK}"/><circle cy="-194" r="6" fill="{BLACK}"/>'
             f'<ellipse cy="-181" rx="9" ry="6.5" fill="{BLACK}"/>')
    return d, folds, sword


def arch_skyline(w, base, rng, color, hmin, hmax, window=None):
    out, x = '', -20
    while x < w + 20:
        tw = rng.randint(34, 78)
        mid = abs((x + tw / 2) - w / 2)
        h = rng.randint(hmin, hmax) * min(1, .18 + mid / 360)
        top = base - h
        shape = rng.choice(('spire', 'spire', 'flat', 'buttress'))
        if shape == 'spire':
            out += f'<path d="M{x} {base}V{top}L{x + tw / 2} {top - tw * 1.5:.0f}L{x + tw} {top}V{base}Z"/>'
        elif shape == 'flat':
            out += (f'<path d="M{x} {base}V{top}h{tw / 4:.0f}v-10h{tw / 4:.0f}v10h{tw / 4:.0f}v-10h{tw / 4:.0f}v10V{base}Z"/>')
        else:
            out += f'<path d="M{x} {base}V{top}L{x + tw * .5:.0f} {top - tw * .9:.0f}L{x + tw} {top}V{base}Z"/>'
        if window and rng.random() < .55:
            wx, wy = x + tw / 2, top + 14 + rng.randint(0, 40)
            out += (f'<path fill="{window}" d="M{wx - 4:.0f} {wy + 22:.0f}V{wy + 7:.0f}Q{wx:.0f} {wy - 8:.0f} {wx + 4:.0f} {wy + 7:.0f}V{wy + 22:.0f}Z" '
                    f'opacity="{rng.choice((.5, .7, .3)):.1f}">{anim("opacity", ".25;.75;.4;.7;.25", rng.randint(5, 11), extra="begin=\"-" + str(rng.randint(0, 9)) + "s\"")}</path>')
        x += tw + rng.randint(-6, 14)
    return f'<g fill="{color}">{out}</g>'


def hero():
    W, H, GROUND = 1280, 700, 545
    rng = random.Random(7)
    kd, folds, sword = knight()
    ash = ''
    for i in range(46):
        x, y = rng.uniform(0, W), rng.uniform(260, H - 60)
        r, dur = rng.uniform(.8, 2.3), rng.uniform(16, 34)
        dx, dy = rng.uniform(-90, 30), -rng.uniform(200, 380)
        ash += (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{SIL}" opacity="0">'
                f'<animateTransform attributeName="transform" type="translate" values="0 0;{dx:.0f} {dy:.0f}" dur="{dur:.1f}s" begin="-{rng.uniform(0, dur):.1f}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0;{rng.uniform(.35, .85):.2f};{rng.uniform(.2, .6):.2f};0" keyTimes="0;.2;.7;1" dur="{dur:.1f}s" begin="-{rng.uniform(0, dur):.1f}s" repeatCount="indefinite"/></circle>')
    # Fog: wide blurred ellipses that drift symmetrically so the loop never jumps.
    def fog(cy, rx, ry, op, dur, amp, cx):
        return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{OFF}" opacity="{op}" filter="url(#blur)">'
                f'<animateTransform attributeName="transform" type="translate" values="{-amp} 0;{amp} 0;{-amp} 0" dur="{dur}s" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1" keyTimes="0;.5;1" repeatCount="indefinite"/></ellipse>')
    back_fog = fog(470, 380, 50, .10, 46, 140, 300) + fog(500, 420, 44, .09, 58, 120, 1000)
    mid_fog = fog(520, 460, 40, .13, 52, 150, 640) + fog(540, 300, 32, .10, 38, 190, 200)
    front_fog = fog(580, 520, 46, .12, 64, 170, 420) + fog(600, 460, 38, .10, 49, 150, 900)
    name = BLACKLETTER.path('John Ray Cacananta', 66, W / 2, 596, fill=OFF)
    alias = ROMAN.path('S I N A G', 20, W / 2, 50, ls=14, fill=SIL)
    tag = ROMAN.path('Forging intelligence. Guarding the unseen.', 22, W / 2, 86, ls=2, fill=SIL)
    spec = ROMAN.path('FULL-STACK DEVELOPER  ·  AI SECURITY  ·  CLOUD & AUTOMATION', 17, W / 2, 634, ls=5, fill=SIL)
    lines = ['Rebuilding myself one commit at a time', 'Securing AI agents with intent-based policy',
             'Shipping full-stack apps on Next.js + Supabase', 'Automating the boring with n8n and MCP']
    cyc = ''
    for i, t in enumerate(lines):
        lo, hi = i / 4, (i + 1) / 4
        pts = [(0, 0)] if lo > 0 else []
        pts += [(lo, 0), (lo + .02, 1), (hi - .02, 1), (hi, 0)]
        if hi < 1:
            pts.append((1, 0))
        pts[0] = (0, pts[0][1])
        cyc += ('<g>' + ROMAN.path(t, 21, W / 2, 674, ls=1.5, fill=SIL)
                + f'<animate attributeName="opacity" values="{";".join(str(v) for _, v in pts)}" keyTimes="{";".join(f"{k:.2f}" for k, _ in pts)}" dur="20s" repeatCount="indefinite"/></g>')
    flick = (f'<rect width="{W}" height="{H}" fill="{BLACK}" opacity="0">'
             + anim('opacity', '0;0.07;0;0.12;0.03;0;0.09;0', 9, '0;.12;.2;.34;.5;.62;.8;1') + '</rect>')
    corners = ''.join(
        f'<path transform="translate({x} {y}) scale({sx} {sy})" d="M0 0V34M0 0H34M10 10V26M10 10H26" fill="none" stroke="{SIL}" stroke-width=".9" opacity=".55"/>'
        for x, y, sx, sy in ((18, 18, 1, 1), (W - 18, 18, -1, 1), (18, H - 18, 1, -1), (W - 18, H - 18, -1, -1)))
    body = f'''<defs>
<radialGradient id="sky" cx="50%" cy="42%" r="70%"><stop offset="0" stop-color="#202020"/><stop offset=".45" stop-color="{OBS}"/><stop offset="1" stop-color="{BLACK}"/></radialGradient>
<radialGradient id="corona" cx="50%" cy="50%" r="50%"><stop offset=".42" stop-color="{OFF}" stop-opacity="0"/><stop offset=".5" stop-color="{OFF}" stop-opacity=".95"/><stop offset=".56" stop-color="{SIL}" stop-opacity=".38"/><stop offset=".8" stop-color="{SIL}" stop-opacity=".07"/><stop offset="1" stop-color="{SIL}" stop-opacity="0"/></radialGradient>
<linearGradient id="ground" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CHAR}" stop-opacity=".0"/><stop offset=".12" stop-color="#0c0c0c"/><stop offset="1" stop-color="{BLACK}"/></linearGradient>
<radialGradient id="vig" cx="50%" cy="48%" r="75%"><stop offset=".55" stop-color="{BLACK}" stop-opacity="0"/><stop offset="1" stop-color="{BLACK}" stop-opacity=".95"/></radialGradient>
<radialGradient id="rimglow" cx="50%" cy="100%" r="60%"><stop offset="0" stop-color="{OFF}" stop-opacity=".22"/><stop offset="1" stop-color="{OFF}" stop-opacity="0"/></radialGradient>
<filter id="blur" x="-30%" y="-100%" width="160%" height="300%"><feGaussianBlur stdDeviation="24"/></filter>
<filter id="soft"><feGaussianBlur stdDeviation="1.2"/></filter></defs>
<rect width="{W}" height="{H}" fill="url(#sky)"/>
{arch_skyline(W, GROUND - 40, random.Random(3), '#0e0e0e', 90, 250, '#BFBFBF')}
{back_fog}
<g transform="translate({W / 2} 312)">
<circle r="200" fill="url(#corona)">{anim('opacity', '.9;1;.82;1;.9', 8, '0;.25;.45;.7;1')}</circle>
{sigil(226, 11, 28, 160, .42)}
<circle r="102" fill="{BLACK}"/>
<circle r="102" fill="none" stroke="{OFF}" stroke-width="1.4" opacity=".8">{anim('opacity', '.8;1;.7;.95;.8', 8, '0;.25;.45;.7;1')}</circle>
</g>
{arch_skyline(W, GROUND - 4, random.Random(9), '#060606', 50, 150)}
{mid_fog}
<ellipse cx="{W / 2}" cy="{GROUND - 8}" rx="190" ry="120" fill="url(#rimglow)"/>
<g transform="translate({W / 2} {GROUND})">
<path d="{kd}" fill="{BLACK}" stroke="{SIL}" stroke-width="1" stroke-opacity=".55" stroke-linejoin="round">{anim('stroke-opacity', '.5;.75;.4;.65;.5', 6, '0;.2;.45;.75;1')}</path>
<path d="{folds}" fill="none" stroke="{CHAR}" stroke-width="1.4" stroke-linecap="round"/>
<g stroke="{SIL}" stroke-width=".8" stroke-opacity=".6">{sword}</g>
</g>
<rect y="{GROUND - 6}" width="{W}" height="{H - GROUND + 6}" fill="url(#ground)"/>
{front_fog}
{ash}
<rect width="{W}" height="{H}" fill="url(#vig)"/>
<g>{alias}</g>
<path d="M{W / 2 - 150} 44H{W / 2 - 100}M{W / 2 + 100} 44H{W / 2 + 150}" stroke="{ASH}" stroke-width=".8"/>
<g>{tag}<animate attributeName="opacity" values="0;1" dur="3s" fill="freeze"/></g>
<g>{name}</g>
<g>{spec}</g>
<g>{cyc}</g>
{corners}
{flick}'''
    write('banners/hero.svg', svg(W, H, body, 'John Ray Cacananta — SINAG',
          'A cloaked wanderer stands before a black eclipse and a slowly turning sigil, among drifting fog and ash. Forging intelligence. Guarding the unseen.'))


def header(slug, title, sub, alt):
    W, H = 900, 150
    t = BLACKLETTER.path(title, 56, W / 2, 84, fill=OFF)
    s = ROMAN.path(sub.upper(), 15, W / 2, 124, ls=7, fill=SIL)
    rng = random.Random(slug)
    ring = (f'<g transform="translate({W / 2} 28)" fill="none" stroke="{SIL}" stroke-width=".8">'
            f'<g>{spin(30)}<circle r="9" stroke-dasharray="1.5 3"/><path d="{rune(rng, 4)}"/></g><circle r="14" opacity=".5"/></g>')
    rule = (f'<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{SIL}" stop-opacity="0"/><stop offset=".5" stop-color="{SIL}" stop-opacity=".9"/><stop offset="1" stop-color="{SIL}" stop-opacity="0"/></linearGradient></defs>'
            f'<rect x="60" y="138" width="{W - 120}" height="1" fill="url(#g)"/>'
            f'<circle r="2" cy="138.5" fill="{OFF}"><animate attributeName="cx" values="60;{W - 60};60" dur="14s" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1" repeatCount="indefinite"/></circle>')
    body = (f'<rect width="{W}" height="{H}" fill="{BLACK}"/><rect x="8" y="8" width="{W - 16}" height="{H - 16}" fill="none" stroke="{CHAR}"/>'
            f'<path d="M8 8h28M8 8v28M{W - 8} 8h-28M{W - 8} 8v28M8 {H - 8}h28M8 {H - 8}v-28M{W - 8} {H - 8}h-28M{W - 8} {H - 8}v-28" stroke="{ASH}" fill="none"/>'
            f'{ring}<g>{t}<animate attributeName="opacity" values="0;1" dur="2.2s" fill="freeze"/></g><g>{s}</g>{rule}')
    write(f'headers/{slug}.svg', svg(W, H, body, alt))


def divider():
    W, H = 900, 44
    pulse = anim('opacity', '.5;1;.5', 5)
    body = (f'<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{SIL}" stop-opacity="0"/><stop offset=".5" stop-color="{SIL}"/><stop offset="1" stop-color="{SIL}" stop-opacity="0"/></linearGradient></defs>'
            f'<rect width="{W}" height="{H}" fill="{BLACK}"/>'
            f'<rect x="40" y="22" width="{W - 80}" height=".8" fill="url(#g)" opacity=".7"/>'
            f'<g transform="translate({W / 2} 22)" fill="none" stroke="{SIL}" stroke-width=".9"><path d="M0 -12L12 0L0 12L-12 0Z" fill="{BLACK}"/><circle r="5">{pulse}</circle>'
            f'<path d="M-44 0H-20M20 0H44M-26 -5L-20 0L-26 5M26 -5L20 0L26 5" opacity=".8"/></g>'
            f'<circle r="1.8" cy="22.4" fill="{OFF}"><animate attributeName="cx" values="40;430;40" keyTimes="0;.5;1" dur="9s" repeatCount="indefinite"/><animate attributeName="opacity" values="0;1;0" dur="9s" repeatCount="indefinite"/></circle>'
            f'<circle r="1.8" cy="22.4" fill="{OFF}"><animate attributeName="cx" values="860;470;860" keyTimes="0;.5;1" dur="9s" repeatCount="indefinite"/><animate attributeName="opacity" values="0;1;0" dur="9s" repeatCount="indefinite"/></circle>')
    write('dividers/divider.svg', svg(W, H, body, 'Ornamental divider'))


ICON = lambda n: re.findall(r'\sd="([^"]+)"', (A / f'icons/{n}.svg').read_text(encoding='utf-8'))
ARSENAL = [
    ('Languages', [('Python', 'python'), ('Java', 'openjdk'), ('JavaScript', 'javascript'), ('TypeScript', 'typescript'), ('Bash', 'gnubash'), ('PowerShell', 'powershell'), ('HTML', 'html5'), ('CSS', 'css3')]),
    ('Frontend', [('React', 'react'), ('Next.js', 'nextdotjs'), ('Vite', 'vite'), ('Tailwind', 'tailwindcss'), ('Bootstrap', 'bootstrap'), ('Three.js', 'threedotjs')]),
    ('Backend', [('FastAPI', 'fastapi'), ('Node.js', 'nodedotjs'), ('Express', 'express'), ('Supabase', 'supabase'), ('Firebase', 'firebase')]),
    ('Databases', [('PostgreSQL', 'postgresql'), ('MySQL', 'mysql'), ('SQLite', 'sqlite')]),
    ('AI / ML', [('PyTorch', 'pytorch'), ('scikit-learn', 'scikitlearn'), ('NumPy', 'numpy'), ('Pandas', 'pandas'), ('Ollama', 'ollama'), ('RAG + pgvector', 'postgresql'), ('Hugging Face', 'huggingface')]),
    ('AI Agents & Security', [('MCP', 'modelcontextprotocol'), ('OPA / Rego', 'mono:OPA'), ('Intent-Based AuthZ', 'glyph:shield'), ('Audit Logging', 'glyph:scroll'), ('Kali Linux', 'kalilinux')]),
    ('Cloud & DevOps', [('AWS', 'amazonaws'), ('Azure', 'microsoftazure'), ('Vercel', 'vercel'), ('Docker', 'docker'), ('Linux', 'linux'), ('Ubuntu', 'ubuntu'), ('Debian', 'debian'), ('Git', 'git'), ('GitHub', 'github'), ('GitLab', 'gitlab')]),
    ('Automation', [('n8n', 'n8n'), ('UiPath', 'uipath'), ('Power Automate', 'mono:PA'), ('Google Apps Script', 'googleappsscript'), ('Webhooks', 'webauthn')]),
    ('Tools', [('VS Code', 'visualstudiocode'), ('IntelliJ IDEA', 'intellijidea'), ('Postman', 'postman'), ('Claude Code', 'claude'), ('Codex', 'openai'), ('Power BI', 'powerbi')]),
]
GLYPH = {'shield': 'M12 2.5L20 5.5V11.5C20 16 16.5 19.7 12 21.5C7.5 19.7 4 16 4 11.5V5.5Z M12 7V16 M8.5 10.5H15.5',
         'scroll': 'M6 3.5H18V20.5H6Z M9 8H15 M9 12H15 M9 16H13',
         'mail': 'M3 6H21V18H3Z M3 7L12 13.5L21 7'}


def arsenal():
    W, ROW, TOP = 720, 100, 36
    H = TOP + ROW * len(ARSENAL) + 12
    out = [f'<rect width="{W}" height="{H}" fill="{BLACK}"/><rect x="6" y="6" width="{W - 12}" height="{H - 12}" fill="none" stroke="{CHAR}"/>',
           f'<g transform="translate({W / 2} {H / 2})" opacity=".09">{sigil(300, 5, 36, 240, 1)}</g>']
    names = []
    for r, (cat, items) in enumerate(ARSENAL):
        y = TOP + r * ROW
        out.append(ROMAN.path(cat.upper(), 14, 36, y + 20, 'start', ls=4, fill=OFF))
        out.append(f'<path d="M{44 + ROMAN.width(cat.upper(), 14, 4):.0f} {y + 15.5}H{W - 36}" stroke="{CHAR}"/>')
        pitch = min(108, (W - 72) / len(items))
        for i, (label, key) in enumerate(items):
            cx = 36 + pitch / 2 + i * pitch
            names.append(label)
            ty = y + 36
            if key.startswith('mono:'):
                g = (f'<circle cx="{cx}" cy="{ty + 16}" r="16" fill="none" stroke="{SIL}" stroke-width="1.6"/>'
                     + ROMAN.path(key[5:], 13, cx, ty + 21, fill=SIL))
            elif key.startswith('glyph:'):
                g = (f'<g transform="translate({cx - 16} {ty}) scale(1.33)" fill="none" stroke="{SIL}" stroke-width="1.5" '
                     f'stroke-linejoin="round" stroke-linecap="round"><path d="{GLYPH[key[6:]]}"/></g>')
            else:
                g = f'<g transform="translate({cx - 16} {ty}) scale(1.333)" fill="{SIL}">' + ''.join(f'<path d="{d}"/>' for d in ICON(key)) + '</g>'
            lines = ROMAN.wrap(label, 10.5, pitch - 8, .6)
            out.append(g + ''.join(ROMAN.path(l, 10.5, cx, ty + 50 + j * 12, ls=.6, fill='#9a9a9a') for j, l in enumerate(lines)))
    sweep = (f'<defs><linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="{OFF}" stop-opacity="0"/><stop offset=".5" stop-color="{OFF}" stop-opacity=".05"/><stop offset="1" stop-color="{OFF}" stop-opacity="0"/></linearGradient></defs>'
             f'<rect y="6" width="140" height="{H - 12}" fill="url(#sw)"><animate attributeName="x" values="-140;{W}" dur="11s" repeatCount="indefinite"/></rect>')
    write('animations/arsenal.svg', svg(W, H, ''.join(out) + sweep, 'The Arsenal — technology stack',
          'Monochrome icons: ' + '; '.join(f'{c}: ' + ', '.join(l for l, _ in it) for c, it in ARSENAL)))


def relic(idx, p):
    W, H = 860, 120
    code = p['code']
    stack = '  ·  '.join(s.upper() for s in p['stack'])
    body = (f'<rect width="{W}" height="{H}" fill="{BLACK}"/><rect x="6" y="6" width="{W - 12}" height="{H - 12}" fill="none" stroke="{CHAR}"/>'
            f'<path d="M6 6h22M6 6v22M{W - 6} 6h-22M{W - 6} 6v22M6 {H - 6}h22M6 {H - 6}v-22M{W - 6} {H - 6}h-22M{W - 6} {H - 6}v-22" stroke="{ASH}" fill="none"/>'
            f'<g transform="translate(82 60)"><g fill="none" stroke="{SIL}" stroke-width=".9"><g>{spin(60 + idx * 7, rev=idx % 2 == 0)}<circle r="44" stroke-dasharray="1 5"/><path d="{rune(random.Random(idx), 5)}" transform="translate(0 -52)"/></g><circle r="38" opacity=".7"/></g>'
            + BLACKLETTER.path(code, 38, 0, 13, fill=OFF) + '</g>'
            f'<path d="M150 22V98" stroke="{CHAR}"/>'
            + BLACKLETTER.path(p['name'], 40, 176, 62, 'start', fill=OFF)
            + ROMAN.path(p['role'].upper(), 13, 178, 86, 'start', ls=3.5, fill=SIL)
            + ROMAN.path(stack, 11, 178, 106, 'start', ls=2.5, fill=ASH))
    write(f'relics/{idx}.svg', svg(W, H, body, f'{p["name"]} — {p["role"]}'))


def seal(slug, label, icon):
    W, H = 230, 58
    if icon.startswith('glyph:'):
        ic = (f'<g transform="translate(20 15) scale(1.2)" fill="none" stroke="{SIL}" stroke-width="1.5" stroke-linejoin="round">'
              f'<path d="{GLYPH[icon[6:]]}"/></g>')
    elif icon.startswith('mono:'):
        ic = f'<circle cx="35" cy="29" r="13" fill="none" stroke="{SIL}" stroke-width="1.5"/>' + ROMAN.path(icon[5:], 15, 35, 34, fill=SIL)
    else:
        ic = f'<g transform="translate(22 17)" fill="{SIL}">' + ''.join(f'<path d="{d}"/>' for d in ICON(icon)) + '</g>'
    body = (f'<rect width="{W}" height="{H}" fill="{BLACK}"/><rect x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" fill="none" stroke="{ASH}" stroke-width="1" stroke-dasharray="6 3"><animate attributeName="stroke-dashoffset" values="0;18" dur="6s" repeatCount="indefinite"/></rect>'
            f'{ic}<path d="M58 14V44" stroke="{CHAR}"/>' + ROMAN.path(label, 16, 76, 35, 'start', ls=4.5, fill=OFF))
    write(f'seals/{slug}.svg', svg(W, H, body, label))


def footer():
    W, H = 900, 200
    rng = random.Random(4)
    ash = ''.join(
        f'<circle cx="{rng.uniform(20, W - 20):.0f}" cy="{rng.uniform(60, H - 10):.0f}" r="{rng.uniform(.7, 1.8):.1f}" fill="{SIL}" opacity="0">'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;{rng.uniform(-30, 20):.0f} -{rng.uniform(80, 150):.0f}" dur="{(d := rng.uniform(12, 24)):.1f}s" begin="-{rng.uniform(0, d):.1f}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0;.7;.4;0" keyTimes="0;.25;.7;1" dur="{d:.1f}s" begin="-{rng.uniform(0, d):.1f}s" repeatCount="indefinite"/></circle>' for _ in range(22))
    body = (f'<defs><radialGradient id="glow" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{OFF}" stop-opacity=".35"/><stop offset="1" stop-color="{OFF}" stop-opacity="0"/></radialGradient>'
            f'<filter id="b"><feGaussianBlur stdDeviation="22"/></filter></defs>'
            f'<rect width="{W}" height="{H}" fill="{BLACK}"/>'
            f'<ellipse cx="{W / 2}" cy="{H - 10}" rx="360" ry="34" fill="{OFF}" opacity=".08" filter="url(#b)"><animateTransform attributeName="transform" type="translate" values="-50 0;50 0;-50 0" dur="30s" repeatCount="indefinite"/></ellipse>'
            f'<g transform="translate({W / 2} 58)"><circle r="40" fill="url(#glow)">{anim("opacity", ".7;1;.6;.95;.7", 5, "0;.3;.5;.8;1")}</circle>'
            f'<g fill="none" stroke="{SIL}" stroke-width=".8"><g>{spin(40)}<circle r="22" stroke-dasharray="1.5 4"/><path d="M0 -22V22M-19 -11L19 11M19 -11L-19 11" opacity=".6"/></g><circle r="9"/><circle r="2.5" fill="{OFF}"/></g></g>'
            + ROMAN.path('Forging intelligence. Guarding the unseen.', 22, W / 2, 132, ls=1.5, fill=SIL)
            + ROMAN.path('H E R E   E N D S   T H E   C O D E X', 12, W / 2, 162, ls=3, fill=ASH)
            + f'<path d="M{W / 2 - 160} 176H{W / 2 + 160}" stroke="{CHAR}"/>{ash}')
    write('banners/footer.svg', svg(W, H, body, 'Here ends the codex'))


if __name__ == '__main__':
    hero()
    divider()
    for slug, title, sub, alt in [
        ('wanderer', 'The Wanderer', 'About Me', 'The Wanderer — About Me'),
        ('oath', 'The Oath', 'Current Focus', 'The Oath — Current Focus'),
        ('arsenal', 'The Arsenal', 'Technology Stack', 'The Arsenal — Technology Stack'),
        ('relics', 'The Relics', 'Featured Projects', 'The Relics — Featured Projects'),
        ('chronicle', 'The Chronicle', 'GitHub Statistics', 'The Chronicle — GitHub Statistics'),
        ('footprints', 'The Footprints', 'Contribution Activity', 'The Footprints — Contribution Activity'),
        ('veil', 'Beyond the Veil', 'Contact & Social Links', 'Beyond the Veil — Contact and Social Links')]:
        header(slug, title, sub, alt)
    arsenal()
    for i, p in enumerate(json.loads((ROOT / 'data/featured-projects.json').read_text(encoding='utf-8'))):
        relic(i, p)
    seal('linkedin', 'LINKEDIN', 'mono:in')
    seal('email', 'EMAIL', 'glyph:mail')
    seal('github', 'GITHUB', 'github')
    footer()
