"""TYPE ONE renderer (R34 GTT example).
Per video, change: AUDIO, the asset table A, words.json, MAN (narrator timeline) and BEATS (elements).
Usage: python3 render_type_one.py out.mp4   |   python3 render_type_one.py x 1.5,10,20  (preview stills)
"""
import json, glob, subprocess, sys, math, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import narrator as chars3

S = '/tmp/claude-0/-home-user-Introvert-niche-/4b8ae4f4-60f4-56d8-b6fb-0b7196bc6596/scratchpad'
U = '/root/.claude/uploads/4b8ae4f4-60f4-56d8-b6fb-0b7196bc6596'
OUT = sys.argv[1]
AUDIO = glob.glob(U + '/9652dd7a*.mp3')[0]
W, H, FPS = 1080, 1920, 30
DUR = 63.6

def up(i): return Image.open(glob.glob(f'{U}/{i}*')[0]).convert('RGBA')
def loc(n): return Image.open(f'{S}/a/{n}').convert('RGBA')
def crop(im):
    bb = im.getbbox(); return im.crop(bb) if bb else im

A = {k: crop(v) for k, v in {
    'gtr': up('a35df269'), 'gtt': loc('gtt_stock.png'), 'purple': up('1089579e'),
    'rear': up('48fdd753'), 'chassis': up('b4f1c104'), 'engine': up('6f29e0a8'),
    'hood': up('80bb760d'), 'ic': up('ddc4e646'), 'turbo': up('cbab4c8d'), 'inj': up('e6b1fdac'),
    'pump': loc('fuelpump.png'), 'exhaust': up('dbcd9419'), 'clutch': up('d5a83a97'),
    'money': up('75bd2d67')}.items()}
A['ecu'] = crop(loc('ecu.png'))
FULL = {'dork': up('c53d4130'), 'tumble': up('1858ef58'), 'drift': up('eaf9bcae'),
        'dyno': up('4ce3ca72'), 'launch': up('352160d8')}

FONT_CAP = ImageFont.truetype(os.path.join(HERE, '..', 'fonts', 'ComicNeue_700Bold.ttf'), 84)
BANG = os.path.join(HERE, '..', 'fonts', 'Bangers_400Regular.ttf')
_fc = {}
def fbig(s):
    if s not in _fc: _fc[s] = ImageFont.truetype(BANG, s)
    return _fc[s]

RED, ORA, BLU, GRN, WHT, NAVY = '#e53935', '#ff9800', '#1e88e5', '#43a047', 'white', '#14286e'

# ---------------- narrator timeline: (t, pos, arm, eyes, brows) ----------------
L_, R_ = 'pointL', 'pointR'
MAN = [
    (0.00, 'BIG', 'hips', 'C', 'up'),
    (0.38, 'R', L_, 'L', 'up'),
    (1.96, 'R', 'hips', 'C', 'one'),
    (2.60, 'R', L_, 'L', 'up'),
    (3.00, 'R', L_, 'L', 'N'),
    (4.12, 'R', 'hips', 'C', 'one'),
    (5.50, 'BIG', 'hips', 'C', 'N'),
    (5.90, 'R', L_, 'L', 'up'),
    (7.54, 'R', L_, 'L', 'N'),
    (8.94, 'R', L_, 'L', 'up'),
    (10.42, 'R', 'hips', 'C', 'N'),
    (11.14, 'R', L_, 'L', 'N'),
    (11.86, 'R', 'hips', 'C', 'one'),
    (12.60, 'BIG', 'hips', 'L', 'frown'),
    (13.50, 'BIG', 'hips', 'C', 'one'),
    (14.80, 'R', L_, 'L', 'N'),
    (15.62, 'R', 'hips', 'C', 'one'),
    (16.36, 'R', L_, 'L', 'N'),
    (16.58, 'R', L_, 'L', 'up'),
    (17.26, 'R', L_, 'L', 'N'),
    (18.22, 'R', 'hips', 'C', 'frown'),
    (19.98, 'R', L_, 'L', 'N'),
    (21.42, 'R', L_, 'L', 'up'),
    (22.78, 'R', L_, 'L', 'N'),
    (24.16, 'R', 'hips', 'C', 'up'),
    (25.54, 'R', L_, 'L', 'one'),
    (26.14, None, '', '', ''),
    (27.18, 'R', L_, 'L', 'N'),
    (29.66, 'R', 'hips', 'C', 'N'),
    (30.62, 'R', 'hips', 'L', 'up'),
    (32.14, 'BIG', 'hips', 'C', 'N'),
    (33.06, 'R', L_, 'L', 'up'),
    (34.28, 'R', 'hips', 'C', 'one'),
    (35.30, 'BIG', 'hips', 'R', 'one'),
    (37.02, 'BIG', 'hips', 'C', 'up'),
    (37.82, 'L', 'hips', 'C', 'N'),
    (38.72, 'R', L_, 'L', 'up'),
    (40.22, 'R', L_, 'L', 'N'),
    (41.74, 'R', 'hips', 'C', 'one'),
    (42.82, 'R', L_, 'L', 'N'),
    (43.74, 'R', L_, 'L', 'up'),
    (45.30, 'BIG', 'hips', 'C', 'N'),
    (47.26, 'BIG', 'hips', 'U', 'up'),
    (48.10, 'BIG', 'hips', 'C', 'frown'),
    (48.76, 'R', L_, 'L', 'up'),
    (49.62, 'R', L_, 'U', 'up'),
    (50.96, 'R', L_, 'U', 'N'),
    (51.64, 'R', L_, 'L', 'up'),
    (52.36, 'R', L_, 'L', 'N'),
    (53.16, 'R', L_, 'L', 'up'),
    (54.92, 'R', L_, 'U', 'one'),
    (56.48, 'R', 'hips', 'C', 'N'),
    (56.88, 'R', L_, 'L', 'up'),
    (57.74, 'R', L_, 'L', 'N'),
    (58.40, 'R', 'hips', 'C', 'one'),
    (59.24, 'R', L_, 'L', 'up'),
    (60.64, 'R', 'hips', 'C', 'one'),
    (61.76, 'R', 'hips', 'U', 'up'),
]

# ---------------- item beats: (t, [items]) ----------------
def I(k, cx, cy, mw, mh, t0): return ('img', k, cx, cy, mw, mh, t0)
def X(s, cx, cy, size, col, t0): return ('txt', s, cx, cy, size, col, t0)
def F(k, t0): return ('full', k, t0)

BEATS = [
    (0.00, []),
    (0.38, [X('$150,000', 360, 1130, 150, RED, 0.38), I('gtr', 360, 860, 640, 240, 1.42)]),
    (2.60, [I('gtt', 360, 980, 660, 250, 2.60)]),
    (3.00, [I('gtt', 360, 1180, 600, 230, 3.00), I('gtr', 360, 820, 600, 230, 3.34),
            X('IDENTICAL', 360, 1000, 100, BLU, 3.34), I('money', 360, 1420, 230, 160, 4.12),
            X('WAY LESS', 360, 1560, 100, GRN, 4.48)]),
    (5.50, []),
    (5.90, [X('R34 GT-T', 380, 720, 190, ORA, 5.90), I('gtt', 380, 1040, 700, 270, 6.44)]),
    (7.54, [I('gtt', 360, 980, 660, 250, 7.80), X('SAME SHELL', 360, 1210, 110, BLU, 8.34)]),
    (8.94, [I('rear', 360, 980, 560, 430, 9.56), X('ROUND TAILS', 360, 1270, 110, RED, 9.82)]),
    (10.42, [I('chassis', 360, 960, 620, 420, 11.14), X('SAME CHASSIS', 360, 1250, 100, BLU, 11.14),
             X('AS THE GT-R', 360, 1380, 90, WHT, 11.86)]),
    (12.60, []),
    (13.50, []),
    (14.80, [I('gtr', 360, 790, 620, 230, 14.80), X('VS', 360, 985, 130, ORA, 14.94), I('gtt', 360, 1180, 620, 230, 15.08),
             X('SAME?', 360, 1390, 110, WHT, 15.08)]),
    (15.62, [I('gtt', 360, 1000, 660, 250, 16.36),
             X('OVERLOOKED', 360, 1300, 130, RED, 16.58)]),
    (17.26, [X('NO BADGE', 360, 1320, 140, RED, 17.36), I('rear', 360, 960, 600, 450, 17.86),
             X('= NO HYPE TAX', 360, 1460, 95, WHT, 18.70)]),
    (19.98, [I('gtr', 360, 760, 620, 230, 20.16), X('6 FIGURES', 360, 960, 130, RED, 21.42),
             I('gtt', 360, 1190, 620, 230, 23.36), I('money', 600, 1370, 200, 140, 25.54),
             X('A FRACTION', 300, 1390, 105, GRN, 25.54)]),
    (26.14, [I('hood', 540, 1020, 1000, 700, 26.14)]),
    (27.18, [I('engine', 360, 930, 640, 470, 27.18), X('RB25DET NEO', 360, 1240, 115, BLU, 27.18),
             X('2.5L', 150, 1400, 105, ORA, 29.76), X('TURBO', 370, 1400, 105, ORA, 30.62),
             X('I6', 580, 1400, 105, ORA, 31.30)]),
    (32.14, []),
    (33.06, [X('250 HP', 360, 960, 210, ORA, 33.06), X('ON PAPER', 360, 1160, 110, WHT, 34.28)]),
    (35.30, []),
    (37.02, [X('SANDBAGGED', 540, 640, 165, RED, 37.02)]),
    (37.82, []),
    (38.72, [I('purple', 380, 900, 680, 240, 38.72), X('RWD', 380, 690, 170, ORA, 38.72)]),
    (42.82, [I('engine', 360, 950, 640, 470, 42.92), X('OVERBUILT', 360, 1270, 145, GRN, 43.74)]),
    (45.30, []),
    (48.76, [I('engine', 360, 990, 470, 340, 48.86),
             I('turbo', 140, 700, 250, 180, 49.62), X('HYBRID TURBO', 360, 1700, 110, BLU, 49.62),
             I('ic', 590, 700, 270, 180, 50.96), X('INTERCOOLER', 360, 1700, 110, BLU, 50.96),
             I('inj', 140, 1290, 250, 180, 51.64), X('INJECTORS', 360, 1700, 110, BLU, 51.64),
             I('pump', 590, 1290, 250, 170, 52.36), X('FUEL PUMP', 360, 1700, 110, BLU, 52.36),
             I('exhaust', 360, 1480, 430, 170, 53.16), X('3" EXHAUST', 360, 1700, 110, BLU, 53.16),
             I('clutch', 365, 640, 230, 160, 54.92), X('STRONGER CLUTCH', 360, 1700, 100, BLU, 54.92)]),
    (56.88, [I('ecu', 360, 1000, 620, 420, 56.88),
             X('DYNO TUNE', 360, 1290, 135, ORA, 56.88)]),
    (57.74, [I('purple', 540, 640, 1000, 330, 57.74), X('STOCK INTERNALS', 380, 1250, 105, GRN, 57.90),
             X('HOLD UP FINE', 380, 1380, 105, WHT, 58.40)]),
    (59.24, [I('purple', 540, 640, 1000, 330, 59.24),
             X('0-60', 360, 1010, 200, ORA, 59.96), X('4.2 - 4.5 SEC', 360, 1230, 120, WHT, 60.64)]),
]

def current(lst, t):
    cur = lst[0]
    for b in lst:
        if b[0] <= t: cur = b
    return cur

# ---------------- drawing ----------------
def pop(t, t0, d=0.13):
    x = (t - t0) / d
    if x >= 1: return 1.0
    if x < 0: return 0.0
    return 0.55 + 0.65 * x if x < 0.75 else 1.04 - 0.16 * (x - 0.75) / 0.25 * 0.25 / 0.25 * 0 + (1.04 - 1.0) * 0

_ic = {}
def fit(k, mw, mh):
    key = (k, mw, mh)
    if key not in _ic:
        im = A[k]; r = min(mw / im.width, mh / im.height)
        _ic[key] = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    return _ic[key]

def paste_scaled(fr, im, cx, cy, s):
    if s != 1.0:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))))
    fr.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

_full = {}
def draw_full(fr, k):
    if k not in _full:
        im = FULL[k]
        if im.height > im.width:
            _full[k] = (im.resize((W, H), Image.LANCZOS), 0)
        else:
            r = W / im.width
            _full[k] = (im.resize((W, int(im.height * r)), Image.LANCZOS), int(1050 - im.height * r / 2))
    im, y = _full[k]
    fr.alpha_composite(im, (0, y))

POS = {'R': (850, 1560, 0.568), 'L': (230, 1560, 0.568), 'C': (540, 1560, 0.62), 'BIG': (540, 2330, 1.1)}
_pc = {}
def man_img(arm, eyes, brows, blink, s):
    key = (arm, eyes, brows, blink, s)
    if key not in _pc:
        _pc[key] = chars3.render(arm, eyes, brows, blink, s)
    return _pc[key]

def draw_man(fr, t):
    t0, pos, arm, eyes, brows = current(MAN, t)
    if pos is None: return
    cx, fy, s = POS[pos]
    blink = (t % 2.9) < 0.1 and (t - t0) > 0.3
    im = man_img(arm, eyes, brows, blink, s)
    ax, ay = chars3.anchor(arm)
    fr.alpha_composite(im, (int(cx - ax * s), int(fy - ay * s)))

def draw_items(fr, t):
    _, items = current(BEATS, t)
    # the newest text that shares a position replaces older ones (used for mod labels)
    texts = {}
    for it in items:
        if it[0] == 'txt' and it[-1] <= t: texts[(it[2], it[3])] = it
    for it in items:
        if it[0] == 'full' and it[2] <= t: draw_full(fr, it[1])
    for it in items:
        if it[0] == 'img' and it[-1] <= t:
            _, k, cx, cy, mw, mh, t0 = it
            paste_scaled(fr, fit(k, mw, mh), cx, cy, popk(t, t0))
    for it in texts.values():
        _, s_, cx, cy, size, col, t0 = it
        k = popk(t, t0)
        ImageDraw.Draw(fr).text((cx, cy), s_, font=fbig(max(8, int(size * k))), fill=col, anchor='mm',
                                stroke_width=max(2, int(9 * k)), stroke_fill='black')

def popk(t, t0, d=0.13):
    x = (t - t0) / d
    if x >= 1: return 1.0
    if x <= 0: return 0.01
    return 0.5 + 0.7 * (x / 0.7) if x < 0.7 else 1.2 - 0.2 * (x - 0.7) / 0.3

# ---------------- captions ----------------
words = json.load(open(S + '/words.json'))
phrases, cur = [], []
for w in words:
    cur.append(w)
    if w['w'][-1] in '.,?!' or len(cur) >= 4:
        phrases.append(cur); cur = []
if cur: phrases.append(cur)

def draw_caption(fr, t):
    ph = None
    for p in phrases:
        if p[0]['s'] - 0.03 <= t: ph = p
    if ph is None: return
    txt = ' '.join(w['w'] for w in ph if w['s'] - 0.03 <= t).upper()
    d = ImageDraw.Draw(fr)
    lines, line = [], ''
    for w in txt.split():
        test = (line + ' ' + w).strip()
        if d.textlength(test, font=FONT_CAP) > 980 and line:
            lines.append(line); line = w
        else: line = test
    lines.append(line)
    y = 320 - (len(lines) - 1) * 42
    for ln in lines:
        d.text((W / 2, y), ln, font=FONT_CAP, fill=NAVY, anchor='mm', stroke_width=3, stroke_fill='white')
        y += 84

def frame(t):
    fr = Image.new('RGBA', (W, H), 'white')
    draw_items(fr, t)
    draw_man(fr, t)
    draw_caption(fr, t)
    return fr.convert('RGB')

# ---------------- sound effects ----------------
def build_sfx(path):
    sr = 44100
    out = np.zeros(int(sr * (DUR + 1)), np.float32)
    n = int(sr * 0.09); tt = np.arange(n) / sr
    popw = (np.sin(2 * np.pi * (950 * tt - 3500 * tt ** 2)) * np.exp(-tt / 0.022)).astype(np.float32)
    n2 = int(sr * 0.32); t2 = np.arange(n2) / sr
    rng = np.random.default_rng(1); nz = rng.standard_normal(n2)
    nz = np.convolve(nz, np.ones(18) / 18, 'same')
    whoosh = (nz * np.sin(np.pi * t2 / t2[-1]) ** 2 * 2.2).astype(np.float32)
    seen = set()
    for _, items in BEATS:
        for it in items:
            t0 = it[-1]; kind = 'w' if it[0] == 'full' else 'p'
            if (round(t0, 2), kind) in seen: continue
            seen.add((round(t0, 2), kind))
            snd = whoosh if kind == 'w' else popw
            i = int(t0 * sr); out[i:i + len(snd)] += snd[:len(out) - i] * (0.5 if kind == 'p' else 0.35)
    out = np.clip(out, -1, 1)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes((out * 32767).astype(np.int16).tobytes())

if len(sys.argv) > 2:
    for t in [float(x) for x in sys.argv[2].split(',')]:
        frame(t).save(f'{S}/p4_{t:05.2f}.jpg', quality=80)
    sys.exit()

build_sfx(S + '/sfx.wav')
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                      '-i', '-', '-i', AUDIO, '-i', S + '/sfx.wav',
                      '-filter_complex', '[1:a][2:a]amix=inputs=2:duration=first:normalize=0[a]',
                      '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                      '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT],
                     stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)):
    p.stdin.write(frame(i / FPS).tobytes())
p.stdin.close(); p.wait()
print('done', OUT)
