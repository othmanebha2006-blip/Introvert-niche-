"""Badges, label chips, captions, icons and motion helpers."""
import math, cairo
from ink import *

FONT = "Lilita One"
MONO = "Space Mono"
YELLOW = hexc("#FFD23F")
RED = hexc("#D7182A")
DARK = hexc("#1C1D21")

SFX = []          # (time, kind) collected while rendering
CLOCK = {"t": 0.0, "dt": 1 / 30}


def sfx_once(local_t, t0, kind):
    """Record a sound effect the first frame an element appears."""
    if 0 <= local_t - t0 < CLOCK["dt"] - 1e-9:
        SFX.append((CLOCK["t"], kind))


def text_path(ctx, s, x, y, size, font=FONT, anchor="c"):
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    xb, yb, w, h, xa, ya = ctx.text_extents(s)
    fe = ctx.font_extents()
    if anchor == "c":
        ox = x - xa / 2
    elif anchor == "l":
        ox = x
    else:
        ox = x - xa
    oy = y + (fe[0] - fe[1]) / 2 * 0.9
    ctx.move_to(ox, oy)
    ctx.text_path(s)
    return xa


def text_w(ctx, s, size, font=FONT):
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    return ctx.text_extents(s)[4]


def label(ctx, s, x, y, size, fill=(1, 1, 1, 1), stroke=DARK, sw=0, font=FONT, anchor="c", shadow=0):
    if shadow:
        ctx.save(); ctx.translate(0, shadow)
        text_path(ctx, s, x, y, size, font, anchor)
        if sw:
            ctx.set_line_width(sw); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.set_source_rgba(0, 0, 0, 0.25); ctx.stroke_preserve()
        ctx.set_source_rgba(0, 0, 0, 0.25); ctx.fill(); ctx.restore()
    w = text_path(ctx, s, x, y, size, font, anchor)
    if sw:
        ctx.set_line_width(sw); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_source_rgba(*stroke); ctx.stroke_preserve()
    if isinstance(fill, cairo.Pattern):
        ctx.set_source(fill)
    else:
        ctx.set_source_rgba(*fill)
    ctx.fill()
    return w


# ---------- badges ----------
STYLES = {
    #        plate         text fill       text stroke
    "chrome": ("#22252B", "chrome", "#0B0C0E"),
    "red":    ("#C8102E", "chrome", "#5A0612"),
    "yellow": ("#FFD23F", "#1C1D21", None),
    "white":  ("#FFFFFF", "#1C1D21", None),
    "green":  ("#2E9E5B", "#FFFFFF", None),
    "blue":   ("#2C6FCF", "#FFFFFF", None),
    "dark":   ("#1C1D21", "#FFFFFF", None),
}


def chip_size(ctx, text, size, pad=0.42):
    return text_w(ctx, text, size) + size * pad * 2, size * 1.25


def chip(ctx, x, y, text, style="chrome", size=64, alpha=1.0, mono=False):
    """Draws one chip centred at (x,y). Returns its width."""
    plate, tfill, tstroke = STYLES[style]
    font = MONO if mono else FONT
    w = text_w(ctx, text, size, font) + size * 0.84; h = size * 1.25
    if alpha < 1:
        ctx.push_group()
    r = rrect(x - w / 2, y - h / 2, w, h, h * 0.22)
    ctx.save(); ctx.translate(0, 6); path(ctx, r); ctx.set_source_rgba(0, 0, 0, 0.18); ctx.fill(); ctx.restore()
    pc = hexc(plate)
    ink(ctx, r, None, 4.5, grad=lin_grad(0, y - h / 2, 0, y + h / 2, [(0, shade(pc, 0.18)), (0.5, pc), (1, shade(pc, -0.2))]))
    if tfill == "chrome":
        g = lin_grad(0, y - size * 0.45, 0, y + size * 0.45,
                     [(0, hexc("#FFFFFF")), (0.45, hexc("#C9CED6")), (0.55, hexc("#8C939D")), (1, hexc("#E8ECF0"))])
        label(ctx, text, x, y, size, g, hexc(tstroke), size * 0.08, font)
    else:
        label(ctx, text, x, y, size, hexc(tfill), font=font)
    if alpha < 1:
        ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha)
    return w


def badge_row(ctx, cx, cy, parts, lt, size=64, gap=14):
    """parts: list of (text, style, t_in). Chips pop in at their t_in (beat-local) and the row stays centred."""
    vis = [(t, s, ti) for t, s, ti in parts if lt >= ti]
    if not vis:
        return
    ws = [chip_size(ctx, t, size)[0] for t, s, ti in vis]
    total = sum(ws) + gap * (len(ws) - 1)
    # frame around the row
    fh = size * 1.25 + 26
    fr = rrect(cx - total / 2 - 13, cy - fh / 2, total + 26, fh, fh * 0.28)
    ink(ctx, fr, hexc("#FFFFFF", 0.85), 4)
    x = cx - total / 2
    for (t, s, ti), w in zip(vis, ws):
        p = max(0.02, ease_out_back((lt - ti) / 0.32))
        sfx_once(lt, ti, "pop")
        ctx.save(); ctx.translate(x + w / 2, cy); ctx.scale(p, p)
        chip(ctx, 0, 0, t, s, size)
        ctx.restore()
        x += w + gap


def pop(ctx, lt, t0, x, y, fn, dur=0.3, out=None, sound="pop"):
    """Scale-pop an element in at t0 (and fade it out at `out`)."""
    if lt < t0:
        return
    if sound:
        sfx_once(lt, t0, sound)
    p = max(0.02, ease_out_back((lt - t0) / dur))
    a = 1.0
    if out is not None and lt > out:
        a = 1 - ease((lt - out) / 0.25)
        if a <= 0:
            return
    ctx.save(); ctx.translate(x, y); ctx.scale(p, p)
    if a < 1:
        ctx.push_group()
    fn(ctx)
    if a < 1:
        ctx.pop_group_to_source(); ctx.paint_with_alpha(a)
    ctx.restore()


def stamp(ctx, text, color="#2E9E5B", size=84, rot=-0.08):
    w = text_w(ctx, text, size) + size * 0.7; h = size * 1.3
    ctx.save(); ctx.rotate(rot)
    r = rrect(-w / 2, -h / 2, w, h, 16)
    ink(ctx, r, hexc("#FFFFFF"), 10, hexc(color))
    label(ctx, text, 0, 0, size, hexc(color))
    ctx.restore()


def tag(ctx, text, style="yellow", size=46, rot=0.0):
    ctx.save(); ctx.rotate(rot)
    chip(ctx, 0, 0, text, style, size)
    ctx.restore()


def speed_lines(ctx, x, y, L, h, strength, seed=0):
    """Horizontal motion streaks behind (to the right of, for a car driving left->right they trail left)."""
    if strength <= 0.02:
        return
    for i in range(7):
        yy = y - h * (0.15 + 0.12 * i)
        ln = L * (0.25 + 0.35 * ((i * 37 + seed) % 7) / 7) * strength
        xx = x - 20 - ((i * 53 + seed) % 5) * 18
        ctx.move_to(xx, yy); ctx.line_to(xx - ln, yy)
        ctx.set_source_rgba(0.35, 0.37, 0.42, 0.55 * strength); ctx.set_line_width(5); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.stroke()


def caption(ctx, word, x, y, age, key=False):
    s = 1.0 + 0.18 * (1 - ease_out((age) / 0.14)) if age < 0.14 else 1.0
    s = min(s, 1.18)
    p = max(0.02, ease_out_back(age / 0.16, 2.2)) if age < 0.16 else 1.0
    size = 122 if len(word) <= 9 else int(122 * 9 / len(word)) + 10
    ctx.save(); ctx.translate(x, y); ctx.scale(p, p)
    fill = YELLOW if key else hexc("#FFFFFF")
    label(ctx, word, 0, 0, size, fill, DARK, 22, shadow=8)
    ctx.restore()


# ---------- icons ----------
def icon_pump(ctx, x, y, s=1.0, color="#2E9E5B"):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, rrect(-34, -46, 52, 92, 8), hexc(color), 4.5)
    ink(ctx, rrect(-26, -36, 36, 26, 4), hexc("#E9F3FF"), 3.5)
    line(ctx, [(18, -20), (36, -20), (40, 10), (40, 30), (32, 34)], 5)
    ink(ctx, rrect(-42, 40, 68, 12, 4), DARK, 0)
    ctx.restore()


def icon_plug(ctx, x, y, s=1.0, color="#2C6FCF"):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, rrect(-26, -20, 52, 44, 10), hexc(color), 4.5)
    for dx in (-11, 11):
        ink(ctx, rrect(dx - 4, -44, 8, 26, 3), hexc("#C9CDD2"), 3.5)
    line(ctx, [(0, 24), (0, 40), (16, 52), (30, 50)], 6)
    ctx.restore()


def icon_battery(ctx, x, y, s=1.0, level=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, rrect(-44, -24, 82, 48, 8), hexc("#FFFFFF"), 4.5)
    ink(ctx, rrect(38, -10, 10, 20, 3), DARK, 0)
    ink(ctx, rrect(-38, -18, 70 * max(0.05, level), 36, 5), hexc("#35C46A"), 0)
    ctx.restore()


def icon_bolt(ctx, x, y, s=1.0, color="#FFD23F"):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ink(ctx, [(8, -44), (-22, 6), (-2, 6), (-10, 44), (24, -10), (4, -10), (14, -44)], hexc(color), 4.5)
    ctx.restore()


def cross(ctx, x, y, r, w=12):
    for a, b in (((-r, -r), (r, r)), ((-r, r), (r, -r))):
        line(ctx, [(x + a[0], y + a[1]), (x + b[0], y + b[1])], w, RED)


def sparkle(ctx, x, y, r, t):
    k = 0.6 + 0.4 * math.sin(t * 9)
    r *= k
    pts = []
    for i in range(8):
        rr = r if i % 2 == 0 else r * 0.3
        a = i * math.pi / 4
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    ink(ctx, pts, YELLOW, 3)


def arrow(ctx, pts, w=8, color=DARK, head=26):
    line(ctx, pts, w, color)
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    a = math.atan2(y1 - y0, x1 - x0)
    hp = [(x1 + math.cos(a) * 6, y1 + math.sin(a) * 6),
          (x1 - math.cos(a - 0.5) * head, y1 - math.sin(a - 0.5) * head),
          (x1 - math.cos(a + 0.5) * head, y1 - math.sin(a + 0.5) * head)]
    ink(ctx, hp, color, 3, color)


def sound_waves(ctx, x, y, t, n=3):
    for i in range(n):
        ph = (t * 1.6 + i / n) % 1
        r = 30 + ph * 120
        ctx.new_sub_path()
        ctx.arc_negative(x, y, r, math.pi + 0.6, math.pi - 0.6)
        ctx.set_source_rgba(0.11, 0.12, 0.14, 0.8 * (1 - ph)); ctx.set_line_width(7); ctx.stroke()
