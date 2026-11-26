"""Parametric side-view cars, drawn in a clean illustrated style with ink outlines.

Units: the car is 1.0 long. x=0 is the rear bumper, x=1 the front; y is up from the ground.
"""
import math, cairo
from ink import *

# body outline: (x, y, corner radius)
BODY = {
    "sedan":   [(0.006, 0.07, .02), (0.0, 0.20, .03), (0.02, 0.265, .03), (0.19, 0.29, .04), (0.32, 0.43, .07),
                (0.565, 0.445, .09), (0.735, 0.30, .05), (0.95, 0.265, .05), (1.0, 0.20, .03), (0.992, 0.075, .02)],
    "hatch":   [(0.006, 0.075, .02), (0.0, 0.22, .03), (0.035, 0.36, .04), (0.115, 0.452, .06), (0.52, 0.47, .1),
                (0.70, 0.315, .05), (0.94, 0.28, .05), (1.0, 0.21, .03), (0.992, 0.08, .02)],
    "avant":   [(0.006, 0.07, .02), (0.0, 0.22, .03), (0.018, 0.35, .04), (0.065, 0.43, .05), (0.565, 0.445, .09),
                (0.735, 0.30, .05), (0.95, 0.265, .05), (1.0, 0.20, .03), (0.992, 0.075, .02)],
    "fastback": [(0.006, 0.07, .02), (0.0, 0.20, .03), (0.02, 0.27, .02), (0.10, 0.30, .03), (0.36, 0.43, .08),
                 (0.565, 0.443, .09), (0.735, 0.30, .05), (0.95, 0.265, .05), (1.0, 0.20, .03), (0.992, 0.075, .02)],
    "suv":     [(0.006, 0.10, .02), (0.0, 0.30, .03), (0.02, 0.46, .04), (0.08, 0.55, .06), (0.56, 0.565, .1),
                (0.725, 0.40, .05), (0.95, 0.36, .05), (1.0, 0.29, .03), (0.992, 0.105, .02)],
    "rally":   [(0.006, 0.07, .015), (0.0, 0.24, .02), (0.02, 0.30, .02), (0.26, 0.32, .02), (0.34, 0.47, .03),
                (0.62, 0.475, .03), (0.745, 0.325, .03), (0.97, 0.29, .02), (1.0, 0.23, .02), (0.992, 0.075, .015)],
    # mid-engine sports car: long rear deck, cab forward, short nose
    "sports":  [(0.006, 0.07, .02), (0.0, 0.21, .03), (0.03, 0.30, .02), (0.30, 0.335, .05), (0.43, 0.44, .07),
                (0.55, 0.445, .07), (0.70, 0.31, .05), (0.95, 0.25, .06), (1.0, 0.185, .03), (0.992, 0.07, .02)],
    # pickup: bed at the back, tall cab, long hood
    # rear-engine coupe (911 shape): the roof slopes all the way down to the tail, round front wings
    "rear911": [(0.006, 0.07, .02), (0.0, 0.20, .03), (0.04, 0.285, .05), (0.20, 0.385, .08), (0.40, 0.47, .08),
                (0.55, 0.47, .07), (0.70, 0.33, .05), (0.93, 0.27, .07), (1.0, 0.185, .03), (0.992, 0.07, .02)],
    # mid-engine roadster (no roof): low deck, short windscreen
    "roadster": [(0.006, 0.07, .02), (0.0, 0.21, .03), (0.03, 0.31, .02), (0.40, 0.335, .03), (0.585, 0.335, .02),
                 (0.625, 0.43, .015), (0.655, 0.43, .015), (0.70, 0.31, .04), (0.95, 0.25, .06), (1.0, 0.185, .03),
                 (0.992, 0.07, .02)],
    "pickup":  [(0.006, 0.11, .02), (0.0, 0.40, .015), (0.40, 0.40, .005), (0.405, 0.625, .02), (0.44, 0.665, .04),
                (0.62, 0.668, .05), (0.70, 0.475, .03), (0.965, 0.448, .03), (1.0, 0.36, .02), (0.992, 0.11, .02)],
}
# glass: polygon, B-pillar x (None = no pillar), extra pillar x
GLASS = {
    "sedan":   ([(0.215, 0.297), (0.325, 0.418), (0.56, 0.43), (0.705, 0.303)], 0.47, None),
    "hatch":   ([(0.075, 0.33), (0.13, 0.435), (0.515, 0.452), (0.675, 0.318)], 0.44, 0.17),
    "avant":   ([(0.05, 0.315), (0.085, 0.415), (0.56, 0.43), (0.705, 0.303)], 0.47, 0.20),
    "fastback": ([(0.15, 0.297), (0.36, 0.418), (0.56, 0.43), (0.705, 0.303)], 0.46, 0.28),
    "suv":     ([(0.055, 0.415), (0.105, 0.532), (0.555, 0.548), (0.695, 0.405)], 0.45, 0.19),
    "rally":   ([(0.30, 0.325), (0.355, 0.455), (0.61, 0.46), (0.715, 0.328)], 0.50, None),
    "sports":  ([(0.40, 0.34), (0.445, 0.425), (0.55, 0.43), (0.68, 0.31)], None, None),
    "rear911": ([(0.24, 0.375), (0.40, 0.455), (0.54, 0.455), (0.68, 0.335)], None, 0.36),
    "roadster": ([(0.60, 0.34), (0.628, 0.42), (0.652, 0.42), (0.685, 0.33)], None, None),
    "pickup":  ([(0.43, 0.48), (0.455, 0.635), (0.61, 0.64), (0.685, 0.48)], 0.55, None),
}
WHEELS = {  # rear x, front x, radius (in car lengths)
    "sedan": (0.175, 0.81, 0.075), "hatch": (0.165, 0.815, 0.082), "avant": (0.175, 0.81, 0.075),
    "fastback": (0.175, 0.81, 0.075), "suv": (0.175, 0.805, 0.092), "rally": (0.17, 0.815, 0.07),
    "sports": (0.17, 0.80, 0.072), "pickup": (0.165, 0.80, 0.088),
    "rear911": (0.17, 0.80, 0.074), "roadster": (0.17, 0.80, 0.072),
}
# vertical squash so height/length matches the real cars
YS = {"sedan": 0.73, "hatch": 0.76, "avant": 0.74, "fastback": 0.72, "suv": 0.69, "rally": 0.72, "sports": 0.6,
      "pickup": 0.53, "rear911": 0.6, "roadster": 0.6}

PAINT = {
    "tango_red": "#C61F2B", "ara_blue": "#1F3F86", "nardo": "#8E9396", "glacier": "#EDEDEA", "mythos": "#1D1E22",
    "kyalami": "#2F5C3E", "python": "#E3BE1F", "nogaro": "#2A4FAE", "daytona": "#4A4D52", "district": "#5E7A63",
    "turbo_blue": "#2C6FCF", "sonoma": "#A2A5A8", "navarra": "#24375E", "progressive": "#B21E28", "plum": "#4E2E4A",
}


# STYLE["real"] = True: the reference look (illustrated, realistic): thin steady ink lines, pencil hatching on the paint,
# light see-through windows, black plastic cladding + roof rails on SUVs, white sticker border with a soft shadow.
STYLE = {"real": False}


def draw_car(ctx, kind, x, y, L, paint="tango_red", wheel_rot=0.0, *, rs=False, s_model=False, sline=False,
             tilt=0.0, bounce=0.0, rims="silver", calipers=None, shadow=True, alpha=1.0, highlight=None, salt=0,
             livery=False, ghost=False, wing=0):
    """x,y = screen position of the rear-bottom corner (ground line). L = length in px."""
    col = hexc(PAINT.get(paint, paint))
    wr, wf, R = WHEELS[kind]
    if rs:
        R *= 1.06
    real = STYLE["real"]
    lw = max(2.2, L * 0.0055) if not real else max(1.5, L * 0.0034)

    ys = YS[kind]

    def P(px, py):
        return (x + px * L, y - (py * ys + bounce) * L)

    if shadow and not ghost:
        ctx.save()
        cx, cy = x + 0.5 * L, y + 2
        ctx.translate(cx, cy); ctx.scale(1, 0.09)
        g = rad_grad(0, 0, 0, L * 0.56, [(0, (0, 0, 0, 0.32 * alpha)), (0.7, (0, 0, 0, 0.16 * alpha)), (1, (0, 0, 0, 0))])
        ctx.arc(0, 0, L * 0.56, 0, 2 * math.pi); ctx.set_source(g); ctx.fill()
        ctx.restore()

    ctx.save()
    if tilt:
        ctx.translate(x + 0.5 * L, y); ctx.rotate(-tilt); ctx.translate(-(x + 0.5 * L), -y)
    if alpha < 1:
        ctx.push_group()

    body = rpoly([P(px, py) for px, py, _ in BODY[kind]], [r * L for *_, r in BODY[kind]])
    top = min(p[1] for p in body); bot = max(p[1] for p in body)

    if ghost:
        ink(ctx, body, hexc("#D9DCE1"), lw * 1.2, hexc("#9EA3AB"), salt=salt)
        for wx in (wr, wf):
            ink(ctx, ellipse(*P(wx, R / ys), R * L, R * L), hexc("#D9DCE1"), lw * 1.2, hexc("#9EA3AB"), salt=salt)
        ctx.restore()
        return

    if real and not ghost:
        # white sticker border + soft drop shadow around the whole car
        wheels_c = [(P(wx, R / ys), R * L) for wx in (wr, wf)]
        for dy, colr, wdt in ((L * 0.010, (0, 0, 0, 0.16), L * 0.030), (0, (1, 1, 1, 1), L * 0.026)):
            ctx.save(); ctx.translate(0, dy)
            path(ctx, body); ctx.set_source_rgba(*colr); ctx.set_line_width(wdt); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve(); ctx.fill()
            for (cx_, cy_), rr_ in wheels_c:
                ctx.arc(cx_, cy_, rr_ + wdt / 2, 0, 2 * math.pi); ctx.fill()
            ctx.restore()
    if rs or s_model:
        n = 2
        for i in range(n):
            ex = 0.02 + i * 0.045
            ink(ctx, rrect(*P(ex + 0.01, BODY[kind][0][1] / 1.0 + 0.004), 0.034 * L, 0.03 * L, 0.009 * L), hexc("#BFC3C8") if s_model else hexc("#2A2B2F"), lw * 0.6, salt=salt)
    # paint
    g = lin_grad(0, top, 0, bot, [(0, shade(col, 0.28)), (0.35, shade(col, 0.06)), (0.62, col), (1, shade(col, -0.38))])
    ink(ctx, body, None, 0, grad=g)
    # clip to body for reflections, arches, lines
    ctx.save(); path(ctx, body); ctx.clip()
    gl, bp, xp = GLASS[kind]
    belt = gl[0][1] - 0.012
    # sky reflection band under the window line
    band = [P(-0.02, belt), P(1.02, belt - 0.035), P(1.02, belt - 0.095), P(-0.02, belt - 0.06)]
    path(ctx, band); ctx.set_source_rgba(1, 1, 1, 0.13); ctx.fill()
    # darker lower body
    low = [P(-0.02, 0.16 + (0.03 if kind == "suv" else 0)), P(1.02, 0.15 + (0.03 if kind == "suv" else 0)), P(1.02, -0.1), P(-0.02, -0.1)]
    path(ctx, low); ctx.set_source_rgba(0, 0, 0, 0.13); ctx.fill()
    if real:
        # pencil hatching: dense light strokes low on the body, a few on the upper panels
        ctx.set_line_width(max(1.0, L * 0.0016))
        for i in range(70):
            u = i / 70
            hx0 = x - 0.05 * L + u * 1.1 * L
            ctx.move_to(hx0, y - 0.02 * L); ctx.line_to(hx0 + 0.07 * L, y - 0.22 * ys * L)
        ctx.set_source_rgba(0, 0, 0, 0.07); ctx.stroke()
        for i in range(24):
            u = i / 24
            hx0 = x + u * L
            ctx.move_to(hx0, y - (belt - 0.03) * ys * L); ctx.line_to(hx0 + 0.05 * L, y - (belt - 0.11) * ys * L)
        ctx.set_source_rgba(1, 1, 1, 0.10); ctx.stroke()
        if kind in ("suv", "pickup"):   # black plastic cladding along the bottom
            path(ctx, [P(-0.02, 0.135), P(1.02, 0.13), P(1.02, -0.1), P(-0.02, -0.1)]); ctx.set_source_rgba(*hexc("#2A2B2F")); ctx.fill()
    if livery:  # rally stripes
        for i, c in enumerate(["#1D1E22", "#C61F2B", "#9AA0A6"]):
            o = i * 0.022
            path(ctx, [P(-0.02, 0.21 - o), P(1.02, 0.20 - o), P(1.02, 0.185 - o), P(-0.02, 0.195 - o)])
            ctx.set_source_rgba(*hexc(c)); ctx.fill()
    # wheel arches (gap behind the wheel)
    for wx in (wr, wf):
        cx, cy = P(wx, R / ys)
        ar = R * L * (1.2 if rs else 1.14)
        ctx.arc(cx, cy, ar, 0, 2 * math.pi); ctx.set_source_rgba(0.07, 0.07, 0.08, 1); ctx.fill()
    ctx.restore()
    ink(ctx, body, None, lw, salt=salt)

    # RS / S line: blistered arches + black side blade
    ctx.save(); path(ctx, body); ctx.clip()
    for wx in (wr, wf):
        cx, cy = P(wx, R / ys)
        ar = R * L * (1.2 if rs else 1.14)
        a0, a1 = math.pi * 1.04, math.pi * 1.96
        flare = ellipse(cx, cy, ar + lw * (2.6 if rs else 1.2), ar + lw * (2.6 if rs else 1.2), 30, a0, a1)
        line(ctx, flare, lw * 0.9, salt=salt)
    ctx.restore()

    if real and kind in ("suv", "pickup"):   # thick black arch mouldings
        for wx in (wr, wf):
            cx, cy = P(wx, R / ys)
            ar = R * L * 1.2
            line(ctx, ellipse(cx, cy, ar, ar, 30, math.pi * 1.02, math.pi * 1.98), L * 0.022, hexc("#2A2B2F"), sketch=False)
    # glass
    glass = rpoly([P(*p) for p in gl], [0.012 * L, 0.03 * L, 0.03 * L, 0.012 * L])
    gtop = min(p[1] for p in glass); gbot = max(p[1] for p in glass)
    trim = hexc("#1A1B1E") if (rs or sline or s_model) else hexc("#C9CDD2")
    if real:      # light see-through windows like an illustration
        gg = lin_grad(0, gtop, 0, gbot, [(0, hexc("#F5F7FA")), (0.6, hexc("#DCE2E9")), (1, hexc("#B9C2CC"))])
    else:
        gg = lin_grad(0, gtop, 0, gbot, [(0, hexc("#5C6F86")), (0.5, hexc("#2B3646")), (1, hexc("#1A2230"))])
    ink(ctx, glass, None, 0, grad=gg)
    ctx.save(); path(ctx, glass); ctx.clip()
    if real:      # seats / headrests seen through the glass + sketch strokes
        for hx in (gl[1][0] + 0.06, (gl[1][0] + gl[2][0]) / 2 + 0.04):
            ink(ctx, rrect(*P(hx, gl[1][1] - 0.035), 0.04 * L, 0.05 * ys * L, 0.016 * L), hexc("#9AA3AE", 0.35), 0)
        ctx.set_line_width(max(1.0, L * 0.0018))
        for i in range(8):
            u = i / 8
            sx0 = x + (gl[0][0] + u * (gl[3][0] - gl[0][0])) * L
            ctx.move_to(sx0, gbot); ctx.line_to(sx0 + 0.06 * L, gtop)
        ctx.set_source_rgba(0.35, 0.40, 0.48, 0.25); ctx.stroke()
    sx = x + (gl[1][0] + 0.08) * L
    path(ctx, [(sx, gtop - 5), (sx + 0.07 * L, gtop - 5), (sx - 0.04 * L, gbot + 5), (sx - 0.11 * L, gbot + 5)])
    ctx.set_source_rgba(1, 1, 1, 0.16); ctx.fill()
    path(ctx, [(sx + 0.10 * L, gtop - 5), (sx + 0.125 * L, gtop - 5), (sx + 0.015 * L, gbot + 5), (sx - 0.01 * L, gbot + 5)])
    ctx.set_source_rgba(1, 1, 1, 0.12); ctx.fill()
    ctx.restore()
    ink(ctx, glass, None, lw * 1.5, trim, salt=salt + 1)
    ink(ctx, glass, None, lw * 0.7, salt=salt)
    # pillars (clipped to the glass)
    ctx.save(); path(ctx, glass); ctx.clip()
    for px in [bp, xp]:
        if px is None:
            continue
        lean = 0.02
        y0 = belt + 0.012; y1 = gl[2][1] + 0.05
        pil = [P(px - 0.012, y0), P(px + 0.012, y0), P(px + 0.012 - lean, y1), P(px - 0.012 - lean, y1)]
        ink(ctx, pil, hexc("#15161A"), 0)
    ctx.restore()

    # door shut lines, handles, shoulder crease
    fx = gl[3][0] + 0.005
    rx = gl[0][0] + (0.06 if kind in ("sedan", "fastback", "rally") else 0.005 if kind == "pickup" else 0.11)
    sill = 0.085 if kind != "suv" else 0.12
    dl = lw * 0.55
    if bp is not None and kind != "rally":
        for dx in (bp + 0.005, rx):
            line(ctx, [P(dx, belt), P(dx - 0.006, sill + 0.02)], dl, salt=salt)
    line(ctx, [P(fx, belt + 0.004), P(fx + 0.004, belt - 0.035), P(wf - R * 1.25, sill + 0.03)], dl, salt=salt)
    for hx in ([bp - 0.07, bp + 0.10] if bp else []):
        ink(ctx, rrect(*P(hx, belt - 0.03), 0.045 * L, 0.011 * L, 0.005 * L), shade(col, -0.25), dl, salt=salt)
    crease_y = belt - 0.055 if kind != "pickup" else 0.33
    ctx.save(); path(ctx, body); ctx.clip()
    line(ctx, [P(0.03, crease_y + 0.01), P(0.5, crease_y), P(0.97, crease_y - 0.012)], dl, shade(col, -0.45) if paint != "mythos" else hexc("#55585E"), salt=salt)
    if kind == "pickup":   # gap between cab and bed, bed rail
        line(ctx, [P(0.408, 0.405), P(0.406, sill + 0.03)], dl * 1.4, salt=salt)
        line(ctx, [P(0.01, 0.375), P(0.40, 0.375)], dl, shade(col, -0.35), salt=salt)
    ctx.restore()

    # side blade / sill
    sill_c = hexc("#1D1E22") if (rs or sline or s_model) else shade(col, -0.3)
    ink(ctx, rpoly([P(wr + R * 1.25, sill + 0.022), P(wf - R * 1.25, sill + 0.022), P(wf - R * 1.25, sill - 0.006), P(wr + R * 1.25, sill - 0.006)], 3),
        sill_c, dl, salt=salt)

    if real and kind == "suv":   # roof rails
        rt = max(p[1] for p in [(q[0], q[1]) for q in BODY[kind]])
        ry = rt - 0.012
        line(ctx, [P(gl[1][0] + 0.03, ry), P(gl[2][0] - 0.06, ry + 0.004)], L * 0.008, hexc("#2A2B2F"), sketch=False)
        for fx_ in (gl[1][0] + 0.05, gl[2][0] - 0.08):
            line(ctx, [P(fx_, ry), P(fx_, rt - 0.03)], L * 0.006, hexc("#2A2B2F"), sketch=False)
    # mirror
    mx, my = gl[3][0] - 0.01, gl[3][1] + 0.012
    ink(ctx, rpoly([P(mx - 0.035, my + 0.035), P(mx + 0.015, my + 0.04), P(mx + 0.02, my - 0.005), P(mx - 0.03, my)], 0.01 * L),
        trim if (rs or s_model) else col, lw * 0.8, salt=salt)

    # front: headlight + grille
    bd = BODY[kind]
    ny = bd[-2][1]
    hl = rpoly([P(0.905, ny + 0.05), P(0.99, ny + 0.02), P(0.995, ny - 0.005), P(0.92, ny + 0.015)], 0.008 * L)
    ink(ctx, hl, hexc("#DDE9F5"), lw * 0.8, salt=salt)
    line(ctx, [P(0.93, ny + 0.022), P(0.985, ny + 0.005)], lw * 0.7, hexc("#5FB0FF"), salt=salt)
    gr = rpoly([P(0.975, ny - 0.03), P(1.0, ny - 0.035), P(0.997, ny - 0.12), P(0.975, ny - 0.11)], 0.006 * L)
    ink(ctx, gr, hexc("#16171A") if not (rs or s_model) else hexc("#0D0D0F"), lw * 0.7, salt=salt)
    if rs or s_model or sline:
        intake = rpoly([P(0.955, 0.10), P(0.993, 0.098), P(0.99, 0.135), P(0.955, 0.14)], 0.004 * L)
        ink(ctx, intake, hexc("#0D0D0F"), lw * 0.6, salt=salt)
    # rear: tail light + exhaust
    ty = bd[2][1]
    tl = rpoly([P(0.003, ty - 0.025), P(0.06, ty - 0.012), P(0.06, ty - 0.04), P(0.004, ty - 0.055)], 0.006 * L)
    ink(ctx, tl, hexc("#C8102E"), lw * 0.8, salt=salt)
    line(ctx, [P(0.008, ty - 0.035), P(0.055, ty - 0.027)], lw * 0.6, hexc("#FF6B6B"), salt=salt)
    if rs:  # rear diffuser + spoiler lip
        ink(ctx, rpoly([P(0.0, 0.1), P(0.1, 0.095), P(0.09, 0.065), P(0.01, 0.07)], 3), hexc("#1A1B1E"), lw * 0.6, salt=salt)

    if wing:   # GT3 / GT3 RS rear wing on two uprights
        h = 0.07 + 0.05 * (wing - 1)
        for ux in (0.07, 0.15):
            ink(ctx, [P(ux - 0.008, 0.30), P(ux + 0.008, 0.31), P(ux + 0.006, 0.30 + h), P(ux - 0.006, 0.30 + h)], hexc("#1A1B1E"), lw * 0.5)
        ww = 0.20 + 0.03 * (wing - 1)
        ink(ctx, rpoly([P(-0.01, 0.30 + h + 0.035), P(ww, 0.30 + h + 0.02), P(ww, 0.30 + h - 0.005), P(-0.01, 0.30 + h + 0.005)], 0.006 * L),
            hexc("#1A1B1E"), lw * 0.8)
    # wheels
    rim_col = {"silver": hexc("#C9CDD2"), "dark": hexc("#3A3D42"), "black": hexc("#1E1F23"), "gold": hexc("#C9A54A"),
               "white": hexc("#E8E8E6")}[rims]
    for wx in (wr, wf):
        draw_wheel(ctx, *P(wx, R / ys), R * L, wheel_rot, rim_col, calipers or ("#C8102E" if rs else None), lw, salt,
                   big=rs or sline)

    if highlight:
        hx0, hx1, hcol = highlight
        ink(ctx, rrect(*P(hx0, 0.5), (hx1 - hx0) * L, 0.02 * L, 0.01 * L), hexc(hcol), 0)

    if alpha < 1:
        ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha)
    ctx.restore()


def draw_wheel(ctx, cx, cy, r, rot, rim_col, caliper=None, lw=3, salt=0, big=False):
    tire = ellipse(cx, cy, r, r, 40)
    ink(ctx, tire, hexc("#1B1C1F"), lw, salt=salt)
    ink(ctx, ellipse(cx, cy, r * 0.93, r * 0.93, 40), hexc("#26272B"), 0)
    rr = r * (0.74 if big else 0.68)
    ink(ctx, ellipse(cx, cy, rr, rr, 40), hexc("#0E0E10"), 0)
    if caliper:
        a0 = -2.2
        cal = ellipse(cx, cy, rr * 0.82, rr * 0.82, 10, a0, a0 + 1.1) + ellipse(cx, cy, rr * 0.5, rr * 0.5, 10, a0 + 1.1, a0)
        ink(ctx, cal, hexc(caliper), 0)
    # disc
    ink(ctx, ellipse(cx, cy, rr * 0.8, rr * 0.8, 30), None, lw * 0.4, hexc("#4A4D52"), sketch=False)
    g = rad_grad(cx - rr * 0.3, cy - rr * 0.3, 0, rr * 1.3, [(0, shade(rim_col, 0.35)), (1, shade(rim_col, -0.3))])
    # 5 double spokes
    for i in range(5):
        a = rot + i * 2 * math.pi / 5
        for off in (-0.13, 0.13):
            b = a + off
            w0, w1 = 0.07, 0.035
            pts = [(cx + math.cos(b - w0) * rr * 0.28, cy + math.sin(b - w0) * rr * 0.28),
                   (cx + math.cos(b + off * 0.4 - w1) * rr * 0.97, cy + math.sin(b + off * 0.4 - w1) * rr * 0.97),
                   (cx + math.cos(b + off * 0.4 + w1) * rr * 0.97, cy + math.sin(b + off * 0.4 + w1) * rr * 0.97),
                   (cx + math.cos(b + w0) * rr * 0.28, cy + math.sin(b + w0) * rr * 0.28)]
            path(ctx, pts); ctx.set_source(g); ctx.fill()
    ring = ellipse(cx, cy, rr, rr, 40) + ellipse(cx, cy, rr * 0.9, rr * 0.9, 40)[::-1]
    path(ctx, ring); ctx.set_source(g); ctx.fill()
    ink(ctx, ellipse(cx, cy, rr * 0.3, rr * 0.3, 20), None, 0, grad=g)
    ink(ctx, ellipse(cx, cy, rr * 0.13, rr * 0.13, 16), hexc("#2A2B2F"), 0)
    ink(ctx, ellipse(cx, cy, rr, rr, 40), None, lw * 0.6, salt=salt)
