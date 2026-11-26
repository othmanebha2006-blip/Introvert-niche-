"""Episode 8: every Lexus model explained. Built like the reference videos (cars/REFERENCE_ANALYSIS.md):
2.5 s hook with the final badge "NX · 450h+ · F SPORT" + ? (open loop), rule first, examples small -> big,
section signposts, a myth-bust ("not a 5-litre engine"), surprising facts (Fuji Speedway, LFA V10), and the ending
decodes the hook badge. Cars in the reference look (car.STYLE["real"]); one car turns into another with a blue scan
line (the reference's main transition). Voice = user's mp3 with pauses shortened; presenter = the user's new
character (green-screen clip, extended with an invisible jump)."""
import json, os, math
from ink import *
from car import draw_car, WHEELS
from widgets import *
import widgets

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = "BADGE DECODED · #8"
BRAND = "LEXUS"
NEXT = "BADGE DECODED #9"

FIX = {"500H": "500h", "450H": "450h", "5-litre": "5-LITRE"}
SPLIT_IDX = [0, 7, 25, 30, 46, 52, 64, 69, 74, 80, 91, 117, 131, 143, 158, 176, 208, 229, 248]
BEAT_OF_SENT = [0, 1, 2, 2, 3, 4, 5, 5, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

KEYWORDS = {"LEXUS", "LETTERS", "IS", "ES", "SALOONS", "SPORTIER", "COMFORTABLE", "EXECUTIVE", "LS", "FLAGSHIP",
            "LUXURY", "X", "SUV", "UX", "URBAN", "NX", "NIMBLE", "RX", "LARGER", "RADIANT", "GX", "RUGGED", "OFF-ROADER",
            "LX", "NUMBER", "350", "500", "ENGINE", "POWERTRAIN", "PERFORMANCE", "H", "HYBRID", "PLUS", "PLUG-IN", "E",
            "ELECTRIC", "500H", "5-LITRE", "F", "SPORT", "DIFFERENT", "RC", "FUJI", "SPEEDWAY", "JAPAN", "L", "LC",
            "GRAND", "TOURING", "COUPE", "JOURNEYS", "LFA", "LEGENDARY", "V10", "SUPERCAR", "450H", "CROSSOVER",
            "PACKAGE", "FOLLOW"}


def load_timing():
    W = json.load(open(os.path.join(HERE, "words.json")))
    cuts = SPLIT_IDX + [len(W)]
    SENT, WORDS = [], []
    for si in range(len(SPLIT_IDX)):
        ws = W[cuts[si]:cuts[si + 1]]
        SENT.append(dict(beat=BEAT_OF_SENT[si], start=ws[0]["s"], end=ws[-1]["e"], text=" ".join(w["w"] for w in ws)))
        for w in ws:
            core = w["w"].strip(",.?!")
            WORDS.append(dict(text=w["w"].replace(core, FIX.get(core, core)), start=w["s"], end=w["e"],
                              beat=BEAT_OF_SENT[si], sent=si))
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
WHITE_, BLACK_, RED_, BLUE_, GREY_, GREEN_, SAND, SILVER = (
    "#ECECE8", "#1C1D21", "#B5121B", "#2C5D9E", "#6E7378", "#4E5B3C", "#B7A27E", "#B6BBC1")
HOOK = [("NX", "chrome"), ("450h+", "green"), ("F SPORT", "chrome")]


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



def morph(ctx, lt, t0, a, b, x, y, L, dur=0.5):
    """scan-line transition: car a (kind, paint, kw) turns into car b behind a moving blue line"""
    if lt < t0:
        draw_car(ctx, a[0], x, y, L, a[1], 0.0, **a[2]); return
    p = ease((lt - t0) / dur)
    if p >= 1:
        draw_car(ctx, b[0], x, y, L, b[1], 0.0, **b[2]); return
    sx = x - 0.05 * L + p * 1.1 * L
    ctx.save(); ctx.rectangle(sx, 0, 2000, 2000); ctx.clip(); draw_car(ctx, a[0], x, y, L, a[1], 0.0, **a[2]); ctx.restore()
    ctx.save(); ctx.rectangle(-1000, 0, sx + 1000, 2000); ctx.clip(); draw_car(ctx, b[0], x, y, L, b[1], 0.0, **b[2]); ctx.restore()
    ctx.set_source(lin_grad(sx - 40, 0, sx + 40, 0, [(0, (0.2, 0.6, 1, 0)), (0.5, (0.2, 0.7, 1, 0.55)), (1, (0.2, 0.6, 1, 0))]))
    ctx.rectangle(sx - 40, y - 0.6 * L, 80, 0.66 * L); ctx.fill()
    line(ctx, [(sx, y - 0.6 * L), (sx, y + 10)], 6, hexc("#3BA6FF"), sketch=False)
    sfx_once(lt, t0, "whoosh")


def engine_block(ctx, x, y, s, text):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, rrect(-120, -70, 240, 140, 18), hexc("#9AA0A6"), 5)
    for i in range(4):
        ink(ctx, rrect(-100 + i * 52, -110, 40, 46, 8), hexc("#B9BDC4"), 4)
    label(ctx, text, 0, 6, 58, DARK, font="Anton")
    ctx.restore()


def fuji(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, [(-170, 80), (-40, -90), (40, -90), (170, 80)], hexc("#5D7FA6"), 5)
    ink(ctx, [(-40, -90), (40, -90), (75, -45), (40, -55), (10, -35), (-20, -55), (-75, -45)], hexc("#FFFFFF"), 4)
    ink(ctx, ellipse(120, -80, 26, 26, 24), hexc("#D7182A"), 0)
    ctx.restore()


def city(ctx, x, y, w):
    hs = [90, 140, 70, 170, 110, 60, 130]
    bw = w / len(hs)
    for i, h in enumerate(hs):
        ink(ctx, rrect(x + i * bw, y - h, bw - 8, h, 4), hexc("#D3D7DD"), 3, hexc("#A9AEB6"))


def hero(ctx, t):          # decoding tracker under the header (keeps the open loop visible)
    B = CTX["beat_t"]
    if t < B[1] or t >= B[14]:
        return
    done = [gw(5, "crossover", 1), gw(8, "hybrid", 1), gw(10, "feel")]
    x, y, size = W / 2, 150, 30
    ws = [chip_size(ctx, tt, size)[0] for tt, _ in HOOK]
    total = sum(ws) + 20 + 120
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
def scene0(ctx, lt):          # HOOK
    b = 0
    car_in(ctx, lt, -0.5, "suv", 160, 880, 760, BLUE_, sline=True, rims="dark", sound=False)
    if lt < 0.6:
        speed_lines(ctx, 160, 880, 760, 280, 1.0 - lt, seed=3)
    pop(ctx, lt, -0.2, W / 2, 230, lambda c: chip(c, 0, 0, "LEXUS", "dark", 70))
    for i, (sx, sy) in enumerate([(340, 190), (740, 200)]):
        sparkle(ctx, sx, sy, 26, lt + i)
    te = wt(b, "explained")
    if lt > te - 0.1:
        p = ease_out_back(min(1, (lt - te + 0.1) / 0.35))
        sfx_once(lt, te - 0.1, "pop")
        ctx.save(); ctx.translate(W / 2, 420); ctx.scale(max(0.02, p), max(0.02, p)); ctx.translate(-W / 2, -420)
        hook_row(ctx, lt, W / 2, 420, 66)
        ctx.restore()
        glow_ring(ctx, W / 2, 420, 440, 90, lt)


def scene1(ctx, lt):          # two letters tell you what kind of car it is
    b = 1
    tl, tk = wt(b, "letters"), wt(b, "kind")
    if lt < tk - 0.25:     # the hook car stays until the outlines take over
        car_in(ctx, lt, -1.0, "suv", 160, 880, 760, BLUE_, sline=True, rims="dark", sound=False)
    for i, ch in enumerate("??"):
        x = 400 + i * 280
        filled = lt > tl
        pop(ctx, lt, -0.1 + 0.1 * i, x, 420, lambda c, i=i, filled=filled: (ink(c, rrect(-110, -110, 220, 220, 30), hexc("#F2B800") if filled else hexc("#FFFFFF"), 6),
                                                                         label(c, "?" if not filled else "NX"[i], 0, 8, 150, DARK)))
    pop(ctx, lt, tl, W / 2, 580, lambda c: tag(c, "TWO LETTERS", "yellow", 44), sound=None)
    if lt > tk - 0.2:
        arrow(ctx, [(W / 2, 640), (W / 2, 700)], 9, DARK, 26)
        pop(ctx, lt, tk - 0.2, 300, 880, lambda c: draw_car(c, "sedan", -200, 0, 400, ghost=True))
        pop(ctx, lt, tk, 780, 880, lambda c: draw_car(c, "suv", -200, 0, 400, ghost=True))
        pop(ctx, lt, tk + 0.1, W / 2, 760, lambda c: tag(c, "= WHAT KIND OF CAR", "dark", 38), sound=None)


def scene2(ctx, lt):          # IS + ES saloons: IS smaller sportier, ES comfortable executive
    b = 2
    ti, te = wt(b, "IS"), wt(b, "ES")
    badge_row(ctx, W / 2, BADGE_Y, [("IS", "chrome", ti - 0.1), ("ES", "chrome", te), ("SALOONS", "white", wt(b, "saloons"))], lt, 60)
    slot(ctx, lt, ti, "sedan", 60, 560, 600, RED_, early=True, sline=True, rims="dark")
    pop(ctx, lt, wt(b, "sportier"), 830, 390, lambda c: tag(c, "SMALLER + SPORTIER", "yellow", 32, 0.04))
    slot(ctx, lt, te, "sedan", 40, 885, 720, SILVER, rims="silver")
    pop(ctx, lt, wt(b, "executive"), 830, 650, lambda c: tag(c, "COMFORTABLE EXECUTIVE", "white", 30, -0.04))


def scene3(ctx, lt):          # LS flagship luxury saloon
    b = 3
    badge_row(ctx, W / 2, BADGE_Y, [("LS", "chrome", -0.1)], lt, 72)
    car_in(ctx, lt, -0.1, "sedan", 100, 860, 880, BLACK_, rims="silver")
    pop(ctx, lt, wt(b, "flagship"), 300, 430, lambda c: stamp(c, "FLAGSHIP", "#B8860B", 64, -0.06), sound="stamp")
    pop(ctx, lt, wt(b, "luxury"), 790, 450, lambda c: crown_mini(c, 0, 0, lt))


def crown_mini(ctx, x, y, lt):
    pts = [(-70, 30), (-76, -36), (-38, -6), (0, -56), (38, -6), (76, -36), (70, 30)]
    ctx.save(); ctx.translate(x, y)
    ink(ctx, pts, hexc("#F2B800"), 5); ink(ctx, rrect(-72, 24, 144, 24, 8), hexc("#E0A200"), 5)
    ctx.restore()
    label(ctx, "LUXURY", x, y + 90, 40, hexc("#B8860B"), DARK, 6)


def scene4(ctx, lt):          # put an X at the end -> SUV (scan-line morph)
    b = 4
    tx, ts = wt(b, "X"), wt(b, "SUV")
    badge_row(ctx, W / 2, BADGE_Y, [("L _", "white", -0.1), ("+ X", "red", tx), ("= SUV", "yellow", ts)], lt, 60)
    morph(ctx, lt, ts - 0.35, ("sedan", BLACK_, dict(rims="silver")), ("suv", BLACK_, dict(rims="silver")), 100, 860, 860, 0.5)
    pop(ctx, lt, tx, 840, 420, lambda c: label(c, "X", 0, 0, 150, RED, DARK, 12))


SUVS = [("UX", "urban", 380, "#E8E6DF", "URBAN"), ("NX", "nimble", 450, BLUE_, "NIMBLE"), ("RX", "larger", 540, GREY_, "LARGER")]


def scene5(ctx, lt):          # UX urban, NX nimble, RX larger radiant
    b = 5
    badge_row(ctx, W / 2, BADGE_Y, [("CROSSOVERS", "white", -0.1)], lt, 56)
    city(ctx, 560, 430, 470)
    for i, (name, word, L, paint, desc) in enumerate(SUVS):
        t0 = wt(b, name)
        y = 520 + i * 185
        slot(ctx, lt, t0, "suv", 40, y, L, paint, early=(i == 0), rims="dark")
        pop(ctx, lt, t0, 40 + L + 140, y - 140, lambda c, n=name: chip(c, 0, 0, n, "chrome", 44), sound=None)
        pop(ctx, lt, wt(b, word), 40 + L + 150, y - 70, lambda c, d=desc: tag(c, d, "yellow", 32, 0.03), sound=None)


def scene6(ctx, lt):          # GX rugged off-roader, LX flagship SUV
    b = 6
    tg, tl = wt(b, "GX"), wt(b, "LX")
    badge_row(ctx, W / 2, BADGE_Y, [("GX", "chrome", -0.1), ("LX", "chrome", tl)], lt, 66)
    rocks(ctx, 800, 560, 1.0)
    slot(ctx, lt, tg, "suv", 40, 560, 620, GREEN_, early=True, rims="dark")
    pop(ctx, lt, wt(b, "rugged"), 860, 380, lambda c: tag(c, "RUGGED OFF-ROADER", "yellow", 30, 0.04))
    slot(ctx, lt, tl, "suv", 40, 885, 760, BLACK_, rims="silver")
    pop(ctx, lt, wt(b, "flagship"), 860, 640, lambda c: stamp(c, "FLAGSHIP", "#B8860B", 50, 0.05), sound="stamp")


def scene7(ctx, lt):          # Then comes the number: 350 / 500 used to be engine size; today powertrain + performance
    b = 7
    t3, t5, te, tt = wt(b, "350"), wt(b, "500"), wt(b, "engine"), wt(b, "today")
    pop(ctx, lt, -0.1, W / 2, 250, lambda c: chip(c, 0, 0, "THEN: THE NUMBER", "dark", 50))
    pop(ctx, lt, t3, 330, 400, lambda c: chip(c, 0, 0, "350", "chrome", 70))
    pop(ctx, lt, t5, 750, 400, lambda c: chip(c, 0, 0, "500", "chrome", 70))
    pop(ctx, lt, te - 0.1, 330, 640, lambda c: engine_block(c, 0, 0, 0.9, "3.5 L"))
    pop(ctx, lt, te, 750, 640, lambda c: engine_block(c, 0, 0, 0.9, "5.0 L"))
    pop(ctx, lt, wt(b, "roughly"), W / 2, 520, lambda c: tag(c, "USED TO = ENGINE SIZE", "white", 34), sound=None)
    if lt > tt:
        for xx in (330, 750):
            cross(ctx, xx, 640, 80, 12)
        sfx_once(lt, tt, "stamp")
        pop(ctx, lt, wt(b, "powertrain"), W / 2, 850, lambda c: tag(c, "TODAY: POWERTRAIN + PERFORMANCE", "yellow", 32), sound=None)


def scene8(ctx, lt):          # H hybrid, H+ plug-in hybrid, E electric
    b = 8
    th, thp, te = wt(b, "H"), wt(b, "plug-in"), wt(b, "E")
    badge_row(ctx, W / 2, BADGE_Y, [("h", "green", th), ("h+", "green", wt(b, "plus") - 0.1), ("e", "blue", te)], lt, 70)
    petrol = 1 if lt < te else 1 - ease((lt - te) / 0.4)
    bat = ease((lt - th) / 0.4) if lt > th else 0
    charge = 1 if thp < lt < te + 0.6 else 0
    chassis(ctx, W / 2 - (60 if charge else 0), 600, lt, 0.95, petrol=petrol, battery=bat, motor=bat, charge=charge)
    if charge:
        outlet(ctx, 1000, 600)
        line(ctx, qbez((W / 2 - 20, 600), (760, 760), (980, 620), 20), 9, DARK)
    pop(ctx, lt, th + 0.1, 220, 830, lambda c: tag(c, "H = HYBRID", "green", 34, -0.03), sound=None)
    pop(ctx, lt, thp, 540, 860, lambda c: tag(c, "H+ = PLUG-IN", "green", 34, 0.02), sound=None)
    pop(ctx, lt, te + 0.1, 860, 830, lambda c: tag(c, "E = ELECTRIC", "blue", 34, 0.03), sound=None)


def scene9(ctx, lt):          # myth: RX 500h is a hybrid SUV, not a 5-litre engine
    b = 9
    tr, tn = wt(b, "RX"), wt(b, "not")
    badge_row(ctx, W / 2, BADGE_Y, [("RX", "chrome", -0.1), ("500h", "green", wt(b, "500h") - 0.1)], lt, 70)
    car_in(ctx, lt, -0.1, "suv", 80, 880, 620, GREY_, rims="dark")
    pop(ctx, lt, wt(b, "hybrid"), 300, 430, lambda c: tag(c, "HYBRID SUV", "green", 42, -0.04))
    pop(ctx, lt, tn - 0.15, 860, 560, lambda c: engine_block(c, 0, 0, 0.8, "5.0 L"))
    if lt > tn:
        cross(ctx, 860, 560, 90, 14)
        pop(ctx, lt, tn, 800, 400, lambda c: stamp(c, "NOT 5 LITRES", "#D7182A", 50, 0.06), sound="stamp")


def scene10(ctx, lt):         # F Sport = sportier look and feel; but F is different
    b = 10
    tf, td = wt(b, "F"), wt(b, "different")
    badge_row(ctx, W / 2, BADGE_Y, [("F SPORT", "chrome", tf - 0.1)], lt, 66)
    morph(ctx, lt, wt(b, "sportier") - 0.3, ("suv", BLUE_, dict(rims="silver")), ("suv", BLUE_, dict(sline=True, rims="black")), 120, 880, 820, 0.5)
    if lt > wt(b, "look"):
        for i, (sx, sy) in enumerate([(300, 560), (640, 520), (900, 640)]):
            sparkle(ctx, sx, sy, 28, lt + i)
    pop(ctx, lt, wt(b, "look"), 290, 420, lambda c: tag(c, "LOOK + FEEL", "yellow", 42, -0.04))
    pop(ctx, lt, td - 0.15, 800, 420, lambda c: (chip(c, 0, 0, "F", "red", 70), label(c, "≠", -110, 0, 70, DARK) if False else None))
    pop(ctx, lt, td, 800, 520, lambda c: tag(c, "F IS DIFFERENT", "red", 34, 0.04), sound=None)


def scene11(ctx, lt):         # F = high performance division, RC F, from Fuji Speedway in Japan
    b = 11
    badge_row(ctx, W / 2, BADGE_Y, [("F", "red", -0.1), ("= HIGH PERFORMANCE", "white", wt(b, "performance"))], lt, 60)
    tr, tf = wt(b, "RC"), wt(b, "Fuji")
    kerb(ctx, 885)
    car_in(ctx, lt, tr - 0.2, "fastback", 120, 875, 800, "#E8E8E2", rs=True, rims="black")
    pop(ctx, lt, tr + 0.1, 300, 430, lambda c: chip(c, 0, 0, "RC F", "red", 52))
    pop(ctx, lt, tf - 0.1, 800, 450, lambda c: fuji(c, 0, 0, 1.0))
    pop(ctx, lt, tf + 0.1, 800, 590, lambda c: tag(c, "F = FUJI SPEEDWAY", "yellow", 34, 0.04), sound=None)
    pop(ctx, lt, wt(b, "Japan"), 300, 560, lambda c: tag(c, "JAPAN", "white", 38, -0.04), sound=None)


def scene12(ctx, lt):         # L = luxury (LS, LX); LC grand touring coupe for long journeys
    b = 12
    tls, tlx, tlc = wt(b, "LS"), wt(b, "LX"), wt(b, "LC")
    badge_row(ctx, W / 2, BADGE_Y, [("L", "chrome", -0.1), ("= LUXURY", "yellow", wt(b, "luxury"))], lt, 64)
    if lt < tlc - 0.3:
        slot(ctx, lt, tls, "sedan", 40, 560, 560, BLACK_, early=True)
        pop(ctx, lt, tls, 820, 400, lambda c: chip(c, 0, 0, "LS", "chrome", 50))
        slot(ctx, lt, tlx, "suv", 40, 885, 620, BLACK_)
        pop(ctx, lt, tlx, 820, 700, lambda c: chip(c, 0, 0, "LX", "chrome", 50))
    else:
        car_in(ctx, lt, tlc - 0.3, "fastback", 120, 860, 820, RED_, rims="dark", dur=0.5)
        pop(ctx, lt, tlc, 300, 420, lambda c: chip(c, 0, 0, "LC", "chrome", 60))
        pop(ctx, lt, wt(b, "grand"), 760, 420, lambda c: tag(c, "GRAND TOURING COUPE", "yellow", 32, 0.04))
        tj = wt(b, "journeys")
        if lt > tj - 0.2:
            k = ease_out(min(1, (lt - tj + 0.2) / 0.6))
            arrow(ctx, [(120, 560), (120 + 840 * k, 560)], 9, DARK, 26)
            pop(ctx, lt, tj, W / 2, 610, lambda c: tag(c, "LONG JOURNEYS", "white", 36), sound=None)


def scene13(ctx, lt):         # LFA legendary V10 supercar, far beyond saloons and SUVs
    b = 13
    badge_row(ctx, W / 2, BADGE_Y, [("LFA", "red", -0.1)], lt, 72)
    kerb(ctx, 885)
    car_in(ctx, lt, -0.1, "sports", 120, 875, 820, "#F2F2EE", rs=True, rims="black")
    speed_lines(ctx, 120, 875, 820, 260, 0.7, seed=int(lt * 6))
    pop(ctx, lt, wt(b, "legendary"), 300, 430, lambda c: stamp(c, "LEGENDARY", "#C8102E", 60, -0.07), sound="stamp")
    tv = wt(b, "V10")
    pop(ctx, lt, tv, 800, 420, lambda c: chip(c, 0, 0, "V10", "red", 64))
    if lt > tv:
        sound_waves(ctx, 110, 820, lt); sfx_once(lt, tv, "rumble")
    pop(ctx, lt, wt(b, "supercar"), 800, 530, lambda c: tag(c, "SUPERCAR", "yellow", 40, 0.04), sound=None)


def scene14(ctx, lt):         # ENDING: So an NX 450h+ F Sport is ...
    b = 14
    car_in(ctx, lt, -0.1, "suv", 160, 885, 760, BLUE_, sline=True, rims="black", sound=False)
    rows = [("NX = NIMBLE CROSSOVER", wt(b, "crossover")), ("450h+ = PLUG-IN HYBRID", wt(b, "hybrid")),
            ("F SPORT = SPORTIER PACKAGE", wt(b, "package"))]
    lit = [1 if lt > t0 else 0.25 for _, t0 in rows]
    hook_row(ctx, lt, W / 2, 236, 60, show_q=False, lit=lit)
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


def scene15(ctx, lt):         # follow me
    b = 15
    tf = wt(b, "follow")
    car_in(ctx, lt, 0.0, "suv", 160, 885, 760, BLUE_, sline=True, rims="black", sound=False)
    hook_row(ctx, lt, W / 2, 236, 60, show_q=False)
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
          scene13, scene14, scene15]
