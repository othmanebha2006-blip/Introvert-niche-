"""Episode 9: every Mercedes-AMG car explained (@Mecmation clip). Renders 1080x1920 @ 30 fps and muxes voice + sound effects.

usage: python3 compose.py out.mp4 [--preview SECONDS ...] [--from T --to T]
"""
import sys, os, json, math, re, subprocess, wave
import numpy as np, cairo
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
from ink import *
from car import draw_car, WHEELS
from clip_presenter import ClipPresenter
# presenter = the clip the user animated for this voiceover (white background removed), frame-synced to voice.wav
PRESENTER = None   # created after `scenes` is imported (it names the clip)
from widgets import *
import widgets
sys.path.insert(0, HERE)
import scenes as S
from clip_presenter import ClipPresenter
PRESENTER = ClipPresenter(os.path.join(HERE, "..", "character_mecmation", S.CLIP),
                          os.environ.get("CLIP_CACHE", os.path.expanduser("~/.cache/mecmation_amg")))
import car as _car
_car.STYLE["real"] = True          # cars in the reference look

W, H, FPS = 1080, 1920, 30
SERIES = S.SERIES
BRAND = S.BRAND
HANDLE = os.environ.get("HANDLE", "@Mecmation")
END_CARD = 0.0   # the end card is part of the last scene ("follow me")

# ---------------------------------------------------------------- timing
SENT, WORDS = S.load_timing()      # real word times from Whisper on the tightened voice
KEYWORDS = S.KEYWORDS

NB = max(s["beat"] for s in SENT) + 1
BEAT_T = [0.0] + [min(s["start"] for s in SENT if s["beat"] == b) - 0.12 for b in range(1, NB)]
VO_END = SENT[-1]["end"]
DUR = VO_END + 1.3


def beat_at(t):
    b = 0
    for i, t0 in enumerate(BEAT_T):
        if t >= t0: b = i
    return b


def wt(beat, word, k=0, end=False):
    """beat-local time of the k-th occurrence of `word` in a beat."""
    n = 0
    for w in WORDS:
        if w["beat"] == beat and re.sub(r"[^\w-]", "", w["text"]).lower() == word.lower():
            if n == k:
                return (w["end"] if end else w["start"]) - BEAT_T[beat]
            n += 1
    raise KeyError((beat, word, k))


def st(beat, i):
    """beat-local start time of the i-th sentence in a beat."""
    ss = [s for s in SENT if s["beat"] == beat]
    return ss[i]["start"] - BEAT_T[beat]


# ---------------------------------------------------------------- audio envelope (mouth)
with wave.open(os.path.join(HERE, "voice.wav")) as wf:
    SR = wf.getframerate(); raw = wf.readframes(wf.getnframes())
    sw = wf.getsampwidth()
VOICE = np.frombuffer(raw, dtype=np.int16 if sw == 2 else np.int32).astype(np.float32)
VOICE /= np.abs(VOICE).max() + 1e-9
hop = SR // FPS
ENV = np.array([np.sqrt(np.mean(VOICE[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(VOICE) else 0 for i in range(int(DUR * FPS) + 2)])
ENV = np.convolve(ENV, [0.25, 0.5, 0.25], "same")
ENV = np.clip((ENV - 0.02) / 0.16, 0, 1)


# ---------------------------------------------------------------- background
def background(ctx):
    ctx.set_source(lin_grad(0, 0, 0, H, [(0, hexc("#F3F4F6")), (0.55, hexc("#E7E9EC")), (1, hexc("#C9CDD3"))])); ctx.paint()
    ctx.set_line_width(1.5); ctx.set_source_rgba(0.5, 0.55, 0.62, 0.10)
    for gx in range(0, W + 1, 60):
        ctx.move_to(gx, 0); ctx.line_to(gx, H)
    for gy in range(0, H + 1, 60):
        ctx.move_to(0, gy); ctx.line_to(W, gy)
    ctx.stroke()
    ctx.set_source(rad_grad(W / 2, H * 0.45, H * 0.3, H * 0.75, [(0, (0, 0, 0, 0)), (1, (0, 0, 0, 0.16))])); ctx.paint()


def header(ctx):
    ctx.set_source_rgba(*hexc("#2A2D33", 0.75))
    text_path(ctx, SERIES, 48, 74, 30, MONO, "l"); ctx.fill()
    text_path(ctx, BRAND, W - 48, 74, 30, MONO, "r"); ctx.fill()
    ctx.rectangle(48, 98, W - 96, 3); ctx.set_source_rgba(0.16, 0.18, 0.2, 0.25); ctx.fill()


# ---------------------------------------------------------------- car helper
def car_in(ctx, lt, t0, kind, x, y, L, paint, out=None, dur=0.6, sound=True, park_rot=0.0, **kw):
    if lt < t0:
        return
    if sound:
        sfx_once(lt, t0, "whoosh")
    R = WHEELS[kind][2] * L
    start = -L - 80
    p = ease_out((lt - t0) / dur)
    cx = start + (x - start) * p
    v = (1 - min(1, (lt - t0) / dur)) ** 2
    tilt = 0.0
    a = lt - t0 - dur
    if a > 0:
        tilt = -0.012 * math.exp(-a * 7) * math.sin(a * 18)
    if out is not None and lt > out:
        q = ((lt - out) / 0.55) ** 2
        cx = x + q * (W + 200)
        v = min(1, (lt - out) * 2.5)
        if out:
            sfx_once(lt, out, "whoosh")
    speed_lines(ctx, cx, y, L, L * 0.3, v * 1.4, seed=int(x))
    draw_car(ctx, kind, cx, y, L, paint, (cx - start) / R + park_rot, tilt=tilt, **kw)


S.CTX.update(wt=lambda b, w, k=0: wt(b, w, k), st=lambda b, i: st(b, i), car_in=car_in, handle=HANDLE)
S.CTX.setdefault("beat_t", BEAT_T); S.CTX.setdefault("car_plate", (540, 760, 170))
SCENES = S.SCENES
assert len(SCENES) == NB


# ---------------------------------------------------------------- presenter state
def caption_now(t):
    cur = None
    for w in WORDS:
        if w["start"] <= t:
            cur = w
    if cur is None or t > SENT[cur["sent"]]["end"] + 0.35:
        return None, 0, False
    txt = cur["text"].strip(",.?")
    if txt.lower() not in ("quattro", "e-tron", "q") and not re.search(r"[a-z]\d|\d[a-z]", txt):
        txt = txt.upper()
    if txt == "QUATTRO":
        txt = "quattro"
    key = txt.upper().strip("'S") in KEYWORDS or bool(re.search(r"\d", txt)) or txt.upper() in KEYWORDS
    return txt, t - cur["start"], key


# ---------------------------------------------------------------- frame
def render(f, surf):
    t = f / FPS
    widgets.CLOCK["t"] = t
    set_boil(f, 4, 0.45)              # steady lines, like the reference illustrations
    ctx = cairo.Context(surf)
    background(ctx)
    header(ctx)
    b = beat_at(t)
    if True:
        lt = t - BEAT_T[b]
        if b > 0 and lt < 0.22:
            # previous scene leaves: fade + lift
            q = ease(lt / 0.22)
            ctx.save(); ctx.translate(0, -60 * q); ctx.push_group()
            SCENES[b - 1](ctx, t - BEAT_T[b - 1])
            ctx.pop_group_to_source(); ctx.paint_with_alpha(1 - q); ctx.restore()
        ctx.save()
        SCENES[b](ctx, lt)
        ctx.restore()
    if hasattr(S, "hero"):      # persistent layer over all scenes (the hero plate)
        S.hero(ctx, t)
    word, age, key = caption_now(t)
    if word:
        caption(ctx, word, W / 2, 978, age, key)
    PRESENTER.draw(ctx, f, 540, 1912, 0.6)


# ---------------------------------------------------------------- sound effects
def synth_sfx(events, n):
    rng = np.random.default_rng(3)
    out = np.zeros(n, np.float32)
    def add(at, sig, g):
        i = int(at * SR)
        if i >= n: return
        k = min(len(sig), n - i); out[i:i + k] += g * sig[:k]
    for at, kind in events:
        if kind == "whoosh":
            d = 0.55; m = int(d * SR); x = rng.standard_normal(m).astype(np.float32)
            # moving low-pass via cumulative smoothing with changing coefficient
            env = np.sin(np.linspace(0, np.pi, m)) ** 2
            y = np.zeros(m, np.float32); a = 0.0
            cs = 0.02 + 0.25 * np.sin(np.linspace(0, np.pi, m))
            for j in range(m):
                a += cs[j] * (x[j] - a); y[j] = a
            add(at, y * env / (np.abs(y).max() + 1e-6), 0.10)
        elif kind == "pop":
            d = 0.09; m = int(d * SR); tt = np.arange(m) / SR
            f = 900 * np.exp(-tt * 18) + 380
            add(at, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 40), 0.10)
        elif kind == "stamp":
            d = 0.18; m = int(d * SR); tt = np.arange(m) / SR
            add(at, (np.sin(2 * np.pi * 90 * tt) + 0.4 * rng.standard_normal(m)) * np.exp(-tt * 28), 0.22)
        elif kind == "rumble":
            d = 1.8; m = int(d * SR); tt = np.arange(m) / SR
            sig = sum(np.sin(2 * np.pi * f0 * tt + np.sin(2 * np.pi * 7 * tt) * 2) for f0 in (55, 82, 110)) / 3
            env = np.minimum(1, tt / 0.15) * np.exp(-tt * 1.2)
            add(at, sig * env, 0.16)
    return out


def main():
    out = sys.argv[1]
    args = sys.argv[2:]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    if args and args[0] == "--preview":
        for s in args[1:]:
            f = int(float(s) * FPS); render(f, surf)
            surf.write_to_png(f"{out}_{float(s):05.1f}.png")
        return
    f0 = int(float(args[args.index("--from") + 1]) * FPS) if "--from" in args else 0
    f1 = int(float(args[args.index("--to") + 1]) * FPS) if "--to" in args else int(DUR * FPS)
    tmpv = out + ".video.mp4"
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p",
                           "-profile:v", "high", "-movflags", "+faststart", tmpv], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        render(f, surf); surf.flush()
        ff.stdin.write(bytes(surf.get_data()))
        if f % 150 == 0:
            print(f"frame {f}/{f1}", flush=True)
    ff.stdin.close(); ff.wait()
    # audio: voice + sfx, padded to the video length
    n = int((f1 - f0) / FPS * SR)
    voice = np.zeros(n, np.float32)
    v = VOICE[int(f0 / FPS * SR):][:n]; voice[:len(v)] = v * 0.92
    fx = synth_sfx([(t - f0 / FPS, k) for t, k in widgets.SFX], n)
    mix = np.clip(voice + fx, -1, 1)
    tmpa = out + ".audio.wav"
    with wave.open(tmpa, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32000).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmpv, "-i", tmpa, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", out], check=True)
    os.remove(tmpv); os.remove(tmpa)
    print("done", out)


if __name__ == "__main__":
    main()
