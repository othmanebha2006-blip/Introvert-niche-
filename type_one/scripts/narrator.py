"""Narrator from the user's own images. Only the eyes and brows move:
the original eye/brow strokes are lifted off the face as sprites and re-placed."""
import numpy as np
from PIL import Image

import os
U = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'character') + '/'
# feature boxes (y0, y1, x0, x1) measured from the images, plus body centre x and feet y
POSES = {
    'hips':   dict(file='narrator_hips.png', cx=433, feet=1614,
                   eyes=[(518, 553, 351, 385), (518, 553, 491, 524)],
                   brows=[(462, 491, 332, 396), (460, 489, 464, 537)]),
    'pointL': dict(file='narrator_point_left.png', cx=540, feet=1422,
                   eyes=[(228, 275, 454, 491), (228, 275, 594, 631)],
                   brows=[(176, 206, 433, 502), (173, 203, 569, 644)]),
}
PADF = 7


def lum(a): return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def _prepare(p):
    im = np.array(Image.open(U + p['file']).convert('RGBA')).astype(np.float32)
    clean = im.copy()
    boxes = []
    for (y0, y1, x0, x1) in p['eyes'] + p['brows']:
        y0, y1, x0, x1 = y0 - PADF, y1 + PADF, x0 - PADF, x1 + PADF
        top, bot = clean[y0 - 2].copy(), clean[y1 + 2].copy()
        for y in range(y0, y1 + 1):          # vertical interpolation keeps the skin shading
            f = (y - y0) / (y1 - y0)
            clean[y, x0:x1 + 1] = top[x0:x1 + 1] * (1 - f) + bot[x0:x1 + 1] * f
        boxes.append((y0, y1, x0, x1))
    from PIL import ImageFilter
    ci = Image.fromarray(clean.astype(np.uint8)); bl = ci.filter(ImageFilter.GaussianBlur(3))
    for (y0, y1, x0, x1) in boxes:
        ci.paste(bl.crop((x0 + 2, y0 + 2, x1 - 1, y1 - 1)), (x0 + 2, y0 + 2))
    clean = np.array(ci).astype(np.float32)
    sprites = []
    for (y0, y1, x0, x1) in boxes:
        src, bg = im[y0:y1 + 1, x0:x1 + 1], clean[y0:y1 + 1, x0:x1 + 1]
        a = np.clip((lum(bg) - lum(src)) / np.maximum(lum(bg) - 18, 1), 0, 1)
        spr = np.zeros(src.shape, np.uint8)
        spr[..., :3] = 16
        spr[..., 3] = (a * 255).astype(np.uint8)
        sprites.append((Image.fromarray(spr), (x0 + x1) / 2, (y0 + y1) / 2))
    return Image.fromarray(clean.astype(np.uint8)), sprites


_prep = {}


def make(arm='hips', eyes='C', brows='N', blink=False):
    if arm not in _prep: _prep[arm] = _prepare(POSES[arm])
    base, sprites = _prep[arm]
    img = base.copy()
    (eL, ex1, ey1), (eR, ex2, ey2), (bL, bx1, by1), (bR, bx2, by2) = sprites
    ew, eh = eL.width - 2 * PADF, eL.height - 2 * PADF
    dx, dy = {'C': (0, 0), 'L': (-0.55 * ew, 0.05 * eh), 'R': (0.55 * ew, 0.05 * eh), 'U': (0, -0.22 * eh)}[eyes]
    for spr, cx, cy in ((eL, ex1, ey1), (eR, ex2, ey2)):
        s = spr
        if blink:
            s = spr.resize((spr.width, max(4, int(spr.height * 0.2))), Image.LANCZOS)
            cy = cy + eh * 0.25
        img.alpha_composite(s, (int(cx + dx - s.width / 2), int(cy + dy - s.height / 2)))
    bh = bL.height - 2 * PADF
    up = {'N': (0, 0), 'up': (0.55, 0.55), 'one': (0, 0.65), 'frown': (-0.15, -0.15)}[brows]
    for i, (spr, cx, cy) in enumerate(((bL, bx1, by1), (bR, bx2, by2))):
        s = spr
        if brows == 'frown':
            s = spr.rotate(-20 if i == 0 else 20, resample=Image.BICUBIC, expand=True)
        img.alpha_composite(s, (int(cx + dx * 0.35 - s.width / 2), int(cy - up[i] * bh - s.height / 2)))
    return img


def render(arm, eyes, brows, blink, scale):
    im = make(arm, eyes, brows, blink)
    return im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)


def anchor(arm):
    p = POSES[arm]; return p['cx'], p['feet']
