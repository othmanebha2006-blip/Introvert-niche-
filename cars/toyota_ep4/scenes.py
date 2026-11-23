"""Episode 4: every Toyota model explained. Timing data + the 14 scenes (one per beat).
Voice = the audio of the user's presenter clip (character_mecmation/toyota_presenter.mp4); words.json = its Whisper timing.
Rule kept in every scene: something is on screen from the first frame (grey outlines wait for their word)."""
import json, os, math
from ink import *
from car import draw_car, WHEELS
from widgets import *

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = "BADGE DECODED · #4"
BRAND = "TOYOTA"
NEXT = "BADGE DECODED #5"
CLIP = "toyota_presenter.mp4"

FIX = {"Guzoo": "Gazoo", "i-Force": "i-FORCE"}
SPLIT_AT = [41.1]                      # extra scene cut inside the long GR sentence (word start time)
BEAT_OF_SENT = [0, 1, 2, 2, 3, 4, 5, 6, 6, 7, 8, 9, 10, 11, 12, 13]

KEYWORDS = {"TOYOTA", "CARS", "SUVS", "TRUCKS", "PERFORMANCE", "COROLLA", "CAMRY", "COMPACT", "BIGGER", "COMFORTABLE",
            "PRIUS", "HYBRID", "PLUG-IN", "CHARGED", "OUTLET", "CROWN", "PREMIUM", "MIRAI", "HYDROGEN", "CROSS", "RAV4",
            "HIGHLANDER", "GRAND", "4RUNNER", "OFF-ROAD", "LAND", "CRUISER", "SEQUOIA", "FAMILY", "TACOMA", "TUNDRA",
            "MID-SIZE", "FULL-SIZE", "BADGES", "GR", "GAZOO", "RACING", "GR86", "LIGHTWEIGHT", "HOT", "HATCH", "SUPRA",
            "TWO-DOOR", "TRD", "DEVELOPMENT", "UPGRADES", "I-FORCE", "MAX", "TURBOCHARGED", "PRO", "FOLLOW", "PICKUP"}


def load_timing():
    W = json.load(open(os.path.join(HERE, "words.json")))
    sents, cur = [], []
    for w in W:
        if cur and any(abs(w["s"] - t) < 0.01 for t in SPLIT_AT):
            sents.append(cur); cur = []
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
RED_, WHITE_, BLACK_, SILVER, BLUE_, GREEN_, SAND, ORANGE_, GREY_ = (
    "#C8102E", "#EDEDEA", "#1D1E22", "#A9ADB2", "#1F4FA8", "#3F5B3A", "#C8B28A", "#D96A1E", "#5E6B78")


def ghost_wait(ctx, lt, t0, kind, x, y, L):
    if lt < t0 + 0.2:
        a = min(1.0, lt / 0.25 + 0.4) * (1 - ease((lt - t0 + 0.05) / 0.25))
        if a > 0:
            ctx.push_group(); draw_car(ctx, kind, x, y, L, ghost=True); ctx.pop_group_to_source(); ctx.paint_with_alpha(min(1, a))


def slot(ctx, lt, t0, kind, x, y, L, paint, early=False, **kw):
    """grey outline from the scene start, the real car drives in on its word
    (early=True: the car arrives as the scene opens, so the screen is never empty while the intro line is spoken)"""
    if early:
        car_in(ctx, lt, 0.0, kind, x, y, L, paint, dur=0.5, **kw)
        return
    ghost_wait(ctx, lt, t0, kind, x, y, L)
    car_in(ctx, lt, t0 - 0.15, kind, x, y, L, paint, dur=0.45, **kw)


def rocks(ctx, x, y, s=1.0):
    pts = [(x - 90 * s, y), (x - 60 * s, y - 40 * s), (x - 10 * s, y - 55 * s), (x + 40 * s, y - 35 * s), (x + 80 * s, y)]
    ink(ctx, rpoly(pts, 10), hexc("#8C8F94"), 5)
    ink(ctx, rpoly([(x + 60 * s, y), (x + 90 * s, y - 25 * s), (x + 130 * s, y)], 6), hexc("#A3A6AB"), 5)


def outlet(ctx, x, y):
    ink(ctx, rrect(x - 38, y - 50, 76, 100, 12), hexc("#FFFFFF"), 5)
    for dx in (-12, 12):
        ink(ctx, rrect(x + dx - 4, y - 22, 8, 20, 3), DARK, 0)
    ink(ctx, ellipse(x, y + 18, 6, 6, 12), DARK, 0)


def h2(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, ellipse(0, 0, 52, 52, 40), hexc("#2C6FCF"), 5)
    label(ctx, "H", -8, -2, 54, hexc("#FFFFFF"))
    label(ctx, "2", 20, 14, 28, hexc("#FFFFFF"))
    ctx.restore()


def kerb(ctx, y):
    for i in range(12):
        ink(ctx, rrect(i * 90, y, 90, 22, 0), hexc("#D7182A" if i % 2 else "#FFFFFF"), 0)
    line(ctx, [(0, y), (1080, y)], 3)


def turbo(ctx, x, y, lt, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, ellipse(0, 0, 60, 60, 40), hexc("#BFC3C8"), 6)
    ctx.save(); ctx.rotate(lt * 12)
    for i in range(6):
        a = i * math.pi / 3
        line(ctx, [(math.cos(a) * 12, math.sin(a) * 12), (math.cos(a + 0.6) * 46, math.sin(a + 0.6) * 46)], 7)
    ctx.restore()
    ink(ctx, ellipse(0, 0, 12, 12, 16), DARK, 0)
    ctx.restore()


# ---------------------------------------------------------------- scenes
def scene0(ctx, lt):          # Every Toyota model explained in one minute
    badge_row(ctx, W / 2, BADGE_Y, [("EVERY MODEL", "yellow", -0.4)], lt, 66)
    car_in(ctx, lt, -0.45, "sedan", 60, 560, 440, RED_, sound=False)      # already driving in on frame 1
    car_in(ctx, lt, -0.35, "suv", 560, 560, 450, WHITE_, sound=False)
    car_in(ctx, lt, -0.25, "pickup", 50, 870, 470, GREY_, sound=False)
    car_in(ctx, lt, -0.15, "sports", 570, 870, 440, "#F2B800", rs=True, rims="black", sound=False)


def scene1(ctx, lt):          # cars, SUVs, trucks, performance models
    b = 1
    badge_row(ctx, W / 2, BADGE_Y, [("TOYOTA", "chrome", 0.0)], lt, 66)
    tiles = [("CARS", "sedan", RED_, wt(b, "cars"), 60, 560), ("SUVS", "suv", SILVER, wt(b, "SUVs"), 570, 560),
             ("TRUCKS", "pickup", GREY_, wt(b, "trucks"), 60, 880),
             ("PERFORMANCE", "sports", "#F2B800", wt(b, "performance"), 570, 880)]
    for name, kind, paint, t0, x, y in tiles:
        slot(ctx, lt, t0, kind, x, y, 430, paint, **(dict(rs=True, rims="black") if kind == "sports" else {}))
        pop(ctx, lt, t0, x + 215, y - 225, lambda c, n=name: chip(c, 0, 0, n, "yellow", 42))


def scene2(ctx, lt):          # Corolla everyday compact, Camry bigger and more comfortable
    b = 2
    tco, tca = wt(b, "Corolla"), wt(b, "Camry")
    badge_row(ctx, W / 2, BADGE_Y, [("CARS", "white", 0.0), ("COROLLA", "chrome", tco), ("CAMRY", "chrome", tca)], lt, 58)
    slot(ctx, lt, tco, "sedan", 120, 560, 560, BLUE_, early=True)
    pop(ctx, lt, wt(b, "everyday"), 840, 380, lambda c: tag(c, "EVERYDAY COMPACT", "yellow", 36, 0.04))
    slot(ctx, lt, tca, "sedan", 60, 880, 720, BLACK_, rims="dark")
    pop(ctx, lt, wt(b, "bigger"), 870, 640, lambda c: tag(c, "BIGGER", "yellow", 42, -0.04))
    pop(ctx, lt, wt(b, "comfortable"), 250, 640, lambda c: tag(c, "MORE COMFORT", "white", 38, 0.03), sound=None)


def scene3(ctx, lt):          # Prius hybrid, Prius Plug-in charged from an outlet
    b = 3
    t1, t2 = wt(b, "Prius", 0), wt(b, "Prius", 1)
    badge_row(ctx, W / 2, BADGE_Y, [("PRIUS", "chrome", 0.0), ("PLUG-IN", "green", wt(b, "plug-in"))], lt, 62)
    slot(ctx, lt, t1, "fastback", 120, 560, 640, SILVER, rims="dark")
    th = wt(b, "hybrid")
    pop(ctx, lt, th, 840, 380, lambda c: tag(c, "HYBRID", "green", 44, 0.04))
    if lt > th:
        icon_pump(ctx, 860, 480, 0.7, "#2E9E5B"); icon_bolt(ctx, 930, 480, 0.8)
    slot(ctx, lt, t2, "fastback", 60, 880, 640, "#2E5E8C", rims="dark")
    tc = wt(b, "charged")
    if lt > tc - 0.1:
        p = ease_out((lt - tc + 0.1) / 0.5)
        outlet(ctx, 960, 780)
        cable = qbez((160, 800), (520, 960), (920, 790), 20)
        n = max(2, int(len(cable) * p))
        line(ctx, cable[:n], 8, DARK)
        sfx_once(lt, tc - 0.1, "pop")
    pop(ctx, lt, wt(b, "outlet"), 830, 650, lambda c: tag(c, "CHARGE FROM AN OUTLET", "yellow", 32, -0.04), sound=None)


def scene4(ctx, lt):          # Crown premium, Mirai hydrogen
    b = 4
    tcr, tm = wt(b, "Crown"), wt(b, "Mirai")
    badge_row(ctx, W / 2, BADGE_Y, [("CROWN", "chrome", 0.0), ("MIRAI", "blue", tm)], lt, 62)
    slot(ctx, lt, tcr, "sedan", 120, 560, 640, "#3A2E2A", sline=True, rims="black")
    pop(ctx, lt, wt(b, "premium"), 300, 380, lambda c: stamp(c, "PREMIUM", "#B8860B", 62, -0.06), sound="stamp")
    slot(ctx, lt, tm, "fastback", 60, 880, 680, "#E4E6EA", rims="dark")
    th = wt(b, "hydrogen")
    pop(ctx, lt, th, 900, 615, lambda c: h2(c, 0, 0, 0.9))
    pop(ctx, lt, th + 0.1, 230, 615, lambda c: tag(c, "HYDROGEN", "blue", 40, -0.04), sound=None)
    tp = wt(b, "petrol")
    if lt > tp:
        icon_pump(ctx, 640, 615, 0.7, "#8C8F94"); cross(ctx, 640, 615, 46, 10)


SUVS = [("COROLLA CROSS", "Corolla", 330, "#C8102E"), ("RAV4", "RAV4", 380, "#3F5B3A"),
        ("HIGHLANDER", "Highlander", 430, "#1D1E22"), ("GRAND HIGHLANDER", "Grand", 480, "#A9ADB2")]


def scene5(ctx, lt):          # Corolla Cross, RAV4, Highlander, Grand Highlander
    b = 5
    badge_row(ctx, W / 2, BADGE_Y, [("SUVS", "white", 0.0), ("SMALL > BIG", "yellow", wt(b, "smaller"))], lt, 60)
    for i, (name, word, L, paint) in enumerate(SUVS):
        t0 = wt(b, word)
        y = 460 + i * 140
        slot(ctx, lt, t0, "suv", 50, y, L, paint, early=(i == 0))
        pop(ctx, lt, t0, 50 + L + 40 + 150, y - L * 0.2, lambda c, n=name: chip(c, 0, 0, n, "chrome", 36), sound=None)


def scene6(ctx, lt):          # 4Runner off-road, Land Cruiser serious off-road, Sequoia big family SUV
    b = 6
    t4, tl, ts = wt(b, "4Runner"), wt(b, "Land"), wt(b, "Sequoia")
    badge_row(ctx, W / 2, BADGE_Y, [("4RUNNER", "chrome", 0.0), ("LAND CRUISER", "chrome", tl), ("SEQUOIA", "chrome", ts)], lt, 50)
    rows = [("suv", t4, 40, 500, 500, GREEN_, "OFF-ROAD", wt(b, "off-road", 0)),
            ("suv", tl, 40, 700, 540, SAND, "SERIOUS OFF-ROAD", wt(b, "off-road", 1)),
            ("suv", ts, 40, 900, 620, BLACK_, "BIG FAMILY SUV", wt(b, "family"))]
    for kind, t0, x, y, L, paint, txt, tt in rows:
        if "OFF" in txt:
            rocks(ctx, x + L + 90, y, 0.7)
        slot(ctx, lt, t0, kind, x, y, L, paint, rims="dark")
        pop(ctx, lt, tt, x + L + 230 if txt != "BIG FAMILY SUV" else x + L + 190, y - 150 if "OFF" in txt else y - 130,
            lambda c, t=txt: tag(c, t, "yellow", 30, 0.03))


def scene7(ctx, lt):          # Tacoma mid-size, Tundra full-size
    b = 7
    tt, tu = wt(b, "Tacoma"), wt(b, "Tundra")
    badge_row(ctx, W / 2, BADGE_Y, [("TRUCKS", "white", 0.0), ("TACOMA", "chrome", tt), ("TUNDRA", "chrome", tu)], lt, 56)
    slot(ctx, lt, tt, "pickup", 80, 560, 560, ORANGE_, rims="dark", early=True)
    pop(ctx, lt, wt(b, "mid-size"), 830, 380, lambda c: tag(c, "MID-SIZE", "yellow", 42, 0.04))
    slot(ctx, lt, tu, "pickup", 50, 885, 760, SILVER, rims="dark")
    pop(ctx, lt, wt(b, "full-size"), 880, 620, lambda c: tag(c, "FULL-SIZE", "yellow", 42, -0.04))


def scene8(ctx, lt):          # GR = Gazoo Racing, Toyota's performance division
    b = 8
    tg = wt(b, "GR")
    badge_row(ctx, W / 2, BADGE_Y, [("PERFORMANCE BADGES", "white", 0.0)], lt, 56)
    kerb(ctx, 880)
    car_in(ctx, lt, 0.05, "sports", 150, 870, 780, "#D7182A", rs=True, rims="black")
    if lt > 0.7:
        speed_lines(ctx, 150, 870, 780, 260, 0.8, seed=int(lt * 6))
    pop(ctx, lt, tg, 260, 420, lambda c: chip(c, 0, 0, "GR", "red", 90))
    pop(ctx, lt, wt(b, "Gazoo"), 650, 420, lambda c: chip(c, 0, 0, "GAZOO RACING", "white", 50))
    pop(ctx, lt, wt(b, "Division"), W / 2, 540, lambda c: tag(c, "TOYOTA'S PERFORMANCE DIVISION", "yellow", 34), sound=None)


def scene9(ctx, lt):          # GR86 coupe, GR Corolla hot hatch, GR Supra two-door sports car
    b = 9
    rows = [("GR86", "sports", wt(b, "GR86"), WHITE_, "LIGHTWEIGHT COUPE", wt(b, "lightweight"), dict(rims="black")),
            ("GR COROLLA", "hatch", wt(b, "Corolla"), "#1D1E22", "HOT HATCH", wt(b, "hot"), dict(s_model=True, rims="black")),
            ("GR SUPRA", "sports", wt(b, "Supra"), "#D7182A", "2-DOOR SPORTS CAR", wt(b, "two-door"), dict(rs=True, rims="black"))]
    badge_row(ctx, W / 2, BADGE_Y, [("GR", "red", 0.0)], lt, 70)
    for i, (name, kind, t0, paint, desc, td, kw) in enumerate(rows):
        y = 500 + i * 195
        slot(ctx, lt, t0, kind, 40, y, 470, paint, **kw)
        pop(ctx, lt, t0, 790, y - 120, lambda c, n=name: chip(c, 0, 0, n, "red", 40), sound=None)
        pop(ctx, lt, td, 790, y - 45, lambda c, d=desc: tag(c, d, "yellow", 30, 0.02), sound=None)


def scene10(ctx, lt):         # TRD = Toyota Racing Development: performance + off-road upgrades
    b = 10
    badge_row(ctx, W / 2, BADGE_Y, [("TRD", "red", 0.0)], lt, 76)
    td = wt(b, "Toyota")
    pop(ctx, lt, td, W / 2, 380, lambda c: chip(c, 0, 0, "TOYOTA RACING DEVELOPMENT", "white", 44))
    rocks(ctx, 900, 880, 1.1)
    car_in(ctx, lt, 0.05, "pickup", 120, 880, 720, "#1D1E22", rs=True, rims="black", calipers="#D7182A")
    pop(ctx, lt, wt(b, "performance"), 280, 500, lambda c: tag(c, "+ PERFORMANCE", "yellow", 40, -0.04))
    pop(ctx, lt, wt(b, "off-road"), 760, 500, lambda c: tag(c, "+ OFF-ROAD UPGRADES", "yellow", 36, 0.04))


def scene11(ctx, lt):         # i-FORCE MAX: turbocharged hybrid powertrain
    b = 11
    badge_row(ctx, W / 2, BADGE_Y, [("i-FORCE MAX", "chrome", 0.0)], lt, 66)
    car_in(ctx, lt, 0.05, "pickup", 120, 880, 720, SILVER, rims="dark")
    tt, th = wt(b, "turbocharged"), wt(b, "hybrid")
    pop(ctx, lt, tt, 300, 470, lambda c: turbo(c, 0, 0, lt, 1.0))
    pop(ctx, lt, tt + 0.1, 300, 580, lambda c: tag(c, "TURBO", "dark", 40), sound=None)
    pop(ctx, lt, th - 0.1, W / 2, 470, lambda c: label(c, "+", 0, 0, 90, DARK), sound=None)
    pop(ctx, lt, th, 780, 470, lambda c: icon_bolt(c, 0, 0, 1.3))
    pop(ctx, lt, th + 0.1, 780, 580, lambda c: tag(c, "HYBRID", "green", 40), sound=None)


def scene12(ctx, lt):         # So a Tacoma TRD Pro i-FORCE MAX = ...
    b = 12
    parts = [("TACOMA", "chrome", wt(b, "Tacoma")), ("TRD PRO", "red", wt(b, "TRD")), ("i-FORCE MAX", "chrome", wt(b, "i-FORCE"))]
    badge_row(ctx, W / 2, BADGE_Y, parts, lt, 52)
    rocks(ctx, 900, 880, 1.1)
    car_in(ctx, lt, 0.05, "pickup", 120, 880, 720, ORANGE_, rs=True, rims="black")
    pop(ctx, lt, wt(b, "pickup"), 270, 400, lambda c: tag(c, "TACOMA = MID-SIZE PICKUP", "white", 32, -0.03))
    pop(ctx, lt, wt(b, "upgrades"), 700, 500, lambda c: tag(c, "TRD PRO = OFF-ROAD UPGRADES", "yellow", 30, 0.03))
    pop(ctx, lt, wt(b, "engine"), 350, 600, lambda c: tag(c, "i-FORCE MAX = TURBO HYBRID", "dark", 30, -0.02))


def scene13(ctx, lt):         # follow me
    b = 13
    tf = wt(b, "follow")
    car_in(ctx, lt, 0.0, "sports", 60, 870, 440, "#D7182A", rs=True, rims="black", sound=False)
    car_in(ctx, lt, 0.1, "pickup", 560, 870, 460, ORANGE_)
    if lt >= tf - 0.3:
        p = max(0.02, ease_out_back((lt - tf + 0.3) / 0.45))
        sfx_once(lt, tf - 0.3, "pop")
        ctx.save(); ctx.translate(W / 2, 470); ctx.scale(p, p)
        ink(ctx, rrect(-420, -170, 840, 340, 50), hexc("#FFFFFF", 0.95), 6)
        label(ctx, "FOLLOW FOR", 0, -80, 64, DARK)
        chip(ctx, 0, 30, NEXT, "red", 60)
        label(ctx, CTX["handle"], 0, 120, 40, hexc("#3A3D44"), font=MONO)
        ctx.restore()


SCENES = [scene0, scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9, scene10, scene11, scene12, scene13]
