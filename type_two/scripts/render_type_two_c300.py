"""TYPE TWO renderer: Mercedes C300 W204."""
import json, glob, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/home/user/Introvert-niche-/type_one/scripts')
import narrator

S = '/tmp/claude-0/-home-user-Introvert-niche-/4b8ae4f4-60f4-56d8-b6fb-0b7196bc6596/scratchpad'
U = '/root/.claude/uploads/4b8ae4f4-60f4-56d8-b6fb-0b7196bc6596/'
W, H, FPS = 1080, 1920, 30
VOICE = glob.glob(U + 'c352a62a*.mp3')[0]
CLIP = {1: glob.glob(U + '57ff2974*')[0], 2: glob.glob(U + '1dd6ed17*')[0], 3: glob.glob(U + 'ef4ae6f6*')[0]}
CUT = 5.62          # end of the hook in the voiceover
GAP = 5.0           # silent B-roll break inserted after the hook
_W = json.load(open(S + '/c300/words.json'))
# pauses between sentences longer than 0.25 s are shortened: keep 0.08 s after a word, 0.06 s before the next
def _silences(path, thr=-40, mind=0.35):
    err = subprocess.run(['ffmpeg', '-i', path, '-af', f'silencedetect=n={thr}dB:d={mind}', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    import re
    st = [float(x) for x in re.findall(r'silence_start: ([0-9.]+)', err)]
    en = [float(x) for x in re.findall(r'silence_end: ([0-9.]+)', err)]
    return list(zip(st, en))
# only real silences are shortened, each down to 0.2 s (0.1 s kept on both sides)
CUTS = [(a + 0.1, b - 0.1) for a, b in _silences(VOICE) if b - a > 0.3 and a > 0.5 and b < 75.5]
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
VOICE_LEN = 76.12
DUR = M(VOICE_LEN) + GAP + 0.1

def T(x):           # original voice time -> video time
    return M(x) if x < CUT else M(x) + GAP
def V2O(t):         # video time -> original voice time (break maps to CUT)
    if t < CUT: return Minv(t)
    if t < CUT + GAP: return CUT
    return Minv(t - GAP)

def up(i):
    im = Image.open(glob.glob(U + i + '*')[0]).convert('RGBA'); return im.crop(im.getbbox())
A = {'c63': up('4c203a47'), 'c63side': up('75d10af9'), 'hood': up('40dc07b0'), 'engine': up('a38b4219'),
     'intake': up('c4dcbd72'), 'exhaust': up('f2376737'), 'ecu': up('4245a9e9'), 'headers': up('6c902933'),
     'front': up('cb7315f1'), 'front2': up('819561e1'), 'side': up('20e6f288')}
CARS = {'hood', 'front', 'front2', 'side'}
MODS = {'intake', 'headers', 'exhaust', 'ecu'}

F_CAP = ImageFont.truetype(S + '/fonts2/package/800ExtraBold/Montserrat_800ExtraBold.ttf', 96)
BLACK = S + '/fonts2/package/900Black/Montserrat_900Black.ttf'
_f = {}
def fb(s):
    if s not in _f: _f[s] = ImageFont.truetype(BLACK, s)
    return _f[s]
RED, BLU, GRN = '#e8202a', '#1e7be0', '#22a845'

# ---------------- narrator: (voice time, pos, arm, eyes, brows) ----------------
L_ = 'pointL'
MAN = [
    (0.00, 'C', 'hips', 'C', 'up'), (0.48, 'R', L_, 'L', 'up'), (2.30, 'R', L_, 'L', 'N'),
    (2.80, 'R', L_, 'L', 'up'), (4.34, 'C', 'hips', 'C', 'one'),
    (5.70, 'CORNER', 'hips', 'C', 'N'),
    (5.78, 'R', L_, 'L', 'up'), (8.26, 'R', L_, 'L', 'N'), (10.20, 'R', L_, 'U', 'one'),
    (11.88, 'BIG', 'hips', 'C', 'one'), (13.36, 'C', 'hips', 'C', 'up'),
    (15.06, 'R', L_, 'L', 'N'), (17.50, 'R', L_, 'L', 'up'), (19.42, 'R', L_, 'U', 'N'), (21.74, 'R', L_, 'U', 'up'),
    (23.28, 'BIG', 'hips', 'C', 'N'), (25.16, 'BIG', 'hips', 'C', 'one'),
    (27.32, 'C', 'hips', 'U', 'up'), (29.54, 'L', 'hips', 'U', 'up'), (33.12, 'R', 'hips', 'U', 'N'),
    (36.70, 'L', 'hips', 'U', 'one'), (41.04, 'R', 'hips', 'U', 'up'), (45.20, 'BIG', 'hips', 'C', 'up'),
    (46.90, 'BIG', 'hips', 'C', 'frown'), (48.64, 'C', 'hips', 'C', 'frown'),
    (51.90, 'R', L_, 'L', 'up'),
    (57.00, 'C', 'hips', 'C', 'one'), (59.00, 'L', 'hips', 'R', 'N'), (61.38, 'C', 'hips', 'C', 'up'),
    (62.76, 'BIG', 'hips', 'C', 'one'), (64.56, 'BIG', 'hips', 'L', 'one'), (66.24, 'C', 'hips', 'C', 'up'),
    (67.54, 'C', 'hips', 'C', 'one'),
    (70.54, 'R', L_, 'L', 'N'), (73.46, 'R', L_, 'L', 'up'), (75.16, 'C', 'hips', 'C', 'up'),
]

# ---------------- elements: (voice time, [items]) ; item times are voice times ----------------
def I(k, cx, cy, mw, mh, t0): return ('img', k, cx, cy, mw, mh, t0)
def X(s, cx, cy, size, col, t0): return ('txt', s, cx, cy, size, col, t0)
def V(n, src_start, src_len, t0, t1): return ('clip', n, src_start, src_len, t0, t1)
def Y(s, cx, cy, size, col, t0): return ('type', s, cx, cy, size, col, t0)
TYPE_CPS = 0.05     # seconds per typed character

BEATS = [
    (0.00, [I('front', 540, 560, 1000, 700, 0.00)]),
    (CUT, [V(3, 0.0, GAP, CUT, CUT)]),                       # silent break, clip with its own sound
    (5.78, [I('side', 540, 640, 1020, 520, 5.78), Y('2008-2014', 540, 140, 130, RED, 6.66),
            Y('MERCEDES C300', 540, 270, 90, RED, 8.26), Y('W204', 540, 380, 90, RED, 10.20)]),
    (11.88, [I('side', 540, 600, 1020, 520, 11.88), X('NO MODERN PRICES', 540, 140, 80, GRN, 13.36)]),
    (15.06, [I('hood', 540, 560, 1000, 700, 15.06), X('NATURALLY ASPIRATED', 540, 130, 70, BLU, 16.28)]),
    (17.50, [I('engine', 540, 580, 900, 640, 17.50), X('V6', 540, 130, 140, BLU, 17.50),
             X('3.0L', 540, 130, 140, BLU, 19.42), X('3.0L  /  3.5L', 540, 130, 120, BLU, 21.74)]),
    (23.28, [I('front2', 540, 470, 1000, 600, 23.28)]),
    (27.32, [I('engine', 540, 540, 500, 320, 27.32),
             I('intake', 335, 290, 330, 210, 29.54), X('INTAKE', 540, 110, 95, BLU, 29.54),
             I('headers', 745, 290, 330, 210, 33.12), X('HEADERS', 540, 110, 95, BLU, 33.12),
             I('exhaust', 335, 800, 330, 210, 36.70), X('CAT-BACK EXHAUST', 540, 110, 78, BLU, 36.70),
             I('ecu', 745, 800, 330, 210, 41.04), X('ECU TUNE', 540, 110, 95, BLU, 41.04)]),
    (45.20, [X('4 MODS', 540, 200, 150, RED, 45.20), I('intake', 335, 470, 330, 210, 45.20),
             I('headers', 745, 470, 330, 210, 45.20), I('exhaust', 335, 730, 330, 210, 45.20),
             I('ecu', 745, 730, 330, 210, 45.20)]),
    (46.90, [I('side', 540, 620, 1000, 500, 46.90), X('NO TURBO', 540, 170, 150, RED, 47.56)]),
    (51.90, [I('front', 540, 560, 1000, 700, 51.90)]),
    (57.00, [I('front2', 540, 560, 1000, 700, 57.00)]),
    (62.76, [I('front', 540, 600, 1000, 640, 62.76), X('NO AMG BADGE', 540, 140, 90, RED, 63.56)]),
    (67.54, [I('side', 540, 600, 1020, 520, 67.54)]),
    (70.54, [I('front2', 540, 560, 1000, 700, 70.54), X('W204 C300', 540, 130, 120, RED, 71.92)]),
]
# car shine (strobe) start times, original voice time: start, result, end
SHINE = [2.80, 52.84, 71.92]
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

def draw_items(fr, t):
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
words = json.load(open(S + '/c300/words.json'))
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
            _streams.clear(); frame(tt).save(f'{S}/c300/p_{tt:05.2f}.jpg', quality=80)
        sys.exit()
    build_sfx(S + '/c300/sfx.wav'); build_voice(S + '/c300/voice_tight.wav')
    voice_fx = ('highpass=f=75,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.2:g=3.5,'
                'acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=2,'
                'loudnorm=I=-14:TP=-1.5:LRA=7,aresample=44100')
    fc = (f"[1:a]{voice_fx},asplit[v1][v2];[v1]atrim=0:{CUT},asetpts=PTS-STARTPTS[va];"
          f"[v2]atrim=start={CUT},asetpts=PTS-STARTPTS[vb];"
          f"[2:a]atrim=0:{GAP},asetpts=PTS-STARTPTS,loudnorm=I=-16:TP=-2,aresample=44100,"
          f"afade=t=in:d=0.15,afade=t=out:st={GAP - 0.4}:d=0.4,aformat=channel_layouts=mono[cl];"
          f"[va]aformat=channel_layouts=mono[va2];[vb]aformat=channel_layouts=mono[vb2];"
          f"[va2][cl][vb2]concat=n=3:v=0:a=1[voice];[3:a]aformat=channel_layouts=mono[sfx];"
          f"[voice][sfx]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[a]")
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-i', S + '/c300/voice_tight.wav', '-i', CLIP[3], '-i', S + '/c300/sfx.wav',
                          '-filter_complex', fc, '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-preset', 'medium',
                          '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest',
                          '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait(); print('done', OUT)
