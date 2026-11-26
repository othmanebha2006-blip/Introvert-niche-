"""Episode 9: every Mercedes-AMG car explained (reference recipe, cars/REFERENCE_ANALYSIS.md).
Hook: the GLC drives on a road from frame 0 with the badge "GLC 63 S · E PERFORMANCE · 4MATIC+" and ? (open loop);
the ending decodes it. Voice + presenter = the user's @Mecmation clip (character_mecmation/amg_presenter.mp4).
Car images: code drawings in the reference look until generated images are dropped into assets/ (IMAGE_PROMPTS.md)."""
import json, os, math
from ink import *
from car import draw_car, WHEELS
from widgets import *
import widgets
from hook import driving_car, topic_fx

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = "BADGE DECODED · #9"
BRAND = "MERCEDES-AMG"
NEXT = "BADGE DECODED #10"
CLIP = "amg_presenter.mp4"

FIX = {"Off-Rect": "Aufrecht", "Gross": "Gross-", "Aspach": "aspach", "Formatic": "4MATIC", "Plus": "+",
       "63SE": "63 S E", "S-version": "S-version"}
SPLIT_IDX = [0, 7, 26, 30, 42, 59, 88, 108, 120, 134, 141, 157, 179]
BEAT_OF_SENT = list(range(len(SPLIT_IDX)))

KEYWORDS = {"MERCEDES-AMG", "AMG", "AUFRECHT", "MELCHER", "GROSS-", "ASPACH", "FOUNDERS", "TOWN", "BORN", "PERFORMANCE",
            "DIVISION", "ENGINE", "SUSPENSION", "UPGRADES", "LINE", "TRIM", "WHEELS", "BUMPERS", "NO", "POWER", "NUMBER",
            "35", "43", "53", "63", "55", "ENTRY", "TOP", "SIZE", "V8", "PLUG-IN", "HYBRID", "GT", "S", "SHARPER", "E",
            "4MATIC", "+", "ALL-WHEEL", "SPORTS", "FAMILY", "G63", "G-CLASS", "GLC", "63 S E", "SUV", "TOP-TIER",
            "S-VERSION", "FOLLOW", "HIGH-PERFORMANCE", "AGGRESSIVE"}


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
SILVER, BLACK_, GREEN_, BLUE_, GREY_, RED_, SAND = "#C7CACD", "#1C1D21", "#3E8E41", "#2C5D9E", "#5E6368", "#B5121B", "#B7A27E"
HOOK = [("GLC 63", "chrome"), ("S", "red"), ("E PERFORMANCE", "green"), ("4MATIC+", "chrome")]


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


def hook_row(ctx, lt, x, y, size, show_q=True, lit=(1, 1, 1, 1)):
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



def spring(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    pts = [(-30 if i % 2 else 30, -60 + i * 12) for i in range(11)]
    line(ctx, pts, 9, hexc("#D7182A"))
    ink(ctx, rrect(-40, -76, 80, 16, 6), hexc("#9AA0A6"), 4); ink(ctx, rrect(-40, 64, 80, 16, 6), hexc("#9AA0A6"), 4)
    ctx.restore()


def town(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    for i, (hx, h) in enumerate([(-120, 90), (-40, 120), (40, 80), (120, 105)]):
        ink(ctx, rrect(hx - 34, -h, 68, h, 4), hexc("#F3E3BF"), 4)
        ink(ctx, [(hx - 42, -h), (hx, -h - 46), (hx + 42, -h)], hexc("#C0563A"), 4)
        ink(ctx, rrect(hx - 10, -30, 20, 30, 3), hexc("#6B4A2B"), 3)
    line(ctx, [(-180, 0), (180, 0)], 5)
    ctx.restore()


def portrait(ctx, x, y, name, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, rrect(-110, -130, 220, 260, 14), hexc("#F3E3BF"), 6, hexc("#6B4A2B"))
    ink(ctx, ellipse(0, -40, 46, 54, 30), hexc("#E8C9A6"), 4)
    ink(ctx, rpoly([(-80, 120), (-70, 40), (70, 40), (80, 120)], 20), hexc("#3A3D44"), 4)
    label(ctx, name, 0, 100, 26, hexc("#FFFFFF"), DARK, 5)
    ctx.restore()


def amg_ticker(ctx, t):
    names = ["35", "43", "53", "55", "63", "S", "GT", "G 63", "4MATIC+", "E PERFORMANCE"]
    widths = [chip_size(ctx, n, 32)[0] + 22 for n in names]
    tot = sum(widths); off = (t * 260) % tot
    for k in range(-1, 2):
        x = k * tot - off
        for n, w in zip(names, widths):
            cx = x + w / 2
            if -150 < cx < 1230:
                ctx.save(); ctx.push_group(); chip(ctx, cx, 430, n, "white", 32); ctx.pop_group_to_source(); ctx.paint_with_alpha(0.55); ctx.restore()
            x += w


def hero(ctx, t):          # DECODING tracker
    B = CTX["beat_t"]
    if t < B[1] or t >= B[11]:
        return
    done = [gw(5, "range"), gw(8, "version"), gw(8, "hybrid"), gw(9, "system")]
    x, y, size = W / 2, 150, 27
    ws = [chip_size(ctx, tt, size)[0] for tt, _ in HOOK]
    total = sum(ws) + 10 * 3 + 120
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
            ctx.save(); ctx.translate(xx + w - 4, y - 20); ctx.scale(max(0.02, p), max(0.02, p)); check(ctx, 0, 0, 0.5); ctx.restore()
            if 0 <= t - done[i] < 1 / 30:
                widgets.SFX.append((t, "pop"))
        else:
            label(ctx, "?", xx + w - 4, y - 22, 24, RED)
        xx += w + 10


def scene0(ctx, lt):          # HOOK
    b = 0
    driving_car(ctx, lt, "suv", BLUE_, L=1000, x=10, y=905, ticker=amg_ticker, rs=True, rims="black")
    ta = wt(b, "Mercedes-AMG")
    pop(ctx, lt, ta - 0.05, W / 2, 175, lambda c: chip(c, 0, 0, "MERCEDES-AMG", "dark", 58))
    if lt > ta:
        for i, (sx, sy) in enumerate([(300, 150), (780, 160)]):
            sparkle(ctx, sx, sy, 24, lt + i)
    te = wt(b, "explained")
    p = min(1, 0.55 + lt / 0.3)
    ctx.save(); ctx.translate(W / 2, 295); ctx.scale(p, p); ctx.translate(-W / 2, -295)
    ctx.translate(3 * math.sin(lt * 40) if te < lt < te + 0.5 else 0, 0)
    hook_row(ctx, lt, W / 2, 295, 50, show_q=False)
    ctx.restore()
    topic_fx(ctx, lt, W / 2, 295, 470, 64, wt(b, "car"), te)


def scene1(ctx, lt):          # AMG = Aufrecht, Melcher, Grossaspach; founders + town
    b = 1
    t = lt + CTX["beat_t"][1]
    tA, tM, tG = wt(b, "Aufrecht"), wt(b, "Melcher"), wt(b, "Gross-")
    tf = wt(b, "founders")
    if lt < tf - 0.1:
        driving_car(ctx, t, "suv", BLUE_, L=1000, x=10, y=905, rs=True, rims="black")
    for i, (L1, rest, t0) in enumerate([("A", "UFRECHT", tA), ("M", "ELCHER", tM), ("G", "ROSSASPACH", tG)]):
        y = 300 + i * 100
        lit = lt >= t0
        ink(ctx, rrect(130, y - 42, 100, 84, 16), hexc("#F2B800") if lit else hexc("#FFFFFF"), 5)
        label(ctx, L1, 180, y, 66, DARK)
        if lit:
            n = min(len(rest), int((lt - t0) / 0.035) + 1)
            label(ctx, rest[:n], 250, y, 54, DARK, anchor="l"); sfx_once(lt, t0, "pop")
    if lt > tf - 0.1:
        pop(ctx, lt, tf - 0.1, 300, 740, lambda c: portrait(c, 0, 0, "AUFRECHT", 0.8))
        pop(ctx, lt, tf + 0.05, 520, 740, lambda c: portrait(c, 0, 0, "MELCHER", 0.8))
        tt = wt(b, "town")
        pop(ctx, lt, tt, 830, 830, lambda c: town(c, 0, 0, 0.9))
        pop(ctx, lt, tt + 0.1, 830, 600, lambda c: tag(c, "GROSSASPACH", "yellow", 34, 0.04), sound=None)
        if lt > wt(b, "born"):
            pin_y = 640 + (1 - ease_out_back(min(1, (lt - wt(b, "born")) / 0.35))) * -100
            ink(ctx, bez((830, pin_y + 60), (800, pin_y + 20), (808, pin_y - 12), (830, pin_y - 12), 12) +
                bez((830, pin_y - 12), (852, pin_y - 12), (860, pin_y + 20), (830, pin_y + 60), 12), hexc("#D7182A"), 4)
            sfx_once(lt, wt(b, "born"), "pop")


def scene2(ctx, lt):          # Mercedes' performance division
    b = 2
    kerb(ctx, 885)
    car_in(ctx, lt, -0.2, "sports", 150, 875, 780, GREEN_, rs=True, rims="black")
    speed_lines(ctx, 150, 875, 780, 260, 0.8, seed=int(lt * 6))
    pop(ctx, lt, 0.0, W / 2, 360, lambda c: chip(c, 0, 0, "AMG", "dark", 80))
    pop(ctx, lt, wt(b, "Performance"), W / 2, 480, lambda c: tag(c, "MERCEDES PERFORMANCE DIVISION", "yellow", 34), sound=None)


def scene3(ctx, lt):          # full AMG: own engine, suspension, performance upgrades
    b = 3
    badge_row(ctx, W / 2, BADGE_Y, [("FULL AMG", "dark", -0.1)], lt, 60)
    car_in(ctx, lt, -0.1, "sedan", 130, 885, 820, BLACK_, rs=True, rims="black")
    tiles = [("OWN ENGINE", lambda c: engine_block(c, 0, -10, 0.45, "V8"), wt(b, "engine")),
             ("SUSPENSION", lambda c: spring(c, 0, -10, 0.75), wt(b, "suspension")),
             ("UPGRADES", lambda c: icon_bolt(c, 0, -10, 1.1), wt(b, "upgrades"))]
    for i, (txt, ic, t0) in enumerate(tiles):
        def draw(c, txt=txt, ic=ic):
            ink(c, rrect(-150, -95, 300, 200, 26), hexc("#FFFFFF", 0.95), 5)
            ic(c); label(c, txt, 0, 72, 30, DARK)
        pop(ctx, lt, t0 - 0.15, 200 + i * 340, 470, draw)


def scene4(ctx, lt):          # myth: AMG Line is just a sporty trim, no extra power
    b = 4
    badge_row(ctx, W / 2, BADGE_Y, [("AMG LINE", "chrome", -0.1), ("= JUST A TRIM", "white", wt(b, "trim"))], lt, 56)
    morph(ctx, lt, wt(b, "sporty") - 0.3, ("sedan", SILVER, dict(rims="silver")), ("sedan", SILVER, dict(sline=True, rims="dark")), 120, 880, 840, 0.5)
    tw, tb = wt(b, "wheels"), wt(b, "bumpers")
    if lt > tw:
        for wx in (0.175, 0.81):
            ctx.new_sub_path(); ctx.arc(120 + wx * 840, 880 - 0.075 * 840, 0.075 * 840 * 1.35, 0, 2 * math.pi * ease_out((lt - tw) / 0.35))
            ctx.set_source_rgba(*YELLOW); ctx.set_line_width(9); ctx.stroke()
    pop(ctx, lt, tw, 300, 420, lambda c: tag(c, "BIGGER WHEELS", "yellow", 38, -0.04), sound=None)
    pop(ctx, lt, tb, 780, 420, lambda c: tag(c, "AGGRESSIVE BUMPERS", "yellow", 32, 0.04), sound=None)
    pop(ctx, lt, wt(b, "no"), W / 2, 560, lambda c: stamp(c, "NO EXTRA POWER", "#D7182A", 62, -0.06), sound="stamp")


def scene5(ctx, lt):          # the number = performance level: 35 / 43 / 53 / 63
    b = 5
    pop(ctx, lt, -0.1, W / 2, 250, lambda c: chip(c, 0, 0, "THE NUMBER = PERFORMANCE LEVEL", "dark", 40))
    steps = [("35", wt(b, "35"), 140, "ENTRY"), ("43", wt(b, "43"), 230, ""), ("53", wt(b, "53"), 330, "MORE"), ("63", wt(b, "63"), 450, "TOP")]
    for i, (n, t0, h, txt) in enumerate(steps):
        x0 = 120 + i * 220
        if lt < t0:
            ink(ctx, rrect(x0, 900 - h, 190, h, 14), hexc("#E4E6EA"), 4, hexc("#B9BDC4"))
            continue
        p = max(0.02, ease_out_back(min(1, (lt - t0) / 0.4)))
        hh = h * p
        ink(ctx, rrect(x0, 900 - hh, 190, hh, 14), hexc("#F2B800") if n == "63" else hexc("#FFFFFF"), 5)
        chip(ctx, x0 + 95, 900 - hh - 50, n, "red" if n == "63" else "chrome", 54)
        if txt:
            label(ctx, txt, x0 + 95, 900 - hh / 2, 34, DARK)
        sfx_once(lt, t0, "pop")


def scene6(ctx, lt):          # numbers don't tell engine size: a 63 can be a V8 or a plug-in hybrid
    b = 6
    td, tv, tp = wt(b, "dont"), wt(b, "V8"), wt(b, "plug-in")
    pop(ctx, lt, -0.1, W / 2, 260, lambda c: chip(c, 0, 0, "63", "red", 80))
    pop(ctx, lt, -0.05, W / 2, 440, lambda c: engine_block(c, 0, 0, 0.8, "6.3 L ?"))
    if lt > td:
        cross(ctx, W / 2, 440, 100, 14); sfx_once(lt, td, "stamp")
        pop(ctx, lt, td, W / 2, 590, lambda c: tag(c, "NOT ENGINE SIZE", "red", 38), sound=None)
    pop(ctx, lt, tv, 280, 790, lambda c: engine_block(c, 0, 0, 0.7, "V8"))
    pop(ctx, lt, tv + 0.1, 280, 900, lambda c: tag(c, "V8", "dark", 34), sound=None)
    pop(ctx, lt, tp, 790, 790, lambda c: chassis(c, 0, 0, lt, 0.45, petrol=1, battery=1, motor=1, charge=1))
    pop(ctx, lt, tp + 0.1, 790, 900, lambda c: tag(c, "PLUG-IN HYBRID", "green", 32), sound=None)


def scene7(ctx, lt):          # 55: powerful V8 models like the AMG GT
    b = 7
    badge_row(ctx, W / 2, BADGE_Y, [("55", "chrome", wt(b, "55") - 0.1)], lt, 76)
    kerb(ctx, 885)
    car_in(ctx, lt, -0.2, "sports", 150, 875, 780, "#E8E8E2", rs=True, rims="black")
    tv = wt(b, "V8")
    pop(ctx, lt, tv, 300, 430, lambda c: tag(c, "POWERFUL V8", "dark", 42, -0.04))
    if lt > tv:
        sound_waves(ctx, 130, 820, lt); sfx_once(lt, tv, "rumble")
    pop(ctx, lt, wt(b, "GT"), 790, 430, lambda c: chip(c, 0, 0, "AMG GT", "red", 50))


def scene8(ctx, lt):          # S sharper; E PERFORMANCE high-performance plug-in hybrid
    b = 8
    ts, te = wt(b, "S"), wt(b, "E")
    badge_row(ctx, W / 2, BADGE_Y, [("S", "red", ts - 0.1), ("E PERFORMANCE", "green", te)], lt, 58)
    if lt < te - 0.3:
        morph(ctx, lt, wt(b, "sharper") - 0.3, ("suv", BLUE_, dict(rims="dark")), ("suv", BLUE_, dict(rs=True, rims="black", calipers="#D7182A")), 140, 880, 800, 0.5)
        pop(ctx, lt, wt(b, "sharper"), 300, 420, lambda c: tag(c, "EVEN SHARPER", "red", 42, -0.04))
    else:
        chassis(ctx, W / 2 - 60, 600, lt, 0.9, petrol=1, battery=1, motor=1, charge=1 if lt > wt(b, "plug-in") else 0)
        if lt > wt(b, "plug-in"):
            outlet(ctx, 990, 600); line(ctx, qbez((W / 2 - 30, 600), (760, 760), (970, 620), 20), 9, DARK)
        pop(ctx, lt, wt(b, "high-performance"), W / 2, 850, lambda c: tag(c, "HIGH-PERFORMANCE PLUG-IN HYBRID", "green", 32), sound=None)


def scene9(ctx, lt):          # 4MATIC+ all-wheel drive
    b = 9
    badge_row(ctx, W / 2, BADGE_Y, [("4MATIC+", "chrome", -0.1)], lt, 70)
    ta = wt(b, "all-wheel")
    chassis(ctx, W / 2, 600, lt, 1.0, petrol=1, awd=ease((lt - ta) / 0.4) if lt > ta else 0)
    pop(ctx, lt, ta, W / 2, 860, lambda c: tag(c, "ALL-WHEEL DRIVE", "yellow", 42), sound=None)


def scene10(ctx, lt):         # GT = sports car family; G 63 = high-performance G-Class
    b = 10
    tg, tg63 = wt(b, "GT"), wt(b, "G63")
    badge_row(ctx, W / 2, BADGE_Y, [("GT", "chrome", tg - 0.1), ("G 63", "red", tg63)], lt, 64)
    slot(ctx, lt, tg, "sports", 40, 560, 620, GREEN_, early=True, rs=True, rims="black")
    pop(ctx, lt, wt(b, "family"), 860, 390, lambda c: tag(c, "SPORTS CAR FAMILY", "yellow", 30, 0.04))
    rocks(ctx, 820, 885, 1.0)
    slot(ctx, lt, tg63, "boxy", 60, 885, 560, BLACK_, rs=True, rims="black")
    pop(ctx, lt, wt(b, "G-Class"), 860, 640, lambda c: tag(c, "FAST G-CLASS", "red", 34, -0.04))


def scene11(ctx, lt):         # ENDING: decode the hook badge
    b = 11
    car_in(ctx, lt, -0.1, "suv", 160, 885, 760, BLUE_, rs=True, rims="black", sound=False)
    rows = [("GLC = PERFORMANCE SUV", wt(b, "SUV")), ("63 = TOP-TIER AMG", wt(b, "AMG", 1)),
            ("S = EXTRA POWERFUL", wt(b, "S-version")), ("E PERFORMANCE = PLUG-IN HYBRID", wt(b, "hybrid")),
            ("4MATIC+ = ALL-WHEEL DRIVE", wt(b, "drive"))]
    lit = [1 if lt > rows[i][1] else 0.25 for i in (1, 2, 3, 4)]
    hook_row(ctx, lt, W / 2, 236, 48, show_q=False, lit=lit)
    p = ease_out_back(min(1, lt / 0.4))
    ctx.save(); ctx.translate(W / 2, 470); ctx.scale(max(0.02, p), max(0.02, p))
    ink(ctx, rrect(-460, -185, 920, 370, 26), hexc("#FFF6D6"), 6)
    for i, (txt, t0) in enumerate(rows):
        y = -136 + i * 68
        label(ctx, txt, -425, y, 32, hexc("#1D1E22", 1 if lt > t0 else 0.3), font=MONO, anchor="l")
        if lt > t0:
            check(ctx, 410, y, 1.0); sfx_once(lt, t0, "pop")
        else:
            ink(ctx, ellipse(410, y, 24, 24, 24), hexc("#E4E6EA"), 4)
    ctx.restore()


def scene12(ctx, lt):         # follow me
    b = 12
    tf = wt(b, "follow")
    car_in(ctx, lt, 0.0, "suv", 160, 885, 760, BLUE_, rs=True, rims="black", sound=False)
    hook_row(ctx, lt, W / 2, 236, 48, show_q=False)
    if lt >= tf - 0.3:
        p = max(0.02, ease_out_back((lt - tf + 0.3) / 0.45))
        sfx_once(lt, tf - 0.3, "pop")
        ctx.save(); ctx.translate(W / 2, 480); ctx.scale(p, p)
        ink(ctx, rrect(-420, -170, 840, 340, 50), hexc("#FFFFFF", 0.95), 6)
        label(ctx, "FOLLOW FOR", 0, -80, 64, DARK)
        chip(ctx, 0, 30, NEXT, "red", 60)
        label(ctx, CTX["handle"], 0, 120, 40, hexc("#3A3D44"), font=MONO)
        ctx.restore()


SCENES = [scene0, scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9, scene10, scene11, scene12]
