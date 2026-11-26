"""Use generated car / object IMAGES the way the reference videos do (they are AI image-model illustrations,
animated with simple moves). Gives every image the same treatment:

- background removed (transparent PNGs are used as they are; plain light backgrounds are keyed by flood fill
  from the border), trimmed to the object
- thin white "sticker" border + soft drop shadow, like the reference cars
- placed by its bottom-centre at a given width (all side-view cars at the same width = consistent scale)
- wipe(): the reference's colour/version change: image B is revealed behind a moving blue scan line over image A
  (A and B must be the same car in the same pose - generate B as an edit of A)
- wheel_blur(): spinning-wheel overlay for the driving hook (wheel centres given as fractions of the image)
"""
import os, math
import numpy as np, cairo
from PIL import Image, ImageFilter
from scipy import ndimage as nd

_CACHE = {}


def _to_surface(rgba):
    a = rgba[..., 3:4].astype(np.float32) / 255
    pre = (rgba[..., :3].astype(np.float32) * a).astype(np.uint8)
    bgra = np.dstack([pre[..., 2], pre[..., 1], pre[..., 0], rgba[..., 3]]).copy()
    h, w = bgra.shape[:2]
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    buf = np.ndarray((h, s.get_stride() // 4, 4), np.uint8, s.get_data())
    buf[:, :w] = bgra
    s.mark_dirty()
    return s


def cutout(path, tol=26, border=10, shadow=True):
    """load an image, remove a plain background, add the white sticker border + soft shadow. Cached."""
    key = (path, tol, border, shadow)
    if key in _CACHE:
        return _CACHE[key]
    im = Image.open(path).convert("RGBA")
    rgba = np.asarray(im).copy()
    if rgba[..., 3].min() > 250:                       # no transparency: key the background
        rgb = rgba[..., :3].astype(np.int16)
        corners = np.array([rgb[0, 0], rgb[0, -1], rgb[-1, 0], rgb[-1, -1]]).mean(0)
        close = np.abs(rgb - corners).max(2) < tol
        lab, n = nd.label(close)
        edge = np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]); edge = edge[edge > 0]
        bg = np.isin(lab, edge)
        alpha = np.where(bg, 0, 255).astype(np.uint8)
        alpha = np.asarray(Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.8)))
        rgba[..., 3] = alpha
    a = rgba[..., 3] > 20
    ys, xs = np.where(a)
    pad = border * 3
    y0, y1, x0, x1 = max(0, ys.min() - pad), ys.max() + pad, max(0, xs.min() - pad), xs.max() + pad
    rgba = np.pad(rgba, ((pad, pad), (pad, pad), (0, 0)))[y0:y1 + 2 * pad, x0:x1 + 2 * pad]
    obj = rgba[..., 3] > 20
    ring = nd.binary_dilation(obj, iterations=border) if border else obj
    out = np.zeros_like(rgba)
    if shadow:
        sh = np.asarray(Image.fromarray((ring * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(border * 1.2)))
        sh = np.roll(sh, border // 2 + 2, axis=0)
        out[..., 3] = (sh * 0.22).astype(np.uint8)
    white = ring.astype(np.uint8) * 255
    out[..., :3] = np.where(ring[..., None], 255, out[..., :3])
    out[..., 3] = np.maximum(out[..., 3], white)
    af = rgba[..., 3:4].astype(np.float32) / 255
    out[..., :3] = (rgba[..., :3] * af + out[..., :3] * (1 - af)).astype(np.uint8)
    out[..., 3] = np.maximum(out[..., 3], rgba[..., 3])
    s = _to_surface(out)
    _CACHE[key] = s
    return s


def draw(ctx, surf, cx, bottom, width, alpha=1.0, flip=False):
    """draw an image by its bottom-centre at a given width"""
    k = width / surf.get_width()
    ctx.save()
    ctx.translate(cx, bottom)
    ctx.scale(-k if flip else k, k)
    ctx.translate(-surf.get_width() / 2, -surf.get_height())
    ctx.set_source_surface(surf, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint_with_alpha(alpha)
    ctx.restore()
    return k


def wipe(ctx, a, b, p, cx, bottom, width, line=True):
    """version change: B revealed behind a moving blue scan line over A (p 0..1)"""
    h = a.get_height() * width / a.get_width()
    x0 = cx - width / 2
    sx = x0 + p * width
    ctx.save(); ctx.rectangle(sx, bottom - h - 50, 4000, h + 100); ctx.clip(); draw(ctx, a, cx, bottom, width); ctx.restore()
    ctx.save(); ctx.rectangle(-2000, bottom - h - 50, sx + 2000, h + 100); ctx.clip(); draw(ctx, b, cx, bottom, width); ctx.restore()
    if line and 0 < p < 1:
        g = cairo.LinearGradient(sx - 40, 0, sx + 40, 0)
        g.add_color_stop_rgba(0, 0.2, 0.6, 1, 0); g.add_color_stop_rgba(0.5, 0.25, 0.75, 1, 0.55); g.add_color_stop_rgba(1, 0.2, 0.6, 1, 0)
        ctx.set_source(g); ctx.rectangle(sx - 40, bottom - h, 80, h); ctx.fill()
        ctx.set_source_rgba(0.23, 0.65, 1, 1); ctx.set_line_width(6); ctx.move_to(sx, bottom - h - 10); ctx.line_to(sx, bottom + 6); ctx.stroke()


def wheel_blur(ctx, surf, cx, bottom, width, wheels, t):
    """wheels: [(fx, fy, fr), ...] centre + radius as fractions of the image width/height"""
    k = width / surf.get_width()
    x0 = cx - width / 2; y0 = bottom - surf.get_height() * k
    for fx, fy, fr in wheels:
        wx, wy, r = x0 + fx * width, y0 + fy * surf.get_height() * k, fr * width * 0.72
        g = cairo.RadialGradient(wx, wy, r * 0.2, wx, wy, r)
        g.add_color_stop_rgba(0, 0.8, 0.82, 0.85, 0.5); g.add_color_stop_rgba(1, 0.55, 0.58, 0.62, 0.3)
        ctx.set_source(g); ctx.arc(wx, wy, r, 0, 2 * math.pi); ctx.fill()
        for j in range(3):
            a0 = -t * 30 + j * 2.1
            ctx.new_sub_path(); ctx.arc(wx, wy, r * (0.45 + 0.17 * j), a0, a0 + 1.6)
            ctx.set_source_rgba(1, 1, 1, 0.5); ctx.set_line_width(3); ctx.stroke()
