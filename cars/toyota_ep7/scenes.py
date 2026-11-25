"""Episode 7: Toyota model names explained (new character). Built with the reference-video recipe
(cars/REFERENCE_ANALYSIS.md): 2.5 s hook that shows the final badge "RAV4 · HYBRID · AWD" with ? (open loop),
one real object per idea, a new visual every 1-2 s, and the ending decodes the hook badge with ✓.
Retention: a small tracker under the header keeps the three ? parts visible and ticks each one when it is explained,
so the viewer waits for the last tick at the end.
Voice = the audio of the user's character clip (identical to the mp3); words.json = its Whisper timing."""
import json, os, math
from ink import *
from car import draw_car, WHEELS
from widgets import *
import widgets

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = "BADGE DECODED · #7"
BRAND = "TOYOTA"
NEXT = "BADGE DECODED #8"

FIX = {"Toyota's": "Toyota's"}
SPLIT_AT = [11.64, 20.02, 28.36, 41.66, 45.04]
BEAT_OF_SENT = [0, 1, 1, 2, 3, 4, 4, 5, 6, 7, 8, 8, 9, 10, 11, 12, 13, 14, 15, 16]

KEYWORDS = {"TOYOTA", "ALPHABET", "NUMBER", "NAME", "COROLLA", "PETALS", "FLOWER", "CAMRY", "JAPANESE", "CROWN",
            "PRIUS", "LATIN", "PRIOR", "BEFORE", "HYBRIDS", "RAV4", "RECREATIONAL", "ACTIVE", "VEHICLE", "FOUR-WHEEL",
            "LAND", "CRUISER", "ROUGH", "PERFORMANCE", "BADGES", "GR", "GAZOO", "RACING", "MOTORSPORT", "SUPRA",
            "SHARPER", "TRD", "DEVELOPMENT", "OFF-ROAD", "HYBRID", "PETROL", "ELECTRIC", "PLUG-IN", "CHARGE",
            "BATTERY", "AWD", "ALL-WHEEL", "FOUR", "WHEELS", "CROSS", "CROSSOVER", "HIGHER", "SUV", "FOLLOW"}


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
        SENT.append(dict(beat=BEAT_OF_SENT[si], start=ws[0]["s"], end=ws[-1]["e"], text=" ".join(w["w"] for w in ws)))
        for w in ws:
            WORDS.append(dict(text=w["w"], start=w["s"], end=w["e"], beat=BEAT_OF_SENT[si], sent=si))
    return SENT, WORDS


CTX = {}


def wt(beat, word, k=0):
    return CTX["wt"](beat, word, k)


def gw(beat, word, k=0):
    return CTX["wt"](beat, word, k) + CTX["beat_t"][beat]


def car_in(*a, **k):
    return CTX["car_in"](*a, **k)


BADGE_Y = 236
W = 1080
RED_, WHITE_, BLACK_, SILVER, BLUE_, GREEN_, SAND, ORANGE_, GREY_ = (
    "#C8102E", "#EDEDEA", "#1D1E22", "#A9ADB2", "#1F4FA8", "#3F5B3A", "#C8B28A", "#D96A1E", "#5E6B78")
HOOK = [("RAV4", "chrome"), ("HYBRID", "green"), ("AWD", "chrome")]


# ================================================================ helpers
def ghost_wait(ctx, lt, t0, kind, x, y, L):
    if lt < t0 + 0.2:
        a = min(1.0, lt / 0.25 + 0.4) * (1 - ease((lt - t0 + 0.05) / 0.25))
        if a > 0:
            ctx.push_group(); draw_car(ctx, kind, x, y, L, ghost=True); ctx.pop_group_to_source(); ctx.paint_with_alpha(min(1, a))


def slot(ctx, lt, t0, kind, x, y, L, paint, early=False, **kw):
    if early:
        car_in(ctx, lt, 0.0, kind, x, y, L, paint, dur=0.5, **kw)
        return
    ghost_wait(ctx, lt, t0, kind, x, y, L)
    car_in(ctx, lt, t0 - 0.15, kind, x, y, L, paint, dur=0.45, **kw)


def check(ctx, x, y, s=1.0):
    ink(ctx, ellipse(x, y, 26 * s, 26 * s, 30), hexc("#2E9E5B"), 4)
    line(ctx, [(x - 12 * s, y), (x - 3 * s, y + 10 * s), (x + 13 * s, y - 10 * s)], 6 * s, hexc("#FFFFFF"))


def qmark(ctx, x, y, lt, i):
    bob = math.sin(lt * 6 + i) * 6
    ink(ctx, ellipse(x, y + bob, 26, 26, 24), hexc("#FFFFFF"), 4)
    label(ctx, "?", x, y + bob + 2, 40, RED)


def glow_ring(ctx, x, y, rx, ry, lt):
    a = 0.55 + 0.25 * math.sin(lt * 7)
    ctx.save(); ctx.translate(x, y); ctx.scale(rx, ry); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    ctx.set_source_rgba(1, 0.82, 0.2, a); ctx.set_line_width(8); ctx.stroke()


def rocks(ctx, x, y, s=1.0):
    pts = [(x - 90 * s, y), (x - 60 * s, y - 40 * s), (x - 10 * s, y - 55 * s), (x + 40 * s, y - 35 * s), (x + 80 * s, y)]
    ink(ctx, rpoly(pts, 10), hexc("#8C8F94"), 5)
    ink(ctx, rpoly([(x + 60 * s, y), (x + 90 * s, y - 25 * s), (x + 130 * s, y)], 6), hexc("#A3A6AB"), 5)


def ground(ctx, y, rough=False, lt=0.0):
    if rough:
        pts = [(0, y)] + [(x, y - 18 * math.sin(x * 0.02) - 10 * math.sin(x * 0.051 + 1)) for x in range(0, 1081, 30)] + [(1080, y + 60), (0, y + 60)]
        ink(ctx, pts, hexc("#B89B72"), 5)
    else:
        line(ctx, [(0, y), (1080, y)], 4, hexc("#9AA0A8"))


def kerb(ctx, y):
    for i in range(12):
        ink(ctx, rrect(i * 90, y, 90, 22, 0), hexc("#D7182A" if i % 2 else "#FFFFFF"), 0)
    line(ctx, [(0, y), (1080, y)], 3)


def flower(ctx, x, y, s, bloom, lt):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    line(ctx, [(0, 40), (0, 220)], 10, hexc("#3F7A3A"))
    ink(ctx, ellipse(30, 150, 40, 16, 20), hexc("#5FA35A"), 4)
    n = 10
    for i in range(n):
        p = ease_out_back(max(0, min(1, bloom * n - i)))
        if p <= 0:
            continue
        a = i * 2 * math.pi / n + lt * 0.3
        ctx.save(); ctx.rotate(a); ctx.translate(0, -70 * p)
        ink(ctx, ellipse(0, 0, 26 * p, 48 * p, 24), hexc("#F49AC1"), 4)
        ctx.restore()
    ink(ctx, ellipse(0, 0, 42, 42, 30), hexc("#F2B800"), 5)
    ctx.restore()


def crown(ctx, x, y, s=1.0, shine=0.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    pts = [(-110, 50), (-120, -60), (-60, -10), (0, -90), (60, -10), (120, -60), (110, 50)]
    ink(ctx, pts, hexc("#F2B800"), 6)
    ink(ctx, rrect(-112, 40, 224, 36, 10), hexc("#E0A200"), 6)
    for gx, gc in ((-60, "#D7182A"), (0, "#2C6FCF"), (60, "#2E9E5B")):
        ink(ctx, ellipse(gx, 58, 12, 12, 16), hexc(gc), 3)
    for px, py in ((-120, -60), (0, -90), (120, -60)):
        ink(ctx, ellipse(px, py, 14, 14, 16), hexc("#FFFFFF"), 4)
    ctx.restore()
    if shine > 0:
        sparkle(ctx, x + 120 * s, y - 80 * s, 30, shine * 10)
        sparkle(ctx, x - 130 * s, y + 10 * s, 22, shine * 10 + 1)


def scroll(ctx, x, y, w, text, sub):
    ink(ctx, rrect(x - w / 2, y - 70, w, 140, 16), hexc("#F3E3BF"), 5)
    for sx in (-1, 1):
        ink(ctx, ellipse(x + sx * w / 2, y, 20, 80, 24), hexc("#E2CB98"), 5)
    label(ctx, text, x, y - 22, 54, hexc("#6B4A2B"))
    label(ctx, sub, x, y + 36, 32, hexc("#6B4A2B"), font=MONO)


def chassis(ctx, cx, cy, lt, s=1.0, petrol=0.0, battery=0.0, charge=0.0, awd=0.0, motor=0.0):
    """top-down chassis (front to the right): engine + petrol tank (green), battery (blue), electric motor, wheels"""
    ctx.save(); ctx.translate(cx, cy); ctx.scale(s, s)
    ink(ctx, rrect(-330, -110, 660, 220, 70), hexc("#FFFFFF", 0.75), 5)
    line(ctx, [(-260, -150), (-260, 150)], 12); line(ctx, [(260, -150), (260, 150)], 12)
    line(ctx, [(-260, 0), (260, 0)], 10)
    # engine (front)
    ink(ctx, rrect(170, -70, 120, 140, 16), hexc("#9AA0A6") if petrol <= 0 else mix(hexc("#9AA0A6"), hexc("#2E9E5B"), petrol), 5)
    label(ctx, "ENGINE", 230, 0, 26, DARK)
    # petrol tank
    ink(ctx, rrect(-220, -60, 120, 120, 20), mix(hexc("#D9DCE1"), hexc("#3CC46A"), petrol), 5)
    if petrol > 0.5:
        icon_pump(ctx, -160, 0, 0.55, "#2E9E5B")
    # battery
    ink(ctx, rrect(-70, -80, 200, 160, 16), mix(hexc("#D9DCE1"), hexc("#3C8CF0"), battery), 5)
    if battery > 0.5:
        lvl = 0.3 + 0.7 * ((lt * 0.7) % 1) if charge > 0.5 else 0.8
        icon_battery(ctx, 30, 0, 1.0, lvl)
    # electric motor on the rear axle
    ink(ctx, ellipse(-260, 0, 34, 34, 24), mix(hexc("#D9DCE1"), hexc("#3C8CF0"), motor), 5)
    if motor > 0.5:
        icon_bolt(ctx, -260, 0, 0.45, "#FFD23F")
    for ax in (-260, 260):
        for sg in (-1, 1):
            if awd > 0:
                k = 0.5 + 0.5 * math.sin(lt * 9 + ax)
                ctx.set_source(rad_grad(ax, sg * 160, 10, 100, [(0, (1, 0.82, 0.25, (0.6 * k + 0.25) * awd)), (1, (1, 0.82, 0.25, 0))]))
                ctx.arc(ax, sg * 160, 100, 0, 2 * math.pi); ctx.fill()
            ink(ctx, rrect(ax - 66, sg * 160 - 36, 132, 72, 22), mix(hexc("#26272B"), hexc("#F2B800"), 0.8 * awd), 5)
            if awd > 0.5:
                arrow(ctx, [(ax - 30, sg * 160 + sg * 62), (ax + 50, sg * 160 + sg * 62)], 6, hexc("#E39B00"), 18)
    ctx.restore()


def outlet(ctx, x, y):
    ink(ctx, rrect(x - 38, y - 50, 76, 100, 12), hexc("#FFFFFF"), 5)
    for dx in (-12, 12):
        ink(ctx, rrect(x + dx - 4, y - 22, 8, 20, 3), DARK, 0)
    ink(ctx, ellipse(x, y + 18, 6, 6, 12), DARK, 0)


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
    ctx.restore()


def hook_row(ctx, lt, x, y, size, show_q=True, lit=(1, 1, 1)):
    ws = [chip_size(ctx, t, size)[0] for t, _ in HOOK]
    total = sum(ws) + 16 * (len(ws) - 1)
    xx = x - total / 2
    for i, ((t, sty), w) in enumerate(zip(HOOK, ws)):
        ctx.save()
        if lit[i] < 1:
            ctx.push_group()
        chip(ctx, xx + w / 2, y, t, sty, size)
        if lit[i] < 1:
            ctx.pop_group_to_source(); ctx.paint_with_alpha(0.35 + 0.65 * lit[i])
        ctx.restore()
        if show_q:
            qmark(ctx, xx + w / 2 + w * 0.3, y - size * 0.95, lt, i)
        xx += w + 16


# ================================================================ overlay: retention tracker (drawn over every scene)
def hero(ctx, t):
    B = CTX["beat_t"]
    if t < B[1] or t >= B[15]:
        return                              # the hook and the ending show the full badge themselves
    done = [gw(5, "drive"), gw(11, "motor"), gw(13, "wheels")]   # when each part has been explained
    x, y, size = W / 2, 150, 30
    ws = [chip_size(ctx, tt, size)[0] for tt, _ in HOOK]
    total = sum(ws) + 10 * 2 + 70
    xx = x - total / 2
    label(ctx, "DECODING:", xx, y, 22, hexc("#3A3D44"), font=MONO, anchor="l")
    xx += 120
    for i, ((tt, sty), w) in enumerate(zip(HOOK, ws)):
        ok = t >= done[i]
        ctx.save(); ctx.push_group()
        chip(ctx, xx + w / 2, y, tt, sty if ok else "white", size)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(1 if ok else 0.55); ctx.restore()
        if ok:
            p = ease_out_back(min(1, (t - done[i]) / 0.3))
            ctx.save(); ctx.translate(xx + w - 4, y - 20); ctx.scale(max(0.02, p), max(0.02, p)); check(ctx, 0, 0, 0.55); ctx.restore()
            if 0 <= t - done[i] < 1 / 30:
                widgets.SFX.append((t, "pop"))
        else:
            label(ctx, "?", xx + w - 4, y - 22, 26, RED)
        xx += w + 10


# ================================================================ scenes
def scene0(ctx, lt):          # HOOK: Toyota model names, explained in one minute
    b = 0
    car_in(ctx, lt, -0.5, "suv", 140, 860, 800, ORANGE_, rims="dark", sound=False)
    if lt < 0.6:
        speed_lines(ctx, 140, 860, 800, 280, 1.0 - lt, seed=3)
    pop(ctx, lt, -0.2, W / 2, 230, lambda c: chip(c, 0, 0, "TOYOTA", "red", 70))
    if lt > 0.1:
        for i, (sx, sy) in enumerate([(320, 190), (760, 200)]):
            sparkle(ctx, sx, sy, 26, lt + i)
    te = wt(b, "explained")
    if lt > te - 0.1:
        p = ease_out_back(min(1, (lt - te + 0.1) / 0.35))
        sfx_once(lt, te - 0.1, "pop")
        ctx.save(); ctx.translate(W / 2, 410); ctx.scale(max(0.02, p), max(0.02, p)); ctx.translate(-W / 2, -410)
        hook_row(ctx, lt, W / 2, 410, 66)
        ctx.restore()
        glow_ring(ctx, W / 2, 410, 420, 90, lt)


def scene1(ctx, lt):          # no simple alphabet or number system; each model has its own name
    b = 1
    tn = wt(b, "own")
    if lt < tn - 0.45:
        for i, ch in enumerate("ABC123"):
            pop(ctx, lt, 0.05 * i, 180 + i * 144, 420, lambda c, ch=ch: chip(c, 0, 0, ch, "white", 70), sound=None)
        ta = wt(b, "alphabet")
        if lt > ta:
            for i in range(3):
                cross(ctx, 180 + i * 144, 420, 46, 10)
        tnum = wt(b, "number")
        if lt > tnum:
            for i in range(3, 6):
                cross(ctx, 180 + i * 144, 420, 46, 10)
        pop(ctx, lt, wt(b, "simple"), W / 2, 560, lambda c: tag(c, "NO SIMPLE SYSTEM", "red", 40), sound=None)
        car_in(ctx, lt, 0.0, "suv", 140, 880, 800, ORANGE_, rims="dark", sound=False)
    else:
        names = ["COROLLA", "CAMRY", "PRIUS", "RAV4", "LAND CRUISER"]
        for i, n in enumerate(names):
            x = 270 + (i % 2) * 540 if i < 4 else W / 2
            y = 430 + (i // 2) * 150
            pop(ctx, lt, tn - 0.45 + 0.08 * i, x, y, lambda c, n=n, i=i: tag(c, n, "yellow" if i % 2 else "white", 50, (-0.06, 0.05, 0.04, -0.05, 0.02)[i]))
        pop(ctx, lt, wt(b, "name"), W / 2, 880, lambda c: tag(c, "EACH MODEL = ITS OWN NAME", "dark", 38), sound=None)


def scene2(ctx, lt):          # Corolla = ring of petals around a flower
    b = 2
    badge_row(ctx, W / 2, BADGE_Y, [("COROLLA", "chrome", -0.2)], lt, 66)
    car_in(ctx, lt, -0.1, "sedan", 40, 880, 620, "#E4E6EA", rims="dark")
    tp = wt(b, "ring")
    bloom = ease((lt - tp + 0.2) / 1.0) if lt > tp - 0.2 else 0
    flower(ctx, 860, 520, 1.0, bloom, lt)
    pop(ctx, lt, wt(b, "petals"), 830, 760, lambda c: tag(c, "RING OF PETALS", "yellow", 36, 0.04), sound=None)
    if bloom > 0:
        sfx_once(lt, tp - 0.2, "pop")


def scene3(ctx, lt):          # Camry = Japanese word for crown
    b = 3
    badge_row(ctx, W / 2, BADGE_Y, [("CAMRY", "chrome", -0.2)], lt, 66)
    car_in(ctx, lt, -0.1, "sedan", 40, 880, 640, BLACK_, rims="dark")
    tj, tc = wt(b, "Japanese"), wt(b, "crown")
    pop(ctx, lt, tj, 300, 430, lambda c: chip(c, 0, 0, "JAPANESE: KANMURI", "white", 40))
    pop(ctx, lt, tc - 0.1, 800, 470, lambda c: crown(c, 0, 0, 1.0, lt))
    pop(ctx, lt, tc, 800, 610, lambda c: tag(c, "= CROWN", "yellow", 44, 0.04), sound=None)


def scene4(ctx, lt):          # Prius = Latin for prior: before hybrids became common
    b = 4
    badge_row(ctx, W / 2, BADGE_Y, [("PRIUS", "green", -0.2)], lt, 66)
    tl, tb, tc = wt(b, "Latin"), wt(b, "before"), wt(b, "common")
    if lt < tb - 0.2:
        car_in(ctx, lt, -0.1, "fastback", 120, 860, 760, SILVER, rims="dark")
        pop(ctx, lt, tl, W / 2, 440, lambda c: scroll(c, 0, 0, 560, "PRIUS", 'LATIN: "PRIOR" = BEFORE'))
    else:
        # timeline: the Prius first, the crowd of hybrids later
        k = ease_out(min(1, (lt - tb + 0.2) / 0.5))
        arrow(ctx, [(80, 760), (80 + 920 * k, 760)], 9, DARK, 26)
        sfx_once(lt, tb - 0.2, "whoosh")
        pop(ctx, lt, tb, 220, 600, lambda c: draw_car(c, "fastback", -150, 120, 300, SILVER, 0.2))
        pop(ctx, lt, tb + 0.1, 220, 820, lambda c: chip(c, 0, 0, "PRIUS FIRST", "green", 34), sound=None)
        for i in range(4):
            pop(ctx, lt, tc - 0.4 + 0.12 * i, 560 + (i % 2) * 230, 560 + (i // 2) * 130,
                lambda c, i=i: draw_car(c, ("suv", "sedan", "hatch", "suv")[i], -110, 50, 220, (BLUE_, RED_, WHITE_, GREY_)[i], 0.2), sound="pop")
        pop(ctx, lt, tc, 790, 830, lambda c: chip(c, 0, 0, "HYBRIDS COMMON", "white", 34), sound=None)


def scene5(ctx, lt):          # RAV4 = Recreational Active Vehicle 4-wheel drive
    b = 5
    car_in(ctx, lt, -0.1, "suv", 190, 905, 700, ORANGE_, rims="dark")
    parts = [("R", "ECREATIONAL", wt(b, "recreational")), ("A", "CTIVE", wt(b, "active")), ("V", "EHICLE", wt(b, "vehicle")),
             ("4", "-WHEEL DRIVE", wt(b, "four-wheel"))]
    for i, (L1, rest, t0) in enumerate(parts):
        y = 290 + i * 98
        lit = lt >= t0
        ink(ctx, rrect(150, y - 44, 110, 88, 18), hexc("#F2B800") if lit else hexc("#FFFFFF"), 5)
        label(ctx, L1, 205, y, 70, DARK)
        if lit:
            n = min(len(rest), int((lt - t0) / 0.035) + 1)
            label(ctx, rest[:n], 280, y, 60, DARK, anchor="l")
            sfx_once(lt, t0, "pop")


def scene6(ctx, lt):          # Land Cruiser: built for going across rough land
    b = 6
    badge_row(ctx, W / 2, BADGE_Y, [("LAND CRUISER", "chrome", -0.2)], lt, 60)
    tr = wt(b, "rough")
    ground(ctx, 890, rough=True)
    rocks(ctx, 860, 885, 1.2); rocks(ctx, 200, 885, 0.8)
    k = lt
    bump = abs(math.sin(lt * 5)) * 10 if lt > 0.5 else 0
    tilt = 0.03 * math.sin(lt * 4)
    x = -800 + min(1, lt / 0.7) * 920
    draw_car(ctx, "suv", x, 880 - bump, 760, SAND, lt * 9, rims="dark", tilt=tilt)
    for i in range(5):      # dust
        ph = (lt * 1.3 + i / 5) % 1
        ctx.arc(x + 20 - ph * 200, 860 - ph * 50 - (i % 3) * 14, 24 + ph * 46, 0, 2 * math.pi)
        ctx.set_source_rgba(0.62, 0.52, 0.40, 0.35 * (1 - ph)); ctx.fill()
    pop(ctx, lt, wt(b, "built"), 300, 420, lambda c: tag(c, "LAND = ROUGH GROUND", "yellow", 40, -0.04))
    pop(ctx, lt, tr, 790, 480, lambda c: tag(c, "CRUISER = TRAVEL ACROSS", "white", 34, 0.04), sound=None)


def scene7(ctx, lt):          # Then come the performance badges (section signpost)
    b = 7
    kerb(ctx, 885)
    car_in(ctx, lt, -0.2, "sports", 150, 875, 780, "#D7182A", rs=True, rims="black")
    speed_lines(ctx, 150, 875, 780, 260, 0.8, seed=int(lt * 6))
    pop(ctx, lt, 0.0, W / 2, 330, lambda c: chip(c, 0, 0, "PERFORMANCE BADGES", "dark", 50))
    pop(ctx, lt, wt(b, "badges"), 380, 470, lambda c: chip(c, 0, 0, "GR", "red", 70))
    pop(ctx, lt, wt(b, "badges") + 0.15, 700, 470, lambda c: chip(c, 0, 0, "TRD", "red", 70))


def scene8(ctx, lt):          # GR = Gazoo Racing, Toyota's motorsport division
    b = 8
    kerb(ctx, 885)
    car_in(ctx, lt, -0.2, "sports", 150, 875, 780, "#D7182A", rs=True, rims="black", sound=False)
    speed_lines(ctx, 150, 875, 780, 260, 0.6, seed=int(lt * 6))
    pop(ctx, lt, 0.0, 250, 360, lambda c: chip(c, 0, 0, "GR", "red", 90))
    pop(ctx, lt, wt(b, "Gazoo"), 640, 360, lambda c: chip(c, 0, 0, "GAZOO RACING", "white", 50))
    tm = wt(b, "Motorsport")
    pop(ctx, lt, tm, 360, 520, lambda c: flag(c, 0, 0, 1.2))
    pop(ctx, lt, tm + 0.1, 660, 520, lambda c: tag(c, "MOTORSPORT DIVISION", "yellow", 34, 0.03), sound=None)


def scene9(ctx, lt):          # GR Corolla / GR Supra: sharper focus on driving
    b = 9
    badge_row(ctx, W / 2, BADGE_Y, [("GR", "red", -0.2)], lt, 66)
    tc, ts = wt(b, "Corolla"), wt(b, "Supra")
    slot(ctx, lt, tc, "hatch", 40, 560, 560, "#1D1E22", early=True, s_model=True, rims="black")
    pop(ctx, lt, tc, 840, 380, lambda c: chip(c, 0, 0, "GR COROLLA", "red", 40))
    slot(ctx, lt, ts, "sports", 40, 880, 620, "#D7182A", rs=True, rims="black")
    pop(ctx, lt, ts, 840, 700, lambda c: chip(c, 0, 0, "GR SUPRA", "red", 40))
    th = wt(b, "sharper")
    pop(ctx, lt, th, 860, 520, lambda c: (steering(c, -110, 0, 0.9), tag(c, "SHARPER", "yellow", 36, 0.03)))


def scene10(ctx, lt):         # TRD = Toyota Racing Development: performance or off-road packages
    b = 10
    badge_row(ctx, W / 2, BADGE_Y, [("TRD", "red", -0.2), ("= TOYOTA RACING DEVELOPMENT", "white", wt(b, "Toyota"))], lt, 42)
    tp, to = wt(b, "performance"), wt(b, "off-road")
    slot(ctx, lt, tp, "sports", 40, 560, 560, "#F2B800", early=True, rs=True, rims="black")
    pop(ctx, lt, tp, 830, 400, lambda c: tag(c, "PERFORMANCE", "yellow", 40, 0.04))
    rocks(ctx, 760, 880, 1.0)
    slot(ctx, lt, to, "pickup", 40, 880, 620, "#1D1E22", rs=True, rims="black")
    pop(ctx, lt, to, 840, 700, lambda c: tag(c, "OFF-ROAD", "yellow", 40, -0.04))


def scene11(ctx, lt):         # Hybrid = petrol engine + electric motor
    b = 11
    badge_row(ctx, W / 2, BADGE_Y, [("HYBRID", "green", -0.2)], lt, 66)
    tp, te = wt(b, "petrol"), wt(b, "electric")
    petrol = ease((lt - tp) / 0.4) if lt > tp else 0
    el = ease((lt - te) / 0.4) if lt > te else 0
    p = max(0.02, ease_out_back(min(1, (lt + 0.2) / 0.45)))
    ctx.save(); ctx.translate(W / 2, 600); ctx.scale(p, p)
    chassis(ctx, 0, 0, lt, 1.0, petrol=petrol, battery=el, motor=el)
    ctx.restore()
    pop(ctx, lt, tp, 300, 830, lambda c: tag(c, "PETROL ENGINE", "green", 36, -0.03), sound=None)
    pop(ctx, lt, te, 780, 830, lambda c: tag(c, "+ ELECTRIC MOTOR", "blue", 36, 0.03), sound=None)


def scene12(ctx, lt):         # plug-in hybrid charges from an external power source
    b = 12
    badge_row(ctx, W / 2, BADGE_Y, [("PLUG-IN HYBRID", "green", -0.2)], lt, 60)
    tc = wt(b, "charge")
    chassis(ctx, W / 2 - 80, 600, lt, 0.9, petrol=1, battery=1, motor=1, charge=1 if lt > tc else 0)
    if lt > tc - 0.2:
        k = ease_out(min(1, (lt - tc + 0.2) / 0.5))
        outlet(ctx, 990, 600)
        cable = qbez((W / 2 - 50, 600), (760, 760), (960, 620), 20)
        n = max(2, int(len(cable) * k))
        line(ctx, cable[:n], 9, DARK)
        sfx_once(lt, tc - 0.2, "pop")
    pop(ctx, lt, wt(b, "external"), W / 2, 830, lambda c: tag(c, "CHARGES FROM A PLUG", "yellow", 38), sound=None)


def scene13(ctx, lt):         # AWD = all-wheel drive, power to all four wheels
    b = 13
    badge_row(ctx, W / 2, BADGE_Y, [("AWD", "chrome", -0.2)], lt, 70)
    ta = wt(b, "all-wheel")
    awd = ease((lt - ta) / 0.4) if lt > ta else 0
    chassis(ctx, W / 2, 600, lt, 1.0, petrol=1, battery=1, motor=1, awd=awd)
    pop(ctx, lt, wt(b, "four"), W / 2, 850, lambda c: tag(c, "POWER TO ALL 4 WHEELS", "yellow", 40), sound=None)


def scene14(ctx, lt):         # Cross = crossover style, sits higher than the regular Corolla
    b = 14
    badge_row(ctx, W / 2, BADGE_Y, [("CROSS", "chrome", -0.2), ("= CROSSOVER", "white", wt(b, "crossover"))], lt, 60)
    tc1, tc2 = wt(b, "Corolla", 0), wt(b, "Corolla", 1)
    car_in(ctx, lt, -0.1, "sedan", 20, 860, 480, "#E4E6EA", rims="dark")
    pop(ctx, lt, tc1, 260, 560, lambda c: chip(c, 0, 0, "COROLLA", "white", 36), sound=None)
    slot(ctx, lt, tc1 + 0.2, "suv", 560, 860, 480, "#C8102E", rims="dark")
    pop(ctx, lt, tc1 + 0.3, 800, 500, lambda c: chip(c, 0, 0, "COROLLA CROSS", "red", 36), sound=None)
    th = wt(b, "higher")
    if lt > th - 0.1:
        k = ease_out(min(1, (lt - th + 0.1) / 0.4))
        y0 = 860 - 0.445 * 0.73 * 480; y1 = 860 - 0.565 * 0.69 * 480
        line(ctx, [(500, y0), (1050, y0)], 4, hexc("#D7182A"))
        arrow(ctx, [(1030, y0), (1030, y0 + (y1 - y0) * k)], 7, hexc("#D7182A"), 20)
        sfx_once(lt, th - 0.1, "whoosh")
        pop(ctx, lt, th, 820, 380, lambda c: tag(c, "SITS HIGHER", "yellow", 40, 0.04), sound=None)


def scene15(ctx, lt):         # ENDING: So a RAV4 Hybrid AWD is ... (decode the hook badge)
    b = 15
    car_in(ctx, lt, -0.1, "suv", 140, 880, 800, ORANGE_, rims="dark", sound=False)
    rows = [("RAV4 = RECREATIONAL SUV", wt(b, "SUV")), ("HYBRID = PETROL + ELECTRIC", wt(b, "powertrain")),
            ("AWD = ALL FOUR WHEELS", wt(b, "wheels"))]
    lit = [1 if lt > t0 else 0.25 for _, t0 in rows]
    hook_row(ctx, lt, W / 2, 230, 62, show_q=False, lit=lit)
    p = ease_out_back(min(1, lt / 0.4))
    ctx.save(); ctx.translate(W / 2, 450); ctx.scale(max(0.02, p), max(0.02, p))
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


def scene16(ctx, lt):         # follow me
    b = 16
    tf = wt(b, "follow")
    car_in(ctx, lt, 0.0, "suv", 140, 880, 800, ORANGE_, rims="dark", sound=False)
    hook_row(ctx, lt, W / 2, 230, 62, show_q=False)
    if lt >= tf - 0.3:
        p = max(0.02, ease_out_back((lt - tf + 0.3) / 0.45))
        sfx_once(lt, tf - 0.3, "pop")
        ctx.save(); ctx.translate(W / 2, 480); ctx.scale(p, p)
        ink(ctx, rrect(-420, -170, 840, 340, 50), hexc("#FFFFFF", 0.95), 6)
        label(ctx, "FOLLOW FOR", 0, -80, 64, DARK)
        chip(ctx, 0, 30, NEXT, "red", 60)
        label(ctx, CTX["handle"], 0, 120, 40, hexc("#3A3D44"), font=MONO)
        ctx.restore()


SCENES = [scene0, scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9, scene10, scene11, scene12,
          scene13, scene14, scene15, scene16]
