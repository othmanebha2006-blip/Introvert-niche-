"""Episode 5: American license plates explained. Timing data + 12 scenes (one per beat).
Voice = the user's mp3 with pauses shortened (tools/tighten.py); presenter = the looped @Mecmation clip.
Plates are generic drawings (state name + made-up numbers), not copies of the real state designs."""
import json, os, math
from ink import *
from car import draw_car
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


def car_in(*a, **k):
    return CTX["car_in"](*a, **k)


BADGE_Y = 222
W = 1080

# ---------------------------------------------------------------- plate drawing
STATES = {   # top text, top colour, number colour, background stops
    "CA": ("California", "#C8102E", "#1E2A6E", ["#FFFFFF", "#F1F3F6"]),
    "TX": ("TEXAS", "#1D1E22", "#1D1E22", ["#FFFFFF", "#E9ECEF"]),
    "FL": ("Florida", "#1E7A3C", "#1E7A3C", ["#FFFFFF", "#F4F1EA"]),
    "NY": ("NEW YORK", "#FFFFFF", "#1E2A6E", ["#F7D36A", "#EDB730"]),
}


def plate(ctx, x, y, w, state, number, sticker=None, ring=None, rot=0.0, top_text=None):
    """US plate (2:1) centred at x,y. sticker = (month, year). ring = 'state'|'number'|'sticker' highlight."""
    h = w / 2
    top, tc, nc, bg = STATES[state]
    top = top_text or top
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot)
    ctx.save(); ctx.translate(0, 8); path(ctx, rrect(-w / 2, -h / 2, w, h, w * 0.05)); ctx.set_source_rgba(0, 0, 0, 0.18); ctx.fill(); ctx.restore()
    ink(ctx, rrect(-w / 2, -h / 2, w, h, w * 0.05), None, w * 0.012, grad=lin_grad(0, -h / 2, 0, h / 2, [(0, hexc(bg[0])), (1, hexc(bg[1]))]))
    ink(ctx, rrect(-w / 2 + w * 0.025, -h / 2 + w * 0.025, w * 0.95, h - w * 0.05, w * 0.035), None, w * 0.004, hexc("#9AA0A8"), sketch=False)
    if state == "NY":
        path(ctx, rrect(-w / 2 + w * 0.03, -h / 2 + w * 0.03, w * 0.94, h * 0.22, w * 0.02)); ctx.set_source_rgba(*hexc("#1E2A6E")); ctx.fill()
    label(ctx, top, 0, -h * 0.30, w * 0.105, hexc(tc))
    label(ctx, number, 0, h * 0.07, w * 0.2, hexc(nc), font="Anton")
    for sx in (-0.33, 0.33):    # bolt holes
        ink(ctx, ellipse(sx * w, -h * 0.30, w * 0.012, w * 0.012, 12), hexc("#B8BDC4"), 0)
    if sticker:
        sw, sh = w * 0.16, h * 0.2
        sx0, sy0 = w / 2 - sw - w * 0.04, -h / 2 + w * 0.04
        ink(ctx, rrect(sx0, sy0, sw, sh, 6), hexc("#F2B800"), 3)
        label(ctx, f"{sticker[0]}  {sticker[1]}", sx0 + sw / 2, sy0 + sh / 2, sh * 0.62, DARK, font="Anton")
    if ring:
        r = {"state": (0, -h * 0.30, w * 0.36, h * 0.17), "number": (0, h * 0.07, w * 0.46, h * 0.28),
             "sticker": (w / 2 - w * 0.12, -h / 2 + w * 0.04 + h * 0.1, w * 0.13, h * 0.17)}[ring]
        ctx.save(); ctx.translate(r[0], r[1]); ctx.scale(r[2], r[3])
        ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgba(*YELLOW); ctx.set_line_width(9); ctx.stroke()
    ctx.restore()


def uk_plate(ctx, x, y, w, number):
    h = w / 4.7
    ctx.save(); ctx.translate(x, y)
    ink(ctx, rrect(-w / 2, -h / 2, w, h, 12), hexc("#F7D417"), w * 0.01)
    label(ctx, number, 0, 2, h * 0.72, DARK, font="Anton")
    ctx.restore()


def car_end(ctx, x, y, w, front=True, has_plate=True, paint="#5E6B78"):
    """simple front or rear view of a car, centred at x, ground y"""
    h = w * 0.62
    body = rpoly([(x - w / 2, y - h * 0.18), (x + w / 2, y - h * 0.18), (x + w / 2, y - h * 0.55), (x + w * 0.34, y - h * 0.62),
                  (x + w * 0.26, y - h), (x - w * 0.26, y - h), (x - w * 0.34, y - h * 0.62), (x - w / 2, y - h * 0.55)],
                 [w * 0.06, w * 0.06, w * 0.05, w * 0.03, w * 0.06, w * 0.06, w * 0.03, w * 0.05])
    for sx in (-0.36, 0.36):
        ink(ctx, rrect(x + sx * w - w * 0.08, y - h * 0.22, w * 0.16, h * 0.22, 10), hexc("#1B1C1F"), 4)
    ink(ctx, body, hexc(paint), 5)
    ink(ctx, rpoly([(x - w * 0.29, y - h * 0.64), (x + w * 0.29, y - h * 0.64), (x + w * 0.22, y - h * 0.93), (x - w * 0.22, y - h * 0.93)], 8),
        hexc("#2B3646"), 4)
    lc = "#DDE9F5" if front else "#C8102E"
    for sx in (-1, 1):
        ink(ctx, rrect(x + sx * w * 0.36 - w * 0.07, y - h * 0.5, w * 0.14, h * 0.1, 8), hexc(lc), 3)
    if front:
        ink(ctx, rrect(x - w * 0.2, y - h * 0.5, w * 0.4, h * 0.12, 8), hexc("#1B1C1F"), 3)
    if has_plate:
        plate(ctx, x, y - h * 0.3, w * 0.32, "TX", "ABC 1234")
    else:
        ink(ctx, rrect(x - w * 0.16, y - h * 0.38, w * 0.32, h * 0.16, 6), None, 3, hexc("#9AA0A8"))


def icon_cap(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, [(-50, -10), (0, -32), (50, -10), (0, 12)], DARK, 3)
    ink(ctx, rrect(-26, 0, 52, 26, 6), DARK, 3)
    line(ctx, [(40, -12), (44, 22)], 4, YELLOW)
    ctx.restore()


def icon_star(ctx, x, y, s=1.0, col="#1E2A6E"):
    pts = [(x + math.cos(-math.pi / 2 + i * math.pi / 5) * (40 if i % 2 == 0 else 17) * s,
            y + math.sin(-math.pi / 2 + i * math.pi / 5) * (40 if i % 2 == 0 else 17) * s) for i in range(10)]
    ink(ctx, pts, hexc(col), 4)


def icon_heart(ctx, x, y, s=1.0):
    pts = bez((x, y + 34 * s), (x - 60 * s, y - 6 * s), (x - 26 * s, y - 50 * s), (x, y - 18 * s), 14) + \
        bez((x, y - 18 * s), (x + 26 * s, y - 50 * s), (x + 60 * s, y - 6 * s), (x, y + 34 * s), 14)
    ink(ctx, pts, hexc("#D7182A"), 4)


def icon_ball(ctx, x, y, s=1.0):
    ink(ctx, ellipse(x, y, 36 * s, 36 * s, 30), hexc("#E06A1E"), 4)
    line(ctx, [(x - 36 * s, y), (x + 36 * s, y)], 3); line(ctx, [(x, y - 36 * s), (x, y + 36 * s)], 3)
    line(ctx, ellipse(x - 52 * s, y, 32 * s, 30 * s, 16, -0.9, 0.9), 3)
    line(ctx, ellipse(x + 52 * s, y, 32 * s, 30 * s, 16, math.pi - 0.9, math.pi + 0.9), 3)


def check(ctx, x, y, s=1.0):
    ink(ctx, ellipse(x, y, 34 * s, 34 * s, 30), hexc("#2E9E5B"), 4)
    line(ctx, [(x - 16 * s, y), (x - 4 * s, y + 13 * s), (x + 18 * s, y - 14 * s)], 8 * s, hexc("#FFFFFF"))


def plate_pop(ctx, lt, t0, x, y, w, *a, **k):
    pop(ctx, lt, t0, x, y, lambda c: plate(c, 0, 0, w, *a, **k))


# ---------------------------------------------------------------- scenes
def scene0(ctx, lt):          # every plate has a story; first look at the state name
    b = 0
    badge_row(ctx, W / 2, BADGE_Y, [("LICENSE PLATES", "yellow", -0.4)], lt, 62)
    p = max(0.02, ease_out_back(min(1, (lt + 0.4) / 0.5)))
    ts = wt(b, "state")
    ctx.save(); ctx.translate(W / 2, 600); ctx.scale(p, p)
    plate(ctx, 0, 0, 760, "CA", "8MEC123", ring="state" if lt > ts else None)
    ctx.restore()
    sfx_once(lt, ts, "pop")
    pop(ctx, lt, ts + 0.1, W / 2, 850, lambda c: tag(c, "STATE NAME", "yellow", 48), sound=None)


def scene1(ctx, lt):          # California, Texas, Florida, New York
    b = 1
    badge_row(ctx, W / 2, BADGE_Y, [("50 STATES", "white", 0.0)], lt, 62)
    items = [("CA", "8ABC234", "California", 290, 480), ("TX", "ABC-1234", "Texas", 790, 480),
             ("FL", "ABC D12", "Florida", 290, 760), ("NY", "ABC-1234", "New", 790, 760)]
    for st, num, word, x, y in items:
        t0 = wt(b, word)
        if lt < t0:      # outline waits for its word
            ink(ctx, rrect(x - 220, y - 110, 440, 220, 22), hexc("#D9DCE1"), 5, hexc("#9EA3AB"))
        plate_pop(ctx, lt, t0, x, y, 440, st, num)
    pop(ctx, lt, wt(b, "designs"), W / 2, 905, lambda c: tag(c, "OWN DESIGN + OWN NUMBERING", "yellow", 36), sound=None)


def scene2(ctx, lt):          # letters + numbers assigned by the state, in sequence
    b = 2
    badge_row(ctx, W / 2, BADGE_Y, [("ASSIGNED BY THE STATE", "white", 0.0)], lt, 56)
    ts = wt(b, "sequence")
    n = 1230 + max(0, int((lt - ts) * 6)) if lt > ts else 1234
    plate_pop(ctx, lt, -0.2, W / 2, 560, 700, "TX", f"ABC-{n}")
    pop(ctx, lt, wt(b, "letters"), 300, 820, lambda c: tag(c, "LETTERS", "yellow", 44, -0.04))
    pop(ctx, lt, wt(b, "numbers"), 780, 820, lambda c: tag(c, "NUMBERS", "yellow", 44, 0.04))
    if lt > ts:
        pop(ctx, lt, ts, W / 2, 380, lambda c: tag(c, "NEXT IN SEQUENCE", "dark", 40))


def scene3(ctx, lt):          # unlike the UK, no age in the number; look at the sticker
    b = 3
    tuk, tst = wt(b, "UK"), wt(b, "sticker")
    badge_row(ctx, W / 2, BADGE_Y, [("UK", "white", tuk), ("vs", "white", tuk + 0.2), ("USA", "red", tuk + 0.3)], lt, 56)
    if lt < tst - 0.3:
        pop(ctx, lt, tuk, W / 2, 420, lambda c: uk_plate(c, 0, 0, 620, "AB12 CDE"))
        if lt > tuk + 0.6:
            pop(ctx, lt, tuk + 0.6, 640, 330, lambda c: tag(c, "12 = AGE", "yellow", 36, 0.05), sound=None)
        plate_pop(ctx, lt, -0.2, W / 2, 700, 560, "TX", "ABC-1234")
        tr = wt(b, "registered")
        if lt > tr:
            pop(ctx, lt, tr, 880, 620, lambda c: (ink(c, ellipse(0, 0, 50, 50, 30), hexc("#FFFFFF"), 5), label(c, "?", 0, 4, 70, RED)))
            pop(ctx, lt, wt(b, "old"), 220, 860, lambda c: tag(c, "NO AGE INFO", "dark", 38, -0.03), sound=None)
    else:
        k = ease_out(min(1, (lt - tst + 0.3) / 0.6))
        ctx.save(); ctx.translate(W / 2, 600); s = 1 + 1.1 * k; ctx.scale(s, s); ctx.translate(-215 * k, 100 * k)   # sticker to centre
        plate(ctx, 0, 0, 560, "TX", "ABC-1234", sticker=("8", "27"), ring="sticker" if lt > wt(b, "corner") else None)
        ctx.restore()
        sfx_once(lt, tst - 0.3, "whoosh")


def scene4(ctx, lt):          # the sticker shows when the registration expires
    b = 4
    badge_row(ctx, W / 2, BADGE_Y, [("STICKER", "yellow", 0.0)], lt, 62)
    p = max(0.02, ease_out_back(min(1, lt / 0.4)))
    ctx.save(); ctx.translate(W / 2, 580); ctx.scale(p, p)
    ink(ctx, rrect(-300, -170, 600, 340, 30), hexc("#F2B800"), 8)
    label(ctx, "EXPIRES", 0, -100, 56, DARK)
    label(ctx, "8   27", 0, 40, 170, DARK, font="Anton")
    ctx.restore()
    pop(ctx, lt, wt(b, "expires"), W / 2, 860, lambda c: tag(c, "REGISTRATION EXPIRES", "dark", 40), sound=None)


def scene5(ctx, lt):          # Florida: birth month + expiration year
    b = 5
    badge_row(ctx, W / 2, BADGE_Y, [("FLORIDA", "white", 0.0)], lt, 62)
    ink(ctx, rrect(W / 2 - 300, 410, 600, 340, 30), hexc("#F2B800"), 8)
    label(ctx, "8", W / 2 - 130, 590, 190, DARK, font="Anton")
    label(ctx, "27", W / 2 + 140, 590, 190, DARK, font="Anton")
    tbm, tey = wt(b, "birth"), wt(b, "expiration")
    if lt > tbm:
        ctx.new_sub_path(); ctx.arc(W / 2 - 130, 590, 110, 0, 2 * math.pi * ease_out((lt - tbm) / 0.4)); ctx.set_source_rgba(*YELLOW); ctx.set_line_width(10); ctx.stroke()
    if lt > tey:
        ctx.new_sub_path(); ctx.arc(W / 2 + 140, 590, 120, 0, 2 * math.pi * ease_out((lt - tey) / 0.4)); ctx.set_source_rgba(*RED); ctx.set_line_width(10); ctx.stroke()
    pop(ctx, lt, tbm, W / 2 - 200, 850, lambda c: tag(c, "OWNER'S BIRTH MONTH", "yellow", 32, -0.03))
    pop(ctx, lt, tey, W / 2 + 230, 380, lambda c: tag(c, "EXPIRATION YEAR", "red", 34, 0.03))


def scene6(ctx, lt):          # two plates (front + back) or rear plate only
    b = 6
    badge_row(ctx, W / 2, BADGE_Y, [("FRONT + BACK", "white", 0.0), ("OR REAR ONLY", "red", wt(b, "others"))], lt, 52)
    tf, tb, to = wt(b, "front"), wt(b, "back"), wt(b, "others")
    pop(ctx, lt, -0.2, 290, 820, lambda c: car_end(c, 0, 0, 380, front=True, has_plate=lt < to))
    pop(ctx, lt, -0.1, 790, 820, lambda c: car_end(c, 0, 0, 380, front=False, has_plate=True))
    pop(ctx, lt, tf, 290, 470, lambda c: tag(c, "FRONT", "yellow", 44), sound=None)
    pop(ctx, lt, tb, 790, 470, lambda c: tag(c, "BACK", "yellow", 44), sound=None)
    if lt > to:
        cross(ctx, 290, 700, 70, 14)
        sfx_once(lt, to, "pop")


def scene7(ctx, lt):          # personalised plates: choose your own letters, if available + approved
    b = 7
    badge_row(ctx, W / 2, BADGE_Y, [("PERSONALIZED", "yellow", 0.0)], lt, 62)
    tc = wt(b, "choose")
    msg = "MECMATN"
    n = 0 if lt < tc else min(len(msg), int((lt - tc) / 0.14) + 1)
    txt = msg[:n] + ("_" if n < len(msg) and int(lt * 3) % 2 == 0 else "")
    plate_pop(ctx, lt, -0.2, W / 2, 560, 720, "CA", txt or " ")
    pop(ctx, lt, wt(b, "available"), 330, 850, lambda c: (check(c, -150, 0), tag(c, "AVAILABLE", "white", 40)))
    pop(ctx, lt, wt(b, "approved"), 760, 850, lambda c: (check(c, -140, 0), tag(c, "APPROVED", "white", 40)))


def scene8(ctx, lt):          # but you can't write anything: offensive / official-looking get rejected
    b = 8
    badge_row(ctx, W / 2, BADGE_Y, [("NOT ANYTHING", "red", 0.0)], lt, 62)
    to, tof = wt(b, "offensive"), wt(b, "official")
    plate_pop(ctx, lt, -0.2, 300, 520, 440, "CA", "#@!%&")
    plate_pop(ctx, lt, 0.0, 790, 520, 440, "CA", "POLICE")
    if lt > to:
        cross(ctx, 300, 520, 90, 14); sfx_once(lt, to, "stamp")
    if lt > tof:
        cross(ctx, 790, 520, 90, 14); sfx_once(lt, tof, "stamp")
    pop(ctx, lt, to, 300, 690, lambda c: tag(c, "OFFENSIVE", "red", 40, -0.04), sound=None)
    pop(ctx, lt, tof, 790, 690, lambda c: tag(c, "LOOKS OFFICIAL", "red", 36, 0.04), sound=None)
    pop(ctx, lt, wt(b, "reject"), W / 2, 810, lambda c: stamp(c, "REJECTED", "#D7182A", 64, -0.05), sound="stamp")


def scene9(ctx, lt):          # special plates: universities, military, charities, sports teams; fund causes
    b = 9
    badge_row(ctx, W / 2, BADGE_Y, [("SPECIAL PLATES", "yellow", 0.0)], lt, 60)
    items = [("universities", "UNIVERSITY", icon_cap, 290, 470), ("military", "MILITARY", icon_star, 790, 470),
             ("charities", "CHARITY", icon_heart, 290, 730), ("sports", "SPORTS TEAM", icon_ball, 790, 730)]
    for word, name, ic, x, y in items:
        t0 = wt(b, word)
        if lt < t0:
            ink(ctx, rrect(x - 210, y - 105, 420, 210, 22), hexc("#D9DCE1"), 5, hexc("#9EA3AB"))
        def draw(c, ic=ic, name=name):
            plate(c, 0, 0, 420, "TX", "", top_text=name)
            ic(c, 0, 30, 0.9)
        pop(ctx, lt, t0, x, y, draw)
    pop(ctx, lt, wt(b, "causes"), W / 2, 895, lambda c: tag(c, "$ HELPS FUND CAUSES", "green", 38))


def scene10(ctx, lt):         # Florida plate + 08-27 sticker = expires August 2027
    b = 10
    badge_row(ctx, W / 2, BADGE_Y, [("FLORIDA", "white", 0.0), ("08-27", "yellow", wt(b, "08-27"))], lt, 62)
    ts = wt(b, "sticker")
    plate_pop(ctx, lt, -0.2, W / 2, 540, 720, "FL", "ABC D12", sticker=("08", "27") if lt > ts else None,
              ring="state" if wt(b, "Florida", 1) < lt < ts else ("sticker" if lt > ts else None))
    pop(ctx, lt, wt(b, "registered"), 280, 800, lambda c: tag(c, "REGISTERED IN FLORIDA", "white", 34, -0.03), sound=None)
    pop(ctx, lt, wt(b, "August"), 780, 820, lambda c: tag(c, "EXPIRES AUGUST 2027", "yellow", 36, 0.03))


def scene11(ctx, lt):         # follow me
    b = 11
    tf = wt(b, "follow")
    plate_pop(ctx, lt, -0.2, W / 2, 800, 520, "NY", "FOLLOW")
    if lt >= tf - 0.3:
        p = max(0.02, ease_out_back((lt - tf + 0.3) / 0.45))
        sfx_once(lt, tf - 0.3, "pop")
        ctx.save(); ctx.translate(W / 2, 450); ctx.scale(p, p)
        ink(ctx, rrect(-420, -170, 840, 340, 50), hexc("#FFFFFF", 0.95), 6)
        label(ctx, "FOLLOW FOR", 0, -80, 64, DARK)
        chip(ctx, 0, 30, NEXT, "red", 60)
        label(ctx, CTX["handle"], 0, 120, 40, hexc("#3A3D44"), font=MONO)
        ctx.restore()


SCENES = [scene0, scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9, scene10, scene11]
