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
SANS = Face(ROOT / 'scripts/fonts/Inter.ttf', 'r')


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



def hero():
    W, H = 1280, 380
    rng = random.Random(7)
    ash = ''
    for _ in range(34):
        x, y = rng.uniform(0, W), rng.uniform(120, H)
        r, dur = rng.uniform(.7, 1.9), rng.uniform(18, 36)
        dx, dy = rng.uniform(-70, 30), -rng.uniform(120, 260)
        b = f'begin="-{rng.uniform(0, dur):.1f}s"'
        ash += (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{SIL}" opacity="0">'
                f'<animateTransform attributeName="transform" type="translate" values="0 0;{dx:.0f} {dy:.0f}" dur="{dur:.1f}s" {b} repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0;{rng.uniform(.3, .7):.2f};{rng.uniform(.15, .4):.2f};0" keyTimes="0;.25;.7;1" dur="{dur:.1f}s" {b} repeatCount="indefinite"/></circle>')

    def fog(cy, rx, ry, op, dur, amp, cx):
        return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{OFF}" opacity="{op}" filter="url(#blur)">'
                f'<animateTransform attributeName="transform" type="translate" values="{-amp} 0;{amp} 0;{-amp} 0" dur="{dur}s" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1" keyTimes="0;.5;1" repeatCount="indefinite"/></ellipse>')
    name = BLACKLETTER.path('John Ray Cacananta', 58, W / 2, 262, fill=OFF)
    spec = SANS.path('Full-Stack Developer  ·  AI Security  ·  Cloud & Automation', 18, W / 2, 316, ls=.6, fill=SIL)
    body = f'''<defs>
<radialGradient id="sky" cx="50%" cy="34%" r="75%"><stop offset="0" stop-color="#1a1a1a"/><stop offset=".5" stop-color="{OBS}"/><stop offset="1" stop-color="{BLACK}"/></radialGradient>
<radialGradient id="corona" cx="50%" cy="50%" r="50%"><stop offset=".4" stop-color="{OFF}" stop-opacity="0"/><stop offset=".48" stop-color="{OFF}" stop-opacity=".95"/><stop offset=".54" stop-color="{SIL}" stop-opacity=".35"/><stop offset=".78" stop-color="{SIL}" stop-opacity=".06"/><stop offset="1" stop-color="{SIL}" stop-opacity="0"/></radialGradient>
<radialGradient id="vig" cx="50%" cy="45%" r="75%"><stop offset=".5" stop-color="{BLACK}" stop-opacity="0"/><stop offset="1" stop-color="{BLACK}" stop-opacity=".9"/></radialGradient>
<filter id="blur" x="-30%" y="-100%" width="160%" height="300%"><feGaussianBlur stdDeviation="22"/></filter></defs>
<rect width="{W}" height="{H}" fill="url(#sky)"/>
{fog(250, 400, 46, .08, 50, 140, 340)}{fog(230, 420, 40, .07, 62, 120, 960)}
<g transform="translate({W / 2} 118)">
<circle r="150" fill="url(#corona)">{anim('opacity', '.9;1;.85;1;.9', 9, '0;.25;.5;.75;1')}</circle>
{sigil(124, 11, 24, 220, .3)}
<circle r="62" fill="{BLACK}"/>
<circle r="62" fill="none" stroke="{OFF}" stroke-width="1.2" opacity=".75">{anim('opacity', '.75;.95;.7;.9;.75', 9, '0;.25;.5;.75;1')}</circle>
</g>
{fog(300, 520, 40, .10, 56, 160, 640)}
{ash}
<rect width="{W}" height="{H}" fill="url(#vig)"/>
<g>{name}<animate attributeName="opacity" values="0;1" dur="2.4s" fill="freeze"/></g>
<g>{spec}<animate attributeName="opacity" values="0;1" dur="2.4s" begin=".6s" fill="freeze"/></g>
<rect width="{W}" height="{H}" fill="{BLACK}" opacity="0">{anim('opacity', '0;0.05;0;0.09;0.02;0', 10, '0;.15;.3;.5;.7;1')}</rect>'''
    write('banners/hero.svg', svg(W, H, body, 'John Ray Cacananta',
          'Full-Stack Developer, AI Security, Cloud and Automation. A black eclipse with a slowly turning sigil, drifting fog and ash.'))


def header(slug, title, alt):
    W, H = 900, 54
    body = (f'<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{SIL}" stop-opacity=".8"/><stop offset="1" stop-color="{SIL}" stop-opacity="0"/></linearGradient></defs>'
            f'<rect width="{W}" height="{H}" fill="{BLACK}"/>'
            + BLACKLETTER.path(title, 30, 16, 36, 'start', fill=OFF)
            + f'<rect x="16" y="46" width="{W - 32}" height="1" fill="url(#g)"/>'
            f'<circle r="1.8" cy="46.5" fill="{OFF}"><animate attributeName="cx" values="16;{W - 16};16" dur="16s" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1" repeatCount="indefinite"/></circle>')
    write(f'headers/{slug}.svg', svg(W, H, body, alt))


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
    W, ROW, TOP = 720, 84, 8
    H = TOP + ROW * len(ARSENAL)
    out = [f'<rect width="{W}" height="{H}" fill="{BLACK}"/>']
    for r, (cat, items) in enumerate(ARSENAL):
        y = TOP + r * ROW
        out.append(SANS.path(cat, 13, 16, y + 18, 'start', ls=.3, fill=OFF))
        out.append(f'<path d="M{24 + SANS.width(cat, 13, .3):.0f} {y + 14.5}H{W - 16}" stroke="{CHAR}"/>')
        pitch = min(104, (W - 32) / len(items))
        for i, (label, key) in enumerate(items):
            cx = 16 + pitch / 2 + i * pitch
            ty = y + 28
            if key.startswith('mono:'):
                g = (f'<circle cx="{cx}" cy="{ty + 12}" r="12" fill="none" stroke="{SIL}" stroke-width="1.4"/>'
                     + SANS.path(key[5:], 9.5, cx, ty + 15.5, fill=SIL))
            elif key.startswith('glyph:'):
                g = (f'<g transform="translate({cx - 12} {ty})" fill="none" stroke="{SIL}" stroke-width="1.5" '
                     f'stroke-linejoin="round" stroke-linecap="round"><path d="{GLYPH[key[6:]]}"/></g>')
            else:
                g = f'<g transform="translate({cx - 12} {ty})" fill="{SIL}">' + ''.join(f'<path d="{d}"/>' for d in ICON(key)) + '</g>'
            lines = SANS.wrap(label, 11, pitch - 6, 0)
            out.append(g + ''.join(SANS.path(l, 11, cx, ty + 38 + j * 12, fill=SIL) for j, l in enumerate(lines)))
    write('animations/arsenal.svg', svg(W, H, ''.join(out), 'Tech Stack',
          'Monochrome icons: ' + '; '.join(f'{c}: ' + ', '.join(l for l, _ in it) for c, it in ARSENAL)))


def seal(slug, label, icon):
    W, H = 150, 40
    if icon.startswith('glyph:'):
        ic = (f'<g transform="translate(12 8)" fill="none" stroke="{SIL}" stroke-width="1.5" stroke-linejoin="round">'
              f'<path d="{GLYPH[icon[6:]]}"/></g>')
    elif icon.startswith('mono:'):
        ic = f'<rect x="12" y="8" width="24" height="24" rx="3" fill="none" stroke="{SIL}" stroke-width="1.5"/>' + SANS.path(icon[5:], 13, 24, 25, fill=SIL)
    else:
        ic = f'<g transform="translate(12 8)" fill="{SIL}">' + ''.join(f'<path d="{d}"/>' for d in ICON(icon)) + '</g>'
    body = (f'<rect width="{W}" height="{H}" fill="{BLACK}"/><rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="3" fill="none" stroke="{ASH}"/>'
            + ic + SANS.path(label, 14, 46, 25, 'start', fill=OFF))
    write(f'seals/{slug}.svg', svg(W, H, body, label))


if __name__ == '__main__':
    hero()
    for slug, title in [('about', 'About'), ('focus', 'Current Focus'), ('stack', 'Tech Stack'),
                        ('stats', 'GitHub Stats'), ('contributions', 'Contributions'), ('connect', 'Connect')]:
        header(slug, title, title)
    arsenal()
    seal('linkedin', 'LinkedIn', 'mono:in')
    seal('email', 'Email', 'glyph:mail')
    seal('github', 'GitHub', 'github')
