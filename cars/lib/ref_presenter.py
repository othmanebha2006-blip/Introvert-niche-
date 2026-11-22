"""@Mecmation presenter = the user's own animation clip, used as is (cars/character_mecmation/animation_reference.mov).

The grey studio background is keyed out and the clip loops seamlessly for any video length:
frame 666 matches frame 12 (mean difference 0.85/255), so frames 12..665 (654 frames, 21.8 s) repeat with no jump.
Nothing in the character or its movement is changed.
"""
import os, subprocess, glob, math
import numpy as np, cairo
from PIL import Image
from scipy import ndimage as nd

CLIP = os.path.join(os.path.dirname(__file__), "..", "character_mecmation", "animation_reference.mov")
LOOP_A, LOOP_B = 12, 665          # 1-based frame numbers, inclusive
BG = 217.0                        # the clip's grey background
CROP = (200, 0, 880, 952)         # x0, y0, x1, y1 of the character area in the clip
SCALE_REF = 0.635                 # clip px per character-image px
FEET_Y = 928.4                    # clip y of the ground under the shoes
CENTER_X = 535.5                  # clip x of the character's centre


def _key(rgb):
    im = rgb.astype(np.float32)
    lum = im.mean(2)
    close = np.abs(im - BG).max(2) < 16
    lab, n = nd.label(close)
    if n:
        sizes = nd.sum(close, lab, range(1, n + 1))
        border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
        keep = []
        objs = nd.find_objects(lab)
        for i, s in enumerate(sizes):
            if (i + 1) in border or s >= 30:
                keep.append(i + 1); continue
            if s < 4:
                continue
            # small enclosed gap (e.g. between arm and shirt): background only if it is not part of a white area
            sl = tuple(slice(max(0, q.start - 3), q.stop + 3) for q in objs[i])
            comp = lab[sl] == i + 1
            ring = nd.binary_dilation(comp, iterations=3) & ~comp
            if lum[sl][ring].max() < 235:
                keep.append(i + 1)
        bg = np.isin(lab, keep)
    else:
        bg = close
    alpha = np.where(bg, 0.0, 1.0)
    edge = nd.binary_dilation(bg, iterations=2) & ~bg
    a = np.clip((BG - lum) / (BG - 20.0), 0.0, 1.0)
    alpha[edge] = np.maximum(a[edge], 0.0)
    col = im.copy()
    ae = np.maximum(alpha[edge], 0.05)[:, None]
    col[edge] = np.clip((im[edge] - (1 - ae) * BG) / ae, 0, 255)
    return np.dstack([col, alpha * 255]).astype(np.uint8)


def prepare(cache_dir):
    """Extract the loop frames, key them, save as RGBA PNGs (done once)."""
    os.makedirs(cache_dir, exist_ok=True)
    n = LOOP_B - LOOP_A + 1
    if len(glob.glob(os.path.join(cache_dir, "k_*.png"))) == n:
        return n
    raw = os.path.join(cache_dir, "raw")
    os.makedirs(raw, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", CLIP, "-vsync", "0", os.path.join(raw, "%04d.png")], check=True)
    x0, y0, x1, y1 = CROP
    for i in range(LOOP_A, LOOP_B + 1):
        rgb = np.asarray(Image.open(os.path.join(raw, f"{i:04d}.png")).convert("RGB"))[y0:y1, x0:x1]
        Image.fromarray(_key(rgb), "RGBA").save(os.path.join(cache_dir, f"k_{i - LOOP_A:04d}.png"))
    return n


class RefPresenter:
    def __init__(self, cache_dir):
        self.dir = cache_dir
        self.n = prepare(cache_dir)

    def draw(self, ctx, f, x, ground, s_img=0.6):
        """f: video frame number. x, ground: screen centre / ground line. s_img: size in character-image scale."""
        k = s_img / SCALE_REF
        idx = f % self.n
        surf = cairo.ImageSurface.create_from_png(os.path.join(self.dir, f"k_{idx:04d}.png"))
        ctx.save()
        ctx.save(); ctx.translate(x, ground - 6); ctx.scale(1, 0.12)
        ctx.arc(0, 0, 210 * s_img, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, 0.14); ctx.fill(); ctx.restore()
        ctx.translate(x - (CENTER_X - CROP[0]) * k, ground - (FEET_Y - CROP[1]) * k)
        ctx.scale(k, k)
        ctx.set_source_surface(surf, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_GOOD)
        ctx.paint()
        ctx.restore()
