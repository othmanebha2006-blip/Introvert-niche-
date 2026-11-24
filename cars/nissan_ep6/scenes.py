"""Episode 6: every Nissan model explained. Timing data + 13 scenes (one per beat).
Voice = the audio of the user's presenter clip (character_mecmation/nissan_presenter.mp4); words.json = its Whisper timing.
Rules kept: something on screen from the first frame of every scene; real objects for each idea; ✓ checklist recap."""
import json, os, math
from ink import *
from car import draw_car, WHEELS
from widgets import *

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = "BADGE DECODED · #6"
BRAND = "NISSAN"
NEXT = "BADGE DECODED #7"
CLIP = "nissan_presenter.mp4"

FIX = {}
SPLIT_AT = []
BEAT_OF_SENT = [0, 1, 2, 2, 3, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 10, 10, 10, 11, 12]

KEYWORDS = {"NISSAN", "CARS", "SUVS", "TRUCKS", "SPORTS", "VERSA", "ENTRY-LEVEL", "SEDAN", "SENTRA", "BIGGER", "ALTIMA",
            "SPACE", "COMFORT", "LEAF", "ELECTRIC", "Z", "TWO-DOOR", "GT-R", "LEGENDARY", "GODZILLA", "KIX", "SMALLEST",
            "ROGUE", "FAMILY", "MURANO", "PREMIUM", "PATHFINDER", "THREE", "ROWS", "ARMADA", "LARGEST", "TOWING",
            "FRONTIER", "MID-SIZE", "TITAN", "FULL-SIZE", "2024", "NISMO", "MOTORSPORT", "POWER", "HANDLING", "SHARPER",
            "UPGRADES", "SPORT", "PERFORMANCE", "BRAKES", "Z-NISMO", "TRACK-FOCUSED", "FOLLOW", "ENDED"}


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
        SENT.append(dict(beat=BEAT_OF_SENT[si], start=ws[0]["s"], end=ws[-1]["e"], text=" ".join(w["w"] for w in ws)))
        for w in ws:
            WORDS.append(dict(text=w["w"], start=w["s"], end=w["e"], beat=BEAT_OF_SENT[si], sent=si))
    return SENT, WORDS


CTX = {}


def wt(beat, word, k=0):
    return CTX["wt"](beat, word, k)


def car_in(*a, **k):
    return CTX["car_in"](*a, **k)


BADGE_Y = 222
W = 1080
RED_, WHITE_, BLACK_, SILVER, BLUE_, GREEN_, ORANGE_, GREY_ = (
    "#C8102E", "#EDEDEA", "#1D1E22", "#A9ADB2", "#1F4FA8", "#3F5B3A", "#D96A1E", "#5E6B78")


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



def godzilla(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    for i in range(5):     # back spikes
        sx = -40 + i * 22
        ink(ctx, [(sx - 12, -40 - i * 6), (sx, -78 - i * 6), (sx + 12, -40 - i * 6)], hexc("#2F6B3A"), 4)
    ink(ctx, rpoly([(-120, 60), (-60, 30), (-40, -40), (30, -70), (70, -110), (120, -105), (130, -80), (90, -60),
                    (80, -20), (60, 60)], 18), hexc("#4C8F53"), 5)
    ink(ctx, rrect(-30, 50, 30, 50, 10), hexc("#4C8F53"), 5); ink(ctx, rrect(20, 50, 30, 50, 10), hexc("#4C8F53"), 5)
    ink(ctx, ellipse(100, -92, 7, 7, 12), hexc("#FFFFFF"), 3)
    line(ctx, [(95, -72), (125, -78)], 4)
    ctx.restore()


def steering(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    line(ctx, ellipse(0, 0, 44, 44, 40), 12)
    line(ctx, [(-44, 0), (-12, 6)], 10); line(ctx, [(12, 6), (44, 0)], 10); line(ctx, [(0, 14), (0, 44)], 10)
    ink(ctx, ellipse(0, 6, 12, 12, 16), hexc("#FFFFFF"), 6)
    ctx.restore()


def flag(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    line(ctx, [(-40, 50), (-40, -50)], 8)
    for r in range(4):
        for c in range(5):
            ink(ctx, rrect(-36 + c * 16, -50 + r * 14, 16, 14, 0), hexc("#1D1E22" if (r + c) % 2 == 0 else "#FFFFFF"), 0)
    ink(ctx, rrect(-36, -50, 80, 56, 0), None, 3)
    ctx.restore()


def seats_top(ctx, x, y, lt, t0):
    """top-down car with three rows of seats lighting up one after the other"""
    ink(ctx, rpoly([(x - 120, y - 260), (x + 120, y - 260), (x + 130, y + 260), (x - 130, y + 260)], 60), hexc("#E4E6EA"), 6)
    ink(ctx, rrect(x - 95, y - 225, 190, 50, 20), hexc("#5C6F86"), 4)
    for r in range(3):
        on = lt > t0 + r * 0.25
        col = hexc("#F2B800") if on else hexc("#C9CDD3")
        n = 2 if r == 0 else 3
        for c in range(n):
            cx = x - (n - 1) * 34 + c * 68
            ink(ctx, rrect(cx - 26, y - 140 + r * 120, 52, 70, 12), col, 4)
        if on:
            sfx_once(lt, t0 + r * 0.25, "pop")


def trailer(ctx, x, y, w, h, wheel_rot):
    ink(ctx, rrect(x, y - h - 30, w, h, 12), hexc("#D9DCE1"), 5)
    for i in range(1, 4):
        line(ctx, [(x + i * w / 4, y - h - 22), (x + i * w / 4, y - 38)], 3, hexc("#A9AEB6"))
    from car import draw_wheel
    draw_wheel(ctx, x + w * 0.62, y - 26, 26, wheel_rot, hexc("#C9CDD2"))
    line(ctx, [(x + w, y - 50), (x + w + 46, y - 50)], 8)


def meter(ctx, lt, levels, x, y, w):
    ink(ctx, rrect(x, y, w, 46, 23), hexc("#FFFFFF", 0.9), 5)
    f = 0.0
    for t0, fr in levels:
        if lt >= t0:
            f = f + (fr - f) * ease((lt - t0) / 0.4) if fr > f else fr
    if f > 0.02:
        ink(ctx, rrect(x + 6, y + 6, (w - 12) * f, 34, 17), None, 0,
            grad=lin_grad(x, 0, x + w, 0, [(0, hexc("#2E9E5B")), (0.6, hexc("#F2B800")), (1, hexc("#D7182A"))]))


def check(ctx, x, y, s=1.0):
    ink(ctx, ellipse(x, y, 26 * s, 26 * s, 30), hexc("#2E9E5B"), 4)
    line(ctx, [(x - 12 * s, y), (x - 3 * s, y + 10 * s), (x + 13 * s, y - 10 * s)], 6 * s, hexc("#FFFFFF"))


def swap_car(ctx, lt, times, specs, kind, x, y, L):
    cur = max([i for i, t in enumerate(times) if lt >= t - 0.1] or [0])
    paint, kw = specs[cur]
    k = lt - (times[cur] - 0.1)
    p = max(0.02, ease_out_back(min(1, k / 0.35))) if cur > 0 else 1
    if cur:
        sfx_once(lt, times[cur] - 0.1, "pop")
    ctx.save(); ctx.translate(x + L / 2, y); ctx.scale(p, p); ctx.translate(-(x + L / 2), -y)
    car_in(ctx, lt, 0.0, kind, x, y, L, paint, **kw)
    ctx.restore()
    return cur


# ---------------------------------------------------------------- scenes
def scene0(ctx, lt):          # Every Nissan model explained in one minute
    badge_row(ctx, W / 2, BADGE_Y, [("EVERY MODEL", "yellow", -0.4)], lt, 66)
    car_in(ctx, lt, -0.45, "sedan", 60, 560, 440, SILVER, sound=False)
    car_in(ctx, lt, -0.35, "suv", 560, 560, 450, RED_, sound=False)
    car_in(ctx, lt, -0.25, "pickup", 50, 870, 470, GREY_, sound=False)
    car_in(ctx, lt, -0.15, "sports", 570, 870, 440, "#F2B800", rs=True, rims="black", sound=False)


def scene1(ctx, lt):          # everyday cars, SUVs, trucks, sports cars
    b = 1
    badge_row(ctx, W / 2, BADGE_Y, [("NISSAN", "chrome", 0.0)], lt, 66)
    tiles = [("EVERYDAY CARS", "sedan", SILVER, wt(b, "everyday"), 60, 560), ("SUVS", "suv", RED_, wt(b, "SUVs"), 570, 560),
             ("TRUCKS", "pickup", GREY_, wt(b, "trucks"), 60, 880), ("SPORTS CARS", "sports", "#F2B800", wt(b, "sports"), 570, 880)]
    for i, (name, kind, paint, t0, x, y) in enumerate(tiles):
        slot(ctx, lt, t0, kind, x, y, 430, paint, **(dict(rs=True, rims="black") if kind == "sports" else {}))
        pop(ctx, lt, t0, x + 215, y - 225, lambda c, n=name: chip(c, 0, 0, n, "yellow", 40))


def scene2(ctx, lt):          # Versa entry-level, Sentra bigger, Altima more space and comfort
    b = 2
    tv, ts, ta = wt(b, "Versa"), wt(b, "Sentra"), wt(b, "Altima")
    badge_row(ctx, W / 2, BADGE_Y, [("VERSA", "chrome", 0.0), ("SENTRA", "chrome", ts), ("ALTIMA", "chrome", ta)], lt, 56)
    rows = [(tv, 440, 460, BLUE_, "ENTRY-LEVEL", wt(b, "entry-level")), (ts, 520, 670, SILVER, "BIGGER", wt(b, "bigger")),
            (ta, 600, 890, BLACK_, "MORE SPACE + COMFORT", wt(b, "comfort"))]
    for i, (t0, L, y, paint, txt, tt) in enumerate(rows):
        slot(ctx, lt, t0, "sedan", 40, y, L, paint, early=(i == 0))
        pop(ctx, lt, tt, min(900, 40 + L + 200), y - 150, lambda c, t=txt: tag(c, t, "yellow", 30, 0.03))


def scene3(ctx, lt):          # Leaf fully electric; Z two-door sports car
    b = 3
    tl, tz = wt(b, "Leaf"), wt(b, "Z")
    badge_row(ctx, W / 2, BADGE_Y, [("LEAF", "green", 0.0), ("Z", "red", tz)], lt, 66)
    slot(ctx, lt, tl, "hatch", 120, 560, 600, "#3E7C5A", early=True)
    te = wt(b, "electric")
    pop(ctx, lt, te, 860, 380, lambda c: tag(c, "FULLY ELECTRIC", "green", 40, 0.04))
    if lt > te:
        icon_battery(ctx, 900, 470, 0.9, 0.3 + 0.7 * ((lt * 0.8) % 1))
    slot(ctx, lt, tz, "sports", 60, 880, 700, "#F2B800", rims="black")
    pop(ctx, lt, wt(b, "two-door"), 860, 650, lambda c: tag(c, "2-DOOR SPORTS CAR", "yellow", 34, -0.04))


def scene4(ctx, lt):          # GT-R, legendary, nicknamed Godzilla
    b = 4
    badge_row(ctx, W / 2, BADGE_Y, [("GT-R", "red", 0.0)], lt, 76)
    kerb(ctx, 880)
    car_in(ctx, lt, 0.0, "sports", 130, 870, 820, "#7A7F86", rs=True, rims="black", wing=1)
    if lt > 0.6:
        speed_lines(ctx, 130, 870, 820, 260, 0.8, seed=int(lt * 6))
    pop(ctx, lt, wt(b, "legendary"), 300, 420, lambda c: stamp(c, "LEGENDARY", "#C8102E", 62, -0.07), sound="stamp")
    tg = wt(b, "Godzilla")
    pop(ctx, lt, tg - 0.1, 830, 470, lambda c: godzilla(c, 0, 0, 1.0))
    pop(ctx, lt, tg, 830, 600, lambda c: tag(c, "GODZILLA", "green", 44, 0.04), sound=None)


def scene5(ctx, lt):          # SUVs: Kix smallest crossover, Rogue popular family SUV
    b = 5
    tk, tr = wt(b, "Kix"), wt(b, "Rogue")
    badge_row(ctx, W / 2, BADGE_Y, [("SUVS", "white", 0.0), ("KIX", "chrome", tk), ("ROGUE", "chrome", tr)], lt, 60)
    slot(ctx, lt, tk, "suv", 60, 820, 380, ORANGE_, early=True)
    pop(ctx, lt, wt(b, "smallest"), 250, 480, lambda c: tag(c, "SMALLEST", "yellow", 40, -0.04))
    slot(ctx, lt, tr, "suv", 480, 820, 540, GREY_)
    pop(ctx, lt, wt(b, "popular"), 760, 420, lambda c: stamp(c, "POPULAR", "#2E9E5B", 56, 0.05), sound="stamp")
    pop(ctx, lt, wt(b, "family"), 760, 530, lambda c: tag(c, "FAMILY SUV", "white", 38, 0.03), sound=None)


def scene6(ctx, lt):          # Murano premium, Pathfinder three rows, Armada largest + towing
    b = 6
    tm, tp, ta = wt(b, "Murano"), wt(b, "Pathfinder"), wt(b, "Armada")
    badge_row(ctx, W / 2, BADGE_Y, [("MURANO", "chrome", 0.0), ("PATHFINDER", "chrome", tp), ("ARMADA", "chrome", ta)], lt, 50)
    if lt < tp - 0.1:
        slot(ctx, lt, tm, "suv", 130, 850, 820, "#3A2E2A", early=True, sline=True, rims="black")
        pop(ctx, lt, wt(b, "premium"), 300, 430, lambda c: stamp(c, "PREMIUM", "#B8860B", 62, -0.06), sound="stamp")
    elif lt < ta - 0.1:
        car_in(ctx, lt, tp - 0.1, "suv", 60, 850, 560, BLUE_, dur=0.45)
        seats_top(ctx, 850, 600, lt, wt(b, "three"))
        pop(ctx, lt, wt(b, "rows"), 330, 470, lambda c: tag(c, "3 ROWS OF SEATS", "yellow", 40, -0.04))
    else:
        k = min(1, (lt - ta + 0.1) / 1.2)
        x = -1100 + (470 + 1100) * ease_out(k)
        R = WHEELS["suv"][2] * 600
        trailer(ctx, x - 440, 860, 400, 230, (x + 1100) / R * 1.6)
        draw_car(ctx, "suv", x, 860, 600, BLACK_, (x + 1100) / R, rims="dark")
        speed_lines(ctx, x - 440, 860, 400, 260, (1 - k) * 1.4)
        sfx_once(lt, ta - 0.1, "rumble")
        pop(ctx, lt, wt(b, "largest"), 300, 420, lambda c: tag(c, "LARGEST", "yellow", 46, -0.04))
        pop(ctx, lt, wt(b, "towing"), 760, 460, lambda c: tag(c, "FAMILIES + TOWING", "dark", 38, 0.04))


def scene7(ctx, lt):          # Frontier mid-size, Titan full-size, ended in 2024
    b = 7
    tf, tt = wt(b, "Frontier"), wt(b, "Titan")
    badge_row(ctx, W / 2, BADGE_Y, [("TRUCKS", "white", 0.0), ("FRONTIER", "chrome", tf), ("TITAN", "chrome", tt)], lt, 56)
    slot(ctx, lt, tf, "pickup", 80, 560, 560, ORANGE_, early=True, rims="dark")
    pop(ctx, lt, wt(b, "mid-size"), 830, 380, lambda c: tag(c, "MID-SIZE", "yellow", 42, 0.04))
    te = wt(b, "ended")
    a = 1 - 0.55 * ease((lt - te) / 0.4) if lt > te else 1
    if lt > tt - 0.15:
        ctx.push_group()
        car_in(ctx, lt, tt - 0.15, "pickup", 50, 885, 760, SILVER, dur=0.45, rims="dark")
        ctx.pop_group_to_source(); ctx.paint_with_alpha(a)
    else:
        ghost_wait(ctx, lt, tt, "pickup", 50, 885, 760)
    pop(ctx, lt, wt(b, "full-size"), 880, 620, lambda c: tag(c, "FULL-SIZE", "yellow", 42, -0.04))
    pop(ctx, lt, te, 430, 720, lambda c: stamp(c, "ENDED 2024", "#D7182A", 70, -0.08), sound="stamp")


def scene8(ctx, lt):          # Nismo = Nissan Motorsport: more power, sharper handling, motorsport upgrades
    b = 8
    badge_row(ctx, W / 2, BADGE_Y, [("NISMO", "red", 0.0), ("= NISSAN MOTORSPORT", "white", wt(b, "Motorsport"))], lt, 54)
    kerb(ctx, 885)
    car_in(ctx, lt, 0.0, "sports", 150, 875, 760, WHITE_, rs=True, rims="black", livery=True)
    tiles = [("MORE POWER", lambda c: icon_bolt(c, 0, -10, 1.0), wt(b, "power")),
             ("SHARPER HANDLING", lambda c: steering(c, 0, -10, 1.0), wt(b, "handling")),
             ("RACE UPGRADES", lambda c: flag(c, 0, -10, 1.0), wt(b, "upgrades"))]
    pop(ctx, lt, wt(b, "division"), W / 2, 360, lambda c: tag(c, "PERFORMANCE DIVISION", "dark", 38), sound=None)
    for i, (txt, ic, t0) in enumerate(tiles):
        x = 200 + i * 340
        def draw(c, txt=txt, ic=ic):
            ink(c, rrect(-150, -80, 300, 170, 26), hexc("#FFFFFF", 0.95), 5)
            ic(c)
            label(c, txt, 0, 60, 28, DARK)
        pop(ctx, lt, t0 - 0.15, x, 520, draw)


def scene9(ctx, lt):          # you'll find it on the Z and GT-R
    b = 9
    badge_row(ctx, W / 2, BADGE_Y, [("NISMO", "red", 0.0)], lt, 70)
    tz, tg = wt(b, "Z"), wt(b, "GT-R")
    slot(ctx, lt, tz, "sports", 60, 560, 600, WHITE_, early=True, rs=True, rims="black", livery=True)
    pop(ctx, lt, tz, 860, 380, lambda c: chip(c, 0, 0, "Z NISMO", "red", 44))
    slot(ctx, lt, tg, "sports", 60, 880, 640, "#7A7F86", rs=True, rims="black", wing=1)
    pop(ctx, lt, tg, 860, 700, lambda c: chip(c, 0, 0, "GT-R NISMO", "red", 44))


def scene10(ctx, lt):         # Z versions: Sport, Performance, Nismo
    b = 10
    names = [("SPORT", wt(b, "Sport")), ("PERFORMANCE", wt(b, "Performance")), ("NISMO", wt(b, "Nismo"))]
    badge_row(ctx, W / 2, BADGE_Y, [("Z", "red", 0.0)] + [(n, "red" if n == "NISMO" else "chrome", t) for n, t in names], lt, 50)
    specs = [(BLUE_, dict(rims="silver")), (BLUE_, dict(rims="black", calipers="#D7182A")),
             (WHITE_, dict(rs=True, rims="black", livery=True))]
    cur = swap_car(ctx, lt, [t for _, t in names], specs, "sports", 130, 780, 820)
    pop(ctx, lt, wt(b, "versions"), W / 2, 380, lambda c: tag(c, "DIFFERENT VERSIONS", "white", 40), sound=None)
    pop(ctx, lt, wt(b, "entry"), 260, 470, lambda c: tag(c, "ENTRY", "yellow", 40, -0.04))
    pop(ctx, lt, wt(b, "brakes"), 560, 470, lambda c: tag(c, "+ BRAKES + HANDLING", "yellow", 32, 0.03))
    pop(ctx, lt, wt(b, "further"), 870, 470, lambda c: tag(c, "FURTHER", "red", 40, 0.05))
    if lt > names[0][1] - 0.1:
        meter(ctx, lt, [(names[0][1], 0.35), (names[1][1], 0.68), (names[2][1], 1.0)], 140, 860, 800)
        label(ctx, "PERFORMANCE", 140, 840, 30, hexc("#3A3D44"), font=MONO, anchor="l")


def scene11(ctx, lt):         # recap: Nissan Z NISMO checklist
    b = 11
    badge_row(ctx, W / 2, BADGE_Y, [("Z", "red", -0.2), ("NISMO", "red", wt(b, "Z-Nismo") + 0.2)], lt, 70)
    kerb(ctx, 885)
    car_in(ctx, lt, 0.0, "sports", 150, 875, 760, WHITE_, rs=True, rims="black", livery=True, sound=False)
    rows = [("Z = TWO-DOOR SPORTS CAR", wt(b, "two-door")), ("NISMO = UPGRADED PERFORMANCE", wt(b, "upgraded")),
            ("+ TRACK-FOCUSED EQUIPMENT", wt(b, "track-focused"))]
    p = ease_out_back(min(1, lt / 0.4))
    ctx.save(); ctx.translate(W / 2, 440); ctx.scale(max(0.02, p), max(0.02, p))
    ink(ctx, rrect(-440, -125, 880, 250, 26), hexc("#FFF6D6"), 6)
    for i, (txt, t0) in enumerate(rows):
        y = -70 + i * 72
        a = 1 if lt > t0 else 0.3
        label(ctx, txt, -405, y, 34, hexc("#1D1E22", a), font=MONO, anchor="l")
        if lt > t0:
            check(ctx, 390, y, 1.1); sfx_once(lt, t0, "pop")
        else:
            ink(ctx, ellipse(390, y, 26, 26, 24), hexc("#E4E6EA"), 4)
    ctx.restore()


def scene12(ctx, lt):         # follow me
    b = 12
    tf = wt(b, "follow")
    car_in(ctx, lt, 0.0, "sports", 60, 870, 440, WHITE_, rs=True, rims="black", livery=True, sound=False)
    car_in(ctx, lt, 0.1, "suv", 560, 870, 450, RED_)
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
