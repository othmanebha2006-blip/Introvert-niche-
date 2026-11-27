"""Episode 1 — "Every Lexus model explained in one minute" — full compositor.

Layers (1080x1920, 30 fps):
  paper-grid background -> header + section progress bar -> badges/keycaps -> cars (true scale,
  spinning wheels, speed lines, suspension settle) -> icons/tags/stamps -> captions (word-highlight)
  -> @Mecmation character (pose stream + lip-sync from voice energy + blinks).

usage: python3 compose.py [--preview t0 t1] [--frames t,t,t]
"""
import json, math, os, random, subprocess, sys, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, 'build')
W, H, FPS = 1080, 1920, 30
random.seed(7)

FONT_BLACK = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
if not os.path.exists(FONT_BLACK):
    FONT_BLACK = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
FONT_XB = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
FONT_MONO = '/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'
if not os.path.exists(FONT_MONO):
    FONT_MONO = '/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf'


@functools.lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, size)


INK = (22, 22, 22)
YEL = (255, 210, 31)
WHITE = (255, 255, 255)
RED = (226, 35, 35)
BLUE = (40, 110, 230)
GREEN = (30, 170, 100)
TEAL = (0, 160, 170)
GOLD = (214, 166, 52)
ORANGE = (255, 122, 0)

# ---------------------------------------------------------------- timing
WORDS = json.load(open(os.path.join(HERE, 'words.json')))['words']
TEXT = [w['w'] for w in WORDS]
END = WORDS[-1]['e'] + 0.45


def at(phrase, occurrence=1):
    """Start time of the given word sequence in the script."""
    toks = phrase.split()
    n = 0
    for i in range(len(TEXT) - len(toks) + 1):
        if all(TEXT[i + j].strip('.,').lower() == toks[j].lower() for j in range(len(toks))):
            n += 1
            if n == occurrence:
                return WORDS[i]['s']
    raise KeyError(phrase)


def ease_out(x):
    x = min(max(x, 0), 1)
    return 1 - (1 - x) ** 3


def ease_back(x):
    x = min(max(x, 0), 1)
    c1, c3 = 1.9, 2.9
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


# ---------------------------------------------------------------- background
def make_background():
    bg = Image.new('RGB', (W, H), (236, 237, 239))
    d = ImageDraw.Draw(bg)
    for x in range(0, W, 27):
        d.line([(x, 0), (x, H)], fill=(226, 228, 231), width=1)
    for y in range(0, H, 27):
        d.line([(0, y), (W, y)], fill=(226, 228, 231), width=1)
    for x in range(0, W, 108):
        d.line([(x, 0), (x, H)], fill=(212, 214, 218), width=2)
    for y in range(0, H, 108):
        d.line([(0, y), (W, y)], fill=(212, 214, 218), width=2)
    a = np.asarray(bg).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.16 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.45) / (H * 0.7)) ** 2)
    noise = np.random.default_rng(3).normal(0, 2.2, (H, W, 1))
    a = np.clip(a * v[..., None] + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(a)


# ---------------------------------------------------------------- text helpers
def text_size(txt, f):
    b = f.getbbox(txt)
    return b[2] - b[0], b[3] - b[1], b


def draw_text_outline(img, xy, txt, f, fill, stroke=8, stroke_fill=INK, anchor='mm', shadow=True):
    bb = ImageDraw.Draw(img).textbbox(xy, txt, font=f, anchor=anchor, stroke_width=stroke)
    x0, y0 = int(bb[0]) - 4, int(bb[1]) - 4
    layer = Image.new('RGBA', (int(bb[2] - bb[0]) + 16, int(bb[3] - bb[1]) + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    p = (xy[0] - x0, xy[1] - y0)
    if shadow:
        d.text((p[0] + 4, p[1] + 6), txt, font=f, fill=(0, 0, 0, 90), anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0, 90))
    d.text(p, txt, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)
    paste_clip(img, layer, x0, y0)


@functools.lru_cache(None)
def keycap(label, style='dark', size=70, pad=26, minw=0):
    """Rounded 'keyboard key' badge, like a car's boot-lid lettering on a key."""
    f = font(FONT_BLACK, size)
    tw, th, bb = text_size(label, f)
    w = max(tw + pad * 2, minw, size + pad)
    h = int(size * 1.45)
    styles = {
        'dark': ((52, 55, 60), (32, 34, 38), (215, 220, 226)),
        'yellow': ((255, 214, 40), (226, 172, 0), (30, 30, 30)),
        'gold': ((236, 196, 92), (184, 135, 30), (40, 30, 10)),
        'blue': ((60, 140, 255), (24, 86, 200), (255, 255, 255)),
        'green': ((52, 200, 120), (20, 140, 76), (255, 255, 255)),
        'teal': ((40, 200, 210), (0, 130, 150), (255, 255, 255)),
        'red': ((240, 64, 56), (176, 18, 22), (255, 255, 255)),
        'white': ((255, 255, 255), (214, 218, 224), (30, 30, 30)),
        'ghost': ((236, 237, 239), (220, 222, 226), (170, 174, 180)),
    }
    top, bot, tc = styles[style]
    im = Image.new('RGBA', (w + 16, h + 22), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 14, w + 8, h + 14), radius=18, fill=(0, 0, 0, 70))         # drop shadow
    d.rounded_rectangle((4, 8, w + 4, h + 8), radius=18, fill=bot, outline=INK, width=4)  # key side
    d.rounded_rectangle((4, 4, w + 4, h - 2), radius=18, fill=top, outline=INK, width=4)  # key top
    d.rounded_rectangle((14, 10, w - 6, 22), radius=6, fill=tuple(min(255, c + 40) for c in top))
    d.text((4 + w / 2, 2 + h / 2), label, font=f, fill=tc, anchor='mm')
    return im


@functools.lru_cache(None)
def tag(label, bg=(30, 30, 30), fg=WHITE, size=40, dot=None):
    f = font(FONT_MONO, size)
    tw, th, _ = text_size(label, f)
    extra = 34 if dot else 0
    w, h = tw + 44 + extra, int(size * 1.7)
    im = Image.new('RGBA', (w + 8, h + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 8, w + 6, h + 8), radius=h // 2, fill=(0, 0, 0, 60))
    d.rounded_rectangle((2, 2, w + 2, h + 2), radius=h // 2, fill=bg, outline=INK, width=3)
    if dot:
        d.ellipse((22, h / 2 - 8, 38, h / 2 + 8), fill=dot)
    d.text((2 + (w + extra) / 2, 2 + h / 2), label, font=f, fill=fg, anchor='mm')
    return im


@functools.lru_cache(None)
def stamp(label, color=RED, size=78, angle=-8):
    f = font(FONT_BLACK, size)
    tw, th, _ = text_size(label, f)
    w, h = tw + 60, int(size * 1.6)
    im = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, w + 10, h + 10), radius=14, fill=(255, 255, 255, 235), outline=color, width=9)
    d.text((10 + w / 2, 10 + h / 2), label, font=f, fill=color, anchor='mm')
    # rubber-stamp grain
    a = np.asarray(im).copy()
    rng = np.random.default_rng(len(label))
    holes = rng.random(a.shape[:2]) < 0.06
    a[..., 3] = np.where(holes & (a[..., 3] > 0), (a[..., 3] * 0.35).astype(np.uint8), a[..., 3])
    return Image.fromarray(a).rotate(angle, expand=True, resample=Image.BICUBIC)


# ---------------------------------------------------------------- icons (sketch style)
@functools.lru_cache(None)
def icon(name, size=220):
    S = 4
    im = Image.new('RGBA', (size * S, size * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = size * S
    lw = 7 * S
    k = lambda *p: [v * s for v in p]

    def poly(pts, fill):
        d.polygon([(x * s, y * s) for x, y in pts], fill=fill, outline=INK)
        d.line([(x * s, y * s) for x, y in pts + [pts[0]]], fill=INK, width=lw, joint='curve')

    if name == 'crown':
        poly([(.1, .78), (.1, .35), (.3, .55), (.5, .22), (.7, .55), (.9, .35), (.9, .78)], (246, 196, 60))
        for x, y in [(.1, .3), (.5, .17), (.9, .3)]:
            d.ellipse(k(x - .05, y - .05, x + .05, y + .05), fill=(255, 230, 120), outline=INK, width=lw // 2)
        d.rectangle(k(.1, .7, .9, .8), fill=(214, 160, 40), outline=INK, width=lw)
    elif name == 'city':
        for x0, w_, h_ in [(.05, .18, .45), (.25, .2, .7), (.47, .16, .5), (.65, .25, .62)]:
            d.rectangle(k(x0, .9 - h_, x0 + w_, .9), fill=(120, 150, 200), outline=INK, width=lw)
            for yy in np.arange(.9 - h_ + .06, .86, .1):
                d.rectangle(k(x0 + .04, yy, x0 + w_ - .04, yy + .04), fill=(255, 230, 140))
    elif name == 'zigzag':
        d.line(k(.1, .75, .35, .4, .55, .65, .85, .25), fill=(40, 110, 230), width=lw * 2, joint='curve')
        poly([(.85, .25), (.68, .26), (.82, .4)], (40, 110, 230))
    elif name == 'sun':
        d.ellipse(k(.3, .3, .7, .7), fill=(255, 196, 40), outline=INK, width=lw)
        for i in range(10):
            a = i * math.pi / 5
            d.line(k(.5 + .28 * math.cos(a), .5 + .28 * math.sin(a), .5 + .44 * math.cos(a), .5 + .44 * math.sin(a)), fill=INK, width=lw)
    elif name == 'rocks':
        poly([(.02, .92), (.25, .45), (.42, .62), (.6, .3), (.98, .92)], (150, 140, 120))
        poly([(.55, .92), (.72, .62), (.98, .92)], (120, 112, 96))
        d.line(k(.25, .45, .33, .58), fill=INK, width=lw // 2)
    elif name == 'engine':
        d.rectangle(k(.15, .35, .8, .8), fill=(160, 166, 174), outline=INK, width=lw)
        d.rectangle(k(.3, .2, .65, .35), fill=(120, 126, 134), outline=INK, width=lw)
        d.rectangle(k(.02, .48, .15, .66), fill=(120, 126, 134), outline=INK, width=lw)
        d.rectangle(k(.8, .45, .95, .7), fill=(120, 126, 134), outline=INK, width=lw)
        for x in (.28, .45, .62):
            d.ellipse(k(x - .05, .5, x + .05, .6), fill=(80, 84, 90), outline=INK, width=lw // 2)
    elif name == 'battery':
        d.rounded_rectangle(k(.12, .25, .82, .78), radius=8 * S, fill=(40, 200, 120), outline=INK, width=lw)
        d.rectangle(k(.82, .4, .92, .62), fill=INK)
        poly([(.5, .3), (.33, .55), (.47, .55), (.42, .74), (.62, .46), (.48, .46)], (255, 230, 60))
    elif name == 'plug':
        d.line(k(.5, .95, .5, .7), fill=INK, width=lw * 2)
        d.rounded_rectangle(k(.28, .38, .72, .72), radius=10 * S, fill=(30, 170, 100), outline=INK, width=lw)
        d.rectangle(k(.35, .14, .43, .38), fill=(200, 205, 212), outline=INK, width=lw // 2)
        d.rectangle(k(.57, .14, .65, .38), fill=(200, 205, 212), outline=INK, width=lw // 2)
    elif name == 'bolt':
        poly([(.55, .05), (.2, .55), (.47, .55), (.38, .95), (.8, .4), (.53, .4)], (60, 140, 255))
    elif name == 'gauge':
        d.pieslice(k(.05, .15, .95, 1.05), 180, 360, fill=(250, 250, 250), outline=INK, width=lw)
        for i in range(9):
            a = math.pi + i * math.pi / 8
            col = RED if i >= 7 else INK
            d.line(k(.5 + .38 * math.cos(a), .6 + .38 * math.sin(a), .5 + .44 * math.cos(a), .6 + .44 * math.sin(a)), fill=col, width=lw)
        d.ellipse(k(.45, .55, .55, .65), fill=INK)
    elif name == 'fuji':
        poly([(.0, .92), (.36, .3), (.64, .3), (1.0, .92)], (90, 120, 170))
        poly([(.36, .3), (.64, .3), (.72, .44), (.6, .4), (.52, .47), (.44, .4), (.3, .42)], (255, 255, 255))
        d.ellipse(k(.7, .04, .9, .24), fill=(220, 30, 40), outline=INK, width=lw // 2)
    elif name == 'flag':
        d.line(k(.18, .95, .18, .08), fill=INK, width=lw)
        n = 5
        for i in range(n):
            for j in range(4):
                x0, y0 = .18 + i * .14, .1 + j * .1
                d.rectangle(k(x0, y0, x0 + .14, y0 + .1), fill=INK if (i + j) % 2 == 0 else WHITE)
        d.rectangle(k(.18, .1, .88, .5), outline=INK, width=lw)
    elif name == 'japan':
        d.rectangle(k(.05, .2, .95, .8), fill=WHITE, outline=INK, width=lw)
        d.ellipse(k(.36, .32, .64, .68), fill=(200, 16, 46))
    elif name == 'route':
        d.line(k(.1, .85, .3, .55, .55, .7, .75, .35, .88, .18), fill=(60, 60, 60), width=lw * 3, joint='curve')
        d.line(k(.1, .85, .3, .55, .55, .7, .75, .35, .88, .18), fill=(255, 255, 255), width=lw // 2, joint='curve')
        for (x, y), c in [((.1, .85), (40, 160, 90)), ((.88, .18), RED)]:
            d.ellipse(k(x - .07, y - .14, x + .07, y), fill=c, outline=INK, width=lw // 2)
    elif name == 'trophy':
        d.pieslice(k(.22, .02, .78, .62), 0, 180, fill=(246, 196, 60), outline=INK, width=lw)
        d.rectangle(k(.22, .1, .78, .33), fill=(246, 196, 60), outline=INK, width=lw)
        d.rectangle(k(.44, .6, .56, .78), fill=(214, 160, 40), outline=INK, width=lw)
        d.rectangle(k(.28, .78, .72, .9), fill=(120, 80, 40), outline=INK, width=lw)
        d.arc(k(.06, .12, .3, .44), 90, 270, fill=INK, width=lw)
        d.arc(k(.7, .12, .94, .44), 270, 90, fill=INK, width=lw)
    elif name == 'sofa':
        d.rounded_rectangle(k(.15, .25, .85, .62), radius=12 * S, fill=(160, 120, 90), outline=INK, width=lw)
        d.rounded_rectangle(k(.05, .45, .95, .8), radius=12 * S, fill=(185, 140, 105), outline=INK, width=lw)
        d.line(k(.12, .8, .12, .9), fill=INK, width=lw)
        d.line(k(.88, .8, .88, .9), fill=INK, width=lw)
    elif name == 'tie':
        poly([(.42, .1), (.58, .1), (.54, .24), (.46, .24)], (40, 60, 120))
        poly([(.46, .24), (.54, .24), (.64, .76), (.5, .92), (.36, .76)], (40, 60, 120))
    elif name == 'question':
        d.text((s / 2, s / 2), '?', font=font(FONT_BLACK, int(s * .8)), fill=YEL, anchor='mm', stroke_width=lw, stroke_fill=INK)
    elif name == 'sparkle':
        poly([(.5, 0), (.6, .4), (1, .5), (.6, .6), (.5, 1), (.4, .6), (0, .5), (.4, .4)], YEL)
    elif name == 'v10':
        d.rounded_rectangle(k(.05, .2, .95, .8), radius=14 * S, fill=INK)
        d.text((s / 2, s / 2), 'V10', font=font(FONT_BLACK, int(s * .4)), fill=YEL, anchor='mm')
    im = im.resize((size, size), Image.LANCZOS)
    return im


def lexus_logo(size=260):
    """Simple ellipse-L emblem drawn as chrome (stylised, not the trademark artwork)."""
    S = 4
    w, h = size * S, int(size * 0.72) * S
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, c in enumerate([(70, 74, 80), (230, 234, 238), (150, 156, 164)]):
        d.ellipse((6 * S + i * 5 * S, 6 * S + i * 5 * S, w - 6 * S - i * 5 * S, h - 6 * S - i * 5 * S), outline=c, width=(10 - i * 2) * S)
    pts = [(.40, .16), (.52, .16), (.36, .74), (.86, .74), (.82, .84), (.24, .84)]
    d.polygon([(x * w, y * h) for x, y in pts], fill=(225, 229, 234), outline=(60, 64, 70))
    d.line([(x * w, y * h) for x, y in pts + [pts[0]]], fill=(60, 64, 70), width=3 * S)
    return im.resize((size, int(size * 0.72)), Image.LANCZOS)


# ---------------------------------------------------------------- cars
CAR_META = json.load(open(os.path.join(B, 'svg', 'meta.json')))
PX_MM_RENDER = 0.4          # PNGs are rendered at 0.2 px/mm * 2x
SCALE_SINGLE = 0.172        # px per mm for hero shots -> every car is true scale vs. the others


@functools.lru_cache(None)
def car_img(key, pxmm):
    im = Image.open(os.path.join(B, 'png', f'{key}.png')).convert('RGBA')
    f = pxmm / PX_MM_RENDER
    return im.resize((int(im.width * f), int(im.height * f)), Image.LANCZOS)


@functools.lru_cache(None)
def wheel_patches(key, pxmm):
    im = car_img(key, pxmm)
    m = CAR_META[key]
    f = pxmm / PX_MM_RENDER * 2  # meta is in svg px (1x) -> png px (2x) -> scaled
    out = []
    rr = m['wheel_r'] * f
    for cx, cy in m['wheels']:
        cx, cy = cx * f, cy * f
        r = int(rr * 0.72)
        box = (int(cx - r), int(cy - r), int(cx - r) + 2 * r, int(cy - r) + 2 * r)
        patch = im.crop(box)
        mask = Image.new('L', patch.size, 0)
        ImageDraw.Draw(mask).ellipse((1, 1, 2 * r - 2, 2 * r - 2), fill=255)
        out.append((box, patch, mask, rr))
    return out


@functools.lru_cache(None)
def shadow_img(w, h):
    im = Image.new('RGBA', (w + 80, h + 60), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((40, 30, w + 40, h + 30), fill=(0, 0, 0, 95))
    return im.filter(ImageFilter.GaussianBlur(14))


def place_car(frame, key, cx, ground_y, pxmm, travelled_px=0.0, speedlines=0.0, ghost=False, alpha=1.0, bob=0.0):
    im = car_img(key, pxmm)
    m = CAR_META[key]
    f = pxmm / PX_MM_RENDER * 2
    gy = m['ground_y'] * f
    x0 = int(cx - im.width / 2)
    y0 = int(ground_y - gy)
    # ground shadow
    sw = int(im.width * 0.86)
    sh = shadow_img(sw, 26)
    paste_clip(frame, sh, int(cx - sh.width / 2), int(ground_y - sh.height / 2 + 4))
    body = im
    if travelled_px:
        body = im.copy()
        for box, patch, mask, rr in wheel_patches(key, pxmm):
            ang = -math.degrees(travelled_px / max(rr, 1))
            rp = patch.rotate(ang, resample=Image.BICUBIC)
            body.paste(rp, box[:2], mask)
    if alpha < 1:
        a = np.asarray(body).copy(); a[..., 3] = (a[..., 3] * alpha).astype(np.uint8); body = Image.fromarray(a)
    if speedlines > 0.02:
        d = ImageDraw.Draw(frame)
        rng = random.Random(int(cx) // 40)
        for i in range(7):
            yy = y0 + im.height * (0.25 + 0.1 * i) + rng.randint(-8, 8)
            ln = (120 + rng.randint(0, 160)) * speedlines
            xs = x0 + im.width * 0.96 + rng.randint(0, 60)
            d.line([(xs, yy), (xs + ln, yy)], fill=(120, 124, 130), width=5)
    paste_clip(frame, body, x0, int(y0 - bob))


def paste_clip(frame, im, x, y):
    if x >= W or y >= H or x + im.width <= 0 or y + im.height <= 0:
        return
    cx0, cy0 = max(0, -x), max(0, -y)
    cx1, cy1 = min(im.width, W - x), min(im.height, H - y)
    frame.alpha_composite(im.crop((cx0, cy0, cx1, cy1)), (x + cx0, y + cy0))


def pop(frame, im, cx, cy, t_rel, dur=0.28, scale_from=0.3):
    """Paste centred with an overshoot pop-in; t_rel = seconds since it appeared."""
    if t_rel < 0:
        return
    k = ease_back(t_rel / dur) if t_rel < dur else 1.0
    sc = scale_from + (1 - scale_from) * k
    if abs(sc - 1) > 0.01:
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR)
    paste_clip(frame, im, int(cx - im.width / 2), int(cy - im.height / 2))


# ---------------------------------------------------------------- scenes
CAR_Y = 900          # ground line for hero car
CAR_X = W // 2
BADGE_Y = 318
TAG_Y = 1000


def car_enter(t, t0, dur=0.45, dist=1200):
    """x-offset and wheel travel for a car arriving from the right."""
    p = ease_out((t - t0) / dur)
    off = (1 - p) * dist
    return off, off * 0.9 + 400, max(0.0, 1 - (t - t0) / dur)


def keyrow(frame, items, y, t, gap=14):
    """items: list of (label, style, t_appear, size). Centred row with pop-ins."""
    ims = [keycap(l, s, sz) for l, s, ta, sz in items]
    total = sum(i.width for i in ims) + gap * (len(ims) - 1)
    x = W / 2 - total / 2
    for (l, s, ta, sz), im in zip(items, ims):
        pop(frame, im, x + im.width / 2, y, t - ta)
        x += im.width + gap


def build_scenes():
    S = []  # (start, fn)

    def scene(start_phrase, occ=1):
        def deco(fn):
            S.append((at(start_phrase, occ) - 0.12 if start_phrase != 'Every' else 0.0, fn))
            return fn
        return deco

    t_two, t_kind = at('two letters'), at('kind of car')

    @scene('Every')
    def s_hook(fr, t, t0):
        logo = lexus_logo(230)
        pop(fr, logo, W / 2, 300, t + 0.3)
        st = 'dark'
        hi = lambda a: 'yellow' if t >= a else 'dark'
        keyrow(fr, [('NX', hi(t_two), -1, 64), ('450', st, -1, 64), ('h+', st, -1, 64), ('F SPORT', st, -1, 64)], 470, t)
        place_car(fr, 'NX', CAR_X, CAR_Y + 10, SCALE_SINGLE)
        tex = at('explained')
        for i, (x, y) in enumerate([(110, 400), (970, 410), (150, 600), (930, 620)]):
            if t > tex + i * 0.08:
                wob = math.sin(t * 5 + i) * 8
                pop(fr, icon('question', 90), x, y + wob, t - tex - i * 0.08)
        if at('one minute') < t < t_kind:
            pop(fr, tag('60 SECONDS', bg=RED, fg=WHITE, size=38), W / 2, 1000, t - at('one minute'))
        if t >= t_two:
            pop(fr, tag('2 LETTERS', bg=(30, 30, 30), size=36, dot=YEL), 330, 560, t - t_two)
        if t >= t_kind:
            pop(fr, tag('= TYPE OF CAR', bg=YEL, fg=INK, size=40), W / 2, 1000, t - t_kind)

    @scene('IS and ES')
    def s_saloons(fr, t, t0):
        keyrow(fr, [('IS', 'yellow', t0, 66), ('ES', 'yellow', at('ES'), 66)], BADGE_Y, t)
        sc = 0.13
        off, trav, sp = car_enter(t, t0)
        place_car(fr, 'IS', W / 2 + off, 590, sc, trav, sp)
        if t > at('ES'):
            off, trav, sp = car_enter(t, at('ES'))
            place_car(fr, 'ES', W / 2 + off, 860, sc, trav, sp)
        if t > at('saloons'):
            pop(fr, tag('SALOONS', bg=BLUE, size=44), W / 2, TAG_Y, t - at('saloons'))

    def hero(key, badge, tags, dims=True, extra=None, badge_style='yellow', start_from=None):
        def fn(fr, t, t0):
            keyrow(fr, [(badge, badge_style, t0, 72)], BADGE_Y, t)
            off, trav, sp = car_enter(t, t0)
            settle = math.sin(max(0, t - t0 - 0.45) * 14) * 6 * math.exp(-max(0, t - t0 - 0.45) * 6) if t > t0 + 0.45 else 0
            place_car(fr, key, CAR_X + off, CAR_Y, SCALE_SINGLE, trav, sp, bob=settle)
            if dims and t > t0 + 0.6:
                m = CAR_META[key]
                Lpx = m['L'] * SCALE_SINGLE
                p = ease_out((t - t0 - 0.6) / 0.4)
                d = ImageDraw.Draw(fr)
                y = CAR_Y + 40
                x0, x1 = CAR_X - Lpx / 2, CAR_X - Lpx / 2 + Lpx * p
                d.line([(x0, y), (x1, y)], fill=(90, 94, 100), width=4)
                d.line([(x0, y - 14), (x0, y + 14)], fill=(90, 94, 100), width=4)
                if p > 0.98:
                    d.line([(x1, y - 14), (x1, y + 14)], fill=(90, 94, 100), width=4)
                    lab = f"{m['L'] / 1000:.2f} m"
                    f = font(FONT_MONO, 34)
                    d.rectangle((CAR_X - 80, y - 22, CAR_X + 80, y + 22), fill=(236, 237, 239))
                    d.text((CAR_X, y), lab, font=f, fill=(60, 64, 70), anchor='mm')
            for i, (word, label, col, x, y, occ) in enumerate(tags):
                ta = at(word, occ)
                if t > ta:
                    fg = INK if col in (YEL, WHITE) else WHITE
                    pop(fr, tag(label, bg=col, fg=fg, size=40), x, y, t - ta)
            if extra:
                extra(fr, t, t0)
        return fn

    S.append((at('the IS is') - 0.1, hero('IS', 'IS', [('smaller', 'SMALLER', (30, 30, 30), 300, 500, 1), ('sportier', 'SPORTIER', RED, 780, 520, 1)])))

    def es_extra(fr, t, t0):
        if t > at('comfortable'):
            pop(fr, icon('sofa', 150), 170, 520, t - at('comfortable'))
        if t > at('executive'):
            pop(fr, icon('tie', 150), 910, 520, t - at('executive'))
    S.append((at('while the ES') - 0.1, hero('ES', 'ES', [('comfortable', 'COMFORT', BLUE, 380, 470, 1), ('executive', 'EXECUTIVE', (30, 30, 30), 720, 590, 1)], extra=es_extra)))

    def ls_extra(fr, t, t0):
        if t > at('flagship'):
            pop(fr, icon('crown', 170), W / 2, 520, t - at('flagship'))
            for i, (x, y) in enumerate([(200, 650), (880, 600), (300, 470), (800, 450)]):
                tw = 0.6 + 0.4 * math.sin(t * 6 + i * 2)
                pop(fr, icon('sparkle', int(50 * tw) + 10), x, y, t - at('flagship') - i * 0.05)
    S.append((at('LS is the') - 0.1, hero('LS', 'LS', [('luxury', 'FLAGSHIP LUXURY', GOLD, W / 2, 1000, 1)], extra=ls_extra, badge_style='gold')))

    @scene('and put an X')
    def s_x(fr, t, t0):
        tx = at('X', 1)
        items = [('?', 'ghost', t0, 72)]
        if t > tx:
            items.append(('X', 'red', tx, 72))
        else:
            items.append(('?', 'ghost', t0, 72))
        keyrow(fr, items, BADGE_Y, t)
        if t > at('the end'):
            pop(fr, tag('LAST LETTER', bg=(30, 30, 30), size=36, dot=RED), W / 2, 450, t - at('the end'))
        ts = at('SUV', 1)
        if t > ts - 0.25:
            # true-scale size comparison: all five SUVs, rear bumpers aligned, biggest at the back
            sc = 0.15
            rear = 120
            keys = ['LX', 'GX', 'RX', 'NX', 'UX']
            for i, k in enumerate(keys):
                ta = ts - 0.25 + i * 0.07
                if t > ta:
                    Lpx = CAR_META[k]['L'] * sc
                    off = (1 - ease_out((t - ta) / 0.35)) * 900
                    place_car(fr, k, rear + Lpx / 2 + 25 + off, 830, sc)
            if t > ts:
                pop(fr, tag('X = SUV', bg=ORANGE, fg=WHITE, size=48), W / 2, TAG_Y, t - ts)

    def suv(key, letter, meaning, ic, col, tags=()):
        def extra(fr, t, t0):
            tw = at(meaning.lower())
            if t > t0 + 0.3:
                pop(fr, icon(ic, 160), 150, 520, t - t0 - 0.3)
            if t > tw:
                pop(fr, tag(f'{letter} = {meaning}', bg=col, fg=WHITE if col != YEL else INK, size=42), W / 2, TAG_Y, t - tw)
        return hero(key, key, list(tags), extra=extra)

    S.append((at('UX is') - 0.1, suv('UX', 'U', 'URBAN', 'city', BLUE)))
    S.append((at('NX is', 1) - 0.1, suv('NX', 'N', 'NIMBLE', 'zigzag', TEAL)))
    S.append((at('RX is', 1) - 0.1, suv('RX', 'R', 'RADIANT', 'sun', ORANGE, [('larger', 'LARGER', (30, 30, 30), 860, 520, 1)])))
    S.append((at('GX is') - 0.1, suv('GX', 'G', 'RUGGED', 'rocks', (110, 120, 80), [('off-roader', 'OFF-ROAD', (30, 30, 30), 860, 520, 1)])))

    def lx_extra(fr, t, t0):
        if t > at('flagship', 2):
            pop(fr, icon('crown', 160), 150, 520, t - at('flagship', 2))
            pop(fr, tag('FLAGSHIP SUV', bg=GOLD, fg=INK, size=42), W / 2, TAG_Y, t - at('flagship', 2))
    S.append((at('and LX is') - 0.1, hero('LX', 'LX', [], extra=lx_extra, badge_style='gold')))

    @scene('then comes the')
    def s_num(fr, t, t0):
        items = [('RX', 'dark', t0, 70)]
        t350, t500 = at('350'), at('500', 1)
        if t > t0 + 0.2:
            items.append(('350' if t < t500 else '500', 'yellow', t350 if t < t500 else t500, 70))
        keyrow(fr, items, BADGE_Y, t)
        place_car(fr, 'RX', CAR_X, CAR_Y, SCALE_SINGLE)
        if t > at('number'):
            pop(fr, tag('THE NUMBER', bg=(30, 30, 30), size=40, dot=YEL), W / 2, TAG_Y, t - at('number'))

    @scene('which used to')
    def s_engine(fr, t, t0):
        pop(fr, icon('engine', 300), 330, 620, t - t0)
        if t > at('engine size') - 0.6:
            pop(fr, tag('3.5 L', bg=WHITE, fg=INK, size=56), 330, 850, t - at('engine size') + 0.6)
        if t > at('engine size'):
            d = ImageDraw.Draw(fr)
            p = ease_out((t - at('engine size')) / 0.3)
            d.line([(520, 620), (520 + 160 * p, 620)], fill=INK, width=12)
            if p > 0.95:
                d.polygon([(690, 620), (660, 598), (660, 642)], fill=INK)
                pop(fr, keycap('350', 'yellow', 90), 860, 620, t - at('engine size') - 0.3)
        if t > at('roughly'):
            pop(fr, tag('ROUGHLY', bg=(30, 30, 30), size=36), W / 2, 380, t - at('roughly'))

    @scene('but today it')
    def s_power(fr, t, t0):
        pop(fr, icon('engine', 210), 220, 600, t - t0)
        if t > at('powertrain') - 0.2:
            pop(fr, icon('battery', 210), W / 2, 600, t - at('powertrain') + 0.2)
            pop(fr, tag('POWERTRAIN', bg=GREEN, size=40), 380, 850, t - at('powertrain'))
        if t > at('performance'):
            pop(fr, icon('gauge', 230), 860, 600, t - at('performance'))
            pop(fr, tag('PERFORMANCE', bg=RED, size=40), 760, 940, t - at('performance'))

    def letter_scene(label, style, icons, text, col):
        def fn(fr, t, t0):
            keyrow(fr, [(label, style, t0, 120)], 430, t)
            for i, ic in enumerate(icons):
                pop(fr, icon(ic, 220), W / 2 + (i - (len(icons) - 1) / 2) * 260, 720, t - t0 - 0.15 - i * 0.1)
            pop(fr, tag(text, bg=col, size=48), W / 2, TAG_Y, t - t0 - 0.35)
        return fn

    S.append((at('an h means') - 0.1, letter_scene('h', 'blue', ['engine', 'battery'], 'HYBRID', BLUE)))
    S.append((at('h plus') - 0.1, letter_scene('h+', 'green', ['engine', 'plug'], 'PLUG-IN HYBRID', GREEN)))
    S.append((at('and e means') - 0.1, letter_scene('e', 'teal', ['battery', 'bolt'], 'FULLY ELECTRIC', TEAL)))

    @scene('so an RX')
    def s_rx500(fr, t, t0):
        items = [('RX', 'dark', t0, 70)]
        if t > at('500h'):
            items += [('500', 'yellow', at('500h'), 70), ('h', 'blue', at('500h') + 0.25, 70)]
        keyrow(fr, items, BADGE_Y, t)
        off, trav, sp = car_enter(t, t0)
        place_car(fr, 'RX', CAR_X + off, CAR_Y, SCALE_SINGLE, trav, sp)
        if t > at('hybrid SUV'):
            pop(fr, tag('HYBRID SUV', bg=BLUE, size=42), W / 2, TAG_Y, t - at('hybrid SUV'))
        if t > at('not a'):
            pop(fr, stamp('NOT 5.0 LITRES'), W / 2, 560, t - at('not a'), dur=0.18, scale_from=1.8)

    @scene("then there's F")
    def s_fsport(fr, t, t0):
        keyrow(fr, [('F SPORT', 'dark', t0, 80)], BADGE_Y, t)
        off, trav, sp = car_enter(t, t0)
        place_car(fr, 'IS', CAR_X + off, CAR_Y, SCALE_SINGLE, trav, sp)
        if t > at('look'):
            pop(fr, tag('SPORTY LOOK', bg=(30, 30, 30), size=40, dot=RED), 300, 500, t - at('look'))
        if t > at('feel', 1):
            pop(fr, tag('+ FEEL', bg=RED, size=40), 800, 520, t - at('feel', 1))
        if t > t0 + 0.6:
            pop(fr, tag('TRIM PACKAGE', bg=WHITE, fg=INK, size=40), W / 2, TAG_Y, t - t0 - 0.6)

    @scene('but F is')
    def s_f(fr, t, t0):
        keyrow(fr, [('F', 'red', t0, 120)], 400, t)
        if t > at('different'):
            pop(fr, stamp('NOT THE SAME!', color=RED, size=54, angle=6), 820, 270, t - at('different'), dur=0.18, scale_from=1.8)
        if t > at('high-performance'):
            pop(fr, icon('gauge', 240), 190, 560, t - at('high-performance'))
            pop(fr, tag('HIGH-PERFORMANCE', bg=RED, size=42), W / 2, TAG_Y, t - at('high-performance'))
        if t > at('RC F') - 0.2:
            ta = at('RC F') - 0.2
            off, trav, sp = car_enter(t, ta, dur=0.32, dist=1400)
            place_car(fr, 'RCF', CAR_X + off, CAR_Y, SCALE_SINGLE, trav, max(sp, 0.35))
            pop(fr, keycap('RC F', 'dark', 60), 860, 560, t - ta - 0.2)

    @scene('and the F comes')
    def s_fuji(fr, t, t0):
        keyrow(fr, [('F', 'red', t0 - 1, 90)], BADGE_Y, t)
        pop(fr, icon('fuji', 420), W / 2, 680, t - t0 - 0.1)
        if t > at('Speedway'):
            pop(fr, icon('flag', 170), 860, 560, t - at('Speedway'))
            pop(fr, tag('FUJI SPEEDWAY', bg=(30, 30, 30), size=44, dot=RED), W / 2, TAG_Y, t - at('Speedway'))
        if t > at('Japan'):
            pop(fr, icon('japan', 150), 190, 520, t - at('Japan'))

    @scene('Lexus also uses')
    def s_l(fr, t, t0):
        keyrow(fr, [('L', 'gold', t0, 110)], 400, t)
        if t > t0 + 0.4:
            pop(fr, icon('crown', 150), 180, 420, t - t0 - 0.4)
        if t > at('luxury-focused'):
            pop(fr, tag('L = LUXURY', bg=GOLD, fg=INK, size=48), W / 2, 560, t - at('luxury-focused'))
        sc = 0.12
        if t > at('LS and'):
            off, trav, sp = car_enter(t, at('LS and'), dur=0.35)
            place_car(fr, 'LS', W / 2 + off, 790, sc, trav, sp)
        if t > at('LS and') + 0.35:
            off, trav, sp = car_enter(t, at('LS and') + 0.35, dur=0.35)
            place_car(fr, 'LX', W / 2 + off, 960, sc, trav, sp)

    def lc_extra(fr, t, t0):
        if t > at('grand'):
            pop(fr, tag('GRAND TOURER', bg=RED, size=42), W / 2, 470, t - at('grand'))
        if t > at('coupe'):
            pop(fr, tag('2-DOOR COUPE', bg=(30, 30, 30), size=36), W / 2, 560, t - at('coupe'))
        if t > at('long journeys'):
            pop(fr, icon('route', 170), 150, 600, t - at('long journeys'))
        if t > at('sporty feel'):
            pop(fr, tag('LONG TRIPS + SPORTY', bg=BLUE, size=40), W / 2, TAG_Y, t - at('sporty feel'))
    S.append((at('while the LC') - 0.1, hero('LC', 'LC', [], extra=lc_extra)))

    def lfa_extra(fr, t, t0):
        if t > at('legendary'):
            pop(fr, tag('LEGENDARY', bg=GOLD, fg=INK, size=40), 280, 480, t - at('legendary'))
        if t > at('V10'):
            pop(fr, icon('v10', 200), 860, 470, t - at('V10'))
        if t > at('supercar'):
            pop(fr, tag('SUPERCAR', bg=RED, size=46), W / 2, TAG_Y, t - at('supercar'))
        if t > at('far beyond'):
            pop(fr, icon('trophy', 170), 150, 600, t - at('far beyond'))
            for i, (x, y) in enumerate([(240, 760), (900, 700), (720, 430)]):
                tw = 0.6 + 0.4 * math.sin(t * 7 + i * 2)
                pop(fr, icon('sparkle', int(56 * tw) + 10), x, y, t - at('far beyond') - i * 0.06)
    S.append((at('And the LFA') - 0.1, hero('LFA', 'LFA', [], extra=lfa_extra, badge_style='yellow')))

    @scene('So an NX')
    def s_recap(fr, t, t0):
        tn, t4, tf = at('NX', 2), at('450h+'), at('F Sport', 2)
        tnim, tplug, tpkg = at('nimble crossover'), at('plug-in hybrid', 2), at('package')
        hi = lambda a, s: s if t >= a else 'dark'
        keyrow(fr, [('NX', hi(tn, 'yellow'), t0, 62), ('450', hi(t4, 'yellow'), t0, 62), ('h+', hi(t4, 'green'), t0, 62), ('F SPORT', hi(tf, 'red'), t0, 62)], BADGE_Y, t)
        off, trav, sp = car_enter(t, t0)
        place_car(fr, 'NX', CAR_X + off, CAR_Y, SCALE_SINGLE, trav, sp)
        y = 470
        for ta, lab, col in [(tnim, 'NIMBLE CROSSOVER', TEAL), (tplug, 'PLUG-IN HYBRID', GREEN), (tpkg, 'F SPORT PACKAGE', RED)]:
            if t > ta:
                pop(fr, tag(lab, bg=col, size=38), W / 2, y, t - ta)
            y += 78

    @scene('and if you')
    def s_end(fr, t, t0):
        cheat_sheet(fr, t - t0)

    S.sort(key=lambda s: s[0])
    return S


def cheat_sheet(fr, tr):
    p = ease_back(tr / 0.35)
    card = Image.new('RGBA', (960, 760), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((10, 16, 950, 756), radius=36, fill=(0, 0, 0, 70))
    d.rounded_rectangle((4, 4, 944, 744), radius=36, fill=(255, 255, 255), outline=INK, width=6)
    d.rounded_rectangle((4, 4, 944, 104), radius=36, fill=(30, 30, 30))
    d.rectangle((4, 70, 944, 104), fill=(30, 30, 30))
    d.text((474, 56), 'AUDI NAMES · CHEAT SHEET', font=font(FONT_MONO, 40), fill=YEL, anchor='mm')
    rows = [
        (['A'], 'yellow', 'REGULAR CARS'),
        (['Q'], 'yellow', 'SUVs'),
        (['3', '4', '5', '6', '7', '8'], 'dark', 'HIGHER = BIGGER'),
        (['S', 'RS'], 'red', 'SPORTY · RACING'),
        (['TFSI', 'TDI', 'TFSI e', 'e-tron'], 'dark', 'ENGINE'),
        (['quattro'], 'teal', 'ALL-WHEEL DRIVE'),
    ]
    y = 160
    for keys, st, lab in rows:
        x = 40
        for k in keys:
            im = keycap(k, st, 40, pad=16)
            card.alpha_composite(im, (x, y - im.height // 2))
            x += im.width + 4
        d.text((910, y), lab, font=font(FONT_XB, 30 if len(lab) > 20 else 36), fill=INK, anchor='rm')
        y += 98
    if p < 0.999:
        card = card.resize((max(1, int(card.width * (0.4 + 0.6 * p))), max(1, int(card.height * (0.4 + 0.6 * p)))), Image.BILINEAR)
    paste_clip(fr, card, int(W / 2 - card.width / 2), int(590 - card.height / 2))
    if tr > 0.5:
        pop(fr, tag('SAVE THIS + FOLLOW @Mecmation', bg=RED, size=36), W / 2, 1010, tr - 0.5)


# ---------------------------------------------------------------- captions
KEYCOL = {
    'hybrid': (90, 170, 255), 'plug-in': (60, 220, 130), 'electric': (60, 220, 220), 'suv': ORANGE, 'suvs': ORANGE,
    'saloons': (90, 170, 255), 'saloon': (90, 170, 255), 'luxury': GOLD, 'flagship': GOLD, 'luxury-focused': GOLD,
    'f': (255, 80, 70), 'sport': (255, 80, 70), 'high-performance': (255, 80, 70), 'performance': (255, 80, 70),
    'v10': (255, 80, 70), 'supercar': (255, 80, 70), 'urban': (90, 170, 255), 'nimble': (60, 220, 220),
    'radiant': ORANGE, 'rugged': (170, 200, 110), 'off-roader': (170, 200, 110), 'fuji': (255, 80, 70),
    'follow': YEL, 'amg': (255, 80, 70), "amg's": (255, 80, 70), 'aufrecht': (90, 170, 255), 'melcher': (90, 170, 255), 'großaspach': (90, 170, 255),
    'engine': ORANGE, 'suspension': ORANGE, 'upgrades': ORANGE, 'trim': (200, 200, 200), 'wheels': (90, 170, 255), 'bumpers': (90, 170, 255),
    '35': YEL, '43': YEL, '53': YEL, '63': YEL, '55': YEL, 'v8': (255, 80, 70), 's': (255, 80, 70), 'gt': (255, 80, 70), '4matic+': (60, 220, 220),
    'all-wheel-drive': (60, 220, 220), 'all-wheel': (60, 220, 220), 'g-class': (170, 200, 110), 'glc': YEL, 'top-tier': GOLD, 'extra-powerful': (255, 80, 70), 'x': (255, 80, 70), 'h': (90, 170, 255), 'e': (60, 220, 220), '5-litre': (255, 80, 70),
}
CAPS = {'is', 'es', 'ls', 'ux', 'nx', 'rx', 'gx', 'lx', 'lc', 'rc', 'lfa', 'suv', 'suvs', 'f', 'x', 'l', 'v10'}


def caption_groups():
    groups, cur = [], []
    for i, w in enumerate(WORDS):
        cur.append(i)
        end = w['w'][-1] in ',.'
        if len(cur) == 3 or end or (i + 1 < len(WORDS) and WORDS[i + 1]['s'] - w['e'] > 0.25):
            groups.append(cur); cur = []
    if cur: groups.append(cur)
    return groups


GROUPS = caption_groups()


def display(w):
    c = w.strip('.,')
    if c in ('h', 'e'):
        return c
    if c in ('500h', '450h+'):
        return c
    return c.upper()


def draw_caption_v2(fr, t):
    g = None
    for grp in GROUPS:
        if WORDS[grp[0]]['s'] - 0.05 <= t <= WORDS[grp[-1]]['e'] + 0.12:
            g = grp
    if g is None:
        return
    words = [display(WORDS[i]['w']) for i in g]
    base = 84
    while True:
        f = font(FONT_BLACK, base)
        widths = [text_size(w_, f)[0] for w_ in words]
        space = int(base * 0.3)
        total = sum(widths) + space * (len(words) - 1) + int(base * 0.1)
        if total < 960 or base <= 52:
            break
        base -= 4
    x = W / 2 - total / 2
    y = 1032
    for i, w_, wd in zip(g, words, widths):
        active = WORDS[i]['s'] <= t
        cur = WORDS[i]['s'] <= t < (WORDS[i + 1]['s'] if i + 1 < len(WORDS) else 999)
        key = WORDS[i]['w'].strip('.,').lower()
        col = KEYCOL.get(key, YEL if cur else WHITE)
        if not active:
            col = (255, 255, 255)
        sc = 1.0
        if cur:
            k = (t - WORDS[i]['s']) / 0.12
            sc = 1.0 + 0.12 * max(0, 1 - k) if k < 1 else 1.0
        ff = font(FONT_BLACK, int(base * (1.06 if cur else 1.0)))
        alpha = 255 if active else 150
        draw_text_outline(fr, (x + wd / 2, y), w_, ff, fill=col + (alpha,), stroke=9, stroke_fill=(20, 20, 20, alpha))
        x += wd + space


# ---------------------------------------------------------------- header / progress
SECTIONS = [('A vs Q', 0), ('NUMBERS', 'and the higher'), ('S · RS', 'but the name'), ('ENGINE', 'then the letters'),
            ('QUATTRO', 'quattro is'), ('RECAP', 'so an RS')]


def draw_header(fr, t):
    d = ImageDraw.Draw(fr)
    f = font(FONT_MONO, 30)
    d.text((48, 128), 'CAR NAMES DECODED · #4', font=f, fill=(40, 42, 46), anchor='lm')
    d.text((W - 48, 128), 'AUDI', font=f, fill=(40, 42, 46), anchor='rm')
    # section progress
    y = 168
    x0, x1 = 48, W - 48
    starts = [0 if s == 0 else at(s) for _, s in SECTIONS] + [END]
    for i, (lab, _) in enumerate(SECTIONS):
        a = x0 + (x1 - x0) * starts[i] / END
        b = x0 + (x1 - x0) * starts[i + 1] / END
        d.rounded_rectangle((a + 3, y, b - 3, y + 10), radius=5, fill=(205, 208, 213))
        if t > starts[i]:
            fill_to = min(b - 3, a + 3 + (b - a - 6) * min(1, (t - starts[i]) / (starts[i + 1] - starts[i])))
            d.rounded_rectangle((a + 3, y, max(a + 13, fill_to), y + 10), radius=5, fill=RED if i < len(SECTIONS) - 1 else YEL)
        if starts[i] <= t < starts[i + 1]:
            d.text(((a + b) / 2, y + 34), lab, font=font(FONT_MONO, 24), fill=(60, 64, 70), anchor='mm')


# ---------------------------------------------------------------- character
CH = json.load(open(os.path.join(B, 'char', 'character.json')))
CH_SC = CH['scale']


@functools.lru_cache(None)
def pose_img(pid):
    return Image.open(os.path.join(B, 'char', f'pose_{pid:03d}.png')).convert('RGBA')


@functools.lru_cache(None)
def patch(name):
    im = Image.open(os.path.join(B, 'char', name)).convert('RGBA')
    return im.resize((max(1, int(im.width * CH_SC)), max(1, int(im.height * CH_SC))), Image.LANCZOS)


def voice_env():
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, 'voiceover.mp3'), '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    hop = 16000 // FPS
    n = len(a) // hop
    rms = np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(1))
    return 20 * np.log10(rms + 1e-6)


ENV = voice_env()


def mouth_track():
    """Viseme per output frame from loudness, with a 2-frame minimum hold."""
    n = int(END * FPS) + 2
    out = []
    last, hold = 'm1', 0
    rng = random.Random(11)
    for i in range(n):
        db = ENV[i] if i < len(ENV) else -90
        if db < -36: m = 'm1'
        elif db < -27: m = rng.choice(['m0', 'm2'])
        elif db < -19: m = 'm3'
        else: m = 'm4' if rng.random() < .75 else 'm3'
        if m != last and hold < 2:
            m = last
            hold += 1
        elif m != last:
            hold = 1
        else:
            hold += 1
        out.append(m); last = m
    return out


MOUTH = mouth_track()
SRC_N = len(CH['pose_of'])
SRC_DUR = SRC_N / CH['fps']


def blink_at(t):
    rng = random.Random(5)
    tt = 1.2
    while tt < t + 1:
        if tt <= t < tt + 0.12:
            return True
        tt += rng.uniform(2.4, 4.6)
    return False


def draw_character(fr, t, fi):
    # walk the source pose stream a bit slower than real time so gestures breathe
    k = int((t * SRC_DUR / max(END, 1)) * CH['fps']) % SRC_N
    pid = CH['pose_of'][k]
    cx_src = CH['poses'][str(pid)]['cx']
    im = pose_img(pid).copy()
    oy = CH['crop'][1]
    m = MOUTH[min(fi, len(MOUTH) - 1)]
    y0, y1, hw = CH['mouth_box']
    mp = patch(f'mouth_{m}.png')
    im.alpha_composite(mp, (int((cx_src - hw) * CH_SC), int((y0 - oy) * CH_SC)))
    if blink_at(t):
        y0, y1, hw = CH['eye_box']
        im.alpha_composite(patch('eyes_blink.png'), (int((cx_src - hw) * CH_SC), int((y0 - oy) * CH_SC)))
    # full body: scale the sprite so hat-to-shoes fits under the caption
    k = 0.78
    im = im.resize((int(im.width * k), int(im.height * k)), Image.BILINEAR)
    bob = math.sin(t * 2.2) * 3
    x = int(W / 2 - (cx_src * CH_SC * k))
    y = int(1062 + bob)
    paste_clip(fr, im, x, y)


# ---------------------------------------------------------------- frame
BG = None
SCENES = None


def render(t, fi):
    global BG, SCENES
    if BG is None:
        BG = make_background().convert('RGBA')
        SCENES = build_scenes()
    fr = BG.copy()
    draw_header(fr, t)
    # loop: very last frames return to the hook layout
    if t > END - 0.2:
        SCENES[0][1](fr, 0.05, 0)
    else:
        idx = max(i for i, (s, _) in enumerate(SCENES) if s <= t) if t >= SCENES[0][0] else 0
        s0, fn = SCENES[idx]
        # previous scene's car slides out to the left during the first 0.3 s
        fn(fr, t, s0)
    draw_caption(fr, t)
    draw_character(fr, t, fi)
    if t < 0.06:  # very first frame: no blank caption state
        pass
    return fr.convert('RGB')


def main():
    args = sys.argv[1:]
    if args and args[0] == '--frames':
        os.makedirs(os.path.join(B, 'frames'), exist_ok=True)
        for tt in args[1].split(','):
            t = float(tt)
            render(t, int(t * FPS)).save(os.path.join(B, 'frames', f'f_{t:06.2f}.png'))
        return
    t0, t1 = 0.0, END
    out = os.path.join(B, 'video_noaudio.mp4')
    if args and args[0] == '--preview':
        t0, t1 = float(args[1]), float(args[2]); out = os.path.join(B, 'preview.mp4')
    n0, n1 = int(t0 * FPS), int(t1 * FPS)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in range(n0, n1):
        p.stdin.write(render(fi / FPS, fi).tobytes())
        if fi % 150 == 0:
            print('frame', fi, '/', n1, flush=True)
    p.stdin.close(); p.wait()
    print('wrote', out)


if __name__ == '__main__':
    main()


# ---------------------------------------------------------------- captions v4 (house rule, 27 Nov 2026)
# Exactly the user's sample: Montserrat Black, ALL CAPS, yellow fill, thick black outline + solid black
# drop shadow (down-right), 1-3 words per chunk (<= 11 characters), punctuation kept, hard cut, no pop.
FONT_CAP = os.path.join(HERE, '..', 'fonts', 'Montserrat-Black.woff')
CAP_SIZE, CAP_Y = 76, 1032
CAP_FILL = (246, 232, 36)


def caption_chunks_v4():
    chunks, cur = [], []
    for i, w in enumerate(WORDS):
        if cur:
            joined = ' '.join(WORDS[j]['w'] for j in cur + [i])
            prev_end_punct = WORDS[cur[-1]]['w'][-1] in ',.'
            if len(cur) < 3 and len(joined) <= 11 and not prev_end_punct:
                cur.append(i)
                continue
            chunks.append(cur)
        cur = [i]
    if cur:
        chunks.append(cur)
    out = []
    for k, ch in enumerate(chunks):
        s0 = WORDS[ch[0]]['s']
        nxt = WORDS[chunks[k + 1][0]]['s'] if k + 1 < len(chunks) else WORDS[ch[-1]]['e'] + 0.4
        end = nxt if nxt - WORDS[ch[-1]]['e'] < 0.6 else WORDS[ch[-1]]['e'] + 0.3
        out.append((s0, end, ' '.join(WORDS[j]['w'] for j in ch).upper()))
    return out


CHUNKS_V4 = caption_chunks_v4()


@functools.lru_cache(maxsize=512)
def caption_img_v4(text, size=CAP_SIZE, track=-0.055):
    """Per-letter layout so the tracking can be tightened like the sample."""
    f = font(FONT_CAP, size)
    sw = max(6, int(size * 0.10))      # outline
    sh = max(4, int(size * 0.075))     # drop-shadow offset (down-right)
    xs, x = [], 0.0
    for ch in text:
        xs.append(x)
        x += f.getlength(ch) + (track * size if ch != ' ' else track * size * 0.5)
    asc, desc = f.getmetrics()
    w, h = int(x + 2 * sw + sh + 12), int(asc + desc + 2 * sw + sh + 8)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = sw + 6, sw + 4
    for layer in ('shadow', 'outline', 'fill'):
        for ch, cx in zip(text, xs):
            if ch == ' ':
                continue
            if layer == 'shadow':
                d.text((ox + cx + sh, oy + sh), ch, font=f, fill=(0, 0, 0, 255), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
            elif layer == 'outline':
                d.text((ox + cx, oy), ch, font=f, fill=(0, 0, 0, 255), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
            else:
                d.text((ox + cx, oy), ch, font=f, fill=CAP_FILL + (255,))
    return im.crop(im.getchannel('A').getbbox())


def draw_caption(fr, t):
    for s0, e0, text in CHUNKS_V4:
        if s0 - 0.03 <= t < e0:
            size = CAP_SIZE
            im = caption_img_v4(text, size)
            while im.width > 980 and size > 56:
                size -= 6
                im = caption_img_v4(text, size)
            paste_clip(fr, im, int(W / 2 - im.width / 2), int(CAP_Y - im.height / 2))
            return
