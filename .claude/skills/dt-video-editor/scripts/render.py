"""Render a talking-head video from plan.json.

usage: python3 render.py PLAN.json [--stills t1 t2 ...]

Reads WORKDIR/words.json and pauses.json (from transcribe.py). Produces in WORKDIR:
  final.mp4        the edit (H.264 main 3.1, yuv420p, AAC, +faststart)
  qa_sheet.jpg     contact sheet, one frame per 1.5 s
  qa_report.txt    automatic checks (timing, overlaps, takeover length)
  still_XX.XX.png  with --stills: single frames only, no video (fast layout check)

Times anywhere in the plan can be seconds (12.4) or a quoted phrase from the
script ("this prompt"); phrases resolve to the moment that word sequence starts.
See references/plan_schema.md for every field.
"""
import sys, os, json, math, re, random, subprocess, difflib
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PLAN_PATH = sys.argv[1]
PLAN = json.load(open(PLAN_PATH))
WORK = PLAN.get('workdir') or os.path.dirname(os.path.abspath(PLAN_PATH))
SRC = PLAN['source']
STILLS = [float(x) for x in sys.argv[sys.argv.index('--stills') + 1:]] if '--stills' in sys.argv else None

W, H, FPS = 720, 1280, 30
FD = '/usr/share/fonts/opentype/inter/Inter-'
_fc = {}
def F(w, s):
    k = (w, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(FD + w + '.otf', s)
    return _fc[k]
YEL = (255, 214, 10); ROSE = (232, 120, 150); INK = (20, 20, 24); GRAY = (120, 120, 130)
GREEN = (52, 168, 83); RED = (226, 72, 72)
COLORS = {'yellow': YEL, 'rose': ROSE, 'ink': INK, 'gray': GRAY, 'green': GREEN, 'red': RED}
def col(c, default=INK): return COLORS.get(c, default) if isinstance(c, str) or c is None else tuple(c)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def spring(t, k=7.0, w=13.0): return 1 - math.exp(-k * t) * math.cos(w * t) if t > 0 else 0.0

# ---------------------------------------------------------------- source info
probe = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=width,height,codec_type',
                                   '-of', 'json', SRC], capture_output=True, text=True).stdout)
SRC_DUR = float(probe['format']['duration'])
vs = [s for s in probe['streams'] if s['codec_type'] == 'video'][0]
SW, SH = int(vs['width']), int(vs['height'])
HAS_AUDIO = any(s['codec_type'] == 'audio' for s in probe['streams'])

# ---------------------------------------------------------------- transcript alignment
VW = json.load(open(os.path.join(WORK, 'words.json')))
PAUSES = json.load(open(os.path.join(WORK, 'pauses.json')))
def norm(x): return re.sub(r'[^a-z0-9]', '', x.lower())

def asr_tokens():
    """ASR words with spelled-out letters merged ("a i" -> "ai") so they match the clean script."""
    single = lambda k: k < len(VW) and len(VW[k][0]) == 1 and VW[k][0].isalpha()
    out = []; i = 0
    while i < len(VW):
        j = i
        while single(j) and j - i < 4: j += 1
        if j - i >= 2:
            out.append([''.join(VW[k][0] for k in range(i, j)), VW[i][1], VW[j - 1][2]]); i = j
        else:
            out.append(list(VW[i])); i += 1
    return out

SCRIPT = PLAN.get('script') or ' '.join(w_ for w_, _, _ in VW)
def align():
    A = asr_tokens()
    sw = SCRIPT.split(); sn = [norm(x) for x in sw]; an = [norm(x[0]) for x in A]
    times = [None] * len(sw)
    sm = difflib.SequenceMatcher(None, sn, an, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1): times[i1 + k] = (A[j1 + k][1], A[j1 + k][2])
        elif tag == 'replace' and j2 > j1:
            # spread the replaced script words across the ASR span by character length
            s0, e0 = A[j1][1], A[j2 - 1][2]; tot = sum(max(1, len(sn[k])) for k in range(i1, i2)); t = s0
            for k in range(i1, i2):
                d = (e0 - s0) * max(1, len(sn[k])) / tot; times[k] = (t, t + d); t += d
    # interpolate anything still missing (inserted words)
    for k in range(len(sw)):
        if times[k] is None:
            prev = next((times[j] for j in range(k - 1, -1, -1) if times[j]), (0, 0))
            nxt = next((times[j] for j in range(k + 1, len(sw)) if times[j]), (prev[1] + 0.3, prev[1] + 0.6))
            times[k] = (prev[1], max(prev[1] + 0.05, min(nxt[0], prev[1] + 0.3)))
    return [(sw[k], times[k][0], times[k][1]) for k in range(len(sw))]
TIMED = align()
TN = [norm(w_) for w_, _, _ in TIMED]

def find_phrase(ph):
    toks = [norm(x) for x in ph.split() if norm(x)]
    for i in range(len(TN) - len(toks) + 1):
        if TN[i:i + len(toks)] == toks: return i
    # fuzzy fallback: best ratio window
    best, bi = 0, None
    for i in range(len(TN) - len(toks) + 1):
        r = difflib.SequenceMatcher(None, ' '.join(TN[i:i + len(toks)]), ' '.join(toks)).ratio()
        if r > best: best, bi = r, i
    if best < 0.75: raise SystemExit(f'phrase not found in script: "{ph}"')
    return bi

def T(v, base=0.0):
    """Resolve a plan time: number = seconds, string = phrase start. Relative to base."""
    if v is None: return None
    if isinstance(v, (int, float)): return float(v) + base
    return TIMED[find_phrase(v)][1]

def pause_before(t):
    """Midpoint of the silent gap that ends right at/before t (for clean cuts)."""
    cands = [p for p in PAUSES if p[1] <= t + 0.15 and t - p[1] < 1.2]
    return (cands[-1][0] + cands[-1][1]) / 2 if cands else t - 0.2

SPEECH_END = TIMED[-1][2] if TIMED else SRC_DUR

# ---------------------------------------------------------------- captions
CAPS = []
if PLAN.get('captions', True):
    sent = []
    for i, tw in enumerate(TIMED):
        sent.append(tw)
        if tw[0][-1] in '.?!' or i == len(TIMED) - 1:
            n = math.ceil(len(sent) / 6); size = math.ceil(len(sent) / n); j = 0
            while j < len(sent):
                ch = sent[j:j + size]; j += size
                CAPS.append([ch[0][1], ch[-1][2] + 0.2, ' '.join(x[0] for x in ch)])
            sent = []
    for i in range(len(CAPS) - 1):
        if CAPS[i + 1][0] - CAPS[i][1] < 0.3 or CAPS[i][1] > CAPS[i + 1][0]: CAPS[i][1] = CAPS[i + 1][0]

# ---------------------------------------------------------------- beats, takeover, timing
TK = PLAN.get('takeover')
if TK:
    raw = T(TK['at']) + TK.get('lead', -0.3)
    TK_S = pause_before(T(TK['at'])) if TK.get('snap', True) else raw
    TK_E = pause_before(T(TK['until'])) if TK.get('until') else TK_S + TK.get('duration', 9)
else:
    TK_S = TK_E = -1

BEATS = []
for b in PLAN.get('beats', []):
    BEATS.append(dict(b, _s=T(b['at'])))
BEATS.sort(key=lambda b: b['_s'])
for i, b in enumerate(BEATS):
    if b.get('until') is not None: e = pause_before(T(b['until']))
    else:
        nxt = BEATS[i + 1]['_s'] if i + 1 < len(BEATS) else None
        e = pause_before(nxt) if nxt else SPEECH_END + 0.25
        if TK and b['_s'] < TK_S <= (nxt or 1e9): e = TK_S
    b['_e'] = e
    b['_side'] = 0 if (TK and b['_s'] < TK_S) or not TK else 1

END = PLAN.get('end_card', {})
END_START = (SPEECH_END + 0.25) if END is not None else SRC_DUR
END_LEN = END.get('length', 3.2) if END is not None else 0
TOTAL = max(SRC_DUR, END_START + END_LEN) if END is not None else SRC_DUR

HOOK = PLAN.get('hook')
HOOK_E = None
if HOOK:
    HOOK_E = T(HOOK['until']) if HOOK.get('until') else (BEATS[0]['_s'] if BEATS else 4.5)
    HOOK_E = pause_before(HOOK_E) if HOOK.get('until') or BEATS else HOOK_E

# ---------------------------------------------------------------- virtual camera
FRAMINGS = [(1.28, -60, 0.12), (1.06, -20, 0.05), (1.32, -65, 0.14), (1.14, 50, 0.08), (1.24, -60, 0.10), (1.30, -30, 0.06)]
SUBJ_X = PLAN.get('subject_x', SW / 2) * W / SW
def build_shots():
    if isinstance(PLAN.get('shots'), list):
        return [(T(s['at']), s['zoom'], s.get('x', SUBJ_X), s.get('top', 0.05)) for s in PLAN['shots']]
    cuts = [0.0]
    pts = sorted([(p[0] + p[1]) / 2 for p in PAUSES] + ([TK_S, TK_E] if TK else []))
    for c in pts:
        if TK and TK_S + 0.05 < c < TK_E - 0.05: continue  # footage is hidden behind the takeover card
        if c - cuts[-1] >= PLAN.get('min_shot', 2.4) and c < END_START - 1.5: cuts.append(c)
    if TK:  # make sure takeover boundaries are cuts
        for c in (TK_S, TK_E):
            if all(abs(c - x) > 0.05 for x in cuts): cuts.append(c)
        cuts.sort()
    shots = []
    for i, c in enumerate(cuts):
        if i == 0 or i == len(cuts) - 1: z, dx, tf = 1.0, 0, 0.0
        else: z, dx, tf = FRAMINGS[(i - 1) % len(FRAMINGS)]
        shots.append((c, z, SUBJ_X + dx, tf))
    return shots
SHOTS = build_shots()

def camera(frame, t):
    i = max(k for k in range(len(SHOTS)) if SHOTS[k][0] <= t + 1e-6)
    s, z, cx, tf = SHOTS[i]
    e = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else TOTAL
    p = (t - s) / max(0.1, e - s); dt = t - s
    zz = z * (1 + 0.05 * p) * (1 + (0.035 * math.exp(-dt * 7) if s > 0 else 0))
    cw, ch = W / zz, H / zz
    x0 = clamp(cx - cw / 2, 0, W - cw); y0 = clamp(tf * (H - ch), 0, H - ch)
    M = np.float32([[zz, 0, -x0 * zz], [0, zz, -y0 * zz]])
    return cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

# ---------------------------------------------------------------- drawing helpers
def rr_mask(w, h, r):
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255); return m

def paste(base, img, x, y, alpha=1.0):
    if alpha <= 0.01: return
    if alpha < 1:
        img = img.copy(); img.putalpha(img.getchannel('A').point(lambda v: int(v * alpha)))
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0)); layer.paste(img, (int(x), int(y)), img)
    base.alpha_composite(layer)

def shadow_text(base, xy, text, font, fill, alpha=1.0, anchor='la', sh=0.55):
    x, y = xy
    l = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(l)
    if sh > 0:
        d.text((x, y + 2), text, font=font, fill=(0, 0, 0, int(255 * sh * alpha)), anchor=anchor)
        l = l.filter(ImageFilter.GaussianBlur(4))
    ImageDraw.Draw(l).text((x, y), text, font=font, fill=tuple(fill) + (int(255 * alpha),), anchor=anchor)
    base.alpha_composite(l)

def frosted(src, x, y, w, h, r=26, tint=0.75):
    x, y = int(x), int(y); pad = 40
    X0, Y0, X1, Y1 = max(0, x - pad), max(0, y - pad), min(W, x + w + pad), min(H, y + h + pad)
    card = Image.new('RGBA', (w, h), (255, 255, 255, 255))
    if X1 > X0 and Y1 > Y0:
        reg = cv2.GaussianBlur(src[Y0:Y1, X0:X1], (0, 0), 16)
        full = np.full((h + 2 * pad, w + 2 * pad, 3), 255, np.uint8)
        ox, oy = X0 - (x - pad), Y0 - (y - pad)
        full[oy:oy + (Y1 - Y0), ox:ox + (X1 - X0)] = reg
        crop = full[pad:pad + h, pad:pad + w].astype(np.float32) * (1 - tint) + 255 * tint
        card = Image.fromarray(crop.astype(np.uint8)).convert('RGBA')
    ImageDraw.Draw(card).line((r, 1, w - r, 1), fill=(255, 255, 255, 255), width=2)
    card.putalpha(rr_mask(w, h, r))
    return card

def card_shadow(w, h, r=26):
    s = Image.new('RGBA', (w + 60, h + 60), (0, 0, 0, 0))
    ImageDraw.Draw(s).rounded_rectangle((30, 36, 30 + w, 36 + h), r, fill=(0, 0, 0, 70))
    return s.filter(ImageFilter.GaussianBlur(12))

def pill(d, x, y, text, bg, fg=(255, 255, 255), font=None, a=255):
    font = font or F('Bold', 15); tw = d.textlength(text, font=font)
    d.rounded_rectangle((x, y, x + tw + 22, y + 28), 14, fill=tuple(bg) + (a,))
    d.text((x + 11, y + 14), text, font=font, fill=tuple(fg) + (a,), anchor='lm')
    return tw + 22

def check(d, x, y, p, c=GREEN):
    d.ellipse((x, y, x + 22, y + 22), fill=c)
    pts = [(x + 6, y + 11.5), (x + 10, y + 15.5), (x + 17, y + 7)]
    if p > 0:
        a = clamp(p * 2); d.line([pts[0], (pts[0][0] + (pts[1][0] - pts[0][0]) * a, pts[0][1] + (pts[1][1] - pts[0][1]) * a)], fill='white', width=3)
    if p > 0.5:
        b = clamp((p - 0.5) * 2); d.line([pts[1], (pts[1][0] + (pts[2][0] - pts[1][0]) * b, pts[1][1] + (pts[2][1] - pts[1][1]) * b)], fill='white', width=3)

def toggle(d, x, y, p):
    c = tuple(int(200 + (cc - 200) * p) for cc in GREEN)
    d.rounded_rectangle((x, y, x + 48, y + 28), 14, fill=c)
    kx = x + 3 + 20 * ease(p); d.ellipse((kx, y + 3, kx + 22, y + 25), fill='white')

def wrap(text, font, width, d):
    words = text.split(); lines = []; cur = ''
    for w_ in words:
        t2 = (cur + ' ' + w_).strip()
        if d.textlength(t2, font=font) <= width: cur = t2
        else: lines.append(cur); cur = w_
    lines.append(cur); return lines

# ---------------------------------------------------------------- generic card widget
CW = 340; CARD_X, CARD_Y = 330 - CW // 2, 670
def rel(v, s):
    """Row time: number = seconds after card entry, string = phrase (absolute) -> relative."""
    if v is None: return 0.0
    return float(v) if isinstance(v, (int, float)) else T(v) - s

def draw_card_content(d, spec, u, s):
    y = 18
    d.text((20, y), spec['title'], font=F('Bold', 20), fill=INK); y += 30
    if spec.get('subtitle'):
        d.text((20, y - 2), spec['subtitle'], font=F('Medium', 14), fill=GRAY); y += 22
    y += 6
    for row in spec.get('rows', []):
        ty = row.get('type', 'text'); at = rel(row.get('at'), s); a = int(255 * clamp((u - at + 0.25) * 4)) if ty != 'counter' else 255
        if ty == 'counter':
            p = ease((u - at) / row.get('dur', 1.8)); n = row.get('from', 0) + (row['to'] - row.get('from', 0)) * p
            txt = f"{row.get('prefix', '')}{int(n):,}"; f = F('ExtraBold', 40)
            d.text((20, y), txt, font=f, fill=INK)
            if row.get('suffix'): d.text((26 + d.textlength(txt, font=f), y + 18), row['suffix'], font=F('Medium', 16), fill=GRAY)
            y += 54
            d.rounded_rectangle((20, y, CW - 20, y + 10), 5, fill=(225, 225, 230))
            d.rounded_rectangle((20, y, 20 + (CW - 40) * p, y + 10), 5, fill=col(row.get('color', 'red')))
            y += 22
        elif ty == 'check':
            if u >= at - 0.25:
                d.text((54, y + 11), row['text'], font=F('SemiBold', 16), fill=INK + (a,), anchor='lm')
                check(d, 20, y, clamp((u - at) * 3), col(row.get('color', 'green')))
            y += 38
        elif ty == 'pending':
            if u >= at - 0.25:
                lines = wrap(row['text'], F('SemiBold', 16), CW - 80, d)
                for k, ln in enumerate(lines): d.text((54, y + 11 + k * 20), ln, font=F('SemiBold', 16), fill=INK + (a,), anchor='lm')
                d.ellipse((20, y, 42, y + 22), outline=col(row.get('color', 'rose')) + (a,), width=3)
            y += 18 + 20 * len(wrap(row['text'], F('SemiBold', 16), CW - 80, d))
        elif ty == 'toggle':
            d.text((20, y + 14), row['text'], font=F('SemiBold', 16), fill=INK, anchor='lm')
            toggle(d, CW - 68, y, clamp((u - at) * 3)); y += 42
        elif ty == 'typing':
            d.rounded_rectangle((20, y, CW - 20, y + 38), 12, fill=(240, 240, 244), outline=(220, 220, 228))
            txt = row['text']; n = int(clamp((u - at) / row.get('dur', 1.2)) * len(txt)); pre = row.get('prefix', '')
            f = F('Medium', 16); d.text((36, y + 19), pre + txt[:n], font=f, fill=INK, anchor='lm')
            if n < len(txt) and int(u * 4) % 2 == 0:
                cx = 37 + d.textlength(pre + txt[:n], font=f); d.line((cx, y + 9, cx, y + 29), fill=INK, width=2)
            y += 48
        elif ty == 'chips':
            x = 20; ats = row.get('ats') or [at + 0.4 * k for k in range(len(row['items']))]
            for k, it in enumerate(row['items']):
                ak = rel(ats[k], s) if k < len(ats) else at
                if u < ak - 0.25: continue
                x += pill(d, x, y, it, col(row.get('color', 'ink')), font=F('SemiBold', 14), a=int(255 * clamp((u - ak + 0.25) * 4))) + 8
            y += 40
        elif ty == 'file':
            if u >= at - 0.25:
                d.rounded_rectangle((20, y, 44, y + 24), 5, fill=(230, 232, 240, a))
                d.text((32, y + 12), '</>', font=F('Bold', 9), fill=INK + (a,), anchor='mm')
                d.text((54, y + 12), row['text'], font=F('SemiBold', 16), fill=INK + (a,), anchor='lm')
                if u > at + 1.1: check(d, CW - 44, y + 1, clamp((u - at - 1.1) * 3))
                else: d.text((CW - 22, y + 12), 'Reading…', font=F('Medium', 13), fill=GRAY + (a,), anchor='rm')
            y += 36
        elif ty == 'field':
            d.text((20, y + 14), row['label'], font=F('Medium', 14), fill=GRAY, anchor='lm')
            pill(d, 24 + d.textlength(row['label'], font=F('Medium', 14)), y, row['value'], (235, 236, 242), fg=INK, font=F('SemiBold', 14)); y += 38
        elif ty == 'type_text':
            txt = row['text']; n = int(clamp((u - at) / row.get('dur', 1.8)) * len(txt)); f = F('Medium', 15)
            d.text((20, y), txt[:n], font=f, fill=INK)
            if n < len(txt) and int(u * 4) % 2 == 0:
                cx = 21 + d.textlength(txt[:n], font=f); d.line((cx, y, cx, y + 18), fill=INK, width=2)
            y += 28
        elif ty == 'bars':
            vals = row['values']; mx = max(vals); bw = (CW - 40 - 8 * (len(vals) - 1)) / len(vals)
            for k, v in enumerate(vals):
                p = ease((u - at - k * 0.12) / 0.6); hh = 70 * v / mx * p
                d.rounded_rectangle((20 + k * (bw + 8), y + 70 - hh, 20 + k * (bw + 8) + bw, y + 70), 4, fill=col(row.get('color', 'yellow')))
            y += 82
        else:  # text
            f = F('Bold' if row.get('bold') else 'Medium', row.get('size', 16))
            for ln in wrap(row['text'], f, CW - 40, d):
                d.text((20, y), ln, font=f, fill=INK + (a,)); y += row.get('size', 16) + 6
            y += 4
    if spec.get('pill'):
        pp = spec['pill']; at = rel(pp.get('at'), s)
        if u > at:
            pill(d, 20, y + 2, pp['text'], col(pp.get('color', 'ink')), a=int(255 * clamp((u - at) * 4)))
        y += 40
    return y + 16

def card_height(spec):
    tmp = Image.new('RGBA', (CW, 600)); return draw_card_content(ImageDraw.Draw(tmp), spec, 99, 0)

def draw_cards(base, src, t):
    carded = [b for b in BEATS if b.get('card')]
    for i, b in enumerate(carded):
        s, e = b['_s'], b['_e']
        if t < s: continue
        later = [c for c in carded[i + 1:] if c['_s'] <= t and c['_side'] == b['_side']]
        if b['_side'] != (1 if (TK and t >= TK_E) else 0) and TK: continue
        if len(later) >= 2: continue
        u = t - s
        if not later:
            x = CARD_X + (W - CARD_X) * (1 - spring(u, 6.5, 11)); a = 1.0
        else:
            v = ease((t - later[0]['_s']) / 0.45)
            x = CARD_X + (-CW + 70 - CARD_X) * v; a = 1 - 0.45 * v
        if TK and b['_side'] == 0 and t > TK_S - 0.3: a *= 1 - clamp((t - (TK_S - 0.3)) * 4)
        if t > END_START - 0.3: a *= 1 - clamp((t - (END_START - 0.3)) * 4)
        if a <= 0.01: continue
        tmp = Image.new('RGBA', (CW, 600), (0, 0, 0, 0))
        hh = draw_card_content(ImageDraw.Draw(tmp), b['card'], u, s)
        card = frosted(src, x, CARD_Y, CW, hh)
        card.alpha_composite(tmp.crop((0, 0, CW, hh)))
        if b['card'].get('example_data', True):
            ImageDraw.Draw(card).text((CW - 16, hh - 12), 'Example data', font=F('Medium', 10), fill=(150, 150, 160), anchor='rm')
        card.putalpha(Image.fromarray(np.minimum(np.array(card.getchannel('A')), np.array(rr_mask(CW, hh, 26)))))
        paste(base, card_shadow(CW, hh), x - 30, CARD_Y - 30, a)
        paste(base, card, x, CARD_Y, a)

# ---------------------------------------------------------------- headlines
def draw_heads(base, t):
    for b in BEATS:
        if not b.get('headline') or not (b['_s'] <= t < b['_e']): continue
        u = t - b['_s']; out = clamp((b['_e'] - t) * 5)
        words = b['headline'].split(); hl = set(b.get('highlight', []))
        if isinstance(b.get('highlight'), str):
            hw = [norm(x) for x in b['highlight'].split()]
            hl = {k for k in range(len(words)) if norm(words[k]) in hw}
        size = 39
        while True:
            f = F('ExtraBold', size); gap = int(size * 0.28)
            widths = [f.getlength(w_) for w_ in words]; tot = sum(widths) + gap * (len(words) - 1)
            if tot <= 560 or size <= 28: break
            size -= 1
        x = max(24, 330 - tot / 2); y = 600
        if b.get('chip'):
            l = Image.new('RGBA', (60, 32), (0, 0, 0, 0)); dd = ImageDraw.Draw(l)
            dd.rounded_rectangle((0, 0, 59, 31), 8, fill=YEL + (255,)); dd.text((30, 16), b['chip'], font=F('ExtraBold', 18), fill=INK, anchor='mm')
            paste(base, l, 300, 548 - (1 - ease(u * 4)) * 10, clamp(u * 5) * out)
        if hl:
            hx0 = x + sum(widths[:min(hl)]) + gap * min(hl) - 6
            hx1 = x + sum(widths[:max(hl) + 1]) + gap * max(hl) + 6
            p = ease((u - 0.5) / 0.4)
            if p > 0:
                l = Image.new('RGBA', base.size, (0, 0, 0, 0))
                ImageDraw.Draw(l).rounded_rectangle((hx0, y + 4, hx0 + (hx1 - hx0) * p, y + size + 11), 8, fill=YEL + (int(255 * out),))
                base.alpha_composite(l)
        for i, w_ in enumerate(words):
            p = ease((u - i * 0.09) / 0.35); on = i in hl and u > 0.7
            shadow_text(base, (x, y + (1 - p) * 18), w_, f, INK if on else (255, 255, 255), alpha=p * out, sh=0 if on else 0.6)
            x += widths[i] + gap

# ---------------------------------------------------------------- hook + orbit carousel
def icon(d, name, cx, cy, s, c=INK):
    k = s / 40; lw = max(2, int(3 * k)); n = name.lower()
    if n in ('login', 'lock', 'security'):
        d.rounded_rectangle((cx - 12 * k, cy - 2 * k, cx + 12 * k, cy + 16 * k), 4 * k, fill=c)
        d.arc((cx - 8 * k, cy - 16 * k, cx + 8 * k, cy + 4 * k), 180, 360, fill=c, width=lw)
    elif n in ('forms', 'docs', 'drive', 'notes'):
        d.rounded_rectangle((cx - 13 * k, cy - 15 * k, cx + 13 * k, cy + 15 * k), 4 * k, outline=c, width=lw)
        for j in range(3): d.line((cx - 7 * k, cy - 6 * k + j * 7 * k, cx + 7 * k, cy - 6 * k + j * 7 * k), fill=c, width=lw)
    elif n in ('plugins', 'apps', 'orders'):
        d.rounded_rectangle((cx - 12 * k, cy - 8 * k, cx + 12 * k, cy + 14 * k), 4 * k, fill=c)
        d.ellipse((cx - 5 * k, cy - 16 * k, cx + 5 * k, cy - 4 * k), fill=c)
    elif n == 'cookies':
        d.ellipse((cx - 14 * k, cy - 14 * k, cx + 14 * k, cy + 14 * k), fill=(196, 140, 80))
        for ox, oy in ((-5, -4), (5, 2), (-2, 7), (6, -7)): d.ellipse((cx + (ox - 2) * k, cy + (oy - 2) * k, cx + (ox + 2) * k, cy + (oy + 2) * k), fill=(90, 55, 30))
    elif n in ('admin', 'people', 'team', 'social', 'clients'):
        d.ellipse((cx - 7 * k, cy - 15 * k, cx + 7 * k, cy - 1 * k), fill=c)
        d.pieslice((cx - 14 * k, cy + 1 * k, cx + 14 * k, cy + 29 * k), 180, 360, fill=c)
    elif n in ('keys', 'key'):
        d.ellipse((cx - 14 * k, cy - 14 * k, cx, cy), outline=c, width=max(2, int(4 * k)))
        d.line((cx - 3 * k, cy - 3 * k, cx + 13 * k, cy + 13 * k), fill=c, width=max(2, int(4 * k)))
        d.line((cx + 7 * k, cy + 7 * k, cx + 11 * k, cy + 3 * k), fill=c, width=max(2, int(4 * k)))
    elif n in ('inbox', 'email', 'mail'):
        d.rounded_rectangle((cx - 15 * k, cy - 11 * k, cx + 15 * k, cy + 11 * k), 3 * k, outline=c, width=lw)
        d.line((cx - 15 * k, cy - 10 * k, cx, cy + 2 * k, cx + 15 * k, cy - 10 * k), fill=c, width=lw)
    elif n in ('calendar', 'schedule'):
        d.rounded_rectangle((cx - 14 * k, cy - 12 * k, cx + 14 * k, cy + 14 * k), 3 * k, outline=c, width=lw)
        d.rectangle((cx - 14 * k, cy - 12 * k, cx + 14 * k, cy - 4 * k), fill=c)
    elif n in ('chart', 'reports', 'analytics', 'data'):
        for j, hh in enumerate((8, 16, 24)): d.rectangle((cx - 13 * k + j * 10 * k, cy + 12 * k - hh * k, cx - 6 * k + j * 10 * k, cy + 12 * k), fill=c)
    else:  # website / default browser window
        d.rounded_rectangle((cx - 15 * k, cy - 12 * k, cx + 15 * k, cy + 12 * k), 4 * k, outline=c, width=lw)
        d.line((cx - 15 * k, cy - 5 * k, cx + 15 * k, cy - 5 * k), fill=c, width=lw)

def draw_hook(base, src, t):
    if not HOOK or t > HOOK_E + 0.1: return
    out = 1 - clamp((t - (HOOK_E - 0.3)) * 4)
    tiles = HOOK.get('tiles', ['Inbox', 'Calendar', 'Website', 'Social', 'Drive', 'Reports'])
    items = []
    for i, name in enumerate(tiles):
        a = t * 0.95 + i * 2 * math.pi / len(tiles); z = (math.sin(a) + 1) / 2
        items.append((z, 360 + 235 * math.cos(a), 830 + 70 * math.sin(a), name))
    for z, x, y, name in sorted(items):
        s = int(64 + 34 * z); r = int(s * 0.26)
        tile = frosted(src, x - s / 2, y - s / 2, s, s, r=r, tint=0.72); d = ImageDraw.Draw(tile)
        icon(d, name, s / 2, s / 2 - s * 0.08, s * 0.62)
        d.text((s / 2, s - s * 0.13), name, font=F('SemiBold', max(9, int(s * 0.13))), fill=INK, anchor='mm')
        tile.putalpha(Image.fromarray(np.minimum(np.array(tile.getchannel('A')), np.array(rr_mask(s, s, r)))))
        a_ = (0.45 + 0.55 * z) * out
        paste(base, card_shadow(s, s, r), x - s / 2 - 30, y - s / 2 - 30, a_ * 0.8)
        paste(base, tile, x - s / 2, y - s / 2, a_)
    y0 = HOOK.get('y', 486)
    shadow_text(base, (360, y0), HOOK['setup'], F('Bold', 31), (255, 255, 255), alpha=out, anchor='mm', sh=0.75)
    keys = HOOK['key'] if isinstance(HOOK['key'], list) else [HOOK['key']]
    size = 52
    while max(F('Black', size).getlength(k) for k in keys) > 640 and size > 34: size -= 2
    for j, line in enumerate(keys):
        shadow_text(base, (360, y0 + 56 + j * (size + 8)), line, F('Black', size), YEL, alpha=out, anchor='mm', sh=0.8)

# ---------------------------------------------------------------- captions
def draw_caps(base, t):
    for a, b, txt in CAPS:
        if a <= t < b:
            f = F('SemiBold', 24); tw = f.getlength(txt)
            l = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(l)
            d.rounded_rectangle((360 - tw / 2 - 14, 943, 360 + tw / 2 + 14, 985), 12, fill=(0, 0, 0, 150))
            d.text((360, 964), txt, font=f, fill='white', anchor='mm')
            base.alpha_composite(l); return

# ---------------------------------------------------------------- full-screen takeover card
PCW, PCY = 656, 168
def build_takeover_card():
    body_size = TK.get('body_size', 22)
    for attempt in range(8):
        card, hc = _build_tk(body_size)
        if PCY + hc <= 1000 - 40 or body_size <= 15: return card
        body_size -= 1
    return card

def _build_tk(bs):
    fb = F('Medium', bs); lh = int(bs * 1.41)
    txt = Image.new('RGBA', (PCW, 1400), (0, 0, 0, 0)); d = ImageDraw.Draw(txt)
    lab_f = F('ExtraBold', 18); lab = TK.get('label', 'SCREENSHOT THIS'); lw = d.textlength(lab, font=lab_f)
    d.rounded_rectangle((28, 26, 28 + 50 + lw + 18, 66), 20, fill=YEL)
    cx, cy = 54, 46
    d.rounded_rectangle((cx - 14, cy - 9, cx + 14, cy + 11), 4, fill=INK); d.rectangle((cx - 6, cy - 13, cx + 4, cy - 8), fill=INK)
    d.ellipse((cx - 6, cy - 5, cx + 6, cy + 7), fill=YEL); d.ellipse((cx - 3, cy - 2, cx + 3, cy + 4), fill=INK)
    d.text((78, 46), lab, font=lab_f, fill=INK, anchor='lm')
    if TK.get('kicker'): d.text((PCW - 28, 46), TK['kicker'], font=F('Bold', 14), fill=ROSE, anchor='rm')
    y = 88
    if TK.get('title'):
        for ln in wrap(TK['title'], F('Bold', 25), PCW - 56, d):
            d.text((28, y), ln, font=F('Bold', 25), fill=INK); y += 32
        y += 10
    d.line((28, y, PCW - 28, y), fill=(232, 232, 238), width=2); y += 18
    box_top = y - 6; y += 14
    hl = TK.get('highlight')
    for item in TK['body']:
        if 'n' in item:
            lines = wrap(item['text'], fb, PCW - 56 - 64, d); x0 = 76
            d.text((46, y), item['n'], font=F('ExtraBold', bs), fill=ROSE)
        else:
            lines = wrap(item.get('p', item.get('text', '')), fb, PCW - 56 - 32, d); x0 = 44
        for ln in lines:
            if hl and hl in ln:
                hx = x0 + d.textlength(ln.split(hl)[0], font=fb); hw = d.textlength(hl, font=fb)
                d.rounded_rectangle((hx - 4, y - 1, hx + hw + 4, y + bs + 7), 6, fill=YEL)
            d.text((x0, y), ln, font=fb, fill=INK); y += lh
        y += int(bs * 0.6)
    box_bot = y; hc = box_bot + (64 if TK.get('footer') else 28)
    card = Image.new('RGBA', (PCW, hc), (0, 0, 0, 0)); dc = ImageDraw.Draw(card)
    dc.rounded_rectangle((0, 0, PCW - 1, hc - 1), 30, fill=(255, 255, 255, 255))
    dc.rounded_rectangle((28, box_top, PCW - 28, box_bot), 18, fill=(245, 246, 250, 255), outline=(225, 227, 235, 255), width=2)
    card.alpha_composite(txt.crop((0, 0, PCW, hc)))
    if TK.get('footer'):
        ImageDraw.Draw(card).text((28, box_bot + 32), TK['footer'], font=F('SemiBold', 15), fill=GRAY, anchor='lm')
    card.putalpha(Image.fromarray(np.minimum(np.array(card.getchannel('A')), np.array(rr_mask(PCW, hc, 30)))))
    return card, hc

PCARD = None
random.seed(7)
SHARDS = []
for i in range(16):
    a1 = i * 2 * math.pi / 16 + random.uniform(-0.12, 0.12); a2 = (i + 1) * 2 * math.pi / 16 + random.uniform(-0.12, 0.12)
    SHARDS.append([(360 + random.uniform(-30, 30), 600 + random.uniform(-30, 30)),
                   (360 + 1500 * math.cos(a1), 600 + 1500 * math.sin(a1)), (360 + 1500 * math.cos(a2), 600 + 1500 * math.sin(a2))])

def takeover(base, src, t):
    global PCARD
    if PCARD is None: PCARD = build_takeover_card()
    u = t - TK_S; hc = PCARD.size[1]
    exit_p = ease((t - (TK_E - 0.42)) / 0.42)
    bg = cv2.GaussianBlur(src, (0, 0), 14).astype(np.float32) * 0.42 + np.array([12, 12, 18]) * 0.58
    bga = clamp(u / 0.25) * (1 - exit_p)
    cur = np.array(base.convert('RGB')).astype(np.float32)
    base.paste(Image.fromarray((cur * (1 - bga) + bg * bga).astype(np.uint8)).convert('RGBA'))
    style = TK.get('style', 'bust')
    if style == 'bust' and u < 0.6:
        sp = u / 0.6; fimg = Image.fromarray(src).convert('RGBA')
        for k, tri in enumerate(SHARDS):
            mask = Image.new('L', (W, H), 0); md = ImageDraw.Draw(mask); md.polygon(tri, fill=255); md.line(tri + [tri[0]], fill=0, width=3)
            sh = fimg.copy(); sh.putalpha(mask)
            ang = math.atan2((tri[1][1] + tri[2][1]) / 2 - 600, (tri[1][0] + tri[2][0]) / 2 - 360)
            sc = 1 + sp * 0.7; dist = sp ** 1.6 * 900
            sh2 = sh.rotate((k % 2 * 2 - 1) * sp * 25, center=(360, 600), resample=Image.BILINEAR).resize((int(W * sc), int(H * sc)), Image.BILINEAR)
            paste(base, sh2, 360 - 360 * sc + math.cos(ang) * dist, 600 - 600 * sc + math.sin(ang) * dist, 1 - sp ** 2)
        if u < 0.18: base.alpha_composite(Image.new('RGBA', base.size, (255, 255, 255, int(255 * (1 - u / 0.18) * 0.85))))
    if u >= 0.06:
        uu = u - 0.06
        if style == 'bust':
            s = (0.25 + 0.75 * spring(uu, 7.5, 12)) * (1 - 0.25 * exit_p); rot = -7 * math.exp(-uu * 6) * math.cos(uu * 10); dy = 0
        else:  # 'slide': card rises from the bottom
            s = 1 - 0.25 * exit_p; rot = 0; dy = (1 - spring(uu, 6.5, 10)) * 1100
        cimg = PCARD.resize((max(2, int(PCW * s)), max(2, int(hc * s))), Image.LANCZOS)
        if abs(rot) > 0.3: cimg = cimg.rotate(rot, expand=True, resample=Image.BICUBIC)
        cy = PCY + hc / 2 - exit_p * 900 + dy
        x, y = 360 - cimg.size[0] / 2, cy - cimg.size[1] / 2
        paste(base, card_shadow(cimg.size[0], cimg.size[1], 30), x - 30, y - 24, 0.9 * (1 - exit_p))
        paste(base, cimg, x, y, 1 - exit_p * 0.3)
    fl = u - 1.6
    if 0 <= fl < 0.35: base.alpha_composite(Image.new('RGBA', base.size, (255, 255, 255, int(255 * 0.55 * (1 - fl / 0.35)))))
    ha = clamp((u - 2.0) * 3) * (1 - exit_p)
    if ha > 0 and TK.get('hint', 'Pause and grab it') and PCY + hc + 30 < 930:
        shadow_text(base, (360, PCY + hc + 30), TK.get('hint', 'Pause and grab it'), F('SemiBold', 20), (255, 255, 255), alpha=ha, anchor='mm')

def shake(arr, t):
    u = t - TK_S
    if TK and TK.get('style', 'bust') == 'bust' and 0 <= u < 0.35:
        amp = 14 * (1 - u / 0.35)
        M = np.float32([[1, 0, int(amp * math.sin(u * 90))], [0, 1, int(amp * math.cos(u * 70))]])
        return cv2.warpAffine(arr, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return arr

# ---------------------------------------------------------------- end card
def end_card(t):
    img = Image.new('RGBA', (W, H), (0, 0, 0, 255)); u = t - END_START
    rows = [(END.get('line1', 'Always assume'), F('ExtraBold', 50), (255, 255, 255), 560),
            (END.get('line2', 'I used AI.'), F('Black', 64), YEL, 632),
            (END.get('name', 'Dr. Denise Turley'), F('SemiBold', 24), (150, 150, 158), 730)]
    for j, (txt, f, c, y) in enumerate(rows):
        p = ease((u - 0.25 - j * 0.18) / 0.45)
        shadow_text(img, (360, y + (1 - p) * 20), txt, f, c, alpha=p, anchor='mm', sh=0)
    disc = END.get('disclosure', 'This video is generated with AI for illustrative purposes.')
    if disc: shadow_text(img, (360, 960), disc, F('Medium', 15), (130, 130, 138), alpha=ease((u - 0.9) / 0.5), anchor='mm', sh=0)
    return img

# ---------------------------------------------------------------- frame compositor
def compose(rgb_src, t):
    if (SW, SH) != (W, H):  # fit any source into 720x1280 (cover)
        sc = max(W / SW, H / SH); rs = cv2.resize(rgb_src, (int(SW * sc + 0.5), int(SH * sc + 0.5)), interpolation=cv2.INTER_AREA)
        oy, ox = (rs.shape[0] - H) // 2, (rs.shape[1] - W) // 2; rgb_src = rs[oy:oy + H, ox:ox + W]
    v = shake(camera(rgb_src, min(t, SRC_DUR - 0.01)), t)
    base = Image.fromarray(v).convert('RGBA')
    if TK and TK_S <= t < TK_E: takeover(base, v, t)
    else:
        draw_hook(base, v, t); draw_cards(base, v, t); draw_heads(base, t)
    if t < END_START + 0.2: draw_caps(base, t)
    if END is not None and t >= END_START:
        base = Image.blend(base, end_card(t), ease((t - END_START) / 0.35))
    return np.array(base.convert('RGB'))

# ---------------------------------------------------------------- sound effects
def build_sfx(path):
    import wave
    SR = 48000; out = np.zeros(int(SR * (TOTAL + 1))); rng = np.random.default_rng(3)
    def add(t, sig, g):
        i = int(t * SR); n = min(len(sig), len(out) - i)
        if n > 0 and i >= 0: out[i:i + n] += sig[:n] * g
    def whoosh(d=0.45):
        n = int(SR * d); x = rng.standard_normal(n); env = np.sin(np.linspace(0, np.pi, n)) ** 2
        a = 0.02 + 0.25 * np.arange(n) / n; y = np.zeros(n); acc = 0.0
        for k in range(n): acc += a[k] * (x[k] - acc); y[k] = acc
        return y * env / (np.abs(y).max() + 1e-9)
    tt = lambda d: np.arange(int(SR * d)) / SR
    thump = lambda: np.sin(2 * np.pi * (90 * np.exp(-tt(.5) * 6)) * tt(.5)) * np.exp(-tt(.5) * 9)
    def glass():
        t_ = tt(.6); x = rng.standard_normal(len(t_)); hp = np.diff(np.concatenate([[0], x]))
        return hp * 0.5 * np.exp(-t_ * 10) + 0.25 * sum(np.sin(2 * np.pi * f * t_) * np.exp(-t_ * r) for f, r in ((3100, 9), (4700, 12), (6300, 15), (2300, 8)))
    def click():
        t_ = tt(.12); x = rng.standard_normal(len(t_)); return x * np.exp(-t_ * 80) + np.roll(x * np.exp(-t_ * 90), int(SR * .05)) * 0.7
    for b in BEATS:
        if b.get('card'): add(b['_s'], whoosh(), 0.10)
    if TK:
        add(TK_S - 0.15, whoosh(0.3), 0.12)
        if TK.get('style', 'bust') == 'bust': add(TK_S - 0.05, thump(), 0.35); add(TK_S, glass(), 0.12)
        add(TK_S + 1.6, click(), 0.10); add(TK_E - 0.4, whoosh(0.4), 0.10)
    if END is not None: add(END_START, whoosh(0.6), 0.08)
    pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
    w = wave.open(path, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()

# ---------------------------------------------------------------- QA
def qa_report():
    lines = []; ok = True
    def flag(msg):
        nonlocal ok; ok = False; lines.append('FAIL ' + msg)
    lines.append(f'source {SRC_DUR:.2f}s, speech ends {SPEECH_END:.2f}s, output {TOTAL:.2f}s')
    for s in SHOTS[1:]:
        c = s[0]; inside = [w_ for w_ in TIMED if w_[1] + 0.05 < c < w_[2] - 0.05]
        if inside: flag(f'camera cut at {c:.2f}s lands inside the word "{inside[0][0]}"')
    lines.append(f'{len(SHOTS)} shots at ' + ', '.join(f'{s[0]:.2f}' for s in SHOTS))
    if TK:
        lines.append(f'takeover {TK_S:.2f}-{TK_E:.2f}s ({TK_E - TK_S:.1f}s)')
        if TK_E - TK_S < 6: flag('takeover shorter than 6 s; too short to screenshot')
        hc = build_takeover_card().size[1]
        if PCY + hc > 1000: flag(f'takeover card bottom at y {PCY + hc} (safe zone ends at 1000)')
    for b in BEATS:
        if b.get('card'):
            h = card_height(b['card'])
            if CARD_Y + h > 935: flag(f'card "{b["card"]["title"]}" is {h}px tall and overlaps captions; cut rows')
        if b['_e'] - b['_s'] < 1.5: flag(f'beat "{b.get("headline")}" only {b["_e"] - b["_s"]:.1f}s on screen')
    for a, b, txt in CAPS:
        if len(txt.split()) > 7: flag(f'caption too long: "{txt}"')
    miss = [w_ for w_ in SCRIPT.split() if not norm(w_)]
    unmatched = sum(1 for k in difflib.SequenceMatcher(None, [norm(x) for x in SCRIPT.split()], [norm(x[0]) for x in asr_tokens()], autojunk=False).get_opcodes() if k[0] != 'equal')
    lines.append(f'script/ASR differing spans: {unmatched} (expected a handful where ASR misheard names)')
    lines.insert(0, 'QA PASS' if ok else 'QA ISSUES FOUND')
    return '\n'.join(lines)

def timeline():
    out = ['resolved timeline:']
    if HOOK: out.append(f'  hook        0.00-{HOOK_E:6.2f}')
    for b in BEATS: out.append(f"  beat     {b['_s']:6.2f}-{b['_e']:6.2f}  {b.get('headline', '')}")
    if TK: out.append(f'  takeover {TK_S:6.2f}-{TK_E:6.2f}')
    out.append(f'  end card {END_START:6.2f}-{TOTAL:6.2f}')
    return '\n'.join(out)

# ---------------------------------------------------------------- main
def main():
    cap = cv2.VideoCapture(SRC); src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    N = int(round(TOTAL * FPS)); last = None; src_idx = -1
    if STILLS:
        want = sorted(STILLS)
        for t in want:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(min(t, SRC_DUR - 0.05) * src_fps)); ok, fr = cap.read()
            Image.fromarray(compose(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB), t)).save(os.path.join(WORK, f'still_{t:05.2f}.png'))
        print('stills written\n'); print(timeline()); print(qa_report()); return
    vid = os.path.join(WORK, '_video_only.mp4')
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', vid], stdin=subprocess.PIPE)
    for n in range(N):
        t = n / FPS
        want_idx = int(min(t, SRC_DUR - 1 / src_fps) * src_fps + 1e-6)
        while src_idx < want_idx:
            ok, fr = cap.read()
            if not ok: break
            last = fr; src_idx += 1
        ff.stdin.write(compose(cv2.cvtColor(last, cv2.COLOR_BGR2RGB), t).tobytes())
    ff.stdin.close(); ff.wait()
    sfx = os.path.join(WORK, '_sfx.wav'); build_sfx(sfx)
    out = PLAN.get('output') or os.path.join(WORK, 'final.mp4')
    if HAS_AUDIO:
        fc = f'[1:a]aresample=48000,apad=whole_dur={TOTAL}[a1];[2:a]aresample=48000,pan=stereo|c0=c0|c1=c0[a2];[a1][a2]amix=inputs=2:normalize=0:duration=first[a]'
        cmd = ['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', SRC, '-i', sfx, '-filter_complex', fc, '-map', '0:v', '-map', '[a]']
    else:
        cmd = ['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', sfx, '-map', '0:v', '-map', '1:a']
    subprocess.run(cmd + ['-c:v', 'libx264', '-profile:v', 'main', '-level', '3.1', '-crf', '19', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-t', f'{TOTAL:.3f}', '-movflags', '+faststart', out], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', out, '-vf', 'fps=2/3,scale=160:-1,tile=9x4', '-frames:v', '1',
                    os.path.join(WORK, 'qa_sheet.jpg')], check=True)
    pr = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,start_time,duration', '-of', 'csv', out], capture_output=True, text=True).stdout
    rep = qa_report() + '\nffprobe:\n' + pr
    open(os.path.join(WORK, 'qa_report.txt'), 'w').write(rep)
    os.remove(vid); os.remove(sfx)
    print(rep); print('output:', out)

if __name__ == '__main__':
    main()
