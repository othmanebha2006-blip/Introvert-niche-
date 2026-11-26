"""Import AI-generated side-view car images (front facing right) as drop-in replacements.

For each image:
  1. remove the light (checkerboard / white) background by flood-filling from the border;
  2. crop to the car and scale it so its length matches the real car (0.4 px/mm, same as the
     drawn PNGs), keeping the whole video true-scale;
  3. find both wheels by fitting circles to the tyre bottoms, and the caliper pixels, so the
     wheels still spin while the calipers stay put;
  4. write build/png/<KEY>.png and update build/svg/meta.json.

usage: python3 import_cars.py KEY=path.png [KEY=path.png ...]
"""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PNG_PX_MM = 0.4
PAD = 80  # px around the car (matches the drawn cars' padding)
sys.path.insert(0, HERE)
from cars import CARS


def remove_bg(im):
    rgb = im.convert('RGB')
    a = np.asarray(rgb).astype(np.int16)
    h, w = a.shape[:2]
    # candidate background: bright and almost grey
    bright = a.min(2) > 228
    flat = (a.max(2) - a.min(2)) < 14
    cand = bright & flat
    mark = Image.fromarray((cand * 255).astype(np.uint8)).copy()
    # flood from every border pixel that is a candidate
    seeds = [(x, 0) for x in range(0, w, 7)] + [(x, h - 1) for x in range(0, w, 7)] + \
            [(0, y) for y in range(0, h, 7)] + [(w - 1, y) for y in range(0, h, 7)]
    for sx, sy in seeds:
        if mark.getpixel((sx, sy)) == 255:
            ImageDraw.floodfill(mark, (sx, sy), 128, thresh=0)
    bg = np.asarray(mark) == 128
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    al = Image.fromarray(alpha).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out = rgb.convert('RGBA')
    out.putalpha(al)
    return out


def fit_circle(xs, ys):
    A = np.c_[2 * xs, 2 * ys, np.ones(len(xs))]
    b = xs ** 2 + ys ** 2
    (cx, cy, c), *_ = np.linalg.lstsq(A, b, rcond=None)
    return cx, cy, np.sqrt(c + cx ** 2 + cy ** 2)


def find_wheels(rgba):
    a = np.asarray(rgba)
    al = a[..., 3] > 128
    h, w = al.shape
    bottom = np.array([np.max(np.where(al[:, x])[0]) if al[:, x].any() else -1 for x in range(w)])
    ymax = bottom.max()
    # tyres reach the ground; body/bumpers stop higher. Columns within ~12% of car height of the ground
    hh = ymax - np.min([np.min(np.where(al[:, x])[0]) for x in range(w) if al[:, x].any()])
    low = bottom > ymax - 0.12 * hh
    # two biggest runs = the two tyres
    runs, x = [], 0
    while x < w:
        if low[x]:
            s = x
            while x < w and low[x]:
                x += 1
            runs.append((s, x))
        x += 1
    runs = sorted(sorted(runs, key=lambda r: r[1] - r[0])[-2:])
    wheels = []
    for s, e in runs:
        xs = np.arange(s, e).astype(float)
        ys = bottom[s:e].astype(float)
        cx, cy, r = fit_circle(xs, ys)
        # sanity: the fit uses only the lower arc; clamp radius by run width
        r = float(np.clip(r, (e - s) / 2 * 0.9, (e - s) * 0.75))
        cy = ymax - r
        wheels.append((float(cx), float(cy), r))
    return wheels, int(ymax)


def find_wheels_geo(rgba, c):
    """Predict axles from the real front overhang + wheelbase, then refine on the tyre bottoms."""
    a = np.asarray(rgba)
    al = a[..., 3] > 128
    h, w = al.shape
    cols = np.where(al.any(0))[0]
    x_front, x_rear = cols.max(), cols.min()
    bottom = np.array([np.max(np.where(al[:, x])[0]) if al[:, x].any() else -1 for x in range(w)])
    k = (x_front - x_rear) / c['L']
    out = []
    for axle_mm in (c['fo'] + c['WB'], c['fo']):
        px = x_front - axle_mm * k
        r0 = c['r'] * k
        win = np.arange(int(px - 0.9 * r0), int(px + 0.9 * r0))
        win = win[(win >= 0) & (win < w)]
        g = bottom[win].max()
        contact = win[bottom[win] >= g - 3]
        cx = float(np.median(contact)) if len(contact) else px
        rs = []
        for dx in np.arange(0.3, 0.75, 0.05) * r0:
            for sgn in (-1, 1):
                x = int(round(cx + sgn * dx))
                if 0 <= x < w:
                    d = g - bottom[x]
                    if d > 1:
                        rs.append((dx * dx + d * d) / (2 * d))
        r = float(np.median(rs)) if rs else r0
        r = float(np.clip(r, 0.8 * r0, 1.25 * r0))
        out.append((cx, float(g - r), r, int(g)))
    ground = max(o[3] for o in out)
    return [o[:3] for o in out], ground


def main(pairs):
    meta_p = os.path.join(HERE, 'build', 'svg', 'meta.json')
    meta = json.load(open(meta_p))
    os.makedirs(os.path.join(HERE, 'build', 'png'), exist_ok=True)
    os.makedirs(os.path.join(HERE, 'build', 'png_drawn'), exist_ok=True)
    for pair in pairs:
        key, path = pair.split('=', 1)
        c = CARS[key]
        im = remove_bg(Image.open(path))
        bbox = im.getchannel('A').getbbox()
        im = im.crop(bbox)
        L_px = c['L'] * PNG_PX_MM
        k = L_px / im.width
        im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
        canvas = Image.new('RGBA', (im.width + 2 * PAD, im.height + 2 * PAD), (0, 0, 0, 0))
        canvas.alpha_composite(im, (PAD, PAD))
        wheels, ground = find_wheels_geo(canvas, c)
        # keep the drawn version for reference
        old = os.path.join(HERE, 'build', 'png', f'{key}.png')
        if os.path.exists(old) and not os.path.exists(os.path.join(HERE, 'build', 'png_drawn', f'{key}.png')):
            os.replace(old, os.path.join(HERE, 'build', 'png_drawn', f'{key}.png'))
        canvas.save(old)
        r = float(np.mean([w_[2] for w_ in wheels]))
        m = meta.get(key, {})
        # meta is stored in SVG units (= half of PNG pixels)
        m.update(W=canvas.width / 2, H=canvas.height / 2, pad=PAD / 2, px_per_mm=PNG_PX_MM / 2, ground_y=ground / 2,
                 front_x=(canvas.width - PAD) / 2, rear_x=PAD / 2, wheels=[[w_[0] / 2, w_[1] / 2] for w_ in wheels],
                 wheel_r=r / 2, L=c['L'], Hmm=c['H'], name=c['name'], color_name=c.get('color_name'), source='image', rim_frac=0.98)
        meta[key] = m
        print(f'{key}: {canvas.size}, wheels at {[(round(w_[0]), round(w_[1]), round(w_[2])) for w_ in wheels]}, ground {ground}')
    json.dump(meta, open(meta_p, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1:])
