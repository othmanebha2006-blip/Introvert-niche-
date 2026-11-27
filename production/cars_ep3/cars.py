"""Hand-built side-profile Lexus illustrations (ink + coloured-pencil look), drawn to true scale.

Each car is described in millimetres from its real published dimensions (length, height,
wheelbase, front overhang) plus a handful of shape points. Front of the car faces RIGHT.
Output: SVG files, rendered to transparent PNG by render_svgs.js (Chromium).
"""
import math, json, os, sys

PX = 0.2  # px per mm in the SVG (rendered at 2x => 0.4 px/mm)

# Real dimensions (mm) and shape points. d_* are distances from the FRONT bumper.
CARS = {
 # real published dimensions (mm); fo = front overhang, r = tyre radius
 'A3':   dict(L=4343, H=1449, WB=2636, fo=880, r=330, name='A3 Sportback', color_name='Progressive Red'),
 'A6':   dict(L=4939, H=1457, WB=2924, fo=930, r=345, name='A6 Sedan', color_name='Mythos Black'),
 'Q3':   dict(L=4484, H=1585, WB=2680, fo=900, r=355, name='Q3', color_name='Navarra Blue'),
 'Q7':   dict(L=5063, H=1741, WB=2995, fo=990, r=375, name='Q7', color_name='Glacier White'),
 'Q8':   dict(L=4986, H=1705, WB=2995, fo=990, r=380, name='Q8', color_name='Daytona Grey'),
 'Q6E':  dict(L=4771, H=1695, WB=2899, fo=900, r=370, name='Q6 e-tron', color_name='Ascari Blue'),
 'A5EH': dict(L=4829, H=1440, WB=2900, fo=900, r=345, name='A5 e-hybrid', color_name='Florett Silver'),
 'A6AV': dict(L=4939, H=1467, WB=2924, fo=930, r=345, name='A6 Avant', color_name='Manhattan Grey'),
 'A5':   dict(L=4829, H=1440, WB=2900, fo=900, r=340, name='A5 Sportback', color_name='Tango Red'),
 'S5':   dict(L=4836, H=1415, WB=2900, fo=905, r=350, name='S5 Sportback', color_name='District Green'),
 'RS5':  dict(L=4783, H=1399, WB=2826, fo=900, r=350, name='RS 5 Sportback', color_name='Nardo Grey'),
 'A5SL': dict(L=4829, H=1440, WB=2900, fo=900, r=345, name='A5 S line', color_name='Ibis White'),
 'RS6':  dict(L=4995, H=1460, WB=2929, fo=960, r=365, name='RS 6 Avant performance', color_name='Ascari Blue'),
}


def car_svg(key, c):
    s = PX
    L, H = c['L'], c['H']
    pad = 40
    W = L * s + 2 * pad
    Ht = (H + 60) * s + 2 * pad
    X = lambda x: pad + x * s                 # x measured from REAR (0) to front (L)
    Y = lambda y: pad + (H + 60 - y) * s      # y up from ground
    F = lambda d: L - d                       # distance from front -> x
    P = lambda x, y: f'{X(x):.1f},{Y(y):.1f}'
    kind = c['kind']
    r, gc = c['r'], c['gc']
    rax, fax = F(c['fo'] + c['WB']), F(c['fo'])
    R = r + (60 if kind in ('suv', 'box', 'cross') else 45)
    dx = math.sqrt(max(R * R - (gc - r) ** 2, 1))
    top, bot = c['paint']

    nose, hood, cowl, apex, rroof, H_ = c['nose'], c['hood'], c['cowl'], c['apex'], c['rroof'], H
    deck, deckh, tail = c['deck'], c['deckh'], c['tail']
    boxy = kind == 'box'
    # ---------- body silhouette ----------
    fb = 70 if boxy else 110
    d = [f'M{P(F(fb), gc + 60)}']
    d.append(f'C{P(F(15), gc + 70)} {P(F(-5), gc + 160)} {P(F(0), (gc + nose) / 2)}')      # front bumper
    d.append(f'C{P(F(5), nose - 60)} {P(F(20), nose)} {P(F(90 if not boxy else 40), nose)}')  # nose top
    hmid = (nose + hood) / 2 + (30 if not boxy else 5)
    d.append(f'C{P(F(cowl * 0.45), hmid + 25)} {P(F(cowl * 0.8), hood)} {P(F(cowl), hood)}')   # hood
    # windscreen (slightly convex)
    wx = (cowl + apex) / 2
    d.append(f'C{P(F(wx - 40), (hood + H_) / 2 + 40)} {P(F(apex - 150), H_ - 10)} {P(F(apex), H_)}')
    # roof
    if kind in ('saloon', 'fastback', 'coupe', 'super'):
        d.append(f'C{P(F(apex + (rroof - apex) * 0.4), H_ + 12)} {P(F(rroof - 200), H_ - c["drop"] * 0.3)} {P(F(rroof), H_ - c["drop"])}')
        # rear glass down to deck
        d.append(f'C{P(F(rroof + (deck - rroof) * 0.45), H_ - c["drop"] - 80)} {P(F(deck - 160), deckh + 40)} {P(F(deck), deckh)}')
        # boot lid / ducktail to tail
        d.append(f'C{P(F(deck + (L - deck) * 0.5), deckh + 8)} {P(140, tail + 20)} {P(45, tail - 10)}')
        d.append(f'C{P(5, tail - 70)} {P(-8, gc + 380)} {P(25, gc + 210)}')
        d.append(f'C{P(45, gc + 120)} {P(80, gc + 80)} {P(120, gc + 60)}')
    else:
        d.append(f'C{P(F(apex + (rroof - apex) * 0.4), H_ + 10)} {P(F(rroof - 300), H_ - c["drop"] * 0.4)} {P(F(rroof), H_ - c["drop"])}')
        # spoiler lip + hatch glass
        d.append(f'L{P(F(rroof + 60), H_ - c["drop"] - 25)}')
        slope = 0.55 if kind == 'cross' else (0.3 if kind == 'suv' else 0.05)
        d.append(f'C{P(F(rroof + 120), H_ - c["drop"] - 120)} {P(F(deck - 40), deckh + 120)} {P(F(deck), deckh)}')
        d.append(f'C{P(10, tail - 80)} {P(-6, gc + 380)} {P(22, gc + 210)}')
        d.append(f'C{P(40, gc + 120)} {P(80, gc + 80)} {P(120, gc + 60)}')
    # underside with wheel arches (rear then front)
    d.append(f'L{P(rax - dx, gc)}')
    d.append(f'A{R * s:.1f},{R * s:.1f} 0 0 1 {P(rax + dx, gc)}')
    d.append(f'L{P(fax - dx, gc)}')
    d.append(f'A{R * s:.1f},{R * s:.1f} 0 0 1 {P(fax + dx, gc)}')
    d.append('Z')
    body = ' '.join(d)

    # ---------- glasshouse ----------
    belt, beltr = c['belt'], c['beltr']
    g0 = F(cowl + 90)
    if kind in ('saloon', 'fastback', 'coupe', 'super'):
        g_end = F(deck - (220 if kind != 'fastback' else 120))
        dlo = (f'M{P(g0, belt + 25)} C{P(F(wx + 10), (belt + H_) / 2 + 20)} {P(F(apex - 80), H_ - 55)} {P(F(apex + 60), H_ - 60)} '
               f'C{P(F(apex + (rroof - apex) * 0.45), H_ - 50)} {P(F(rroof - 150), H_ - c["drop"] - 45)} {P(F(rroof + 40), H_ - c["drop"] - 70)} '
               f'C{P(F(rroof + 260), H_ - c["drop"] - 170)} {P(g_end + 120, beltr + 60)} {P(g_end, beltr + 15)} '
               f'L{P(g_end - 40, beltr)} Z')
    else:
        g_end = F(deck - 170)
        dlo = (f'M{P(g0, belt + 30)} C{P(F(wx + 10), (belt + H_) / 2 + 20)} {P(F(apex - 80), H_ - 65)} {P(F(apex + 60), H_ - 70)} '
               f'L{P(F(rroof - 60), H_ - c["drop"] - 70)} '
               f'C{P(F(rroof + 40), H_ - c["drop"] - 90)} {P(g_end + 60, beltr + 140)} {P(g_end, beltr + 40)} '
               f'L{P(g_end - 10, beltr)} Z')
    # pillars
    bx = F(cowl + (apex - cowl) + (rroof - apex) * (0.36 if kind not in ('coupe', 'super') else 0.62))
    pillars = f'<path d="M{P(bx, belt + 20)} L{P(bx + 85, belt + 20)} L{P(bx + 70, H_ - 40)} L{P(bx - 10, H_ - 40)} Z" fill="#141414"/>'
    cx_ = None
    if kind in ('suv', 'box', 'cross'):
        cx_ = F(cowl + (rroof - cowl) * 0.72)
        pillars += f'<path d="M{P(cx_, beltr + 5)} L{P(cx_ + 110, beltr + 5)} L{P(cx_ + 95, H_ - c["drop"] - 30)} L{P(cx_ - 5, H_ - c["drop"] - 30)} Z" fill="{bot}"/>'
    if kind == 'fastback':
        cx_ = F(rroof - 120)
        pillars += f'<path d="M{P(cx_, beltr + 5)} L{P(cx_ + 70, beltr + 5)} L{P(cx_ + 60, H_ - 120)} L{P(cx_ - 5, H_ - 120)} Z" fill="#141414"/>'
    # chrome window surround (Lexus signature)
    chrome = f'<path d="{dlo}" fill="none" stroke="url(#chrome)" stroke-width="6"/>'

    # ---------- details ----------
    det = []
    ink = '#161616'
    # door shut lines
    dlines = [g0 + 10, bx + 40]
    if kind in ('saloon', 'fastback', 'suv', 'box', 'cross'):
        dlines.append(bx - (fax - bx) * 0.0 - 900 if False else (rax + R + 30 if kind != 'box' else rax + R + 60))
    for i, x in enumerate(dlines):
        det.append(f'<path d="M{P(x, belt + 15)} C{P(x - 15, (belt + gc) / 2)} {P(x - 10, gc + 90)} {P(x - 5, gc + 30)}" stroke="{ink}" stroke-width="2" fill="none" opacity=".8"/>')
    # door handles (flush)
    for x in ([bx + 260, bx - 320] if kind not in ('coupe', 'super') else [bx - 260]):
        det.append(f'<rect x="{X(x - 70):.1f}" y="{Y(belt - 70):.1f}" width="{140 * s:.1f}" height="{26 * s:.1f}" rx="{12 * s:.1f}" fill="url(#chrome)" stroke="{ink}" stroke-width="1.2"/>')
    # character line (L-finesse) rising to the rear + highlight
    cl0, cl1 = F(c['fo'] + R * 0.3), F(L - 250)
    det.append(f'<path d="M{P(cl0, (gc + belt) / 2 + 90)} C{P(cl0 - 900, (gc + belt) / 2 + 60)} {P(cl1 + 700, belt - 150)} {P(cl1, belt - 60)}" stroke="{ink}" stroke-width="1.6" fill="none" opacity=".65"/>')
    det.append(f'<path d="M{P(cl0 - 100, (gc + belt) / 2 + 125)} C{P(cl0 - 900, (gc + belt) / 2 + 95)} {P(cl1 + 700, belt - 110)} {P(cl1 + 80, belt - 30)}" stroke="#fff" stroke-width="5" fill="none" opacity=".55" stroke-linecap="round"/>')
    # lower sculpted shadow (concave lower door)
    det.append(f'<path d="M{P(fax - R - 40, gc + 40)} L{P(rax + R + 40, gc + 40)} L{P(rax + R + 60, gc + 150)} C{P((fax + rax) / 2, gc + 230)} {P((fax + rax) / 2, gc + 230)} {P(fax - R - 60, gc + 170)} Z" fill="#000" opacity=".18"/>')
    # rocker
    det.append(f'<path d="M{P(rax + dx + 10, gc)} L{P(fax - dx - 10, gc)} L{P(fax - dx - 20, gc + 55)} L{P(rax + dx + 20, gc + 55)} Z" fill="#1b1b1b" opacity=".85"/>')
    # wheel-arch cladding
    if c.get('clad'):
        for ax in (rax, fax):
            det.append(f'<path d="M{P(ax - dx - 40, gc - 5)} A{(R + 55) * s:.1f},{(R + 55) * s:.1f} 0 0 1 {P(ax + dx + 40, gc - 5)} L{P(ax + dx, gc)} A{R * s:.1f},{R * s:.1f} 0 0 0 {P(ax - dx, gc)} Z" fill="#202020"/>')
    # mirror
    mx = F(cowl + 170)
    mirror = (f'<path d="M{P(mx, belt + 20)} C{P(mx - 40, belt + 150)} {P(mx - 230, belt + 170)} {P(mx - 250, belt + 60)} C{P(mx - 240, belt + 10)} {P(mx - 80, belt - 10)} {P(mx, belt + 20)} Z" fill="url(#body)" stroke="{ink}" stroke-width="2"/>')
    outside = []
    hl_y = nose - 60
    if c.get('gclass'):
        # round headlight + indicator on the wing, upright slatted grille, side exhausts, spare wheel
        det.append(f'<circle cx="{X(F(60)):.1f}" cy="{Y(nose - 110):.1f}" r="{95 * s:.1f}" fill="url(#lamp)" stroke="{ink}" stroke-width="2.5"/>')
        det.append(f'<circle cx="{X(F(60)):.1f}" cy="{Y(nose - 110):.1f}" r="{60 * s:.1f}" fill="none" stroke="#fff" stroke-width="3"/>')
        outside.append(f'<rect x="{X(F(330)):.1f}" y="{Y(hood + 55):.1f}" width="{150 * s:.1f}" height="{55 * s:.1f}" rx="{20 * s:.1f}" fill="#f0a020" stroke="{ink}" stroke-width="2"/>')
        for k in range(3):
            det.append(f'<rect x="{X(rax + R + 40 + k * 70):.1f}" y="{Y(gc + 70):.1f}" width="{50 * s:.1f}" height="{40 * s:.1f}" rx="{8 * s:.1f}" fill="#c9ccd0" stroke="{ink}" stroke-width="1.5"/>')
        sr = 380
        outside.append(f'<rect x="{X(-170):.1f}" y="{Y(tail - 120):.1f}" width="{170 * s:.1f}" height="{2 * sr * s:.1f}" rx="{60 * s:.1f}" fill="#1c1c1c" stroke="{ink}" stroke-width="2.5"/>')
        outside.append(f'<rect x="{X(-175):.1f}" y="{Y(tail - 120):.1f}" width="{40 * s:.1f}" height="{2 * sr * s:.1f}" rx="{15 * s:.1f}" fill="url(#chrome)" stroke="{ink}" stroke-width="1.5"/>')
        det.append(f'<rect x="{X(F(70)):.1f}" y="{Y(nose - 60):.1f}" width="{70 * s:.1f}" height="{(nose - gc - 260) * s:.1f}" fill="url(#grille)" stroke="{ink}" stroke-width="1.5"/>')
    else:
        # wide headlight with an 'eyebrow' DRL
        det.append(f'<path d="M{P(F(25), hl_y + 5)} C{P(F(200), hl_y + 50)} {P(F(420), hl_y + 70)} {P(F(560), hl_y + 60)} L{P(F(540), hl_y - 10)} C{P(F(380), hl_y - 30)} {P(F(180), hl_y - 70)} {P(F(70), hl_y - 90)} Z" fill="url(#lamp)" stroke="{ink}" stroke-width="2"/>')
        det.append(f'<path d="M{P(F(70), hl_y - 70)} C{P(F(200), hl_y - 45)} {P(F(380), hl_y - 5)} {P(F(520), hl_y + 15)}" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" filter="url(#glow)"/>')
        # Panamericana / AMG grille: vertical slats on the nose
        det.append(f'<path d="M{P(F(6), nose - 140)} L{P(F(-4), gc + 220)} L{P(F(60), gc + 200)} L{P(F(80), nose - 160)} Z" fill="url(#grille)" stroke="{ink}" stroke-width="1.5"/>')
        for k in range(4):
            yk = nose - 170 - k * (nose - gc - 380) / 4
            det.append(f'<line x1="{X(F(0)):.1f}" y1="{Y(yk):.1f}" x2="{X(F(70)):.1f}" y2="{Y(yk):.1f}" stroke="#bfc4ca" stroke-width="1.6"/>')
        # big AMG side intakes in the front bumper
        det.append(f'<path d="M{P(F(120), gc + 80)} L{P(F(430), gc + 110)} L{P(F(400), gc + 250)} L{P(F(100), gc + 220)} Z" fill="url(#mesh)" stroke="{ink}" stroke-width="1.5"/>')
    # tail light
    det.append(f'<path d="M{P(10, tail - 25)} L{P(380 if kind != "box" else 150, tail - 45)} L{P(360 if kind != "box" else 140, tail - 140)} L{P(18, tail - 125)} Z" fill="url(#tail)" stroke="{ink}" stroke-width="2"/>')
    # rear diffuser + quad AMG exhaust tips (twin visible from the side)
    if not c.get('gclass'):
        det.append(f'<path d="M{P(15, gc + 150)} L{P(420, gc + 120)} L{P(400, gc + 55)} L{P(60, gc + 55)} Z" fill="#1c1c1c" opacity=".92"/>')
        if not c.get('amgline'):
            for k in range(2):
                outside.append(f'<rect x="{X(-20 + k * 0):.1f}" y="{Y(gc + 125 - k * 55):.1f}" width="{70 * s:.1f}" height="{45 * s:.1f}" rx="{14 * s:.1f}" fill="url(#chrome)" stroke="{ink}" stroke-width="1.5"/>')
    # fuel / charge flap
    fx = rax + R * 0.25
    det.append(f'<rect x="{X(fx - 80):.1f}" y="{Y(belt - 40):.1f}" width="{170 * s:.1f}" height="{150 * s:.1f}" rx="{30 * s:.1f}" fill="none" stroke="{ink}" stroke-width="1.4" opacity=".6"/>')
    if c.get('rails'):
        det.append(f'<path d="M{P(F(apex + 150), H_ + 5)} L{P(F(rroof - 80), H_ - c["drop"] + 5)} L{P(F(rroof - 80), H_ - c["drop"] + 45)} L{P(F(apex + 150), H_ + 45)} Z" fill="#1d1d1d" stroke="{ink}" stroke-width="1.5"/>')
    if key == 'GT':
        outside.append(f'<path d="M{P(20, tail + 70)} L{P(330, tail + 55)} L{P(310, tail + 15)} L{P(25, tail + 20)} Z" fill="#141414" stroke="{ink}" stroke-width="2"/>')
        det.append(f'<path d="M{P(fax - R - 40, belt - 40)} L{P(fax - R - 160, belt - 240)} L{P(fax - R - 120, belt - 240)} L{P(fax - R + 10, belt - 60)} Z" fill="#151515"/>')
    # badge on the front wing: AMG (full AMG) or 'AMG Line' looks
    lab = 'AMG Line' if c.get('amgline') else ('V8 BITURBO' if key in ('GT', 'G63', 'S63') else 'AMG')
    det.append(f'<text x="{X(fax - R - 120):.1f}" y="{Y(belt - 160):.1f}" text-anchor="end" font-family="Inter" font-weight="900" font-style="italic" font-size="{62 * s:.1f}" fill="url(#chrome)" stroke="{ink}" stroke-width=".5">{lab}</text>')

    # ---------- wheels ----------
    wheels = []
    spokes = 10 if kind in ('super', 'coupe') else (6 if kind == 'box' else 5)
    for ax in (rax, fax):
        cx, cy = X(ax), Y(r)
        rr = r * s
        rim = rr * (0.7 if kind in ('super', 'coupe', 'saloon', 'fastback') else 0.66)
        g = [f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="url(#tyre)" stroke="{ink}" stroke-width="2.2"/>',
             f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{(rr + rim) / 2:.1f}" fill="none" stroke="#4a4a4a" stroke-width="{(rr - rim) * .35:.1f}" opacity=".6"/>',
             f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rim + 3:.1f}" fill="#2a2a2a"/>',
             f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rim:.1f}" fill="#3b3d40"/>']
        # brake disc + caliper behind the spokes
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rim * .82:.1f}" fill="url(#disc)" stroke="#222" stroke-width="1"/>')
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rim * .36:.1f}" fill="#3a3c3f"/>')
        if c.get('amgline'):
            g.append(f'<path d="M{cx - rim * .5:.1f},{cy - rim * .6:.1f} A{rim * .78:.1f},{rim * .78:.1f} 0 0 1 {cx + rim * .3:.1f},{cy - rim * .72:.1f} L{cx + rim * .2:.1f},{cy - rim * .5:.1f} A{rim * .54:.1f},{rim * .54:.1f} 0 0 0 {cx - rim * .35:.1f},{cy - rim * .42:.1f} Z" fill="#5a5c60" stroke="{ink}" stroke-width="1"/>')
        if not c.get('amgline'):  # red AMG calipers
            g.append(f'<path d="M{cx - rim * .55:.1f},{cy - rim * .55:.1f} A{rim * .78:.1f},{rim * .78:.1f} 0 0 1 {cx + rim * .55:.1f},{cy - rim * .55:.1f} L{cx + rim * .38:.1f},{cy - rim * .38:.1f} A{rim * .54:.1f},{rim * .54:.1f} 0 0 0 {cx - rim * .38:.1f},{cy - rim * .38:.1f} Z" fill="#d6121b" stroke="{ink}" stroke-width="1"/>')
        g.append(f'<g class="spin" data-cx="{cx:.1f}" data-cy="{cy:.1f}">')
        for k in range(spokes):
            a = 2 * math.pi * k / spokes
            for off in ((-0.17, -0.03), (0.03, 0.17)) if spokes <= 6 else ((-0.075, 0.075),):
                a0, a1 = a + off[0], a + off[1]
                x0, y0 = cx + math.cos(a0) * rim * .2, cy + math.sin(a0) * rim * .2
                x1, y1 = cx + math.cos(a1) * rim * .2, cy + math.sin(a1) * rim * .2
                x2, y2 = cx + math.cos(a1 + .06) * rim * .98, cy + math.sin(a1 + .06) * rim * .98
                x3, y3 = cx + math.cos(a0 - .06) * rim * .98, cy + math.sin(a0 - .06) * rim * .98
                g.append(f'<path d="M{x0:.1f},{y0:.1f} L{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f} L{x3:.1f},{y3:.1f} Z" fill="url(#alloy)" stroke="{ink}" stroke-width=".9"/>')
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rim * .2:.1f}" fill="url(#alloy)" stroke="{ink}" stroke-width="1"/>')
        g.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rim * .11:.1f}" ry="{rim * .08:.1f}" fill="none" stroke="#222" stroke-width="1.2"/>')
        g.append('</g>')
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rim:.1f}" fill="none" stroke="{ink}" stroke-width="1.6"/>')
        # inner arch shadow
        g.append(f'<path d="M{X(ax - dx):.1f},{Y(gc):.1f} A{R * s:.1f},{R * s:.1f} 0 0 1 {X(ax + dx):.1f},{Y(gc):.1f}" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="{(R - r) * s * 1.2:.1f}"/>')
        wheels.append(''.join(g))

    defs = f'''
<defs>
 <linearGradient id="body" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{top}"/><stop offset=".38" stop-color="{top}"/>
  <stop offset=".42" stop-color="#ffffff" stop-opacity=".9"/><stop offset=".47" stop-color="{top}"/>
  <stop offset=".78" stop-color="{bot}"/><stop offset="1" stop-color="{bot}"/>
 </linearGradient>
 <linearGradient id="bodyx" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#000" stop-opacity=".18"/><stop offset=".35" stop-color="#fff" stop-opacity=".08"/>
  <stop offset=".6" stop-color="#fff" stop-opacity=".0"/><stop offset="1" stop-color="#000" stop-opacity=".14"/>
 </linearGradient>
 <linearGradient id="glass" x1="0" y1="0" x2=".3" y2="1">
  <stop offset="0" stop-color="#5d6670"/><stop offset=".55" stop-color="#2c3238"/><stop offset="1" stop-color="#1b1f23"/>
 </linearGradient>
 <linearGradient id="chrome" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#ffffff"/><stop offset=".45" stop-color="#b9bec4"/><stop offset=".55" stop-color="#5f656c"/><stop offset="1" stop-color="#dfe3e7"/>
 </linearGradient>
 <linearGradient id="alloy" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#f4f5f6"/><stop offset=".5" stop-color="#aeb3b9"/><stop offset="1" stop-color="#6b7178"/>
 </linearGradient>
 <radialGradient id="disc"><stop offset=".45" stop-color="#4a4c50"/><stop offset=".5" stop-color="#8e9196"/><stop offset="1" stop-color="#6e7176"/></radialGradient>
 <radialGradient id="tyre"><stop offset=".6" stop-color="#2b2b2b"/><stop offset=".85" stop-color="#1a1a1a"/><stop offset="1" stop-color="#0d0d0d"/></radialGradient>
 <linearGradient id="lamp" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#eef3f8"/><stop offset="1" stop-color="#8c97a3"/></linearGradient>
 <linearGradient id="tail" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff5a5a"/><stop offset=".5" stop-color="#c3121b"/><stop offset="1" stop-color="#6d0509"/></linearGradient>
 <pattern id="mesh" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="#151515"/><rect width="3" height="3" fill="#3a3a3a"/></pattern>
 <linearGradient id="grille"><stop offset="0" stop-color="#111"/><stop offset="1" stop-color="#2d2d2d"/></linearGradient>
 <pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(-32)"><line x1="0" y1="0" x2="0" y2="7" stroke="#000" stroke-width="1.1"/></pattern>
 <pattern id="hatch2" width="11" height="11" patternUnits="userSpaceOnUse" patternTransform="rotate(58)"><line x1="0" y1="0" x2="0" y2="11" stroke="#000" stroke-width=".9"/></pattern>
 <filter id="wobble" x="-5%" y="-5%" width="110%" height="110%">
  <feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="2" seed="{abs(hash(key)) % 97}"/>
  <feDisplacementMap in="SourceGraphic" scale="2.6"/>
 </filter>
 <filter id="pencil" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="4" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.6 1.25" result="grain"/>
  <feComposite in="SourceGraphic" in2="grain" operator="in"/>
 </filter>
 <filter id="glow"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
 <clipPath id="bodyclip"><path d="{body}"/></clipPath>
 <clipPath id="dloclip"><path d="{dlo}"/></clipPath>
</defs>'''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{Ht:.0f}" viewBox="0 0 {W:.1f} {Ht:.1f}">
{defs}
<g filter="url(#wobble)">
 <path d="{body}" fill="url(#body)"/>
 <path d="{body}" fill="url(#bodyx)"/>
 <g clip-path="url(#bodyclip)">
  <rect x="0" y="0" width="{W}" height="{Ht}" fill="url(#hatch)" opacity=".16" filter="url(#pencil)"/>
  <rect x="0" y="{Y(belt - 60):.1f}" width="{W}" height="{Ht}" fill="url(#hatch2)" opacity=".18" filter="url(#pencil)"/>
  {''.join(det)}
 </g>
 <path d="{dlo}" fill="url(#glass)" stroke="{ink}" stroke-width="2"/>
 <path d="M{P(g0 - 120, belt + 60)} L{P(F(apex + 40), H_ - 80)} L{P(F(apex + 240), H_ - 80)} L{P(g0 - 280, belt + 60)} Z" fill="#fff" opacity=".16"/>
 <path d="M{P(bx - 300, belt + 40)} L{P(bx - 120, H_ - 90)} L{P(bx - 60, H_ - 90)} L{P(bx - 240, belt + 40)} Z" fill="#fff" opacity=".10"/>
 <g clip-path="url(#dloclip)"><ellipse cx="{X(bx + 330):.1f}" cy="{Y(belt + 230):.1f}" rx="{90 * s:.1f}" ry="{110 * s:.1f}" fill="#111" opacity=".55"/>
 <ellipse cx="{X(bx - 380):.1f}" cy="{Y(belt + 220):.1f}" rx="{85 * s:.1f}" ry="{105 * s:.1f}" fill="#111" opacity=".45"/></g>
 {pillars}
 {chrome}
 {mirror}
 <path d="{body}" fill="none" stroke="{ink}" stroke-width="2.6" stroke-linejoin="round"/>
 {''.join(wheels)}
 {''.join(outside)}
</g>
</svg>'''
    return svg, dict(W=W, H=Ht, pad=pad, px_per_mm=PX, ground_y=Y(0), front_x=X(L), rear_x=X(0),
                     wheels=[[X(rax), Y(r)], [X(fax), Y(r)]], wheel_r=r * s)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'cars_svg'
    os.makedirs(out, exist_ok=True)
    meta = {}
    for k, c in CARS.items():
        svg, m = car_svg(k, c)
        open(f'{out}/{k}.svg', 'w').write(svg)
        m.update(L=c['L'], Hmm=c['H'], name=c['name'], color_name=c.get('color_name'))
        meta[k] = m
    json.dump(meta, open(f'{out}/meta.json', 'w'), indent=1)
    print('wrote', len(meta))
