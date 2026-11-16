"""Cut-out puppetry on the user's own character images (no redrawing): sitting legs, raised forearm, pointing arm."""
import os, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = os.path.dirname(os.path.abspath(__file__)); CUT = os.path.join(S, 'matte', 'cut'); OUT = os.path.join(S, 'matte', 'pup')
os.makedirs(OUT, exist_ok=True)
GEOM = {  # fractions of image height / width, measured on the references
    'bf': dict(hem=0.53, knee=0.745, arm_l=0.215, arm_r=0.785, elbow=(0.105, 0.445), shoulder=(0.15, 0.27), hand_bottom=0.665),
    'gf': dict(hem=0.565, knee=0.75, arm_l=0.0, arm_r=1.0),
}


def sit(im, g, thigh_keep=0.26, spread=1.06):
    """Front-view sitting: thighs foreshortened, shins unchanged, lower arms untouched."""
    W, H = im.size; a = np.asarray(im).copy()
    yh, yk = int(g['hem'] * H) - 6, int(g['knee'] * H)
    xl, xr = int(g['arm_l'] * W), int(g['arm_r'] * W)
    arms = np.zeros_like(a); body = a.copy()
    if g['arm_l'] > 0:
        arms[yh - 40:, :xl] = a[yh - 40:, :xl]; arms[yh - 40:, xr:] = a[yh - 40:, xr:]
        body[yh - 40:, :xl] = 0; body[yh - 40:, xr:] = 0
    bimg = Image.fromarray(body)
    top = bimg.crop((0, 0, W, yh))
    th = bimg.crop((0, yh, W, yk)); th_h = max(1, int((yk - yh) * thigh_keep))
    th = th.resize((int(W * spread), th_h), Image.LANCZOS)
    shin = bimg.crop((0, yk, W, H)); shin = shin.resize((int(W * spread), int(shin.height)), Image.LANCZOS)
    newH = yh + th_h + shin.height
    out = Image.new('RGBA', (int(W * spread), newH), (0, 0, 0, 0)); ox = (out.width - W) // 2
    out.alpha_composite(top, (ox, 0))
    # knee shading: shins sit under the knee, so darken their top a little
    sh = np.asarray(shin).astype(np.float32); ramp = np.ones(sh.shape[0], np.float32)
    n = int(sh.shape[0] * 0.18); ramp[:n] = np.linspace(0.72, 1.0, n)
    sh[..., :3] *= ramp[:, None, None]
    out.alpha_composite(Image.fromarray(sh.clip(0, 255).astype(np.uint8)), (0, yh + th_h))
    t = np.asarray(th).astype(np.float32); r2 = np.linspace(1.12, 0.95, t.shape[0])
    t[..., :3] *= r2[:, None, None]
    out.alpha_composite(Image.fromarray(t.clip(0, 255).astype(np.uint8)), (0, yh))
    # lower arms/hands stay where they were (resting beside the thighs)
    am = Image.fromarray(arms).crop((0, 0, W, min(H, newH)))
    out.alpha_composite(am, (ox, 0))
    return out


def rotate_part(im, region, pivot, angle, cover=None):
    """Cut region (x0,y0,x1,y1 fractions), rotate about pivot (fractions) by angle deg (+ = counter-clockwise), paste on top."""
    W, H = im.size; a = np.asarray(im).copy()
    x0, y0, x1, y1 = [int(v * s) for v, s in zip(region, (W, H, W, H))]
    part = np.zeros_like(a); part[y0:y1, x0:x1] = a[y0:y1, x0:x1]; a[y0:y1, x0:x1] = 0
    base = Image.fromarray(a); pimg = Image.fromarray(part)
    px, py = pivot[0] * W, pivot[1] * H
    pad = max(W, H)
    canvas = Image.new('RGBA', (W + 2 * pad, H + 2 * pad), (0, 0, 0, 0)); canvas.alpha_composite(base, (pad, pad))
    big = Image.new('RGBA', canvas.size, (0, 0, 0, 0)); big.alpha_composite(pimg, (pad, pad))
    big = big.rotate(angle, resample=Image.BICUBIC, center=(px + pad, py + pad))
    if cover:  # skin disc over the joint
        d = ImageDraw.Draw(canvas); r = cover[1] * W
        d.ellipse((px + pad - r, py + pad - r, px + pad + r, py + pad + r), fill=cover[0])
    canvas.alpha_composite(big)
    bb = canvas.getbbox(); return canvas.crop(bb)


def skin_at(im, x, y):
    W, H = im.size; return im.getpixel((int(x * W), int(y * H)))


if __name__ == '__main__':
    from scipy import ndimage
    names = []
    for b in ('bf_ref', 'bf_happy', 'bf_worried', 'bf_smug', 'bf_surprised'):
        for suf in ('', '_talk', '_blink'):
            if os.path.exists(os.path.join(CUT, b + suf + '.png')):
                names.append(b + suf)
    for n in names:
        im = Image.open(os.path.join(CUT, n + '.png')).convert('RGBA'); g = GEOM['bf']
        a = np.asarray(im).copy(); W, H = im.size
        r, gg, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
        trouser = (b > r) & (r < 90) & (gg < 90)          # never move trouser pixels with the arm
        colmask = np.zeros(trouser.shape, bool); colmask[int(0.29 * H):, :int(0.215 * W)] = True
        arm_only = a.copy(); arm_only[~colmask] = 0; arm_only[trouser] = 0
        body = a.copy(); body[colmask & ~trouser] = 0
        body_img = Image.fromarray(body)
        sk = im.getpixel((int(0.105 * W), int(0.40 * H))); tee = im.getpixel((int(0.5 * W), int(0.35 * H)))
        def pose(region, pivot, angle, cover, name, hand=(0.105, 0.655)):
            ax0, ay0, ax1, ay1 = [int(v * s_) for v, s_ in zip(region, (W, H, W, H))]
            part = np.zeros_like(a); part[ay0:ay1, ax0:ax1] = arm_only[ay0:ay1, ax0:ax1]
            rest = arm_only.copy(); rest[ay0:ay1, ax0:ax1] = 0
            pad = 600; C = Image.new('RGBA', (W + 2 * pad, H + 2 * pad), (0, 0, 0, 0))
            C.alpha_composite(body_img, (pad, pad)); C.alpha_composite(Image.fromarray(rest), (pad, pad))
            px, py = pivot[0] * W + pad, pivot[1] * H + pad
            if cover:
                d = ImageDraw.Draw(C); r_ = cover[1] * W; d.ellipse((px - r_, py - r_ * cover[2], px + r_, py + r_ * cover[2]), fill=cover[0])
            P = Image.new('RGBA', C.size, (0, 0, 0, 0)); P.alpha_composite(Image.fromarray(part), (pad, pad))
            P = P.rotate(angle, resample=Image.BICUBIC, center=(px, py))
            C.alpha_composite(P)
            bb = C.getbbox(); out = np.asarray(C.crop(bb)).copy()
            al = out[..., 3] > 128
            core = ndimage.binary_opening(al, structure=np.ones((7, 7)))       # drops thin slivers
            keep = ndimage.binary_dilation(core, iterations=2)
            out[..., 3] = np.where(keep, out[..., 3], 0)
            Image.fromarray(out, 'RGBA').save(os.path.join(OUT, f'{n}_{name}.png'))
            import math, json
            hx, hy = hand[0] * W + pad, hand[1] * H + pad; th = math.radians(angle)
            rx = px + (hx - px) * math.cos(th) + (hy - py) * math.sin(th)
            ry = py - (hx - px) * math.sin(th) + (hy - py) * math.cos(th)
            jf = os.path.join(OUT, 'hands.json'); dct = json.load(open(jf)) if os.path.exists(jf) else {}
            dct[f'{n}_{name}'] = [(rx - bb[0]) / out.shape[1], (ry - bb[1]) / out.shape[0]]
            json.dump(dct, open(jf, 'w'))
        pose((0.0, 0.44, 0.215, 0.70), g['elbow'], 150, (sk, 0.045, 1.0), 'phone')
        pose((0.0, 0.28, 0.215, 0.70), (0.155, 0.285), -150, (tee, 0.07, 0.9), 'raise')
        pose((0.0, 0.28, 0.215, 0.70), (0.155, 0.285), -80, (tee, 0.07, 0.9), 'point')
        print('done', n)
