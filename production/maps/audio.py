"""Music bed + sound effects, synthesised (no third-party audio), mixed under the narration.

usage: python3 audio.py <episode_dir>   -> build/mix.wav
"""
import sys, os, json, importlib.util
import numpy as np, soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E

EP = os.path.abspath(sys.argv[1]); B = os.path.join(EP, "build")
SR = 48000
rng = np.random.default_rng(1)
voice, vsr = sf.read(os.path.join(B, "voice.wav"), dtype="float32")
if vsr != SR:
    idx = np.arange(0, len(voice), vsr / SR); voice = np.interp(idx, np.arange(len(voice)), voice).astype(np.float32)
N = len(voice); dur = N / SR
t_all = np.arange(N) / SR


def lp(x, fc):                     # one-pole low-pass
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); acc = 0.0
    from scipy.signal import lfilter  # noqa
    return lfilter([1 - a], [1, -a], x)

def hp(x, fc):
    return x - lp(x, fc)

def env(n, a, r):
    e = np.ones(n); na = int(a * SR); nr = int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e

def note(f):
    return 440 * 2 ** ((f - 69) / 12)

# ---------------------------------------------------------------- music
music = np.zeros(N)
bpm = 76; beat = 60 / bpm; bar = beat * 4
prog = [(50, [62, 65, 69]), (46, [62, 65, 70]), (41, [60, 65, 69]), (48, [60, 64, 67])]  # Dm Bb F C
nbars = int(dur / bar) + 2
for b in range(nbars):
    root, ch = prog[b % 4]
    t0 = b * bar; s0 = int(t0 * SR)
    if s0 >= N: break
    L = int(bar * 1.6 * SR); tt = np.arange(L) / SR
    pad = np.zeros(L)
    for n in ch:
        for det in (-0.07, 0.0, 0.07):
            f = note(n - 12) * 2 ** (det / 12)
            pad += np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) * 0.5 + 0.18 * np.sin(4 * np.pi * f * tt)
    pad *= env(L, 0.9, 1.0) * 0.05
    bass = np.sin(2 * np.pi * note(root - 12) * tt) * env(L, 0.05, 1.2) * np.exp(-tt * 0.5) * 0.16
    seg = pad + bass
    e = min(N, s0 + L); music[s0:e] += seg[: e - s0]
    # soft plucked arpeggio, eighth notes
    arp = ch + [ch[1] + 12, ch[0] + 12, ch[2]]
    for k in range(8):
        ts = t0 + k * beat / 2; s = int(ts * SR)
        if s >= N: break
        Lp = int(1.2 * SR); tp = np.arange(Lp) / SR
        f = note(arp[k % len(arp)])
        pl = (np.sin(2 * np.pi * f * tp) + 0.3 * np.sin(4 * np.pi * f * tp) + 0.1 * np.sin(6 * np.pi * f * tp)) * np.exp(-tp * 4.5)
        pl *= 0.045 * (0.8 + 0.2 * rng.random())
        e = min(N, s + Lp); music[s:e] += pl[: e - s]
music = lp(music, 3800)
# gentle fade in/out
music *= np.clip(t_all / 1.5, 0, 1) * np.clip((dur - t_all) / 2.0, 0, 1)

# ducking under the voice
venv = lp(np.abs(voice).astype(np.float64), 6)
venv = venv / (venv.max() + 1e-9)
duck = 1 - 0.45 * np.clip(venv * 6, 0, 1)
music *= lp(duck, 3)

# ---------------------------------------------------------------- sfx
def sfx(kind):
    if kind == "pop":
        L = int(0.14 * SR); t = np.arange(L) / SR
        f = 900 * np.exp(-t * 18) + 260
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30) * 0.55
    if kind == "whoosh":
        L = int(0.9 * SR); t = np.arange(L) / SR
        n = rng.standard_normal(L); sweep = np.sin(np.pi * t / t[-1]) ** 2
        y = lp(n, 900) * 0.6 + hp(lp(n, 3000), 600) * 0.4
        return y * sweep * 0.22
    if kind == "rewind":
        L = int(1.5 * SR); t = np.arange(L) / SR
        f = 300 + 1600 * (t / t[-1]) ** 0.7 + 120 * np.sin(2 * np.pi * 9 * t)
        tone = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.25
        y = lp(tone + 0.5 * rng.standard_normal(L), 2500) * env(L, 0.1, 0.4)
        return y * 0.22
    if kind == "fire":
        L = int(2.2 * SR); t = np.arange(L) / SR
        y = lp(rng.standard_normal(L), 700) * 0.35
        for _ in range(60):
            s = rng.integers(0, L - 800); y[s:s + 300] += rng.standard_normal(300) * np.exp(-np.arange(300) / 40) * 0.9
        return hp(y, 120) * env(L, 0.3, 0.9) * 0.4
    if kind == "boom":
        L = int(1.6 * SR); t = np.arange(L) / SR
        f = 70 * np.exp(-t * 1.5) + 38
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2) + lp(rng.standard_normal(L), 400) * np.exp(-t * 6) * 0.5
        return y * 0.6
    if kind == "ding":
        L = int(2.2 * SR); t = np.arange(L) / SR
        y = sum(a * np.sin(2 * np.pi * 1046.5 * m * t) * np.exp(-t * d) for a, m, d in ((1, 1, 2.2), (0.5, 2.0, 3.5), (0.3, 3.01, 5), (0.2, 4.2, 7)))
        return y * 0.18
    if kind == "title":
        L = int(1.6 * SR); t = np.arange(L) / SR
        y = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f in (1568, 2093, 2637, 3136))
        return y * env(L, 0.5, 1.0) * 0.025 + lp(rng.standard_normal(L), 5000) * env(L, 0.6, 0.9) * 0.03
    if kind == "draw":
        L = int(2.4 * SR); t = np.arange(L) / SR
        y = hp(rng.standard_normal(L), 2500) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t) ** 2)
        return y * env(L, 0.1, 0.5) * 0.07
    if kind == "paper":
        L = int(0.7 * SR); t = np.arange(L) / SR
        y = hp(lp(rng.standard_normal(L), 6000), 900) * np.abs(np.sin(2 * np.pi * 5 * t))
        return y * env(L, 0.05, 0.3) * 0.2
    raise KeyError(kind)

fx = np.zeros(N)
spec = importlib.util.spec_from_file_location("shots", os.path.join(EP, "shots.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
timing = json.load(open(os.path.join(B, "timing.json")))
scene = mod.Scene(E.Geo(os.path.join(B, "geo.pkl")), timing)
for t, kind, g in scene.sfx:
    y = sfx(kind) * g; s = int(max(0, t) * SR); e = min(N, s + len(y))
    if s < N: fx[s:e] += y[: e - s]

# ---------------------------------------------------------------- mix (stereo, light width on music)
mus_l = music; mus_r = np.roll(music, int(0.012 * SR))
L = voice * 1.0 + mus_l * 0.24 + fx * 0.5
R = voice * 1.0 + mus_r * 0.24 + fx * 0.5
mix = np.stack([L, R], 1)
mix /= max(1e-9, np.abs(mix).max()) / 0.95
np.save(os.path.join(B, "stems.npy"), np.stack([voice[:N], music, fx]))
sf.write(os.path.join(B, "mix.wav"), mix.astype(np.float32), SR)
print("mix", dur, "s;", len(scene.sfx), "sfx")
