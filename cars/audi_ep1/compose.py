"""Episode 1: Audi badges explained. Renders 1080x1920 @ 30 fps and muxes voice + sound effects.

usage: python3 compose.py out.mp4 [--preview SECONDS ...] [--from T --to T]
"""
import sys, os, json, math, re, subprocess, wave
import numpy as np, cairo
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
from ink import *
from car import draw_car, WHEELS
from mecmation import draw_mecmation, lerp_pose
from widgets import *
import widgets

W, H, FPS = 1080, 1920, 30
SERIES = "BADGE DECODED · #1"
BRAND = "AUDI"
HANDLE = os.environ.get("HANDLE", "@Mecmation")
END_CARD = 2.0

# ---------------------------------------------------------------- timing
SENT = json.load(open(os.path.join(HERE, "voice.json")))
KEYWORDS = {"A", "Q", "S", "RS", "SUV", "RENNSPORT", "AVANT", "SPORTBACK", "QUATTRO", "Q.", "TFSI", "TDI", "E-TRON",
            "LINE", "ESTATE", "PORSCHE", "FIRST", "POWER", "ALL-WHEEL", "BAND", "PETROL", "DIESEL", "HYBRID",
            "ELECTRIC", "LOOK", "FAST", "RACING", "SPORT", "SPORTY", "BIGGER", "HEAR", "SAME", "E", "RALLYING", "BIG", "SMALL"}


def weight(w):
    core = re.sub(r"[^\w-]", "", w)
    if re.fullmatch(r"\d+", core):
        return {2: 3.2, 4: 6.5}.get(len(core), 2.5 * len(core))
    if re.fullmatch(r"[A-Z]+\d*", core) and len(core) >= 2 or re.fullmatch(r"[A-Z]\d", core):
        return 1.3 * len(core) + 0.6
    syl = max(1, len(re.findall(r"[aeiouy]+", core.lower())))
    v = syl * 1.0 + 0.4
    if w[-1] in ",": v += 0.8
    return v


WORDS = []   # dict(text, start, end, beat, sent)
for si, s in enumerate(SENT):
    ws = s["text"].split()
    wt = [weight(w) for w in ws]; tot = sum(wt); acc = 0
    for w, k in zip(ws, wt):
        a = s["start"] + (s["end"] - s["start"]) * acc / tot
        acc += k
        WORDS.append(dict(text=w, start=a, end=s["start"] + (s["end"] - s["start"]) * acc / tot, beat=s["beat"], sent=si))

NB = max(s["beat"] for s in SENT) + 1
BEAT_T = [0.0] + [min(s["start"] for s in SENT if s["beat"] == b) - 0.12 for b in range(1, NB)]
VO_END = SENT[-1]["end"]
DUR = VO_END + 0.9 + END_CARD


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


# ---------------------------------------------------------------- presenter direction (one per sentence)
DIRECT = [
    ("explain", "up"), ("point", "neutral"), ("count", "up"), ("shrug", "neutral"), ("point", "neutral"), ("explain", "smug"),
    ("point", "smug"), ("explain", "up"), ("point", "up"), ("explain", "neutral"), ("thumb", "smug"), ("hips", "skeptic"),
    ("shrug", "up"), ("explain", "neutral"), ("point", "neutral"), ("explain", "neutral"), ("point", "up"),
    ("explain", "smug"), ("shrug", "skeptic"), ("hips", "frown"), ("point", "neutral"), ("explain", "up"),
    ("thumb", "smug"), ("point", "neutral"), ("count", "neutral"), ("explain", "neutral"), ("point", "up"),
    ("hips", "skeptic"), ("shrug", "neutral"), ("explain", "neutral"), ("explain", "smug"), ("point", "up"),
    ("thumb", "smug"),
]
assert len(DIRECT) == len(SENT), (len(DIRECT), len(SENT))

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


# Zone for the illustration: y 330..900. Badge row at y 225.
BADGE_Y = 222


# ---------------------------------------------------------------- scenes
def scene0(ctx, lt):
    b = 0
    badge_row(ctx, W / 2, BADGE_Y, [("A", "chrome", 0.15), ("S", "chrome", 0.35), ("RS", "red", 0.55)], lt, 70)
    car_in(ctx, lt, 0.0, "hatch", 70, 580, 430, "python", s_model=True, sound=False)
    car_in(ctx, lt, 0.12, "suv", 560, 580, 450, "glacier")
    car_in(ctx, lt, 0.24, "avant", 60, 850, 470, "nardo", rs=True, rims="dark")
    car_in(ctx, lt, 0.36, "sedan", 560, 850, 450, "tango_red")


def scene1(ctx, lt):
    b = 1
    badge_row(ctx, W / 2, BADGE_Y, [("A", "chrome", 0.0)], lt, 70)
    t_list = wt(b, "A3")
    car_in(ctx, lt, 0.05, "sedan", 140, 760, 800, "glacier", out=t_list - 0.15)
    rows = [("A3", "hatch", 380, 520, "tango_red", wt(b, "A3")), ("A4", "sedan", 450, 700, "navarra", wt(b, "A4")),
            ("A6", "sedan", 540, 900, "daytona", wt(b, "A6"))]
    for name, kind, L, y, paint, t0 in rows:
        car_in(ctx, lt, t0 - 0.1, kind, 70, y, L, paint, dur=0.5)
        pop(ctx, lt, t0 + 0.2, 70 + L + 105, y - L * 0.16, lambda c, n=name: chip(c, 0, 0, n, "chrome", 56), sound=None)
    tsize = wt(b, "big")
    if lt > tsize - 0.3:
        p = ease_out((lt - tsize + 0.3) / 0.5)
        x = 1010
        arrow(ctx, [(x, 900), (x, 900 - 470 * p)], 9)
        pop(ctx, lt, tsize - 0.2, 905, 660, lambda c: tag(c, "SIZE", "yellow", 44, -0.05))


def scene2(ctx, lt):
    b = 2
    badge_row(ctx, W / 2, BADGE_Y, [("Q", "chrome", 0.0), ("= SUV", "white", wt(b, "SUV"))], lt, 70)
    t_rule = st(b, 1)
    car_in(ctx, lt, 0.05, "suv", 150, 780, 780, "kyalami", out=t_rule - 0.1)
    t3, t7 = wt(b, "Q3"), wt(b, "Q7")
    car_in(ctx, lt, t3 - 0.15, "suv", 40, 820, 400, "turbo_blue", dur=0.5)
    pop(ctx, lt, t3 + 0.1, 240, 540, lambda c: chip(c, 0, 0, "Q3", "chrome", 60))
    pop(ctx, lt, wt(b, "small") , 240, 900, lambda c: tag(c, "SMALL", "white", 40), sound=None)
    car_in(ctx, lt, t7 - 0.15, "suv", 470, 820, 580, "mythos", dur=0.5)
    pop(ctx, lt, t7 + 0.1, 760, 470, lambda c: chip(c, 0, 0, "Q7", "chrome", 60))
    pop(ctx, lt, wt(b, "big"), 760, 900, lambda c: tag(c, "BIG", "yellow", 40), sound=None)


def scene3(ctx, lt):
    b = 3
    badge_row(ctx, W / 2, BADGE_Y, [("S", "chrome", 0.0), ("SPORTY", "white", wt(b, "sporty"))], lt, 70)
    tA = wt(b, "A3")
    car_in(ctx, lt, 0.05, "hatch", 130, 800, 820, "python", s_model=True, rims="dark", calipers="#9AA0A6")
    # equation  S3 = A3 + power + suspension
    pop(ctx, lt, wt(b, "S3"), 200, 400, lambda c: chip(c, 0, 0, "S3", "chrome", 62))
    pop(ctx, lt, tA - 0.05, 330, 400, lambda c: label(c, "=", 0, 0, 80, DARK), sound=None)
    pop(ctx, lt, tA, 460, 400, lambda c: chip(c, 0, 0, "A3", "chrome", 62))
    pop(ctx, lt, wt(b, "power"), 640, 400, lambda c: (label(c, "+", -60, 0, 70, DARK), tag(c, "POWER", "yellow", 46, -0.04)))
    tf = wt(b, "firmer")
    pop(ctx, lt, tf, 760, 500, lambda c: (label(c, "+", -190, 0, 70, DARK), tag(c, "FIRMER SUSPENSION", "white", 38, 0.03)))
    if lt > wt(b, "power"):
        icon_bolt(ctx, 960, 400 + 6 * math.sin(lt * 10), 1.0)


def scene4(ctx, lt):
    b = 4
    tR = wt(b, "RennSport")
    badge_row(ctx, W / 2, BADGE_Y, [("RS", "red", 0.0), ("= RennSport", "white", tR)], lt, 70)
    t_top = st(b, 2)
    car_in(ctx, lt, 0.05, "avant", 120, 820, 840, "nardo", out=t_top - 0.1, rs=True, rims="black")
    if lt > 0.6 and lt < t_top:
        sound_waves(ctx, 110, 770, lt)
    tg = st(b, 1)
    pop(ctx, lt, tg + 0.1, W / 2, 400, lambda c: (chip(c, -200, 0, "RENNSPORT", "dark", 52), arrow(c, [(-5, 0), (65, 0)], 9, DARK, 24),
                                                  chip(c, 250, 0, "RACING SPORT", "yellow", 52)), out=t_top - 0.1)
    # podium
    if lt > t_top - 0.1:
        steps = [("A", 0, 150, 0.0), ("S", 1, 250, 0.15), ("RS", 2, 380, 0.3)]
        for name, i, hgt, d in steps:
            t0 = t_top + d
            if lt < t0:
                continue
            p = ease_out_back((lt - t0) / 0.4)
            x0 = 120 + i * 290; h = hgt * p
            ink(ctx, rrect(x0, 900 - h, 260, h, 14), hexc("#FFFFFF") if i < 2 else hexc("#FFD23F"), 5)
            sfx_once(lt, t0, "pop")
            chip(ctx, x0 + 130, 900 - h - 60, name, "red" if name == "RS" else "chrome", 62 if i == 2 else 52)
        tt = wt(b, "top")
        pop(ctx, lt, tt, 120 + 2 * 290 + 130, 900 - 380 + 70, lambda c: label(c, "TOP", 0, 0, 64, DARK), sound=None)


def scene5(ctx, lt):
    b = 5
    t_est = st(b, 1)
    badge_row(ctx, W / 2, BADGE_Y, [("RS", "red", 0.0), ("2", "red", wt(b, "RS2")), ("AVANT", "white", wt(b, "Avant"))], lt, 70)
    # three ghosts and a question mark
    if lt < t_est + 0.2:
        a = 1 - ease((lt - t_est + 0.05) / 0.25)
        ctx.push_group()
        for i, k in enumerate(["sedan", "fastback", "suv"]):
            draw_car(ctx, k, 50 + i * 335, 640, 310, ghost=True, wheel_rot=0)
        label(ctx, "?", W / 2, 800, 150, hexc("#FFD23F"), DARK, 14)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(max(0, a))
    car_in(ctx, lt, t_est - 0.05, "avant", 120, 820, 840, "nogaro", rs=True, rims="silver", calipers="#C8102E")
    pop(ctx, lt, t_est + 0.35, 300, 430, lambda c: stamp(c, "FIRST", "#2E9E5B", 84, -0.1), sound="stamp")
    pop(ctx, lt, wt(b, "Porsche"), 760, 420, lambda c: tag(c, "+ PORSCHE", "dark", 48, 0.04))
    pop(ctx, lt, wt(b, "1994"), 780, 530, lambda c: tag(c, "1994", "yellow", 64, -0.05))


def roof_line(ctx, kind, x, y, L, color, p):
    from car import BODY, YS
    pts = BODY[kind]; ys = YS[kind]
    # from the top of the windscreen backwards over the roof to the rear
    idx = [i for i, q in enumerate(pts) if q[1] > 0.25]
    sel = [pts[i] for i in idx][::-1]
    poly = [(x + q[0] * L, y - q[1] * ys * L - 10) for q in sel]
    n = max(2, int(len(poly) * p + 1))
    seg = poly[:n]
    if len(seg) >= 2:
        line(ctx, seg, 12, hexc(color))


def scene6(ctx, lt):
    b = 6
    t_sb = st(b, 1)
    badge_row(ctx, W / 2, BADGE_Y, [("AVANT", "chrome", 0.0), ("SPORTBACK", "chrome", wt(b, "Sportback"))], lt, 62)
    car_in(ctx, lt, 0.05, "avant", 200, 580, 600, "kyalami")
    if lt > wt(b, "estate"):
        roof_line(ctx, "avant", 200, 580, 600, "#FFD23F", ease((lt - wt(b, "estate")) / 0.5))
    pop(ctx, lt, wt(b, "estate"), 140, 380, lambda c: tag(c, "= ESTATE", "yellow", 46, -0.05))
    car_in(ctx, lt, t_sb - 0.05, "fastback", 200, 880, 600, "navarra", dur=0.5)
    tr = wt(b, "roof")
    if lt > tr - 0.2:
        roof_line(ctx, "fastback", 200, 880, 600, "#FF5A5F", ease((lt - tr + 0.2) / 0.5))
    pop(ctx, lt, tr, 150, 720, lambda c: tag(c, "SLOPING ROOF", "white", 38, -0.04))


def drivetrain(ctx, cx, cy, lt, glow):
    ctx.save(); ctx.translate(cx, cy)
    # frame
    ink(ctx, rrect(-330, -110, 660, 220, 70), hexc("#FFFFFF", 0.7), 5)
    ink(ctx, rrect(170, -70, 130, 140, 14), hexc("#9AA0A6"), 5)         # engine (front = right)
    label(ctx, "ENGINE", 235, 0, 30, DARK)
    line(ctx, [(170, 0), (-250, 0)], 14)                                  # prop shaft
    ink(ctx, ellipse(-20, 0, 30, 30), hexc("#FFD23F") if glow > 0 else hexc("#C9CDD2"), 4)  # centre diff
    for ax in (-250, 250):
        line(ctx, [(ax, -150), (ax, 150)], 14)
        for s in (-1, 1):
            g = glow > 0
            k = 0.5 + 0.5 * math.sin(lt * 10 + ax) if g else 0
            if g:
                ctx.set_source(rad_grad(ax, s * 160, 10, 110, [(0, (1, 0.82, 0.25, 0.6 * k + 0.2)), (1, (1, 0.82, 0.25, 0))]))
                ctx.arc(ax, s * 160, 110, 0, 2 * math.pi); ctx.fill()
            ink(ctx, rrect(ax - 70, s * 160 - 40, 140, 80, 22), hexc("#26272B"), 5)
            for i in range(5):
                xx = ax - 55 + i * 27 + ((lt * 200) % 27 if g else 0)
                if xx < ax + 60:
                    line(ctx, [(xx, s * 160 - 34), (xx, s * 160 + 34)], 3, hexc("#4A4D52"), sketch=False)
            if g:
                arrow(ctx, [(ax - 30, s * 160 + s * 70), (ax + 60, s * 160 + s * 70)], 7, hexc("#E39B00"), 20)
    ctx.restore()


def scene7(ctx, lt):
    b = 7
    t_r, t_q = st(b, 1), st(b, 2)
    badge_row(ctx, W / 2, BADGE_Y, [("quattro", "chrome", 0.0), ("= AWD", "yellow", wt(b, "all-wheel"))], lt, 66)
    if lt < t_r:
        a = 1 if lt < t_r - 0.2 else 1 - ease((lt - t_r + 0.2) / 0.2)
        ctx.push_group()
        p = ease_out_back(lt / 0.4)
        ctx.save(); ctx.translate(W / 2, 620); ctx.scale(p, p); ctx.translate(-W / 2, -620)
        drivetrain(ctx, W / 2, 620, lt, glow=1 if lt > wt(b, "all-wheel") else 0)
        ctx.restore()
        pop(ctx, lt, wt(b, "all-wheel") + 0.15, W / 2, 870, lambda c: tag(c, "ALL 4 WHEELS DRIVEN", "dark", 40), sound=None)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(a)
        sfx_once(lt, wt(b, "all-wheel"), "pop")
    if t_r - 0.1 < lt < t_q + 0.2 or lt >= t_r:
        if lt > t_r - 0.1:
            # rally car jumping over a crest
            k = lt - (t_r - 0.1)
            sfx_once(lt, t_r - 0.1, "whoosh")
            x = -500 + min(1, k / 1.1) * 680 if k < 1.1 else 180
            jump = max(0, math.sin(min(1, k / 1.1) * math.pi)) * 140 if k < 1.1 else 0
            land = lt - (t_r - 0.1 + 1.1)
            tilt = 0.08 * math.sin(min(1, k / 1.1) * math.pi) if k < 1.1 else -0.02 * math.exp(-land * 6) * math.sin(land * 20)
            # dust
            for i in range(6):
                ph = (lt * 1.3 + i / 6) % 1
                ctx.arc(x + 40 - ph * 260, 840 - 20 - ph * 60 - (i % 3) * 18, 30 + ph * 60, 0, 2 * math.pi)
                ctx.set_source_rgba(0.72, 0.62, 0.48, 0.35 * (1 - ph)); ctx.fill()
            draw_car(ctx, "rally", x, 840 - jump, 720, "glacier", lt * 18, livery=True, rims="white", tilt=tilt,
                     shadow=jump < 30)
            pop(ctx, lt, t_r + 0.5, 830, 420, lambda c: tag(c, "RALLY · 1980s", "yellow", 46, 0.05))
    if lt > t_q - 0.05:
        p = ease_out_back((lt - t_q + 0.05) / 0.35)
        sfx_once(lt, t_q - 0.05, "pop")
        ctx.save(); ctx.translate(300, 470); ctx.scale(p, p)
        ink(ctx, rrect(-230, -80, 460, 160, 40), hexc("#FFFFFF"), 6)
        ink(ctx, [(-60, 75), (-20, 75), (-70, 130)], hexc("#FFFFFF"), 0)
        line(ctx, [(-60, 80), (-70, 130), (-20, 80)], 6)
        label(ctx, "quattro", 10, 0, 92, DARK)
        if lt > wt(b, "q") - 0.1:
            r = ease_out((lt - wt(b, "q") + 0.1) / 0.4)
            ctx.new_sub_path(); ctx.arc(-138, 18, 56, -math.pi / 2, -math.pi / 2 + 2 * math.pi * r)
            ctx.set_source_rgba(*RED); ctx.set_line_width(9); ctx.stroke()
        ctx.restore()


def boot(ctx, cx, cy, lt, text_alpha=1.0):
    """Close-up of a car's tailgate with the model badge."""
    body = rpoly([(cx - 420, cy - 220), (cx + 420, cy - 220), (cx + 470, cy + 60), (cx + 470, cy + 230),
                  (cx - 470, cy + 230), (cx - 470, cy + 60)], [80, 80, 30, 20, 20, 30])
    col = hexc("#8E9396")
    ink(ctx, body, None, 6, grad=lin_grad(0, cy - 220, 0, cy + 230, [(0, shade(col, 0.3)), (0.5, col), (1, shade(col, -0.35))]))
    ink(ctx, rpoly([(cx - 330, cy - 200), (cx + 330, cy - 200), (cx + 360, cy - 70), (cx - 360, cy - 70)], 30),
        None, 5, grad=lin_grad(0, cy - 200, 0, cy - 70, [(0, hexc("#5C6F86")), (1, hexc("#1A2230"))]))
    for s in (-1, 1):
        ink(ctx, rpoly([(cx + s * 470, cy - 30), (cx + s * 260, cy - 20), (cx + s * 260, cy + 25), (cx + s * 470, cy + 30)], 14), hexc("#C8102E"), 5)
        line(ctx, [(cx + s * 450, cy), (cx + s * 280, cy + 3)], 5, hexc("#FF7A7A"))
    line(ctx, [(cx - 260, cy + 2), (cx + 260, cy + 2)], 6, hexc("#D04050"))
    ink(ctx, rrect(cx - 150, cy + 120, 300, 80, 8), hexc("#F5D23A"), 5)
    label(ctx, "BD 26 CAR", cx, cy + 160, 46, DARK, font=MONO)
    if text_alpha > 0:
        g = lin_grad(0, cy + 55, 0, cy + 105, [(0, hexc("#FFFFFF")), (0.5, hexc("#9AA1AB")), (1, hexc("#E8ECF0"))])
        label(ctx, "45 TFSI", cx + 300, cy + 82, 56, g, hexc("#2A2D33"), 5)
    return (cx + 300, cy + 82)


def scene8(ctx, lt):
    b = 8
    t_eng, t_band, t_more = st(b, 1), st(b, 2), st(b, 3)
    badge_row(ctx, W / 2, BADGE_Y, [("35", "chrome", wt(b, "35")), ("45", "chrome", wt(b, "45")),
                                     ("NOT LITRES", "white", wt(b, "isnt"))], lt, 66)
    if lt < t_band:
        a = 1 if lt < t_band - 0.2 else 1 - ease((lt - t_band + 0.2) / 0.2)
        ctx.push_group()
        p = ease_out(lt / 0.5)
        ctx.save(); ctx.translate(0, (1 - p) * 300)
        bx, by = boot(ctx, W / 2, 610, lt)
        if lt > wt(b, "boot"):
            r = ease_out((lt - wt(b, "boot")) / 0.4)
            ctx.new_sub_path(); ctx.arc(bx, by, 125, 0, 2 * math.pi * r); ctx.set_source_rgba(*YELLOW); ctx.set_line_width(10); ctx.stroke()
        ctx.restore()
        pop(ctx, lt, wt(b, "engine"), W / 2, 335, lambda c: (tag(c, "4.5 LITRE ENGINE?", "white", 50, -0.03), cross(c, 0, 0, 60)))
        ctx.pop_group_to_source(); ctx.paint_with_alpha(a)
    else:
        bands = [("30", 0.30, "120"), ("35", 0.40, "150"), ("40", 0.52, "200"), ("45", 0.64, "245"), ("50", 0.78, "290"), ("55", 0.92, "340")]
        x0, base, bw = 110, 900, 130
        for i, (n, hgt, hp) in enumerate(bands):
            t0 = t_band + 0.06 * i
            if lt < t0:
                continue
            p = ease_out_back((lt - t0) / 0.4)
            h = 520 * hgt * p
            x = x0 + i * 148
            hot = n == "45"
            ink(ctx, rrect(x, base - h, bw, h, 14), hexc("#FFD23F") if hot else hexc("#FFFFFF"), 5)
            label(ctx, n, x + bw / 2, base - h + 44, 50, DARK)
            label(ctx, hp, x + bw / 2, base - h - 30, 34, hexc("#3A3D44"), font=MONO)
        sfx_once(lt, t_band, "pop")
        label(ctx, "APPROX. HP", 110, 345, 36, hexc("#3A3D44"), font=MONO, anchor="l")
        if lt > t_more:
            p = ease_out((lt - t_more) / 0.6)
            arrow(ctx, [(150, 760), (150 + 760 * p, 760 - 330 * p)], 12, hexc("#D7182A"), 34)
            sfx_once(lt, t_more, "whoosh")


def scene9(ctx, lt):
    b = 9
    rows = [("TFSI", "PETROL TURBO", wt(b, "TFSI"), "pump"), ("TDI", "DIESEL", wt(b, "TDI"), "pumpd"),
            ("TFSI e", "PLUG-IN HYBRID", wt(b, "TFSI", 1), "hybrid"), ("e-tron", "ELECTRIC", wt(b, "e-tron"), "ev")]
    badge_row(ctx, W / 2, BADGE_Y, [("FUEL", "white", 0.0)], lt, 62)
    for i, (badge, desc, t0, ic) in enumerate(rows):
        y = 400 + i * 150
        def draw(c, badge=badge, desc=desc, ic=ic):
            ink(c, rrect(-470, -62, 940, 124, 30), hexc("#FFFFFF", 0.92), 5)
            chip(c, -300, 0, badge, "chrome", 56)
            label(c, desc, -120, 0, 50, DARK, anchor="l")
            if ic == "pump":
                icon_pump(c, 400, 0, 0.9, "#2E9E5B")
            elif ic == "pumpd":
                icon_pump(c, 400, 0, 0.9, "#1C1D21")
            elif ic == "hybrid":
                icon_pump(c, 360, 0, 0.75, "#2E9E5B"); icon_plug(c, 425, 0, 0.75)
            else:
                icon_battery(c, 390, 0, 0.9, 0.3 + 0.7 * ((lt * 0.8) % 1))
        pop(ctx, lt, t0 - 0.05, W / 2, y, draw)


def ring(ctx, x, y, r, lt, t0):
    if lt < t0:
        return
    p = ease_out((lt - t0) / 0.35)
    ctx.new_sub_path(); ctx.arc(x, y, r, -math.pi / 2, -math.pi / 2 + 2 * math.pi * p)
    ctx.set_source_rgba(*YELLOW); ctx.set_line_width(10); ctx.stroke()
    sfx_once(lt, t0, "pop")


def scene10(ctx, lt):
    b = 10
    L, x, y = 820, 130, 800
    badge_row(ctx, W / 2, BADGE_Y, [("S line", "chrome", 0.0), ("= LOOKS", "white", wt(b, "look"))], lt, 66)
    car_in(ctx, lt, 0.05, "sedan", x, y, L, "glacier", sline=True, rims="dark")
    if wt(b, "look") < lt < wt(b, "Bigger"):
        for i, (sx, sy) in enumerate([(300, 620), (620, 600), (860, 700), (200, 740)]):
            sparkle(ctx, sx, sy, 34, lt + i)
    R = WHEELS["sedan"][2] * L
    from car import YS
    wy = y - R
    for wx in (0.175, 0.81):
        ring(ctx, x + wx * L, wy, R * 1.35, lt, wt(b, "wheels") - 0.1)
    ring(ctx, x + 0.99 * L, y - 0.13 * L, 70, lt, wt(b, "bumpers") - 0.1)
    ring(ctx, x + 0.01 * L, y - 0.13 * L, 70, lt, wt(b, "bumpers") - 0.05)
    pop(ctx, lt, wt(b, "same"), W / 2, 420, lambda c: (chip(c, -170, 0, "ENGINE", "dark", 50), label(c, "=", 20, 0, 80, DARK),
                                                        chip(c, 160, 0, "SAME", "yellow", 50)))


def scene11(ctx, lt):
    b = 11
    rows = [("S line", "chrome", "LOOKS FAST", st(b, 0), dict(sline=True, rims="dark"), "glacier", 0.0),
            ("S", "chrome", "IS FAST", st(b, 1), dict(s_model=True, rims="dark"), "python", 0.7),
            ("RS", "red", "LOUD + FAST", st(b, 2), dict(rs=True, rims="black"), "nardo", 1.4)]
    for i, (bd, sty, desc, t0, kw, paint, speed) in enumerate(rows):
        y = 480 + i * 200
        if lt < t0 - 0.1:
            continue
        car_in(ctx, lt, t0 - 0.1, "sedan" if i == 0 else ("hatch" if i == 1 else "avant"), 430, y, 470, paint, dur=0.5, **kw)
        if speed and lt > t0 + 0.5:
            speed_lines(ctx, 430, y, 470, 140, speed * 0.7, seed=i * 31 + int(lt * 6))
        pop(ctx, lt, t0, 200, y - 100, lambda c, bd=bd, sty=sty: chip(c, 0, 0, bd, sty, 56), sound=None)
        pop(ctx, lt, t0 + 0.2, 200, y - 30, lambda c, d=desc: label(c, d, 0, 0, 34, DARK, font=MONO), sound=None)
        if i == 2 and lt > wt(b, "hear"):
            sound_waves(ctx, 420, y - 40, lt)
            sfx_once(lt, wt(b, "hear"), "rumble")


SCENES = [scene0, scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9, scene10, scene11]
assert len(SCENES) == NB


def end_card(ctx, t):
    p = ease_out_back(t / 0.45)
    ctx.save(); ctx.translate(W / 2, 520); ctx.scale(p, p)
    ink(ctx, rrect(-420, -170, 840, 340, 50), hexc("#FFFFFF", 0.95), 6)
    label(ctx, "FOLLOW FOR", 0, -80, 64, DARK)
    chip(ctx, 0, 30, "BADGE DECODED #2", "red", 60)
    label(ctx, HANDLE, 0, 120, 40, hexc("#3A3D44"), font=MONO)
    ctx.restore()


# ---------------------------------------------------------------- presenter state
HOPS = {0, 12, 22, 32}        # sentences that start with a little jump


def presenter_state(t, f):
    si = 0
    for i, s in enumerate(SENT):
        if t >= s["start"] - 0.15: si = i
    pose_now, brow = DIRECT[si]
    pose_prev = DIRECT[si - 1][0] if si > 0 else "rest"
    t_s = SENT[si]["start"] - 0.15
    tp = ease((t - t_s) / 0.3) if t >= SENT[0]["start"] - 0.15 else 1
    if t < SENT[0]["start"] - 0.15:
        pose_now, pose_prev, brow = "rest", "rest", "neutral"
    wave = 0.0
    if t > VO_END + 0.3:
        pose_prev, pose_now, brow = DIRECT[-1][0], "wave", "up"
        tp = ease((t - VO_END - 0.3) / 0.3)
        wave = 0.35 * math.sin((t - VO_END) * 11)
    mouth = float(ENV[min(f, len(ENV) - 1)])
    shape = ["ah", "ee", "ah", "oh"][(f // 3 + si) % 4]
    ph = (t + 0.7) % 3.1
    blink = 1.0 if ph < 0.1 else (0.5 if ph < 0.14 else 0)
    if pose_now == "point":
        look = (-0.35, -0.75)
    elif pose_now in ("explain", "thumb", "wave"):
        look = (0.0, 0.0)
    else:
        look = (0.3 * math.sin(t * 0.9), -0.2)
    # body: breathing, talk bounce, weight shift, lean into gestures
    bob = 6 * math.sin(t * 2.4) + 12 * mouth
    squash = 1.0 - 0.012 * mouth
    lean_pose = {"point": -0.045, "shrug": 0.0, "thumb": 0.03, "hips": 0.02, "explain": -0.015, "count": 0.0,
                 "rest": 0.0, "wave": 0.03}
    lean = 0.022 * math.sin(t * 0.9) + lean_pose[pose_prev] * (1 - tp) + lean_pose[pose_now] * tp
    tilt = 0.035 * math.sin(t * 1.3) + 0.035 * mouth * math.sin(t * 8.5)
    if brow == "skeptic":
        tilt += 0.08
    elif brow == "frown":
        tilt -= 0.05
    # gesture overshoot: a small extra bounce when the pose changes
    if 0 < t - t_s < 0.45:
        bob += 14 * math.sin((t - t_s) / 0.45 * math.pi)
    hop = 0.0
    if si in HOPS:
        k = t - t_s
        if 0 <= k < 0.12:
            squash *= 1 - 0.07 * math.sin(k / 0.12 * math.pi / 2)
        elif 0.12 <= k < 0.52:
            q = (k - 0.12) / 0.4
            hop = 70 * 4 * q * (1 - q)
            squash *= 1 + 0.04 * math.sin(q * math.pi)
        elif 0.52 <= k < 0.66:
            squash *= 1 - 0.06 * math.sin((k - 0.52) / 0.14 * math.pi)
    return dict(x=540, ground=1912, s=0.6, mouth=mouth, shape=shape, blink=blink, brows=brow, look=look,
                pose=lerp_pose(pose_prev, pose_now, tp), lean=lean, tilt=tilt, bob=bob, squash=squash, hop=hop,
                smile=0.8 if brow == "smug" else 0.5, wave=wave)


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
    set_boil(f, 4, 1.25)
    ctx = cairo.Context(surf)
    background(ctx)
    header(ctx)
    b = beat_at(t)
    if t < VO_END + 0.9:
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
    else:
        te = t - (VO_END + 0.9)
        sfx_once(te, 0, "pop")
        end_card(ctx, te)
    word, age, key = caption_now(t)
    if word:
        caption(ctx, word, W / 2, 978, age, key)
    draw_mecmation(ctx, presenter_state(t, f))


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
