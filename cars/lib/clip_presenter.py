"""Presenter from a clip the user animated for one specific voiceover (white background, frame-synced to its audio).

usage:  P = ClipPresenter(clip_path, cache_dir);  P.draw(ctx, frame, x, ground, s_img)
The clip's frame f is shown at video frame f (same timeline as the clip's audio); after the clip ends the last
frame is held. Nothing in the character is changed: only the white background is removed.
"""
import os, glob, math, subprocess
from concurrent.futures import ProcessPoolExecutor
import numpy as np, cairo
from PIL import Image
from scipy import ndimage as nd
from skimage.morphology import convex_hull_image

# where the character sits in these 1080x1920 clips (measured: shirt bbox vs the character image)
SCALE_REF = 1.02            # clip px per character-image px
CENTER_X = 536.3            # clip x of the character centre (image x 518)
GROUND_Y = 1814.4           # clip y of the ground line (image y 1455)
CROP_Y = (330, 1850)        # rows that contain the character


def _key_white(rgb):
    im = rgb.astype(np.float32)
    lum = im.mean(2)
    white = im.min(2) > 238
    lab, n = nd.label(white)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    # body parts that may contain white (logo, teeth, beanie text, laces) - filled, plus their outline
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    red = (r > 170) & (g < 110) & (b < 110)
    skin = (r > 225) & (g > 170) & (g < 225) & (b > 120) & (b < 190)
    grey = (np.abs(r - g) < 14) & (np.abs(g - b) < 14) & (r > 80) & (r < 170)
    # convex outline of each body part (shirt, head, beanie, shoes): a white area inside one of them belongs to
    # the character (logo, teeth, text, laces) even when a hand crosses it; gaps next to the body are outside
    parts = red | skin | grey
    labp, npart = nd.label(parts)
    body = np.zeros_like(parts)
    if npart:
        sizes = nd.sum(parts, labp, range(1, npart + 1))
        objs_p = nd.find_objects(labp)
        for i, sz in enumerate(sizes):
            if sz < 400:
                continue
            sl = objs_p[i]
            body[sl] |= convex_hull_image(labp[sl] == i + 1)
    body = nd.binary_dilation(body, iterations=4)
    bg = np.zeros_like(white)
    if n:
        objs = nd.find_objects(lab)
        for i in range(n):
            k = i + 1
            if k in border:
                bg |= lab == k
                continue
            sl = objs[i]
            comp = lab[sl] == k
            inside = body[sl][comp].mean()
            if inside < 0.5:            # enclosed gap between an arm and the body -> background
                bg[sl] |= comp
    alpha = np.where(bg, 0.0, 1.0)
    edge = nd.binary_dilation(bg, iterations=2) & ~bg
    a = np.clip((255.0 - lum) / (255.0 - 25.0), 0.0, 1.0)
    alpha[edge] = a[edge]
    col = im.copy()
    ae = np.maximum(alpha[edge], 0.05)[:, None]
    col[edge] = np.clip((im[edge] - (1 - ae) * 255.0) / ae, 0, 255)
    return np.dstack([col, alpha * 255]).astype(np.uint8)


def _job(args):
    src, dst = args
    if os.path.exists(dst):
        return
    rgb = np.asarray(Image.open(src).convert("RGB"))[CROP_Y[0]:CROP_Y[1]]
    Image.fromarray(_key_white(rgb), "RGBA").save(dst, compress_level=1)


def prepare(clip, cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
    raw = os.path.join(cache_dir, "raw")
    if not os.path.isdir(raw) or not os.listdir(raw):
        os.makedirs(raw, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", clip, "-vsync", "0", os.path.join(raw, "%05d.png")], check=True)
    srcs = sorted(glob.glob(os.path.join(raw, "*.png")))
    jobs = [(s, os.path.join(cache_dir, f"k_{i:05d}.png")) for i, s in enumerate(srcs)]
    with ProcessPoolExecutor() as ex:
        list(ex.map(_job, jobs, chunksize=8))
    return len(jobs)


class ClipPresenter:
    def __init__(self, clip, cache_dir):
        self.dir = cache_dir
        self.n = prepare(clip, cache_dir)

    def draw(self, ctx, f, x, ground, s_img=0.6):
        k = s_img / SCALE_REF
        idx = min(f, self.n - 1)
        surf = cairo.ImageSurface.create_from_png(os.path.join(self.dir, f"k_{idx:05d}.png"))
        ctx.save()
        ctx.save(); ctx.translate(x, ground - 6); ctx.scale(1, 0.12)
        ctx.arc(0, 0, 210 * s_img, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, 0.14); ctx.fill(); ctx.restore()
        ctx.translate(x - CENTER_X * k, ground - (GROUND_Y - CROP_Y[0]) * k)
        ctx.scale(k, k)
        ctx.set_source_surface(surf, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_GOOD)
        ctx.paint()
        ctx.restore()
