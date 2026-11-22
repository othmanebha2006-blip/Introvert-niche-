"""Episode 3: every Porsche model explained. Timing data + the 15 scenes (one per beat).
Voice = the audio of the user's presenter clip (character_mecmation/porsche_presenter.mp4); words.json = its Whisper timing."""
import json, os, math
from ink import *
from car import draw_car, WHEELS
from widgets import *

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = "BADGE DECODED · #3"
BRAND = "PORSCHE"
NEXT = "BADGE DECODED #4"
CLIP = "porsche_presenter.mp4"

FIX = {"McCann": "Macan", "it's": "its"}
BEAT_OF_SENT = [0, 1, 2, 2, 3, 4, 4, 5, 5, 6, 7, 7, 8, 9, 10, 10, 11, 12, 13, 14]

KEYWORDS = {"PORSCHE", "SPORTS", "CARS", "SUVS", "FOUR-DOOR", "718", "MID-ENGINE", "BOXSTER", "CONVERTIBLE", "CAYMAN",
            "COUPE", "LEGENDARY", "911", "ICONIC", "REAR", "CARRERA", "S", "GTS", "TURBO", "FASTEST", "GT3", "RS", "TRACK",
            "MACAN", "CAYENNE", "SMALLER", "BIGGER", "PANAMERA", "TAYCAN", "ELECTRIC", "LUXURY", "BADGES", "GT", "GRAN",
            "TURISMO", "FOUR", "4", "FOUR-WHEEL", "E-HYBRID", "PLUG-IN", "HYBRID", "CROSS", "WAGON-STYLE", "ALL-WHEEL",
            "POWER", "FOLLOW", "POWERFUL", "SPORTIER", "PERFORMANCE"}


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
            WORDS.append(dict(text=w["w"].replace(core, FIX.get(core, core)), start=w["s"], end=w["e"],
                              beat=BEAT_OF_SENT[si], sent=si))
    return SENT, WORDS


CTX = {}


def wt(beat, word, k=0):
    return CTX["wt"](beat, word, k)


def car_in(*a, **k):
    return CTX["car_in"](*a, **k)


BADGE_Y = 222
W = 1080
GUARDS, WHITE_, BLACK_, SILVER, BLUE_, GREEN_, YELLOW_, CHALK = (
    "#C8102E", "#EDEDEA", "#1D1E22", "#A9ADB2", "#1F4FA8", "#5BA33B", "#F2B800", "#CFCBC2")


def ghost_wait(ctx, lt, t0, kind, x, y, L):
    """grey outline that waits for its word"""
    if lt < t0 + 0.2:
        a = min(1.0, lt / 0.3) * (1 - ease((lt - t0 + 0.05) / 0.25))
        if a > 0:
            ctx.push_group(); draw_car(ctx, kind, x, y, L, ghost=True); ctx.pop_group_to_source(); ctx.paint_with_alpha(a)


def swap_car(ctx, lt, times, specs, kind, x, y, L):
    """one car that changes look at each time (pop)"""
    cur = max([i for i, t in enumerate(times) if lt >= t - 0.1] or [0])
    paint, kw = specs[cur]
    k = lt - (times[cur] - 0.1)
    p = max(0.02, ease_out_back(min(1, k / 0.35))) if cur > 0 else 1
    if cur:
        sfx_once(lt, times[cur] - 0.1, "pop")
    ctx.save(); ctx.translate(x + L / 2, y); ctx.scale(p, p); ctx.translate(-(x + L / 2), -y)
    car_in(ctx, lt, 0.05, kind, x, y, L, paint, **kw)
    ctx.restore()
    return cur


def meter(ctx, lt, levels, x, y, w):
    """performance meter: list of (t_in, fraction)"""
    ink(ctx, rrect(x, y, w, 46, 23), hexc("#FFFFFF", 0.9), 5)
    f = 0.0
    for t0, fr in levels:
        if lt >= t0:
            f = f + (fr - f) * ease((lt - t0) / 0.4) if fr > f else fr
    if f > 0.02:
        ink(ctx, rrect(x + 6, y + 6, (w - 12) * f, 34, 17), None, 0,
            grad=lin_grad(x, 0, x + w, 0, [(0, hexc("#2E9E5B")), (0.6, hexc("#F2B800")), (1, hexc("#D7182A"))]))


def drivetrain(ctx, cx, cy, lt, glow, s=1.0):
    ctx.save(); ctx.translate(cx, cy); ctx.scale(s, s)
    ink(ctx, rrect(-330, -110, 660, 220, 70), hexc("#FFFFFF", 0.7), 5)
    ink(ctx, rrect(-310, -70, 130, 140, 14), hexc("#9AA0A6"), 5)            # engine at the rear (left)
    label(ctx, "ENGINE", -245, 0, 30, DARK)
    line(ctx, [(-180, 0), (250, 0)], 14)
    for ax in (-250, 250):
        line(ctx, [(ax, -150), (ax, 150)], 14)
        for sgn in (-1, 1):
            k = 0.5 + 0.5 * math.sin(lt * 10 + ax) if glow else 0
            if glow:
                ctx.set_source(rad_grad(ax, sgn * 160, 10, 110, [(0, (1, 0.82, 0.25, 0.6 * k + 0.2)), (1, (1, 0.82, 0.25, 0))]))
                ctx.arc(ax, sgn * 160, 110, 0, 2 * math.pi); ctx.fill()
            ink(ctx, rrect(ax - 70, sgn * 160 - 40, 140, 80, 22), hexc("#26272B"), 5)
    ctx.restore()


# ---------------------------------------------------------------- scenes
def scene0(ctx, lt):          # Every Porsche model explained in one minute
    badge_row(ctx, W / 2, BADGE_Y, [("EVERY MODEL", "yellow", 0.15)], lt, 66)
    car_in(ctx, lt, 0.0, "rear911", 60, 560, 440, GUARDS, sound=False)
    car_in(ctx, lt, 0.12, "suv", 560, 560, 450, WHITE_)
    car_in(ctx, lt, 0.24, "fastback", 50, 870, 470, BLUE_)
    car_in(ctx, lt, 0.36, "sports", 570, 870, 440, YELLOW_)


def scene1(ctx, lt):          # sports cars, SUVs, four-door performance cars
    b = 1
    badge_row(ctx, W / 2, BADGE_Y, [("PORSCHE", "chrome", 0.0)], lt, 66)
    tiles = [("SPORTS CARS", "rear911", GUARDS, wt(b, "sports"), 60, 560), ("SUVS", "suv", SILVER, wt(b, "SUVs"), 570, 560),
             ("4-DOOR", "fastback", BLACK_, wt(b, "four-door"), 300, 880)]
    for name, kind, paint, t0, x, y in tiles:
        ghost_wait(ctx, lt, t0, kind, x, y, 440)
        car_in(ctx, lt, t0 - 0.15, kind, x, y, 440, paint, dur=0.45)
        pop(ctx, lt, t0, x + 220, y - 235, lambda c, n=name: chip(c, 0, 0, n, "yellow", 44))


def scene2(ctx, lt):          # sports cars: the 718, smaller mid-engine
    b = 2
    t7 = wt(b, "718")
    badge_row(ctx, W / 2, BADGE_Y, [("SPORTS CARS", "white", 0.0), ("718", "chrome", t7)], lt, 64)
    car_in(ctx, lt, t7 - 0.2, "sports", 110, 820, 860, YELLOW_)
    tm = wt(b, "mid-engine")
    if lt > tm:     # engine sits between the seats and the rear axle
        a = 0.5 + 0.5 * math.sin((lt - tm) * 8)
        ctx.set_source(rad_grad(110 + 0.33 * 860, 820 - 110, 10, 120, [(0, (1, 0.55, 0.1, 0.65 * a + 0.2)), (1, (1, 0.55, 0.1, 0))]))
        ctx.arc(110 + 0.33 * 860, 820 - 110, 120, 0, 2 * math.pi); ctx.fill()
    pop(ctx, lt, tm, 300, 430, lambda c: tag(c, "MID-ENGINE", "yellow", 50, -0.05))
    pop(ctx, lt, wt(b, "smaller"), 780, 450, lambda c: tag(c, "SMALLER", "white", 44, 0.04), sound=None)


def scene3(ctx, lt):          # Boxster = convertible, Cayman = coupe
    b = 3
    tb, tc = wt(b, "Boxster"), wt(b, "Cayman")
    badge_row(ctx, W / 2, BADGE_Y, [("BOXSTER", "chrome", tb), ("CAYMAN", "chrome", tc)], lt, 62)
    car_in(ctx, lt, tb - 0.15, "roadster", 120, 560, 640, BLUE_, dur=0.5)
    pop(ctx, lt, wt(b, "convertible"), 820, 380, lambda c: tag(c, "CONVERTIBLE", "yellow", 42, 0.04))
    car_in(ctx, lt, tc - 0.15, "sports", 120, 880, 640, YELLOW_, dur=0.5)
    pop(ctx, lt, wt(b, "coupe"), 840, 700, lambda c: tag(c, "COUPE", "yellow", 42, -0.04))


def scene4(ctx, lt):          # the legendary 911, engine at the rear
    b = 4
    badge_row(ctx, W / 2, BADGE_Y, [("911", "red", wt(b, "911"))], lt, 76)
    car_in(ctx, lt, 0.05, "rear911", 110, 840, 860, GUARDS)
    pop(ctx, lt, wt(b, "legendary"), 300, 430, lambda c: stamp(c, "LEGENDARY", "#C8102E", 66, -0.07), sound="stamp")
    pop(ctx, lt, wt(b, "iconic"), 790, 440, lambda c: tag(c, "MOST ICONIC", "yellow", 42, 0.04), sound=None)
    tr = wt(b, "rear")
    if lt > tr - 0.2:
        a = 0.5 + 0.5 * math.sin((lt - tr) * 8)
        ex, ey = 110 + 0.09 * 860, 840 - 120
        ctx.set_source(rad_grad(ex, ey, 10, 130, [(0, (1, 0.55, 0.1, 0.65 * a + 0.2)), (1, (1, 0.55, 0.1, 0))]))
        ctx.arc(ex, ey, 130, 0, 2 * math.pi); ctx.fill()
        pop(ctx, lt, tr - 0.2, 260, 560, lambda c: tag(c, "ENGINE AT THE REAR", "dark", 38, -0.03))


def scene5(ctx, lt):          # 911 versions: Carrera, S, GTS, Turbo
    b = 5
    names = ["Carrera", "S", "GTS", "Turbo"]
    times = [wt(b, n) for n in names]
    badge_row(ctx, W / 2, BADGE_Y, [("911", "red", 0.0)] + [(n.upper(), "chrome", t) for n, t in zip(names, times)], lt, 54)
    specs = [(WHITE_, {}), (SILVER, dict(s_model=True)), (BLACK_, dict(sline=True, rims="black")),
             ("#6E7378", dict(rs=True, rims="dark"))]
    cur = swap_car(ctx, lt, times, specs, "rear911", 150, 780, 780)
    pop(ctx, lt, wt(b, "versions"), 760, 420, lambda c: tag(c, "SEVERAL VERSIONS", "white", 40, 0.04), sound=None)
    if lt > times[0] - 0.1:
        meter(ctx, lt, [(times[0], 0.25), (times[1], 0.5), (times[2], 0.72), (times[3], 1.0)], 140, 860, 800)
        label(ctx, "PERFORMANCE", 140, 840, 30, hexc("#3A3D44"), font=MONO, anchor="l")
    if cur == 3 and lt > wt(b, "fastest"):
        speed_lines(ctx, 150, 780, 780, 250, 0.9, seed=int(lt * 6))


def scene6(ctx, lt):          # GT3 for track, GT3 RS further
    b = 6
    t3, trs = wt(b, "GT3", 0), wt(b, "GT3", 1)
    badge_row(ctx, W / 2, BADGE_Y, [("GT3", "chrome", t3), ("GT3 RS", "red", trs)], lt, 62)
    # track kerb
    if lt > 0.1:
        for i in range(12):
            ink(ctx, rrect(i * 90, 868, 90, 22, 0), hexc("#D7182A" if i % 2 else "#FFFFFF"), 0)
        line(ctx, [(0, 868), (1080, 868)], 3)
    cur = swap_car(ctx, lt, [t3, trs], [(YELLOW_, dict(wing=1, rims="black")), (GREEN_, dict(wing=2, rs=True, rims="black"))],
                   "rear911", 150, 860, 780)
    pop(ctx, lt, wt(b, "track"), 300, 430, lambda c: tag(c, "BUILT FOR TRACK", "yellow", 44, -0.04))
    pop(ctx, lt, wt(b, "further"), 780, 440, lambda c: tag(c, "EVEN FURTHER", "dark", 44, 0.04))
    if lt > t3 + 0.6:
        speed_lines(ctx, 150, 860, 780, 250, 0.7, seed=int(lt * 6))


def scene7(ctx, lt):          # Now the SUVs: Macan smaller, Cayenne bigger
    b = 7
    tm, tc = wt(b, "Macan"), wt(b, "Cayenne")
    badge_row(ctx, W / 2, BADGE_Y, [("SUVS", "white", 0.0), ("MACAN", "chrome", tm), ("CAYENNE", "chrome", tc)], lt, 58)
    ghost_wait(ctx, lt, tm, "suv", 40, 820, 400)
    ghost_wait(ctx, lt, tc, "suv", 470, 820, 580)
    car_in(ctx, lt, tm - 0.15, "suv", 40, 820, 400, BLUE_, dur=0.5)
    pop(ctx, lt, wt(b, "smaller"), 240, 500, lambda c: tag(c, "SMALLER", "white", 40))
    car_in(ctx, lt, tc - 0.15, "suv", 470, 820, 580, BLACK_, dur=0.5)
    pop(ctx, lt, wt(b, "bigger"), 760, 440, lambda c: tag(c, "BIGGER", "yellow", 44))
    pop(ctx, lt, wt(b, "spacious"), 760, 540, lambda c: tag(c, "MORE SPACE", "white", 38), sound=None)


def scene8(ctx, lt):          # both have GTS and Turbo versions
    b = 8
    badge_row(ctx, W / 2, BADGE_Y, [("MACAN", "chrome", 0.0), ("CAYENNE", "chrome", 0.0)], lt, 58)
    car_in(ctx, lt, 0.0, "suv", 40, 820, 400, BLUE_, sound=False, rims="dark")
    car_in(ctx, lt, 0.0, "suv", 470, 820, 580, BLACK_, sound=False, rims="dark")
    for i, (x, w) in enumerate(((40, 400), (470, 580))):
        pop(ctx, lt, wt(b, "GTS"), x + w / 2 - 80, 470, lambda c: chip(c, 0, 0, "GTS", "chrome", 46))
        pop(ctx, lt, wt(b, "Turbo"), x + w / 2 + 90, 470, lambda c: chip(c, 0, 0, "TURBO", "red", 46))
    pop(ctx, lt, wt(b, "performance"), W / 2, 380, lambda c: tag(c, "DIFFERENT PERFORMANCE LEVELS", "white", 38), sound=None)


def scene9(ctx, lt):          # Panamera luxury sports sedan, Taycan fully electric
    b = 9
    tp, tt = wt(b, "Panamera"), wt(b, "Taycan")
    badge_row(ctx, W / 2, BADGE_Y, [("4-DOOR", "white", 0.0), ("PANAMERA", "chrome", tp), ("TAYCAN", "green", tt)], lt, 56)
    ghost_wait(ctx, lt, tp, "fastback", 120, 560, 640)
    ghost_wait(ctx, lt, tt, "fastback", 120, 880, 640)
    car_in(ctx, lt, tp - 0.15, "fastback", 120, 560, 640, SILVER, dur=0.5, rims="dark")
    pop(ctx, lt, wt(b, "luxury"), 860, 380, lambda c: tag(c, "LUXURY SPORTS SEDAN", "yellow", 34, 0.04))
    car_in(ctx, lt, tt - 0.15, "fastback", 120, 880, 640, BLUE_, dur=0.5, rims="dark")
    te = wt(b, "electric")
    pop(ctx, lt, te, 860, 700, lambda c: tag(c, "FULLY ELECTRIC", "green", 38, -0.04))
    if lt > te:
        icon_battery(ctx, 920, 790, 0.9, 0.3 + 0.7 * ((lt * 0.8) % 1))


def scene10(ctx, lt):         # Now the badges: S, GTS, GT = Gran Turismo
    b = 10
    rows = [("S", "chrome", wt(b, "S"), "MORE POWER", "yellow"), ("GTS", "chrome", wt(b, "GTS"), "SPORTIER", "yellow"),
            ("GT", "red", wt(b, "GT"), "GRAN TURISMO", "white")]
    badge_row(ctx, W / 2, BADGE_Y, [("BADGES", "white", 0.0)], lt, 62)
    for i, (n, sty, t0, desc, dsty) in enumerate(rows):
        y = 430 + i * 170
        pop(ctx, lt, t0, 250, y, lambda c, n=n, sty=sty: chip(c, 0, 0, n, sty, 84))
        pop(ctx, lt, t0 + 0.25, 420, y, lambda c: arrow(c, [(-40, 0), (40, 0)], 9, DARK, 26), sound=None)
        pop(ctx, lt, t0 + 0.3, 700, y, lambda c, d=desc, s=dsty: chip(c, 0, 0, d, s, 52), sound=None)


def scene11(ctx, lt):         # add a 4 -> four-wheel drive
    b = 11
    t4 = wt(b, "four")
    badge_row(ctx, W / 2, BADGE_Y, [("CARRERA", "chrome", 0.0), ("4", "red", t4)], lt, 70)
    p = max(0.02, ease_out_back(min(1, lt / 0.4)))
    ctx.save(); ctx.translate(W / 2, 620); ctx.scale(p, p)
    drivetrain(ctx, 0, 0, lt, glow=lt > wt(b, "four-wheel"), s=1.0)
    ctx.restore()
    pop(ctx, lt, wt(b, "four-wheel"), W / 2, 870, lambda c: tag(c, "FOUR-WHEEL DRIVE", "yellow", 46))


def scene12(ctx, lt):         # E-Hybrid = plug-in hybrid, Cross Turismo = wagon-style
    b = 12
    te, tc = wt(b, "E-Hybrid"), wt(b, "Cross")
    badge_row(ctx, W / 2, BADGE_Y, [("E-HYBRID", "green", te), ("CROSS TURISMO", "chrome", tc)], lt, 54)
    car_in(ctx, lt, te - 0.15, "fastback", 120, 560, 640, "#3E7C5A", dur=0.5, rims="dark")
    tpl = wt(b, "plug-in")
    if lt > tpl:
        icon_pump(ctx, 860, 420, 0.8, "#2E9E5B"); icon_plug(ctx, 940, 420, 0.8)
    pop(ctx, lt, tpl, 300, 390, lambda c: tag(c, "PLUG-IN HYBRID", "green", 42, -0.04), sound="pop")
    car_in(ctx, lt, tc - 0.15, "avant", 120, 880, 640, CHALK, dur=0.5, rims="dark")
    pop(ctx, lt, wt(b, "wagon-style"), 830, 700, lambda c: tag(c, "WAGON-STYLE", "yellow", 42, -0.04))


def scene13(ctx, lt):         # So a 911 Carrera 4 GTS = AWD sports car with extra performance
    b = 13
    parts = [("911", "red", wt(b, "911")), ("CARRERA", "chrome", wt(b, "Carrera")), ("4", "chrome", wt(b, "4")),
             ("GTS", "chrome", wt(b, "GTS"))]
    badge_row(ctx, W / 2, BADGE_Y, parts, lt, 64)
    car_in(ctx, lt, wt(b, "911") - 0.2, "rear911", 150, 870, 780, BLACK_, sline=True, rims="black")
    pop(ctx, lt, wt(b, "all-wheel"), 300, 420, lambda c: tag(c, "4 = ALL-WHEEL DRIVE", "yellow", 40, -0.04))
    pop(ctx, lt, wt(b, "extra"), 760, 520, lambda c: tag(c, "GTS = EXTRA PERFORMANCE", "dark", 34, 0.04))
    pop(ctx, lt, wt(b, "sports"), 330, 560, lambda c: tag(c, "911 = SPORTS CAR", "white", 36, -0.02), sound=None)


def scene14(ctx, lt):         # follow me
    b = 14
    tf = wt(b, "follow")
    car_in(ctx, lt, 0.0, "rear911", 60, 870, 440, GUARDS, sound=False)
    car_in(ctx, lt, 0.1, "suv", 560, 870, 450, BLACK_)
    if lt >= tf - 0.3:
        p = max(0.02, ease_out_back((lt - tf + 0.3) / 0.45))
        sfx_once(lt, tf - 0.3, "pop")
        ctx.save(); ctx.translate(W / 2, 470); ctx.scale(p, p)
        ink(ctx, rrect(-420, -170, 840, 340, 50), hexc("#FFFFFF", 0.95), 6)
        label(ctx, "FOLLOW FOR", 0, -80, 64, DARK)
        chip(ctx, 0, 30, NEXT, "red", 60)
        label(ctx, CTX["handle"], 0, 120, 40, hexc("#3A3D44"), font=MONO)
        ctx.restore()


SCENES = [scene0, scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9, scene10, scene11, scene12,
          scene13, scene14]
