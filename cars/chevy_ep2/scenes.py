"""Episode 2: every Chevrolet model explained. Timing data + the 13 scenes (one per beat).
Voice = the audio of the user's presenter clip (character_mecmation/chevrolet_presenter.mp4); words.json = its Whisper timing."""
import json, os, re, math
from ink import *
from car import draw_car, WHEELS
from widgets import *

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = "BADGE DECODED · #2"
BRAND = "CHEVROLET"
NEXT = "BADGE DECODED #3"

# Whisper mishears a few names: fix the caption text, keep the timing
FIX = {"Sting-Rae": "Stingray", "E-Rae": "E-Ray", "tracks": "Trax", "mid-sized": "mid-size", "2,500": "2500",
       "3,500": "3500", "Supersport": "Super Sport"}
# sentence index -> beat
BEAT_OF_SENT = [0, 1, 2, 2, 3, 3, 3, 4, 5, 5, 6, 7, 8, 8, 9, 9, 10, 11, 12]

KEYWORDS = {"CHEVROLET", "CHEVY", "CARS", "SUVS", "TRUCKS", "ELECTRIC", "CORVETTE", "STINGRAY", "E-RAY", "HYBRID",
            "Z06", "ZR1", "TRACK", "POWER", "TRAX", "TRAILBLAZER", "EQUINOX", "BLAZER", "TRAVERSE", "TAHOE", "SUBURBAN",
            "LONGER", "COLORADO", "SILVERADO", "MID-SIZE", "FULL-SIZE", "HD", "HEAVY-DUTY", "TOWING", "HAULING",
            "BADGES", "LT", "RS", "Z71", "OFF-ROAD", "ZR2", "SS", "SUPER", "SPORT", "SUPER SPORT", "PERFORMANCE", "EV", "FOLLOW",
            "FLAGSHIP", "SMALLEST", "SPORTS", "SPORTIER", "PICKUP", "CARGO", "PASSENGERS"}


def load_timing():
    W = json.load(open(os.path.join(HERE, "words.json")))
    sents, cur = [], []
    for w in W:
        cur.append(w)
        if w["w"][-1:] in ".?!":
            sents.append(cur); cur = []
    if cur:
        sents.append(cur)
    assert len(sents) == len(BEAT_OF_SENT), len(sents)
    SENT, WORDS = [], []
    for si, ws in enumerate(sents):
        SENT.append(dict(beat=BEAT_OF_SENT[si], start=ws[0]["s"], end=ws[-1]["e"],
                         text=" ".join(FIX.get(w["w"].strip(",.?!"), w["w"]) for w in ws)))
        for w in ws:
            core = w["w"].strip(",.?!")
            txt = w["w"].replace(core, FIX.get(core, core))
            WORDS.append(dict(text=txt, start=w["s"], end=w["e"], beat=BEAT_OF_SENT[si], sent=si))
    return SENT, WORDS


# ---------------------------------------------------------------- scene helpers (set by compose)
CTX = {}


def wt(beat, word, k=0):
    return CTX["wt"](beat, word, k)


def st(beat, i):
    return CTX["st"](beat, i)


def car_in(*a, **k):
    return CTX["car_in"](*a, **k)


BADGE_Y = 222
W = 1080
RED, BLUE, YEL, BLK, WHT = "#C8102E", "#1F4FA8", "#F2B800", "#1D1E22", "#EDEDEA"


def bars(ctx, lt, items, x0, base, bw, gap, hmax, vmax):
    """items: (label, value, t_in, colour)"""
    for i, (name, val, t0, col) in enumerate(items):
        if lt < t0:
            continue
        p = ease_out_back((lt - t0) / 0.4)
        sfx_once(lt, t0, "pop")
        h = hmax * val / vmax * p
        x = x0 + i * (bw + gap)
        ink(ctx, rrect(x, base - h, bw, h, 14), hexc(col), 5)
        label(ctx, f"{val:,}", x + bw / 2, base - h - 32, 40, DARK)
        label(ctx, name, x + bw / 2, base + 28, 30, DARK, font=MONO)


def trailer(ctx, x, y, w, h, wheel_rot):
    ink(ctx, rrect(x, y - h - 30, w, h, 12), hexc("#D9DCE1"), 5)
    for i in range(1, 4):
        line(ctx, [(x + i * w / 4, y - h - 22), (x + i * w / 4, y - 38)], 3, hexc("#A9AEB6"))
    from car import draw_wheel
    draw_wheel(ctx, x + w * 0.62, y - 26, 26, wheel_rot, hexc("#C9CDD2"))
    line(ctx, [(x + w, y - 50), (x + w + 46, y - 50)], 8)


def rocks(ctx, x, y, s=1.0):
    pts = [(x - 90 * s, y), (x - 60 * s, y - 40 * s), (x - 10 * s, y - 55 * s), (x + 40 * s, y - 35 * s), (x + 80 * s, y)]
    ink(ctx, rpoly(pts, 10), hexc("#8C8F94"), 5)
    ink(ctx, rpoly([(x + 60 * s, y), (x + 90 * s, y - 25 * s), (x + 130 * s, y)], 6), hexc("#A3A6AB"), 5)


def dust(ctx, x, y, lt):
    for i in range(6):
        ph = (lt * 1.3 + i / 6) % 1
        ctx.arc(x - ph * 220, y - 20 - ph * 50 - (i % 3) * 16, 26 + ph * 50, 0, 2 * math.pi)
        ctx.set_source_rgba(0.62, 0.52, 0.40, 0.35 * (1 - ph)); ctx.fill()


# ---------------------------------------------------------------- scenes
def scene0(ctx, lt):          # Every Chevrolet model explained in one minute
    badge_row(ctx, W / 2, BADGE_Y, [("EVERY MODEL", "yellow", 0.15)], lt, 66)
    car_in(ctx, lt, 0.0, "sports", 60, 560, 440, RED, rs=True, rims="black", sound=False)
    car_in(ctx, lt, 0.12, "suv", 560, 560, 450, WHT)
    car_in(ctx, lt, 0.24, "pickup", 50, 870, 470, BLUE)
    car_in(ctx, lt, 0.36, "suv", 570, 870, 440, "#3E7C5A")
    if lt > 0.9:
        icon_plug(ctx, 1000, 700, 0.8)


def scene1(ctx, lt):          # cars, SUVs, trucks, electric vehicles
    b = 1
    tiles = [("CARS", "sports", RED, wt(b, "cars"), 60, 560), ("SUVS", "suv", "#8E9396", wt(b, "SUVs"), 570, 560),
             ("TRUCKS", "pickup", BLUE, wt(b, "trucks"), 60, 880), ("ELECTRIC", "suv", "#3E7C5A", wt(b, "electric"), 570, 880)]
    badge_row(ctx, W / 2, BADGE_Y, [("CHEVY", "chrome", 0.0)], lt, 66)
    for name, kind, paint, t0, x, y in tiles:
        if lt < t0 + 0.2:      # grey outlines wait for their word
            a = min(1.0, lt / 0.3) * (1 - ease((lt - t0 + 0.05) / 0.25))
            if a > 0:
                ctx.push_group(); draw_car(ctx, kind, x, y, 430, ghost=True); ctx.pop_group_to_source(); ctx.paint_with_alpha(a)
        car_in(ctx, lt, t0 - 0.15, kind, x, y, 430, paint, dur=0.45)
        pop(ctx, lt, t0, x + 215, y - 230, lambda c, n=name: chip(c, 0, 0, n, "yellow" if n != "ELECTRIC" else "green", 46))
    if lt > wt(b, "electric") + 0.3:
        icon_battery(ctx, 990, 690, 0.8, 0.3 + 0.7 * ((lt * 0.8) % 1))


def scene2(ctx, lt):          # sports cars: the Corvette, flagship
    b = 2
    tc = wt(b, "Corvette")
    badge_row(ctx, W / 2, BADGE_Y, [("SPORTS CAR", "white", 0.0), ("CORVETTE", "red", tc)], lt, 62)
    car_in(ctx, lt, 0.1, "sports", 110, 800, 860, RED, rs=True, rims="black")
    if lt > 0.8:
        speed_lines(ctx, 110, 800, 860, 260, 0.5 + 0.2 * math.sin(lt * 6), seed=int(lt * 5))
    pop(ctx, lt, wt(b, "flagship"), 300, 430, lambda c: stamp(c, "FLAGSHIP", "#C8102E", 78, -0.08), sound="stamp")


CORVETTES = [("STINGRAY", RED, 495, {}), ("E-RAY", "#1F4FA8", 655, {}), ("Z06", "#F2B800", 670, dict(rs=True)),
             ("ZR1", "#1D1E22", 1064, dict(rs=True))]


def scene3(ctx, lt):          # Stingray, E-Ray, Z06, ZR1
    b = 3
    times = [wt(b, "Stingray"), wt(b, "E-Ray"), wt(b, "Z06"), wt(b, "ZR1")]
    badge_row(ctx, W / 2, BADGE_Y, [(n, "red" if n == "ZR1" else "chrome", t) for (n, *_), t in zip(CORVETTES, times)], lt, 50)
    cur = max([i for i, t in enumerate(times) if lt >= t - 0.1] or [0])
    name, paint, hp, kw = CORVETTES[cur]
    k = lt - (times[cur] - 0.1)
    p = max(0.02, ease_out_back(min(1, k / 0.35))) if cur > 0 else 1
    ctx.save(); ctx.translate(W / 2, 560); ctx.scale(p, p); ctx.translate(-W / 2, -560)
    car_in(ctx, lt, 0.05, "sports", 230, 560, 620, paint, rims="black" if cur else "silver", **kw)
    ctx.restore()
    if cur:
        sfx_once(lt, times[cur] - 0.1, "pop")
    bars(ctx, lt, [(n, v, t, c if i != 1 else "#7FB2FF") for i, ((n, c, v, _), t) in enumerate(zip(CORVETTES, times))],
         150, 850, 170, 30, 210, 1064)
    label(ctx, "HP", 80, 640, 36, hexc("#3A3D44"), font=MONO, anchor="l")
    pop(ctx, lt, wt(b, "hybrid"), 330, 640, lambda c: icon_bolt(c, 0, 0, 0.9), sound=None)
    pop(ctx, lt, wt(b, "track"), 560, 610, lambda c: tag(c, "TRACK", "dark", 38, -0.05), sound=None)
    pop(ctx, lt, wt(b, "power"), 760, 395, lambda c: tag(c, "MORE POWER", "yellow", 38, 0.04), sound=None)


SUVS = [("TRAX", 290, "#C8102E"), ("TRAILBLAZER", 330, "#E4E6EA"), ("EQUINOX", 370, "#5E6B78"),
        ("BLAZER", 410, "#1D1E22"), ("TRAVERSE", 460, "#24375E")]


def scene4(ctx, lt):          # Trax -> Traverse
    b = 4
    badge_row(ctx, W / 2, BADGE_Y, [("SUVS", "white", 0.0), ("SMALL → BIG".replace("→", ">"), "yellow", wt(b, "smallest"))], lt, 60)
    for i, (name, L, paint) in enumerate(SUVS):
        t0 = wt(b, name.capitalize() if name != "TRAILBLAZER" else "Trailblazer")
        y = 440 + i * 112
        car_in(ctx, lt, t0 - 0.12, "suv", 60, y, L, paint, dur=0.45)
        pop(ctx, lt, t0, 60 + L + 40 + 130, y - L * 0.2, lambda c, n=name: chip(c, 0, 0, n, "chrome", 40), sound=None)


def scene5(ctx, lt):          # Tahoe and Suburban, longer, passengers and cargo
    b = 5
    tt, ts = wt(b, "Tahoe"), wt(b, "Suburban")
    badge_row(ctx, W / 2, BADGE_Y, [("TAHOE", "chrome", tt), ("SUBURBAN", "chrome", ts)], lt, 60)
    car_in(ctx, lt, tt - 0.15, "suv", 120, 560, 620, "#1D1E22", rims="dark")
    car_in(ctx, lt, ts - 0.15, "suv", 60, 870, 760, "#E4E6EA", rims="dark")
    pop(ctx, lt, tt + 0.1, 860, 360, lambda c: tag(c, "TAHOE", "dark", 40), sound=None)
    pop(ctx, lt, ts + 0.1, 900, 640, lambda c: tag(c, "SUBURBAN", "dark", 40), sound=None)
    pop(ctx, lt, wt(b, "family"), 250, 360, lambda c: tag(c, "BIG FAMILY SUVS", "yellow", 40, -0.04), sound=None)
    tl = wt(b, "longer")
    if lt > tl - 0.1:
        p = ease_out((lt - tl + 0.1) / 0.5)
        y = 905
        arrow(ctx, [(60 + 380, y), (60 + 380 - 360 * p, y)], 8, DARK, 22)
        arrow(ctx, [(60 + 380, y), (60 + 380 + 360 * p, y)], 8, DARK, 22)
        sfx_once(lt, tl - 0.1, "whoosh")
    pop(ctx, lt, wt(b, "passengers"), 330, 700, lambda c: tag(c, "PASSENGERS", "white", 36, -0.03), sound="pop")
    pop(ctx, lt, wt(b, "cargo"), 690, 700, lambda c: tag(c, "CARGO", "white", 36, 0.03), sound="pop")


def scene6(ctx, lt):          # Colorado mid-size, Silverado full-size
    b = 6
    tcol, tsil = wt(b, "Colorado"), wt(b, "Silverado")
    badge_row(ctx, W / 2, BADGE_Y, [("TRUCKS", "white", 0.0), ("COLORADO", "chrome", tcol), ("SILVERADO", "chrome", tsil)], lt, 54)
    car_in(ctx, lt, tcol - 0.15, "pickup", 80, 560, 560, "#B8BCC2")
    pop(ctx, lt, wt(b, "mid-size"), 820, 380, lambda c: tag(c, "MID-SIZE", "yellow", 42, 0.04))
    car_in(ctx, lt, tsil - 0.15, "pickup", 50, 885, 760, RED)
    pop(ctx, lt, wt(b, "full-size"), 880, 620, lambda c: tag(c, "FULL-SIZE", "yellow", 42, -0.04))


def scene7(ctx, lt):          # 2500 / 3500 HD heavy-duty towing and hauling
    b = 7
    badge_row(ctx, W / 2, BADGE_Y, [("2500HD", "chrome", wt(b, "2500")), ("3500HD", "red", wt(b, "3500"))], lt, 62)
    t0 = 0.05
    if lt >= t0:
        p = ease_out((lt - t0) / 1.2)
        x = -1100 + (470 + 1100) * p
        R = WHEELS["pickup"][2] * 560
        rot = (x + 1100) / R
        trailer(ctx, x - 440, 820, 400, 230, rot * 1.6)
        draw_car(ctx, "pickup", x, 820, 560, "#1D1E22", rot, rims="dark", rs=True, calipers="#9AA0A6")
        speed_lines(ctx, x - 440, 820, 400, 260, (1 - p) * 1.4)
        sfx_once(lt, t0, "rumble")
    pop(ctx, lt, wt(b, "heavy-duty"), 760, 410, lambda c: tag(c, "HEAVY-DUTY", "dark", 42, 0.04))
    pop(ctx, lt, wt(b, "towing"), 260, 420, lambda c: tag(c, "TOWING", "yellow", 42, -0.05))
    pop(ctx, lt, wt(b, "hauling"), 300, 510, lambda c: tag(c, "HAULING", "yellow", 42, 0.03))


def scene8(ctx, lt):          # Now the badges. LT is a popular trim level
    b = 8
    names = ["LT", "RS", "Z71", "ZR2", "SS"]
    tl = wt(b, "LT")
    if lt < tl:
        for i, n in enumerate(names):
            pop(ctx, lt, 0.1 + 0.1 * i, 170 + i * 185, 560, lambda c, n=n: chip(c, 0, 0, n, "red" if n == "SS" else "chrome", 70))
    else:
        badge_row(ctx, W / 2, BADGE_Y, [("LT", "chrome", tl)], lt, 70)
        car_in(ctx, lt, tl - 0.05, "suv", 130, 850, 800, "#5E6B78", dur=0.5)
        pop(ctx, lt, wt(b, "popular"), 300, 420, lambda c: stamp(c, "POPULAR", "#2E9E5B", 70, -0.07), sound="stamp")
        pop(ctx, lt, wt(b, "trim"), 760, 430, lambda c: tag(c, "TRIM LEVEL", "white", 42, 0.04), sound=None)


def scene9(ctx, lt):          # RS sporty look; Z71 off-road; ZR2 more off-road
    b = 9
    trs, tz, tzr = wt(b, "RS"), wt(b, "Z71"), wt(b, "ZR2")
    badge_row(ctx, W / 2, BADGE_Y, [("RS", "chrome", trs), ("Z71", "chrome", tz), ("ZR2", "red", tzr)], lt, 66)
    car_in(ctx, lt, trs - 0.05, "suv", 130, 850, 800, "#C8102E", out=tz - 0.3, sline=True, rims="black")
    if trs + 0.5 < lt < tz - 0.3:
        for i, (sx, sy) in enumerate([(300, 560), (620, 540), (880, 650), (220, 700)]):
            sparkle(ctx, sx, sy, 30, lt + i)
        pop(ctx, lt, wt(b, "appearance"), 760, 420, lambda c: tag(c, "SPORTY LOOK", "yellow", 42, 0.04), sound=None)
    if tz - 0.2 <= lt < tzr - 0.05:
        rocks(ctx, 860, 885, 1.0)
        car_in(ctx, lt, tz - 0.2, "pickup", 110, 885, 700, "#4A5B3C", dur=0.5, rims="dark")
        dust(ctx, 140, 885, lt)
        pop(ctx, lt, wt(b, "off-road"), 760, 420, lambda c: tag(c, "OFF-ROAD", "yellow", 44, 0.04))
    if lt >= tzr - 0.05:
        k = lt - (tzr - 0.05)
        jump = max(0, math.sin(min(1, k / 0.9) * math.pi)) * 120 if k < 0.9 else 0
        tilt = 0.07 * math.sin(min(1, k / 0.9) * math.pi) if k < 0.9 else 0
        x = -300 + min(1, k / 0.9) * 420 if k < 0.9 else 120
        rocks(ctx, 520, 885, 1.3)
        dust(ctx, x + 40, 885, lt)
        draw_car(ctx, "pickup", x, 885 - jump, 700, "#D96A1E", lt * 14, rs=True, rims="black", tilt=tilt, shadow=jump < 25)
        sfx_once(lt, tzr - 0.05, "whoosh")
        pop(ctx, lt, wt(b, "hardware"), 740, 420, lambda c: tag(c, "MORE OFF-ROAD GEAR", "dark", 38, 0.04))


def scene10(ctx, lt):         # SS = Super Sport, performance badge
    b = 10
    badge_row(ctx, W / 2, BADGE_Y, [("SS", "red", 0.0), ("= SUPER SPORT", "white", wt(b, "Supersport"))], lt, 66)
    car_in(ctx, lt, 0.05, "fastback", 110, 850, 860, "#F2B800", s_model=True, rims="black")
    if lt > 0.7:
        speed_lines(ctx, 110, 850, 860, 280, 0.8, seed=int(lt * 6))
        sound_waves(ctx, 100, 790, lt)
        sfx_once(lt, 0.7, "rumble")
    pop(ctx, lt, wt(b, "performance"), 300, 430, lambda c: stamp(c, "PERFORMANCE", "#C8102E", 64, -0.07), sound="stamp")


EVS = [("EQUINOX EV", "suv", 440, "#3E7C5A"), ("BLAZER EV", "suv", 490, "#1F4FA8"), ("SILVERADO EV", "pickup", 560, "#E4E6EA")]


def scene11(ctx, lt):         # Equinox EV, Blazer EV, Silverado EV
    b = 11
    badge_row(ctx, W / 2, BADGE_Y, [("ELECTRIC", "green", 0.0), ("EV", "green", wt(b, "electric"))], lt, 66)
    times = [wt(b, "EV", 0), wt(b, "EV", 1), wt(b, "EV", 2)]
    starts = [wt(b, "Equinox"), wt(b, "Blazer"), wt(b, "Silverado")]
    for i, ((name, kind, L, paint), t0) in enumerate(zip(EVS, starts)):
        y = 500 + i * 200
        car_in(ctx, lt, t0 - 0.15, kind, 40, y, L, paint, dur=0.45)
        pop(ctx, lt, times[i], 40 + L + 40 + 150, y - 90, lambda c, n=name: chip(c, 0, 0, n, "green", 38), sound=None)
        if lt > times[i]:
            icon_battery(ctx, 40 + L + 190, y - 30, 0.75, 0.3 + 0.7 * ((lt * 0.8 + i * 0.3) % 1))


def scene12(ctx, lt):         # follow me
    b = 12
    tf = wt(b, "follow")
    car_in(ctx, lt, 0.0, "sports", 60, 870, 440, RED, rs=True, rims="black", sound=False)
    car_in(ctx, lt, 0.1, "pickup", 560, 870, 460, BLUE)
    if lt >= tf - 0.3:
        p = max(0.02, ease_out_back((lt - tf + 0.3) / 0.45))
        sfx_once(lt, tf - 0.3, "pop")
        ctx.save(); ctx.translate(W / 2, 470); ctx.scale(p, p)
        ink(ctx, rrect(-420, -170, 840, 340, 50), hexc("#FFFFFF", 0.95), 6)
        label(ctx, "FOLLOW FOR", 0, -80, 64, DARK)
        chip(ctx, 0, 30, NEXT, "red", 60)
        label(ctx, CTX["handle"], 0, 120, 40, hexc("#3A3D44"), font=MONO)
        ctx.restore()


SCENES = [scene0, scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9, scene10, scene11, scene12]
