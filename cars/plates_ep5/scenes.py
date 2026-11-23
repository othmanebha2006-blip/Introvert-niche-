"""Episode 5: American license plates explained - storytelling version.

One HERO plate (Florida, ABC D12, sticker 08|27) stays on screen and is decoded piece by piece: the part being talked
about is lit, the rest is dimmed. Each idea is shown with a real object (road + car, US map with pins, number reels,
calendar, magnifier, birthday cake, front/rear cars, typing, rejection stamp, special plates, money jar, ✓ checklist).
Voice = the user's mp3 with pauses shortened (tools/tighten.py); presenter = the looped @Mecmation clip.
Plates are generic drawings (state name + made-up numbers), not copies of the real state designs."""
import json, os, math, random
from ink import *
from widgets import *

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = "PLATES DECODED · #5"
BRAND = "USA"
NEXT = "MORE DECODED"
CLIP = None          # no presenter clip for this voice -> looped @Mecmation clip

FIX = {}
SPLIT_AT = []
BEAT_OF_SENT = [0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 9, 10, 11]

KEYWORDS = {"LICENSE", "PLATE", "PLATES", "STATE", "CALIFORNIA", "TEXAS", "FLORIDA", "NEW", "YORK", "DESIGNS",
            "NUMBERING", "LETTERS", "NUMBERS", "SEQUENCE", "UK", "REGISTERED", "OLD", "STICKER", "CORNER", "EXPIRES",
            "BIRTH", "MONTH", "YEAR", "EXPIRATION", "TWO", "FRONT", "BACK", "REAR", "PERSONALIZED", "CHOOSE",
            "AVAILABLE", "APPROVED", "CAN'T", "ANYTHING", "REJECT", "OFFENSIVE", "OFFICIAL", "SPECIAL", "UNIVERSITIES",
            "MILITARY", "CHARITIES", "SPORTS", "TEAMS", "CAUSES", "AUGUST", "08-27", "2027", "FOLLOW", "STORY"}


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
    """global time of a word"""
    return CTX["wt"](beat, word, k) + CTX["beat_t"][beat]


W = 1080
GRASS, ROAD = hexc("#CFE0BE"), hexc("#E3E5E8")
HERO_NUM = "ABC D12"
HERO = dict(x=540, y=330, w=560)


# ================================================================ drawing helpers
def hero_plate(ctx, x, y, w, lit=None, number=HERO_NUM, cursor=False, sticker=("08", "27")):
    """The hero Florida plate. lit: dict part -> 0..1 (1 = lit, 0 = dimmed)."""
    lit = lit or {}
    h = w / 2
    L = lambda k: 0.22 + 0.78 * lit.get(k, 1.0)
    ctx.save(); ctx.translate(x, y)
    ctx.save(); ctx.translate(0, w * 0.015); path(ctx, rrect(-w / 2, -h / 2, w, h, w * 0.05)); ctx.set_source_rgba(0, 0, 0, 0.2); ctx.fill(); ctx.restore()
    ink(ctx, rrect(-w / 2, -h / 2, w, h, w * 0.05), None, max(2.5, w * 0.011),
        grad=lin_grad(0, -h / 2, 0, h / 2, [(0, hexc("#FFFFFF")), (1, hexc("#EFEBE2"))]))
    ink(ctx, rrect(-w / 2 + w * 0.025, -h / 2 + w * 0.025, w * 0.95, h - w * 0.05, w * 0.035), None, max(1, w * 0.004),
        hexc("#9AA0A8"), sketch=False)
    for sx in (-0.33, 0.33):
        ink(ctx, ellipse(sx * w, -h * 0.30, w * 0.012, w * 0.012, 12), hexc("#B8BDC4"), 0)
    label(ctx, "Florida", 0, -h * 0.30, w * 0.105, hexc("#1E7A3C", L("state")))
    label(ctx, number + ("_" if cursor else ""), 0, h * 0.07, w * 0.2, hexc("#1E7A3C", L("number")), font="Anton")
    label(ctx, "SUNSHINE STATE", 0, h * 0.37, w * 0.045, hexc("#1E7A3C", L("state")), font=MONO)
    if sticker:
        sw, sh = w * 0.16, h * 0.2
        sx0, sy0 = w / 2 - sw - w * 0.04, -h / 2 + w * 0.04
        ctx.save(); ctx.push_group()
        ink(ctx, rrect(sx0, sy0, sw, sh, max(2, w * 0.01)), hexc("#F2B800"), max(1.5, w * 0.005))
        label(ctx, f"{sticker[0]} {sticker[1]}", sx0 + sw / 2, sy0 + sh / 2, sh * 0.62, DARK, font="Anton")
        ctx.pop_group_to_source(); ctx.paint_with_alpha(L("sticker")); ctx.restore()
    ctx.restore()


def sticker_pos(x, y, w):
    h = w / 2
    sw, sh = w * 0.16, h * 0.2
    return x + w / 2 - sw / 2 - w * 0.04, y - h / 2 + w * 0.04 + sh / 2


def mini_plate(ctx, x, y, w, top, number, tc="#1D1E22", nc="#1D1E22", bg="#FFFFFF", band=None):
    h = w / 2
    ctx.save(); ctx.translate(x, y)
    ink(ctx, rrect(-w / 2, -h / 2, w, h, w * 0.05), hexc(bg), max(2.5, w * 0.012))
    if band:
        path(ctx, rrect(-w / 2 + w * 0.03, -h / 2 + w * 0.03, w * 0.94, h * 0.24, w * 0.02)); ctx.set_source_rgba(*hexc(band)); ctx.fill()
    label(ctx, top, 0, -h * 0.29, w * 0.105, hexc(tc))
    label(ctx, number, 0, h * 0.09, w * 0.2, hexc(nc), font="Anton")
    ctx.restore()


def road(ctx, horizon=540, ground=930):
    path(ctx, [(0, horizon), (W, horizon), (W, ground), (0, ground)]); ctx.set_source_rgba(*GRASS); ctx.fill()
    path(ctx, [(470, horizon), (610, horizon), (980, ground), (100, ground)]); ctx.set_source_rgba(*ROAD); ctx.fill()
    for side in (-1, 1):
        line(ctx, [(540 + side * 70, horizon), (540 + side * 440, ground)], 4, hexc("#FFFFFF"), sketch=False)
    for i in range(6):
        t0 = i / 6; t1 = t0 + 0.07
        y0 = horizon + (ground - horizon) * t0 ** 1.6; y1 = horizon + (ground - horizon) * t1 ** 1.6
        line(ctx, [(540, y0), (540, y1)], 3 + 8 * t0, hexc("#FFFFFF"), sketch=False)
    for side in (-1, 1):       # little posts
        for i in range(4):
            t = 0.15 + i * 0.25
            px = 540 + side * (90 + 520 * t); py = horizon + (ground - horizon) * t
            line(ctx, [(px, py), (px, py - 14 - 26 * t)], 3 + 3 * t, hexc("#FFFFFF"), sketch=False)


def car_view(ctx, x, y, w, front=False, paint="#4A5563", plate_fn=None, plate_alpha=1.0):
    """front or rear view of a car standing at ground y. plate_fn(ctx, px, py, pw) draws its plate."""
    h = w * 0.62
    for sx in (-0.36, 0.36):
        ink(ctx, rrect(x + sx * w - w * 0.08, y - h * 0.22, w * 0.16, h * 0.22, 10), hexc("#1B1C1F"), 4)
    body = rpoly([(x - w / 2, y - h * 0.18), (x + w / 2, y - h * 0.18), (x + w / 2, y - h * 0.55), (x + w * 0.34, y - h * 0.63),
                  (x + w * 0.26, y - h), (x - w * 0.26, y - h), (x - w * 0.34, y - h * 0.63), (x - w / 2, y - h * 0.55)],
                 [w * 0.06, w * 0.06, w * 0.05, w * 0.03, w * 0.07, w * 0.07, w * 0.03, w * 0.05])
    ink(ctx, body, None, 5, grad=lin_grad(0, y - h, 0, y, [(0, shade(hexc(paint), 0.25)), (0.6, hexc(paint)), (1, shade(hexc(paint), -0.3))]))
    ink(ctx, rpoly([(x - w * 0.29, y - h * 0.65), (x + w * 0.29, y - h * 0.65), (x + w * 0.22, y - h * 0.94), (x - w * 0.22, y - h * 0.94)], 8),
        None, 4, grad=lin_grad(0, y - h, 0, y - h * 0.6, [(0, hexc("#5C6F86")), (1, hexc("#1A2230"))]))
    for sx in (-1, 1):
        ink(ctx, rrect(x + sx * w * 0.37 - w * 0.075, y - h * 0.52, w * 0.15, h * 0.1, 8), hexc("#DDE9F5" if front else "#C8102E"), 3)
    if front:
        ink(ctx, rrect(x - w * 0.2, y - h * 0.52, w * 0.4, h * 0.12, 8), hexc("#1B1C1F"), 3)
    pw = w * 0.3
    px, py = x, y - h * 0.31
    if plate_fn and plate_alpha > 0:
        ctx.push_group(); plate_fn(ctx, px, py, pw); ctx.pop_group_to_source(); ctx.paint_with_alpha(plate_alpha)
    elif not plate_fn:
        ink(ctx, rrect(px - pw / 2, py - pw / 4, pw, pw / 2, 6), None, 3, hexc("#8C9199"))
    return px, py, pw


def calendar(ctx, x, y, s, month, year=None, flip=0.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, rrect(-110, -100, 220, 220, 18), hexc("#FFFFFF"), 6)
    ink(ctx, rrect(-110, -100, 220, 56, 18), hexc("#E04848"), 6)
    for rx in (-60, 60):
        ink(ctx, rrect(rx - 8, -126, 16, 46, 8), hexc("#B9BDC4"), 4)
    label(ctx, month, 0, 12, 40 if len(month) > 5 else 56, DARK)
    if year:
        label(ctx, year, 0, 72, 46, hexc("#F2B800"), DARK, 8)
    if flip > 0:
        ctx.save(); ctx.translate(0, -44); ctx.scale(1, max(0.02, 1 - flip))
        ink(ctx, rrect(-110, 0, 220, 164, 10), hexc("#FFFFFF"), 5); ctx.restore()
    ctx.restore()


def magnifier(ctx, x, y, r):
    line(ctx, [(x + r * 0.7, y + r * 0.7), (x + r * 1.6, y + r * 1.6)], r * 0.32, hexc("#6B4A2B"))
    ink(ctx, ellipse(x, y, r, r, 40), (1, 1, 1, 0.18), r * 0.16, hexc("#2A2D33"))
    line(ctx, ellipse(x, y, r * 0.75, r * 0.75, 12, 3.6, 4.4), r * 0.07, (1, 1, 1, 0.8))


def cake(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, rrect(-80, -10, 160, 70, 12), hexc("#F6C1CF"), 5)
    ink(ctx, rrect(-90, 50, 180, 20, 8), hexc("#FFFFFF"), 5)
    line(ctx, [(-80, 12), (-40, 24), (0, 10), (40, 24), (80, 12)], 6, hexc("#FFFFFF"))
    ink(ctx, rrect(-7, -60, 14, 50, 4), hexc("#7FB2FF"), 4)
    ink(ctx, [(0, -92), (10, -72), (0, -62), (-10, -72)], hexc("#F2B800"), 3)
    ctx.restore()


def emoji_blush(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, ellipse(0, 0, 56, 56, 40), hexc("#FFD34D"), 5)
    for sx in (-1, 1):
        line(ctx, qbez((sx * 30, -6), (sx * 20, -18), (sx * 10, -6), 8), 5)
        ink(ctx, ellipse(sx * 30, 14, 14, 8, 16), hexc("#F28C9C"), 0)
    ink(ctx, ellipse(0, 26, 8, 10, 16), hexc("#8A3A2A"), 3)
    ctx.restore()


def check(ctx, x, y, s=1.0):
    ink(ctx, ellipse(x, y, 26 * s, 26 * s, 30), hexc("#2E9E5B"), 4)
    line(ctx, [(x - 12 * s, y), (x - 3 * s, y + 10 * s), (x + 13 * s, y - 10 * s)], 6 * s, hexc("#FFFFFF"))


def rubber_stamp(ctx, x, y, s, p):
    """the stamp comes down (p 0..1) and leaves REJECTED"""
    drop = (1 - ease_out(min(1, p * 2))) * 160
    ctx.save(); ctx.translate(x, y - drop)
    ink(ctx, rrect(-70 * s, -150 * s, 140 * s, 70 * s, 14), hexc("#8B5A2B"), 5)
    ink(ctx, rrect(-26 * s, -200 * s, 52 * s, 60 * s, 12), hexc("#6B4A2B"), 5)
    ink(ctx, rrect(-90 * s, -84 * s, 180 * s, 30 * s, 8), hexc("#D7182A"), 5)
    ctx.restore()


# US outline (lat, lon), simplified
US = [(48.4, -124.7), (46.2, -124.0), (42.0, -124.2), (40.4, -124.4), (38.0, -122.9), (36.6, -121.9), (34.5, -120.6),
      (34.0, -118.5), (32.5, -117.1), (32.7, -114.7), (31.3, -111.0), (31.3, -108.2), (31.8, -106.5), (29.6, -104.5),
      (29.8, -101.4), (27.5, -99.5), (25.9, -97.2), (27.8, -97.3), (29.4, -94.7), (29.7, -93.8), (29.1, -90.9),
      (29.0, -89.2), (30.2, -88.0), (30.4, -86.5), (29.7, -84.9), (29.1, -83.1), (27.8, -82.7), (26.5, -82.0),
      (25.1, -81.1), (25.3, -80.3), (27.0, -80.1), (29.0, -80.9), (30.7, -81.4), (32.0, -80.8), (33.8, -78.5),
      (35.2, -75.5), (36.9, -76.0), (38.9, -74.9), (40.5, -74.0), (41.2, -72.0), (41.6, -70.0), (42.8, -70.8),
      (43.9, -69.0), (44.8, -67.0), (47.3, -68.3), (45.3, -71.1), (45.0, -74.7), (43.6, -76.5), (43.2, -79.1),
      (42.0, -80.5), (41.7, -83.5), (43.5, -82.4), (45.8, -83.5), (46.5, -84.5), (46.7, -90.0), (48.0, -89.5),
      (49.0, -95.2), (49.0, -123.1)]


def proj(lat, lon, cx=540, cy=705, k=16.0):
    return (cx + (lon + 96.0) * k * math.cos(math.radians(38)), cy - (lat - 37.5) * k)


PINS = {"California": (36.7, -119.5), "Texas": (31.0, -99.0), "Florida": (28.3, -81.7), "New": (42.9, -75.3)}


def us_map(ctx, lit=None):
    pts = [proj(a, b) for a, b in US]
    ink(ctx, rpoly(pts, 4), hexc("#BFD8B0"), 5, hexc("#5E7A63"))
    if lit:
        for st, a in lit.items():
            if a > 0:
                ctx.set_source(rad_grad(*proj(*PINS[st]), 5, 90, [(0, (1, 0.82, 0.2, 0.55 * a)), (1, (1, 0.82, 0.2, 0))]))
                ctx.arc(*proj(*PINS[st]), 90, 0, 2 * math.pi); ctx.fill()


def pin(ctx, x, y, p, col="#D7182A"):
    if p <= 0:
        return
    dy = (1 - ease_out_back(min(1, p))) * -120
    ctx.save(); ctx.translate(x, y + dy)
    ink(ctx, bez((0, 0), (-40, -40), (-28, -78), (0, -78), 12) + bez((0, -78), (28, -78), (40, -40), (0, 0), 12), hexc(col), 4)
    ink(ctx, ellipse(0, -52, 11, 11, 16), hexc("#FFFFFF"), 0)
    ctx.restore()


# ================================================================ the hero plate layer (drawn over every scene)
def hero(ctx, t):
    B = CTX["beat_t"]
    t_fly = gw(0, "state") - 0.45
    if t < t_fly:
        return                                   # still on the car (scene 0 draws it)
    # visibility: hidden while big close-ups need the space
    hidden = [(B[4], B[6]), (B[8], B[10]), (gw(11, "follow") - 0.3, 999)]
    vis = 1.0
    for a, b in hidden:
        if a - 0.25 <= t <= b:
            vis = min(vis, 1 - ease((t - (a - 0.25)) / 0.25))
        if b < t < b + 0.3:
            vis = min(vis, ease((t - b) / 0.3))
    if vis <= 0.01:
        return
    x, y, w = HERO["x"], HERO["y"] - (1 - vis) * 260, HERO["w"]
    k = (t - t_fly) / 0.6
    if k < 1:                                    # fly up from the car
        q = ease(k)
        x0, y0, w0 = CTX["car_plate"]
        x, y, w = x0 + (x - x0) * q, y0 + (y - y0) * q, w0 + (w - w0) * q
        if 0 <= t - t_fly < 1 / 30:
            widgets.SFX.append((t, "whoosh"))
    lit = dict(state=1, number=1, sticker=1)
    number, cursor = HERO_NUM, False
    if t < B[2]:
        lit = dict(state=1, number=0, sticker=0)
    elif t < B[3]:
        lit = dict(state=0, number=1, sticker=0)
    elif t < B[4]:
        lit = dict(state=0, number=1, sticker=0) if t < gw(3, "sticker") - 0.2 else dict(state=0, number=0, sticker=1)
    elif B[7] <= t < B[8]:
        tc = gw(7, "choose")
        if t >= tc:
            msg = "MECMATN"
            n = min(len(msg), int((t - tc) / 0.13) + 1)
            number, cursor = msg[:n], n < len(msg) and int(t * 4) % 2 == 0
        lit = dict(state=0.3, number=1, sticker=0.3)
    elif B[10] <= t:
        tf, ts = gw(10, "Florida"), gw(10, "sticker")
        if t < tf:
            lit = dict(state=1, number=1, sticker=1)
        elif t < ts:
            lit = dict(state=1, number=0, sticker=0)
        else:
            lit = dict(state=0, number=0, sticker=1)
    ctx.save(); ctx.push_group()
    hero_plate(ctx, x, y, w, lit, number, cursor)
    ctx.pop_group_to_source(); ctx.paint_with_alpha(vis); ctx.restore()


import widgets


# ================================================================ scenes (content below the hero plate)
def scene0(ctx, lt):          # the car, the plate, then the state name
    road(ctx)
    t_fly = wt(0, "state") - 0.45
    def pl(c, px, py, pw):
        hero_plate(c, px, py, pw, dict(state=1, number=1, sticker=1))
    px, py, pw = car_view(ctx, 540, 900, 560, front=False, plate_fn=pl if lt < t_fly else None)
    CTX["car_plate"] = (px, py, pw)
    if lt < t_fly:            # attention rings on the plate
        for i in range(3):
            ph = (lt * 0.9 + i / 3) % 1
            ctx.new_sub_path(); ctx.arc(px, py, 40 + ph * 260, 0, 2 * math.pi)
            ctx.set_source_rgba(0.85, 0.65, 0.1, 0.7 * (1 - ph)); ctx.set_line_width(5); ctx.stroke()


def scene1(ctx, lt):          # map with pins: California, Texas, Florida, New York
    b = 1
    lit = {}
    for st in PINS:
        t0 = wt(b, st)
        lit[st] = ease((lt - t0) / 0.3) if lt > t0 else 0
    us_map(ctx, lit)
    minis = {"California": ("California", "8ABC234", "#C8102E", "#1E2A6E", "#FFFFFF", None, (130, 545)),
             "Texas": ("TEXAS", "ABC-1234", "#1D1E22", "#1D1E22", "#FFFFFF", None, (250, 860)),
             "Florida": ("Florida", "ABC D12", "#1E7A3C", "#1E7A3C", "#FFFFFF", None, (880, 860)),
             "New": ("NEW YORK", "ABC-1234", "#FFFFFF", "#1E2A6E", "#F7D36A", "#1E2A6E", (950, 545))}
    for st, (top, num, tc, nc, bg, band, (mx, my)) in minis.items():
        t0 = wt(b, st)
        x, y = proj(*PINS[st])
        if lt > t0 + 0.15:          # leader line from the pin to its plate
            q = ease_out((lt - t0 - 0.15) / 0.3)
            line(ctx, [(x, y - 40), (x + (mx - x) * q, y - 40 + (my - y + 40) * q)], 4, hexc("#2A2D33", 0.6))
        pin(ctx, x, y, (lt - t0) / 0.35 if lt > t0 else 0)
        sfx_once(lt, t0, "pop")
        pop(ctx, lt, t0 + 0.15, mx, my, lambda c, a=(top, num, tc, nc, bg, band): mini_plate(c, 0, 0, 180, *a), sound=None)
    pop(ctx, lt, wt(b, "designs"), W / 2, 545, lambda c: tag(c, "OWN DESIGN + OWN NUMBERS", "yellow", 30), sound=None)


def scene2(ctx, lt):          # number reels: assigned by the state, in sequence
    b = 2
    chars = list(HERO_NUM)
    alpha = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
    t_start, t_end = wt(b, "letters") - 0.1, wt(b, "sequence")
    x0 = W / 2 - (len(chars) * 112) / 2 + 56
    for i, ch in enumerate(chars):
        x = x0 + i * 112
        if ch == " ":
            continue
        stop = t_start + 0.6 + (t_end - t_start - 0.6) * i / (len(chars) - 1)
        ink(ctx, rrect(x - 48, 570, 96, 150, 16), hexc("#FFFFFF"), 5)
        ctx.save(); path(ctx, rrect(x - 48, 570, 96, 150, 16)); ctx.clip()
        if lt < stop and lt > t_start:
            off = ((lt * 18 + i * 0.37) % 1) * 110
            for k in range(-1, 3):
                c = alpha[(int(lt * 18) + k + i * 5) % len(alpha)]
                label(ctx, c, x, 645 - off + k * 110 - 110, 96, hexc("#9AA0A8"), font="Anton")
        else:
            p = min(1, (lt - stop) / 0.15) if lt > stop else 1
            label(ctx, ch, x, 645 + (1 - ease_out_back(p)) * 30, 100, hexc("#1E7A3C"), font="Anton")
        ctx.restore()
        sfx_once(lt, stop, "pop")
        # reel shading
        path(ctx, rrect(x - 48, 570, 96, 40, 16)); ctx.set_source_rgba(0, 0, 0, 0.08); ctx.fill()
    pop(ctx, lt, wt(b, "assigned"), W / 2, 515, lambda c: tag(c, "ASSIGNED BY THE STATE", "dark", 34), sound=None)
    ts = wt(b, "sequence")
    if lt > ts:
        for i, s in enumerate(["D10", "D11", "D12"]):
            pop(ctx, lt, ts + i * 0.18, 300 + i * 240, 800, lambda c, s=s, i=i: chip(c, 0, 0, s, "yellow" if i == 2 else "white", 48), sound=None)
            if i:
                pop(ctx, lt, ts + i * 0.18, 180 + i * 240, 800, lambda c: arrow(c, [(-30, 0), (30, 0)], 8, DARK, 20), sound=None)


def scene3(ctx, lt):          # UK plates show age, US numbers don't. Then the sticker in the corner.
    b = 3
    tuk, tno, tst = wt(b, "UK"), wt(b, "dont"), wt(b, "sticker")
    if lt < tst - 0.4:
        # UK: plate + calendar 2012 + tick
        pop(ctx, lt, 0.0, 300, 590, lambda c: (ink(c, rrect(-190, -42, 380, 84, 12), hexc("#F7D417"), 5),
                                                    label(c, "AB12 CDE", 0, 3, 62, DARK, font="Anton")))
        pop(ctx, lt, tuk + 0.3, 300, 750, lambda c: calendar(c, 0, 0, 0.75, "MARCH", "2012"))
        pop(ctx, lt, 0.1, 140, 520, lambda c: chip(c, 0, 0, "UK", "white", 40), sound=None)
        if lt > tuk + 0.6:
            check(ctx, 440, 650, 1.4)
        # USA: the number gives nothing away
        pop(ctx, lt, tno - 0.1, 940, 520, lambda c: chip(c, 0, 0, "USA", "red", 40), sound=None)
        pop(ctx, lt, tno, 780, 700, lambda c: (ink(c, ellipse(0, 0, 110, 110, 40), hexc("#FFFFFF"), 6), label(c, "?", 0, 10, 160, RED)))
        pop(ctx, lt, wt(b, "old"), 780, 860, lambda c: tag(c, "NO AGE IN THE NUMBER", "dark", 32), sound=None)
    else:
        # magnifier travels to the sticker on the hero plate
        sx, sy = sticker_pos(HERO["x"], HERO["y"], HERO["w"])
        k = ease_out(min(1, (lt - tst + 0.4) / 0.6))
        mx, my = 300 + (sx - 300) * k, 700 + (sy - 700) * k
        magnifier(ctx, mx, my, 70 + 20 * k)
        sfx_once(lt, tst - 0.4, "whoosh")
        pop(ctx, lt, wt(b, "corner"), 620, 620, lambda c: tag(c, "THE STICKER", "yellow", 50, -0.03))


def scene4(ctx, lt):          # the sticker shows when the registration expires
    b = 4
    p = max(0.02, ease_out_back(min(1, lt / 0.45)))
    ctx.save(); ctx.translate(W / 2, 430); ctx.scale(p, p)
    ink(ctx, rrect(-300, -150, 600, 300, 30), hexc("#F2B800"), 8)
    label(ctx, "08 27", 0, 10, 190, DARK, font="Anton")
    ctx.restore()
    te = wt(b, "expires")
    flip = ease((lt - te + 0.4) / 0.35) if lt > te - 0.4 else 0
    pop(ctx, lt, te - 0.6, W / 2, 760, lambda c: calendar(c, 0, 0, 0.85, "AUGUST" if flip >= 1 else "...", "2027" if flip >= 1 else None, flip=0 if flip >= 1 else flip))
    pop(ctx, lt, te, 860, 700, lambda c: tag(c, "EXPIRES", "red", 44, 0.05))


def scene5(ctx, lt):          # in Florida: owner's birth month + expiration year
    b = 5
    ink(ctx, rrect(W / 2 - 300, 280, 600, 300, 30), hexc("#F2B800"), 8)
    label(ctx, "08", W / 2 - 130, 440, 190, DARK, font="Anton")
    label(ctx, "27", W / 2 + 140, 440, 190, DARK, font="Anton")
    tbm, tey = wt(b, "birth"), wt(b, "expiration")
    if lt > tbm - 0.1:
        ctx.new_sub_path(); ctx.arc(W / 2 - 130, 440, 120, 0, 2 * math.pi * ease_out((lt - tbm + 0.1) / 0.4))
        ctx.set_source_rgba(*YELLOW[:3], 1); ctx.set_line_width(12); ctx.stroke()
        line(ctx, [(W / 2 - 130, 560), (W / 2 - 230, 650)], 6, DARK)
    if lt > tey - 0.1:
        ctx.new_sub_path(); ctx.arc(W / 2 + 140, 440, 120, 0, 2 * math.pi * ease_out((lt - tey + 0.1) / 0.4))
        ctx.set_source_rgba(*RED); ctx.set_line_width(12); ctx.stroke()
        line(ctx, [(W / 2 + 140, 560), (W / 2 + 240, 650)], 6, DARK)
    pop(ctx, lt, tbm, 290, 760, lambda c: cake(c, 0, 0, 1.0))
    pop(ctx, lt, tbm + 0.2, 290, 880, lambda c: tag(c, "BIRTH MONTH = AUGUST", "yellow", 30, -0.03), sound=None)
    pop(ctx, lt, tey, 800, 760, lambda c: calendar(c, 0, 0, 0.7, "YEAR", "2027"))
    pop(ctx, lt, tey + 0.2, 800, 890, lambda c: tag(c, "EXPIRES 2027", "red", 32, 0.03), sound=None)


def scene6(ctx, lt):          # two plates (front + back) or rear plate only
    b = 6
    road(ctx)
    to = wt(b, "others")
    fa = 1 - ease((lt - to - 0.2) / 0.3) if lt > to + 0.2 else 1
    def pl(c, px, py, pw):
        mini_plate(c, px, py, pw, "Florida", "ABC D12", "#1E7A3C", "#1E7A3C")
    pop(ctx, lt, -0.3, 290, 900, lambda c: car_view(c, 0, 0, 400, front=True, paint="#4A5563", plate_fn=pl, plate_alpha=fa))
    pop(ctx, lt, -0.2, 790, 900, lambda c: car_view(c, 0, 0, 400, front=False, paint="#4A5563", plate_fn=pl))
    pop(ctx, lt, wt(b, "front"), 290, 560, lambda c: chip(c, 0, 0, "FRONT", "yellow", 46))
    pop(ctx, lt, wt(b, "back"), 790, 560, lambda c: chip(c, 0, 0, "BACK", "yellow", 46))
    if lt > to + 0.2:
        cross(ctx, 290, 780, 60, 14); sfx_once(lt, to + 0.2, "pop")
        pop(ctx, lt, wt(b, "rear"), W / 2, 640, lambda c: tag(c, "SOME STATES: REAR ONLY", "red", 36), sound=None)


def scene7(ctx, lt):          # personalised: choose your own letters, if available + approved
    b = 7
    pop(ctx, lt, -0.2, W / 2, 540, lambda c: chip(c, 0, 0, "PERSONALIZED PLATE", "yellow", 52))
    rows = [("AVAILABLE", wt(b, "available")), ("APPROVED", wt(b, "approved"))]
    for i, (txt, t0) in enumerate(rows):
        y = 680 + i * 120
        ink(ctx, rrect(240, y - 45, 600, 90, 24), hexc("#FFFFFF", 0.92), 5)
        label(ctx, txt, 320, y, 52, DARK, anchor="l")
        if lt > t0:
            p = ease_out_back(min(1, (lt - t0) / 0.3))
            ctx.save(); ctx.translate(770, y); ctx.scale(max(0.02, p), max(0.02, p)); check(ctx, 0, 0, 1.4); ctx.restore()
            sfx_once(lt, t0, "pop")
        else:
            ink(ctx, ellipse(770, y, 36, 36, 30), hexc("#E4E6EA"), 4)


def scene8(ctx, lt):          # can't write anything: offensive or official-looking -> rejected
    b = 8
    to, tof, tr = wt(b, "offensive"), wt(b, "official"), wt(b, "reject")
    pop(ctx, lt, -0.2, W / 2, 230, lambda c: chip(c, 0, 0, "NOT EVERYTHING IS ALLOWED", "red", 46))
    # offensive plate, blurred then censored
    def bad(c):
        mini_plate(c, 0, 0, 440, "Florida", "BAD W0RD", "#1E7A3C", "#1E7A3C")
        if lt > to:
            path(c, rrect(-170, -10, 340, 80, 10)); c.set_source_rgba(0.08, 0.08, 0.1, 1); c.fill()
    pop(ctx, lt, 0.0, 300, 450, bad)
    if lt > to:
        pop(ctx, lt, to, 120, 560, lambda c: emoji_blush(c, 0, 0, 0.9))
        pop(ctx, lt, to + 0.1, 300, 610, lambda c: tag(c, "OFFENSIVE", "red", 38, -0.04), sound=None)
    pop(ctx, lt, 0.1, 780, 450, lambda c: mini_plate(c, 0, 0, 440, "Florida", "POLICE 1", "#1E7A3C", "#1E2A6E"))
    pop(ctx, lt, tof, 780, 610, lambda c: tag(c, "LOOKS OFFICIAL", "red", 36, 0.04), sound=None)
    for x, t0 in ((300, tr), (780, tof + 0.2)):
        if lt > t0 - 0.25:
            p = (lt - t0 + 0.25) / 0.5
            if p < 1:
                rubber_stamp(ctx, x, 470, 1.0, p)
            if p > 0.5:
                pop(ctx, lt, t0, x, 450, lambda c: stamp(c, "REJECTED", "#D7182A", 54, -0.1), sound="stamp")


SPECIAL = [("universities", "UNIVERSITY", "#5B2C83"), ("military", "MILITARY", "#3F5B3A"),
           ("charities", "CHARITY", "#D7182A"), ("sports", "SPORTS TEAM", "#E06A1E")]


def scene9(ctx, lt):          # special plates + they help fund causes
    b = 9
    pop(ctx, lt, -0.2, W / 2, 230, lambda c: chip(c, 0, 0, "SPECIAL PLATES", "yellow", 52))
    for i, (word, name, col) in enumerate(SPECIAL):
        t0 = wt(b, word)
        ang = (-0.24 + i * 0.16)
        x = 240 + i * 200; y = 520 + abs(i - 1.5) * 26
        if lt < t0:
            ctx.save(); ctx.translate(x, y); ctx.rotate(ang)
            ink(ctx, rrect(-150, -75, 300, 150, 18), hexc("#D9DCE1"), 5, hexc("#9EA3AB")); ctx.restore()
        def draw(c, name=name, col=col, ang=ang):
            c.rotate(ang)
            mini_plate(c, 0, 0, 300, name, "★ 123", "#FFFFFF", col, "#FFFFFF", band=col)
        pop(ctx, lt, t0, x, y, draw)
    tf = wt(b, "fund")
    if lt > tf - 0.2:
        jx, jy = 540, 800
        ink(ctx, rpoly([(jx - 90, jy - 110), (jx + 90, jy - 110), (jx + 100, jy + 90), (jx - 100, jy + 90)], 30), (0.85, 0.92, 1, 0.6), 6)
        for i in range(5):
            ph = (lt - tf) * 1.6 - i * 0.25
            if ph > 0:
                yy = min(jy + 60 - i * 22, jy - 260 + ph * 420)
                ink(ctx, ellipse(jx - 40 + (i % 3) * 40, yy, 30, 12, 20), hexc("#F2B800"), 4)
        label(ctx, "$", jx, jy - 20, 90, hexc("#2E9E5B"), DARK, 6)
        sfx_once(lt, tf - 0.2, "pop")
        pop(ctx, lt, wt(b, "causes"), 850, 760, lambda c: tag(c, "FUNDS GOOD CAUSES", "green", 32, 0.04), sound=None)


def scene10(ctx, lt):         # recap: checklist under the hero plate
    b = 10
    road(ctx)
    car_view(ctx, 540, 930, 520, front=False, plate_fn=lambda c, px, py, pw: hero_plate(c, px, py, pw))
    rows = [("FLORIDA = REGISTERED IN FLORIDA", wt(b, "registered")), ("08 27 = EXPIRES AUGUST 2027", wt(b, "August"))]
    p = ease_out_back(min(1, lt / 0.4))
    ctx.save(); ctx.translate(W / 2, 560); ctx.scale(max(0.02, p), max(0.02, p))
    ink(ctx, rrect(-420, -90, 840, 180, 24), hexc("#FFF6D6"), 6)
    for i, (txt, t0) in enumerate(rows):
        y = -42 + i * 84
        a = 1 if lt > t0 else 0.3
        label(ctx, txt, -390, y, 36, hexc("#1D1E22", a), font=MONO, anchor="l")
        if lt > t0:
            check(ctx, 370, y, 1.1); sfx_once(lt, t0, "pop")
        else:
            ink(ctx, ellipse(370, y, 26, 26, 24), hexc("#E4E6EA"), 4)
    ctx.restore()


def scene11(ctx, lt):         # follow me
    b = 11
    road(ctx)
    car_view(ctx, 540, 930, 520, front=False, plate_fn=lambda c, px, py, pw: hero_plate(c, px, py, pw))
    tf = wt(b, "follow")
    if lt >= tf - 0.3:
        p = max(0.02, ease_out_back((lt - tf + 0.3) / 0.45))
        sfx_once(lt, tf - 0.3, "pop")
        ctx.save(); ctx.translate(W / 2, 360); ctx.scale(p, p)
        ink(ctx, rrect(-420, -170, 840, 340, 50), hexc("#FFFFFF", 0.95), 6)
        label(ctx, "FOLLOW FOR", 0, -80, 64, DARK)
        chip(ctx, 0, 30, NEXT, "red", 60)
        label(ctx, CTX["handle"], 0, 120, 40, hexc("#3A3D44"), font=MONO)
        ctx.restore()


SCENES = [scene0, scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9, scene10, scene11]
