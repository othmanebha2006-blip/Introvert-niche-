"""TYPE TWO renderer: Mitsubishi 3000GT VR-4 (no dyno sound, 5 mods)."""
import json, glob, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/home/user/Introvert-niche-/type_one/scripts')
import narrator

S = '/tmp/claude-0/-home-user-Introvert-niche-/4b8ae4f4-60f4-56d8-b6fb-0b7196bc6596/scratchpad'
U = '/root/.claude/uploads/4b8ae4f4-60f4-56d8-b6fb-0b7196bc6596/'
W, H, FPS = 1080, 1920, 30
VOICE = glob.glob(U + '5bc6a8e4*')[0]
CLIP = {1: glob.glob(U + '57ff2974*')[0], 2: glob.glob(U + '1dd6ed17*')[0], 3: glob.glob(U + 'ef4ae6f6*')[0]}
CUT = 999.0          # end of the hook in the voiceover
GAP = 0.0           # silent B-roll break inserted after the hook
VOICE_LEN0 = 74.42
_W = json.load(open(S + '/gt/words.json'))
# pauses between sentences longer than 0.25 s are shortened: keep 0.08 s after a word, 0.06 s before the next
def _silences(path, thr=-40, mind=0.35):
    err = subprocess.run(['ffmpeg', '-i', path, '-af', f'silencedetect=n={thr}dB:d={mind}', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    import re
    st = [float(x) for x in re.findall(r'silence_start: ([0-9.]+)', err)]
    en = [float(x) for x in re.findall(r'silence_end: ([0-9.]+)', err)]
    return list(zip(st, en))
# only real silences are shortened, each down to 0.2 s (0.1 s kept on both sides)
CUTS = [(a + 0.1, b - 0.1) for a, b in _silences(VOICE) if b - a > 0.3 and a > 0.5 and b < VOICE_LEN0 - 0.5]
def M(x):           # original voice time -> tightened voice time
    d = 0.0
    for g0, g1 in CUTS:
        if x >= g1: d += g1 - g0
        elif x > g0: d += x - g0
    return x - d
def Minv(y):        # tightened voice time -> original voice time
    x, d = y, 0.0
    for g0, g1 in CUTS:
        if g0 - d <= y: d += g1 - g0
        else: break
    return y + d
VOICE_LEN = VOICE_LEN0
DUR = M(VOICE_LEN) + GAP + 0.1

def T(x):           # original voice time -> video time
    return M(x) if x < CUT else M(x) + GAP
def V2O(t):         # video time -> original voice time (break maps to CUT)
    if t < CUT: return Minv(t)
    if t < CUT + GAP: return CUT
    return Minv(t - GAP)

def up(i):
    im = Image.open(glob.glob(U + i + '*')[0]).convert('RGBA'); return im.crop(im.getbbox())
def ga(n): return Image.open(S + '/gt/a/' + n).convert('RGBA')
A = {'front': ga('front.png'), 'side': ga('side.png'), 'hood': ga('hood.png'), 'engine': up('dd550c08'),
     'turbo': up('c95ead79'), 'ic': ga('ic.png'), 'exh': up('8ec7b045'), 'fuel': up('1f21dec2'), 'ecu': ga('ecu.png'),
     'logo': up('4ad43085')}
CARS = {'front', 'hood', 'side'}
MODS = {'turbo', 'ic', 'exh', 'fuel', 'ecu'}

import os
REPO2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
F_CAP = ImageFont.truetype(os.path.join(REPO2, 'fonts', 'Montserrat_800ExtraBold.ttf'), 96)
BLACK = os.path.join(REPO2, 'fonts', 'Montserrat_900Black.ttf')
_f = {}
def fb(s):
    if s not in _f: _f[s] = ImageFont.truetype(BLACK, s)
    return _f[s]
RED, BLU, GRN = '#e8202a', '#1e7be0', '#22a845'

# ---------------- narrator: (voice time, pos, arm, eyes, brows) ----------------
L_ = 'pointL'
MAN = [
    (0.00, 'C', 'hips', 'C', 'N'), (1.24, 'C', 'hips', 'C', 'frown'), (3.22, 'BIG', 'hips', 'C', 'one'),
    (4.34, 'BIG', 'hips', 'U', 'up'), (6.14, 'R', L_, 'L', 'up'), (7.14, 'R', L_, 'L', 'N'),
    (8.86, 'R', L_, 'L', 'up'), (10.20, 'R', L_, 'L', 'N'),
    (12.30, 'R', L_, 'L', 'N'), (15.00, 'R', L_, 'U', 'up'), (18.52, 'R', L_, 'L', 'up'), (21.34, 'R', L_, 'L', 'N'),
    (22.70, 'BIG', 'hips', 'C', 'one'), (24.78, 'BIG', 'hips', 'C', 'up'),
    (26.44, 'C', 'hips', 'C', 'frown'), (28.12, 'L', 'hips', 'R', 'one'), (29.34, 'BIG', 'hips', 'C', 'up'),
    (31.76, 'C', 'hips', 'U', 'up'), (33.36, 'L', 'hips', 'U', 'up'), (34.44, 'R', 'hips', 'U', 'N'),
    (36.04, 'L', 'hips', 'U', 'one'), (37.42, 'R', 'hips', 'U', 'up'), (38.72, 'C', 'hips', 'U', 'N'),
    (40.58, 'R', L_, 'L', 'up'), (42.68, 'R', L_, 'L', 'N'),
    (45.48, 'R', L_, 'L', 'N'), (47.94, 'R', L_, 'L', 'up'), (50.14, 'C', 'hips', 'C', 'N'),
    (52.00, 'BIG', 'hips', 'C', 'up'), (54.64, 'R', L_, 'L', 'N'), (57.04, 'R', L_, 'L', 'one'),
    (59.06, 'C', 'hips', 'C', 'N'), (62.30, 'C', 'hips', 'C', 'one'),
    (64.00, 'R', L_, 'L', 'N'), (67.02, 'R', L_, 'L', 'up'), (69.16, 'C', 'hips', 'C', 'one'), (72.54, 'C', 'hips', 'C', 'up'),
]

# ---------------- elements: (voice time, [items]) ; item times are voice times ----------------
def I(k, cx, cy, mw, mh, t0): return ('img', k, cx, cy, mw, mh, t0)
def X(s, cx, cy, size, col, t0): return ('txt', s, cx, cy, size, col, t0)
def V(n, src_start, src_len, t0, t1): return ('clip', n, src_start, src_len, t0, t1)
def Y(s, cx, cy, size, col, t0): return ('type', s, cx, cy, size, col, t0)
TYPE_CPS = 0.05     # seconds per typed character

BEATS = [
    (0.00, [I('logo', 540, 380, 740, 740, 0.00), I('front', 540, 700, 1000, 500, 0.00)]),
    (3.22, [I('side', 540, 620, 1020, 360, 3.22), X('AHEAD OF ITS ERA', 540, 170, 80, BLU, 5.16)]),
    (6.14, [I('front', 540, 620, 1000, 520, 6.14), X('SUPERCAR', 540, 170, 130, RED, 8.10)]),
    (8.86, [I('side', 540, 640, 1020, 360, 8.86), Y('MITSUBISHI', 540, 140, 110, RED, 9.74),
            Y('3000GT VR-4', 540, 270, 100, RED, 10.20)]),
    (12.30, [I('hood', 540, 600, 1000, 560, 12.30), X('AWD', 540, 130, 130, BLU, 15.44),
             X('ACTIVE AERO', 540, 130, 115, BLU, 16.34), X('4-WHEEL STEERING', 540, 130, 82, BLU, 17.56)]),
    (18.52, [I('engine', 540, 580, 900, 640, 18.52), X('TWIN-TURBO V6', 540, 130, 100, BLU, 18.70),
             X('300 HP', 540, 130, 140, BLU, 21.34)]),
    (22.70, [I('front', 540, 620, 1000, 520, 22.70), X('REASONABLE MONEY', 540, 170, 80, GRN, 25.18)]),
    (26.44, [I('side', 540, 620, 1020, 360, 26.44), X('HEAVY & OLD', 540, 170, 110, RED, 27.06),
             X('"SLOW"', 540, 170, 130, RED, 29.08), X('SLEEPER', 540, 170, 140, GRN, 31.14)]),
    (31.76, [I('engine', 540, 520, 640, 400, 31.76),
             I('turbo', 300, 270, 300, 200, 33.36), X('UPGRADED TURBOS', 540, 110, 82, BLU, 33.36),
             I('ic', 780, 270, 300, 200, 34.44), X('FRONT-MOUNT INTERCOOLER', 540, 110, 58, BLU, 34.44),
             I('exh', 230, 800, 260, 180, 36.04), X('FREE-FLOWING EXHAUST', 540, 110, 66, BLU, 36.04),
             I('fuel', 850, 800, 260, 180, 37.42), X('FUEL SYSTEM', 540, 110, 95, BLU, 37.42),
             I('ecu', 540, 830, 230, 160, 38.72), X('PROPER TUNE', 540, 110, 95, BLU, 38.72)]),
    (40.58, [I('hood', 540, 600, 1000, 560, 40.58), X('500 HP', 540, 140, 150, RED, 42.68),
             X('AWD', 540, 280, 110, BLU, 44.20)]),
    (45.48, [I('front', 540, 620, 1000, 520, 45.48)]),
    (52.00, [I('side', 540, 640, 1020, 360, 52.00), X('0-60', 540, 140, 150, RED, 52.00),
             X('LOW 3s', 540, 280, 110, RED, 53.38)]),
    (54.64, [I('front', 540, 620, 1000, 520, 54.64), X('VS MUSCLE CARS', 540, 170, 95, RED, 57.04)]),
    (59.06, [I('side', 540, 620, 1020, 360, 59.06)]),
    (64.00, [I('logo', 540, 380, 740, 740, 64.00), I('front', 540, 700, 1000, 500, 64.00)]),
]
# car shine (strobe) start times, original voice time: start, result, end
SHINE = [7.14, 45.48, 65.34]   # 'this car', the result ('With that setup'), '3000 GT' at the end
SHINE_PAT = 'FFFWFFNFFWFFNFFWN'

def current(lst, tv):
    cur = lst[0]
    for b in lst:
        if b[0] <= tv: cur = b
    return cur

def popk(t, t0, d=0.13):
    x = (t - t0) / d
    if x >= 1: return 1.0
    if x <= 0: return 0.01
    return 0.5 + 0.7 * (x / 0.7) if x < 0.7 else 1.2 - 0.2 * (x - 0.7) / 0.3

_ic = {}
def fit(k, mw, mh):
    key = (k, mw, mh)
    if key not in _ic:
        im = A[k]; r = min(mw / im.width, mh / im.height)
        _ic[key] = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    return _ic[key]

# ---------------- clips: streamed frames ----------------
CLIP_H = 1560
class Stream:
    def __init__(self, n, start, length, t0, t1):
        self.t0, self.t1 = t0, t1
        speed = length / (t1 - t0)
        vf = (f"trim=start={start}:duration={length},setpts=(PTS-STARTPTS)/{speed},fps={FPS},"
              f"scale={W}:{CLIP_H}:force_original_aspect_ratio=increase,crop={W}:{CLIP_H}")
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', CLIP[n], '-vf', vf, '-an', '-f', 'rawvideo',
                                   '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
        self.idx, self.last = -1, None
    def frame(self, t):
        want = int((t - self.t0) * FPS)
        while self.idx < want:
            b = self.p.stdout.read(W * CLIP_H * 3)
            if len(b) < W * CLIP_H * 3: break
            self.last = Image.frombytes('RGB', (W, CLIP_H), b); self.idx += 1
        return self.last
_streams = {}

_white = {}
def shine_state(t):
    for s in SHINE:
        k = int((t - T(s)) * FPS)
        if 0 <= k < len(SHINE_PAT): return SHINE_PAT[k]
    return 'N'

def shined(im, st):
    if st == 'N': return im
    key = (id(im), st)
    if key not in _white:
        a = np.array(im).astype(np.float32)
        if st == 'W': a[..., :3] = 228
        else:
            a[..., :3] = a[..., :3] * 0.35 + 255 * 0.65; a[..., 3] *= 0.8
        _white[key] = Image.fromarray(a.astype(np.uint8))
    return _white[key]

# dyno break: only the engine sound is used; the car shakes with it (pattern measured from the reference)
DYNO_SRC = None   # this video has no dyno sound
SHAKE_DX = [0, -1, -1, 1, 1, 0, 1, 1, -1, -1]          # 10-frame cycle (3 per second), units of amplitude
SHAKE_DY = [0, -1, 1, 1, -1, 0, -1, 1, 1, -1]
def _dyno_env():
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', DYNO_SRC, '-t', str(GAP), '-ac', '1', '-ar', '44100',
                          '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32); hop = 44100 // FPS
    rms = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a), hop)])
    rms = rms / max(np.percentile(rms, 95), 1e-6)
    return np.clip(rms, 0, 1.3)
DYNO_ENV = _dyno_env() if DYNO_SRC else None

def draw_dyno(fr, t):
    k = int((t - CUT) * FPS)
    e = DYNO_ENV[min(k, len(DYNO_ENV) - 1)]
    lg = fit('logo', 740, 740)
    fr.alpha_composite(lg, (int(540 - lg.width / 2), int(380 - lg.height / 2)))
    im = fit('frontS', 1000, 500)
    g = 0.45 + 0.55 * min(e, 1.0)                          # always visible, stronger when the engine is loud
    ax, ay = 0.014 * im.width * g, 0.009 * im.width * g
    dx, dy = SHAKE_DX[k % 10] * ax, SHAKE_DY[k % 10] * ay
    fr.alpha_composite(im, (int(540 - im.width / 2 + dx), int(700 - im.height / 2 + dy)))

def draw_items(fr, t):
    if CUT <= t < CUT + GAP:
        draw_dyno(fr, t); return
    tv = V2O(t)
    _, items = current(BEATS, tv)
    texts = {}
    for it in items:
        if it[0] == 'clip':
            _, n, s0, ln, a, b = it
            t0, t1 = CUT, CUT + GAP
            key = (n, s0, a)
            if key not in _streams: _streams[key] = Stream(n, s0, ln, t0, t1)
            f = _streams[key].frame(t)
            if f is not None: fr.paste(f, (0, 0))
    st = shine_state(t)
    for it in items:
        if it[0] == 'img' and T(it[-1]) <= t:
            _, k, cx, cy, mw, mh, t0 = it
            im = fit(k, mw, mh); s = popk(t, T(t0))
            if k in CARS: im = shined(im, st)
            if s != 1.0: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))))
            fr.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
        if it[0] in ('txt', 'type') and T(it[-1]) <= t:
            texts[(it[2], it[3])] = it
    d = ImageDraw.Draw(fr)
    for it in texts.values():
        kind, s_, cx, cy, size, col, t0 = it
        if kind == 'type':
            n = min(len(s_), int((t - T(t0)) / TYPE_CPS) + 1)
            full = fb(size).getlength(s_)
            d.text((cx - full / 2, cy), s_[:n], font=fb(size), fill=col, anchor='lm', stroke_width=7, stroke_fill='black')
            continue
        k = popk(t, T(t0))
        d.text((cx, cy), s_, font=fb(max(8, int(size * k))), fill=col, anchor='mm',
               stroke_width=max(2, int(7 * k)), stroke_fill='black')

POS = {'C': (540, 1900, 0.64), 'R': (800, 1900, 0.6), 'L': (280, 1900, 0.6), 'BIG': (540, 2560, 1.2),
       'CORNER': (930, 1915, 0.38)}
_pc = {}
def draw_man(fr, t):
    tv = V2O(t) if not (CUT <= t < CUT + GAP) else CUT + 0.1
    t0, pos, arm, eyes, brows = current(MAN, tv)
    cx, fy, s = POS[pos]
    blink = (t % 2.9) < 0.1
    key = (arm, eyes, brows, blink, s)
    if key not in _pc: _pc[key] = narrator.render(arm, eyes, brows, blink, s)
    ax, ay = narrator.anchor(arm)
    fr.alpha_composite(_pc[key], (int(cx - ax * s), int(fy - ay * s)))

# ---------------- caption: one word ----------------
words = json.load(open(S + '/gt/words.json'))
def draw_caption(fr, t):
    if CUT <= t < CUT + GAP: return
    tv = V2O(t)
    cur = None
    for w in words:
        if w['s'] - 0.02 <= tv: cur = w
    if cur is None or tv > cur['e'] + 0.6: return
    ImageDraw.Draw(fr).text((W / 2, 1000), cur['w'], font=F_CAP, fill='white', anchor='mm',
                            stroke_width=9, stroke_fill='black')

def frame(t):
    fr = Image.new('RGBA', (W, H), 'white')
    draw_items(fr, t); draw_man(fr, t); draw_caption(fr, t)
    return fr.convert('RGB')

def load_sfx(pattern):
    f = glob.glob(U + pattern)[0]
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', '44100', '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def build_sfx(path):
    sr = 44100; out = np.zeros(int(sr * (DUR + 2)), np.float32)
    car, typ, mod, shn = load_sfx('c4b828b8*'), load_sfx('f4f7d949*'), load_sfx('57e303dc*'), load_sfx('c8e8f8e3*')
    def put(snd, t, g=1.0):
        i = max(0, int(t * sr)); n = min(len(snd), len(out) - i); out[i:i + n] += snd[:n] * g
    seen = set()
    for _, items in BEATS:
        for it in items:
            if it[0] == 'img':
                k, t0 = it[1], round(T(it[-1]), 2)
                if (k in CARS) and ('c', t0) not in seen:
                    seen.add(('c', t0)); put(car, t0, 0.8)
                if (k in MODS) and ('m', t0) not in seen:
                    seen.add(('m', t0)); put(mod, t0 - 0.165, 0.7)      # hit sits 0.165 s into the file
            if it[0] == 'txt' and it[5] == BLU:
                t0 = round(T(it[-1]), 2)
                if ('m', t0) not in seen:
                    seen.add(('m', t0)); put(mod, t0 - 0.165, 0.7)
            if it[0] == 'type':
                t0 = T(it[-1]); ln = len(it[1]) * TYPE_CPS + 0.08
                seg = typ[:int(ln * sr)].copy(); f = min(len(seg), int(0.04 * sr)); seg[-f:] *= np.linspace(1, 0, f)
                put(seg, t0, 1.6)
    for s in SHINE: put(shn, T(s), 0.55)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())

def build_voice(path):
    keep, x = [], 0.0
    for g0, g1 in CUTS: keep.append((x, g0)); x = g1
    keep.append((x, VOICE_LEN))
    parts = ''.join(f'[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,'
                    f'afade=t=out:st={b - a - 0.012:.3f}:d=0.012[s{i}];' for i, (a, b) in enumerate(keep))
    fc = parts + ''.join(f'[s{i}]' for i in range(len(keep))) + f'concat=n={len(keep)}:v=0:a=1[o]'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', VOICE, '-filter_complex', fc, '-map', '[o]', path], check=True)

if __name__ == '__main__':
    OUT = sys.argv[1]
    if len(sys.argv) > 2:
        for tt in [float(x) for x in sys.argv[2].split(',')]:
            _streams.clear(); frame(tt).save(f'{S}/gt/p_{tt:05.2f}.jpg', quality=80)
        sys.exit()
    build_sfx(S + '/gt/sfx.wav'); build_voice(S + '/gt/voice_tight.wav')
    voice_fx = ('highpass=f=75,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.2:g=3.5,'
                'acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=2,'
                'loudnorm=I=-14:TP=-1.5:LRA=7,aresample=44100')
    fc = (f"[1:a]{voice_fx},aformat=channel_layouts=mono[voice];[2:a]aformat=channel_layouts=mono[sfx];"
          f"[voice][sfx]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[a]")
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-i', S + '/gt/voice_tight.wav', '-i', S + '/gt/sfx.wav',
                          '-filter_complex', fc, '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-preset', 'medium',
                          '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest',
                          '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait(); print('done', OUT)
